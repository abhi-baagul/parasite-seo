"""Parasite SEO AI workflow — orchestrates existing Phase 3–5 services."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.content import ContentAsset, ContentLink
from app.models.enums import ContentStatus, LinkAttribute, LinkStatus, MediaStatus, MediaType
from app.models.media import MediaAsset
from app.models.parasite_seo import ParasiteSEOJob
from app.models.user import User
from app.schemas.ai_pipeline import ConfirmRequirementsRequest, PromptAnalysisSchema
from app.services import content_generation as generation_service
from app.services import seo_enrichment
from app.services.ownership import get_owned_project, owned_project_ids
from app.storage import get_storage_provider, safe_filename
from app.utils.html_sanitize import sanitize_html
from app.utils.url_safety import slugify, validate_safe_url
from app.services import public_pages as public_page_service

DEFAULT_STEPS = {
    "prompt_analysis": "pending",
    "content_generation": "pending",
    "seo_analysis": "pending",
    "media_analysis": "pending",
    "link_analysis": "pending",
    "web_page": "pending",
    "publication": "pending",
}

ALLOWED_UPLOAD_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024


def _job_or_404(session: Session, user: User, job_id: UUID) -> ParasiteSEOJob:
    job = session.get(ParasiteSEOJob, job_id)
    if not job:
        raise NotFoundError("Parasite SEO job not found")
    ids = owned_project_ids(session, user)
    if job.project_id not in ids and job.user_id != user.id:
        raise ForbiddenError("You do not own this job")
    return job


def _set_step(job: ParasiteSEOJob, key: str, value: str) -> None:
    state = dict(job.step_state or {})
    state[key] = value
    job.step_state = state


def _public_base() -> str:
    return public_page_service.public_base_url()


def serialize_job(session: Session, job: ParasiteSEOJob) -> dict:
    from app.models.public_page import PublicPage

    content = session.get(ContentAsset, job.content_id) if job.content_id else None
    media = []
    if content:
        media = list(session.scalars(select(MediaAsset).where(MediaAsset.content_asset_id == content.id)))
    page = session.scalar(select(PublicPage).where(PublicPage.job_id == job.id))
    return {
        "id": str(job.id),
        "project_id": str(job.project_id),
        "prompt_id": str(job.prompt_id) if job.prompt_id else None,
        "content_id": str(job.content_id) if job.content_id else None,
        "original_prompt": job.original_prompt,
        "advanced_settings": job.advanced_settings or {},
        "target_link": job.target_link,
        "requirements": job.requirements,
        "step_state": job.step_state or dict(DEFAULT_STEPS),
        "status": job.status,
        "current_step": job.current_step,
        "error_message": job.error_message,
        "public_slug": job.public_slug,
        "public_url": job.public_url,
        "is_public": job.is_public,
        "published_at": job.published_at.isoformat() if job.published_at else None,
        "optimize_before": job.optimize_before,
        "optimize_after": job.optimize_after,
        "web_page": public_page_service.serialize_page(session, page) if page else None,
        "content": (
            {
                "id": str(content.id),
                "title": content.title,
                "slug": content.slug,
                "content": content.content,
                "seo_title": content.seo_title,
                "meta_description": content.meta_description,
                "word_count": content.word_count,
                "seo_score": content.seo_score,
                "quality_score": content.quality_score,
                "status": content.status,
            }
            if content
            else None
        ),
        "media": [
            {
                "id": str(m.id),
                "media_type": m.media_type,
                "url": m.url,
                "alt_text": m.alt_text,
                "caption": m.caption,
                "status": m.status,
            }
            for m in media
        ],
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


def create_job(
    session: Session,
    user: User,
    *,
    project_id: UUID,
    prompt: str,
    advanced_settings: dict | None = None,
    target_link: dict | None = None,
) -> dict:
    get_owned_project(session, user, project_id)
    text = (prompt or "").strip()
    if len(text) < 20:
        raise BadRequestError("Prompt is too short")
    link_payload = None
    if target_link and target_link.get("target_url"):
        url = validate_safe_url(str(target_link["target_url"]))
        link_payload = {
            "target_url": url,
            "anchor_text": (target_link.get("anchor_text") or "").strip() or None,
            "link_attribute": target_link.get("link_attribute") or LinkAttribute.SPONSORED.value,
        }
    job = ParasiteSEOJob(
        project_id=project_id,
        user_id=user.id,
        original_prompt=text,
        advanced_settings=advanced_settings or {},
        target_link=link_payload,
        step_state=dict(DEFAULT_STEPS),
        status="draft",
        current_step="input",
    )
    session.add(job)
    session.flush()
    return serialize_job(session, job)


def list_jobs(session: Session, user: User, *, project_id: UUID | None = None) -> tuple[list[dict], dict]:
    ids = owned_project_ids(session, user)
    filters = [ParasiteSEOJob.project_id.in_(ids)] if ids else [ParasiteSEOJob.project_id.is_(None)]
    if project_id:
        get_owned_project(session, user, project_id)
        filters = [ParasiteSEOJob.project_id == project_id]
    rows = list(
        session.scalars(
            select(ParasiteSEOJob).where(*filters).order_by(ParasiteSEOJob.created_at.desc()).limit(100)
        )
    )
    items = [serialize_job(session, row) for row in rows]
    published = sum(1 for r in rows if r.is_public)
    drafts = sum(1 for r in rows if not r.is_public)
    scores = []
    for row in rows:
        if row.content_id:
            content = session.get(ContentAsset, row.content_id)
            if content and content.seo_score is not None:
                scores.append(content.seo_score)
    stats = {
        "total_generated_pages": len(rows),
        "published_pages": published,
        "draft_pages": drafts,
        "average_seo_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "total_content": len(rows),
    }
    return items, stats


def get_job(session: Session, user: User, job_id: UUID) -> dict:
    return serialize_job(session, _job_or_404(session, user, job_id))


def analyze_job(session: Session, user: User, job_id: UUID) -> dict:
    job = _job_or_404(session, user, job_id)
    job.status = "analyzing"
    job.current_step = "analyze"
    job.error_message = None
    _set_step(job, "prompt_analysis", "running")
    session.flush()
    try:
        extras = []
        settings_map = job.advanced_settings or {}
        for key in ("language", "country", "audience", "tone", "content_type", "word_count"):
            if settings_map.get(key):
                extras.append(f"{key}: {settings_map[key]}")
        prompt_text = job.original_prompt
        if extras:
            prompt_text = prompt_text + "\n\nAdditional preferences:\n" + "\n".join(extras)
        result = generation_service.analyze_prompt(
            session,
            user,
            project_id=job.project_id,
            campaign_id=None,
            raw_prompt=prompt_text,
        )
        job.prompt_id = UUID(result["prompt_id"])
        job.requirements = result.get("requirements")
        _set_step(job, "prompt_analysis", "completed")
        job.status = "draft"
        job.current_step = "analyze"
        session.flush()
        return serialize_job(session, job)
    except Exception as exc:
        _set_step(job, "prompt_analysis", "failed")
        job.status = "failed"
        job.error_message = str(exc)[:500]
        session.flush()
        raise


def update_requirements(session: Session, user: User, job_id: UUID, requirements: dict) -> dict:
    job = _job_or_404(session, user, job_id)
    if not job.prompt_id:
        raise BadRequestError("Analyze the prompt before editing requirements")
    parsed = PromptAnalysisSchema.model_validate(requirements)
    job.requirements = parsed.model_dump(mode="json")
    session.flush()
    return serialize_job(session, job)


def generate_job(session: Session, user: User, job_id: UUID, *, stage: str | None = None) -> dict:
    """Run content generation in short stages to avoid proxy timeouts.

    stage: confirm | research | strategy | outline | write | all
    Default ``all`` runs stages sequentially (tests / direct API).
    """
    job = _job_or_404(session, user, job_id)
    if not job.prompt_id or not job.requirements:
        raise BadRequestError("Analyze and confirm requirements first")

    stages = ["confirm", "research", "strategy", "outline", "write"]
    selected = stage or "all"
    if selected not in stages and selected != "all":
        raise BadRequestError(f"Unknown generation stage: {selected}")
    to_run = stages if selected == "all" else [selected]

    job.status = "generating"
    job.current_step = "generate"
    job.error_message = None
    _set_step(job, "content_generation", "running")
    session.flush()

    try:
        content_id = job.content_id
        for step_name in to_run:
            if step_name == "confirm":
                if not content_id:
                    confirm = generation_service.confirm_requirements(
                        session,
                        user,
                        job.prompt_id,
                        ConfirmRequirementsRequest(
                            requirements=PromptAnalysisSchema.model_validate(job.requirements)
                        ),
                    )
                    content_id = UUID(confirm["content_id"])
                    job.content_id = content_id
                    session.flush()
                    pending = list(
                        session.scalars(
                            select(MediaAsset).where(
                                MediaAsset.project_id == job.project_id,
                                MediaAsset.content_asset_id.is_(None),
                                MediaAsset.prompt == f"parasite-job:{job.id}",
                            )
                        )
                    )
                    for media in pending:
                        media.content_asset_id = content_id
                continue

            if not content_id:
                raise BadRequestError("Run confirm stage before research/write")

            if step_name == "research":
                generation_service.run_research(session, user, content_id)
            elif step_name == "strategy":
                generation_service.run_strategy(session, user, content_id)
            elif step_name == "outline":
                generation_service.run_outline(session, user, content_id)
                generation_service.approve_outline(session, user, content_id, None)
            elif step_name == "write":
                generation_service.generate_content(session, user, content_id)
                session.expire_all()
                content = session.get(ContentAsset, content_id)
                assert content
                if not (content.content or "").strip():
                    raise BadRequestError("Content generation returned an empty article — retry write stage")
                if job.target_link and job.target_link.get("target_url"):
                    existing = session.scalar(
                        select(ContentLink).where(
                            ContentLink.content_asset_id == content.id,
                            ContentLink.target_url == job.target_link["target_url"],
                        )
                    )
                    if not existing:
                        session.add(
                            ContentLink(
                                content_asset_id=content.id,
                                target_url=job.target_link["target_url"],
                                anchor_text=job.target_link.get("anchor_text") or content.title[:120],
                                placement_description="Optional target link from Parasite SEO AI",
                                link_attribute=job.target_link.get("link_attribute")
                                or LinkAttribute.SPONSORED.value,
                                status=LinkStatus.PLANNED.value,
                            )
                        )
                _set_step(job, "content_generation", "completed")
                job.status = "review"
                job.current_step = "generate"

        # Intermediate stages stay generating until write completes
        if selected != "all" and selected != "write" and job.status == "generating":
            job.status = "generating"
        session.flush()
        data = serialize_job(session, job)
        data["generation_stage"] = selected
        data["generation_complete"] = bool(job.content_id and (job.step_state or {}).get("content_generation") == "completed")
        return data
    except Exception as exc:
        _set_step(job, "content_generation", "failed")
        job.status = "failed"
        job.error_message = str(exc)[:500]
        session.flush()
        raise


def seo_analyze_job(session: Session, user: User, job_id: UUID) -> dict:
    job = _job_or_404(session, user, job_id)
    if not job.content_id:
        raise BadRequestError("Generate content before SEO analysis")
    job.status = "optimizing"
    job.current_step = "seo"
    _set_step(job, "seo_analysis", "running")
    session.flush()
    try:
        generation_service.run_seo_check(session, user, job.content_id)
        generation_service.run_quality_check(session, user, job.content_id)
        seo_enrichment.analyze_seo(session, user, job.content_id)
        seo_enrichment.generate_metadata(session, user, job.content_id)
        _set_step(job, "seo_analysis", "completed")
        job.status = "review"
        session.flush()
        payload = serialize_job(session, job)
        from app.models.seo_enrichment import SEOAnalysisRecord

        seo = session.scalar(
            select(SEOAnalysisRecord)
            .where(SEOAnalysisRecord.content_asset_id == job.content_id)
            .order_by(SEOAnalysisRecord.created_at.desc())
            .limit(1)
        )
        payload["seo_analysis"] = seo.payload if seo else None
        return payload
    except Exception as exc:
        _set_step(job, "seo_analysis", "failed")
        job.status = "failed"
        job.error_message = str(exc)[:500]
        session.flush()
        raise


def optimize_job(session: Session, user: User, job_id: UUID) -> dict:
    job = _job_or_404(session, user, job_id)
    if not job.content_id:
        raise BadRequestError("Generate content before optimization")
    content = session.get(ContentAsset, job.content_id)
    assert content
    job.optimize_before = content.content
    result = generation_service.run_optimize(session, user, job.content_id)
    suggestions = result.get("suggestions") or []
    # Apply first suggestion as a full-body rewrite if provided; otherwise keep before/after from agent notes
    after = content.content
    if suggestions:
        # Build a lightweight after preview: replace first before/after pair when present in body
        for item in suggestions:
            before = item.get("before") or ""
            rewritten = item.get("after") or ""
            if before and rewritten and before in after:
                after = after.replace(before, rewritten, 1)
    job.optimize_after = after
    session.flush()
    data = serialize_job(session, job)
    data["optimization_suggestions"] = suggestions
    return data


def accept_optimize(session: Session, user: User, job_id: UUID, *, accept: bool) -> dict:
    job = _job_or_404(session, user, job_id)
    if not job.content_id or not job.optimize_after:
        raise BadRequestError("No pending optimization to accept")
    content = session.get(ContentAsset, job.content_id)
    assert content
    if accept:
        from app.services import content_studio as studio_service

        studio_service.create_content_version(
            session,
            content=content,
            user=user,
            body=content.content or "",
            change_summary="Pre-optimize snapshot (Parasite SEO AI)",
            source="manual",
        )
        content.content = sanitize_html(job.optimize_after)
        content.word_count = len(content.content.split())
        studio_service.create_content_version(
            session,
            content=content,
            user=user,
            body=content.content,
            change_summary="Accepted AI SEO optimization",
            source="ai",
        )
    job.optimize_before = None
    job.optimize_after = None
    session.flush()
    return serialize_job(session, job)


def link_analysis_job(session: Session, user: User, job_id: UUID) -> dict:
    job = _job_or_404(session, user, job_id)
    if not job.content_id:
        raise BadRequestError("Generate content before link analysis")
    _set_step(job, "link_analysis", "running")
    session.flush()
    try:
        seo_enrichment.suggest_internal_links(session, user, job.content_id)
        seo_enrichment.suggest_external_references(session, user, job.content_id)
        links = seo_enrichment.analyze_links(session, user, job.content_id)
        _set_step(job, "link_analysis", "completed")
        job.current_step = "media"
        session.flush()
        data = serialize_job(session, job)
        data["link_analysis"] = links
        return data
    except Exception as exc:
        _set_step(job, "link_analysis", "failed")
        job.error_message = str(exc)[:500]
        session.flush()
        raise


def media_analysis_job(session: Session, user: User, job_id: UUID) -> dict:
    job = _job_or_404(session, user, job_id)
    if not job.content_id:
        raise BadRequestError("Generate content before media analysis")
    _set_step(job, "media_analysis", "running")
    session.flush()
    try:
        plan = seo_enrichment.generate_media_plan(session, user, job.content_id)
        _set_step(job, "media_analysis", "completed")
        _set_step(job, "web_page", "completed")
        job.current_step = "preview"
        job.status = "ready"
        session.flush()
        data = serialize_job(session, job)
        data["media_plan"] = plan
        return data
    except Exception as exc:
        _set_step(job, "media_analysis", "failed")
        job.error_message = str(exc)[:500]
        session.flush()
        raise


def publish_job(session: Session, user: User, job_id: UUID) -> dict:
    """Legacy publish endpoint — creates/publishes via Phase 6 PublicPage engine."""
    public_page_service.publish_web_page(session, user, job_id)
    job = _job_or_404(session, user, job_id)
    _set_step(job, "publication", "completed")
    _set_step(job, "web_page", "completed")
    session.flush()
    return serialize_job(session, job)


def get_public_page(session: Session, slug: str) -> dict:
    return public_page_service.get_public_page_by_slug(session, slug)


def upload_media(
    session: Session,
    user: User,
    job_id: UUID,
    *,
    filename: str,
    content_type: str,
    data: bytes,
) -> dict:
    job = _job_or_404(session, user, job_id)
    if content_type not in ALLOWED_UPLOAD_TYPES:
        raise BadRequestError("Unsupported file type. Use JPEG, PNG, WebP, GIF, MP4, or WebM.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise BadRequestError("File exceeds 15MB limit")
    if len(data) == 0:
        raise BadRequestError("Empty file")
    ext = ALLOWED_UPLOAD_TYPES[content_type]
    key = f"uploads/{job.project_id}/{job.id}/{uuid4().hex}_{safe_filename(Path(filename).stem)}{ext}"
    storage = get_storage_provider()
    storage.put_bytes(key, data, content_type=content_type)
    media_type = MediaType.UPLOADED_IMAGE.value if content_type.startswith("image/") else MediaType.VIDEO.value
    # Served via authenticated media URL endpoint — never expose FS path.
    public_ref = f"/api/v1/parasite-seo/media-file/{key}"
    asset = MediaAsset(
        project_id=job.project_id,
        content_asset_id=job.content_id,
        media_type=media_type,
        url=public_ref,
        storage_key=key,
        prompt=f"parasite-job:{job.id}",
        alt_text=safe_filename(Path(filename).stem).replace("-", " "),
        caption=None,
        source="user_upload",
        license_information="User uploaded",
        status=MediaStatus.APPROVED.value,
    )
    session.add(asset)
    session.flush()
    return {
        "id": str(asset.id),
        "media_type": asset.media_type,
        "url": asset.url,
        "alt_text": asset.alt_text,
        "filename": filename,
        "size_bytes": len(data),
        "content_type": content_type,
    }


def get_stored_media_bytes(session: Session, key: str) -> tuple[bytes, str]:
    # Public media for published pages + auth uploads. Key validated by storage provider.
    if ".." in key or key.startswith("/"):
        raise BadRequestError("Invalid media key")
    storage = get_storage_provider()
    data = storage.get_bytes(key)
    ext = Path(key).suffix.lower()
    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
    }.get(ext, "application/octet-stream")
    return data, mime

