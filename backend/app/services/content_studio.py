"""Phase 5 Content Studio aggregate operations."""

from __future__ import annotations

import difflib
import re
from copy import deepcopy
from uuid import UUID, uuid4

from bs4 import BeautifulSoup
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.agents.section_edit_agent import SectionEditAgent, SectionEditResult
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.integrations.ai.base import AIProvider
from app.models.ai_run import AIRun
from app.models.asset_file import ContentAssetFile
from app.models.content import ContentAsset, ContentLink, ContentVersion
from app.models.enums import ContentStatus, LinkStatus
from app.models.media import MediaAsset
from app.models.pipeline import ContentResearchBrief
from app.models.quality import QualityCheck
from app.models.seo_enrichment import (
    ContentCategory,
    ContentMetadata,
    ContentTag,
    ExternalReference,
    KeywordAnalysisRecord,
    MediaSuggestion,
    SEOAnalysisRecord,
)
from app.models.user import User
from app.schemas.resources import ContentRead, ContentVersionRead
from app.services.ownership import get_owned_content, owned_project_ids
from app.storage import get_storage_provider, safe_filename
from app.services import export as export_service
from app.utils.html_sanitize import count_characters, count_words, reading_time_minutes, sanitize_html

SECTION_ACTIONS = {
    "improve",
    "rewrite",
    "expand",
    "shorten",
    "simplify",
    "change_tone",
    "fix_grammar",
    "more_concise",
    "more_detailed",
    "clarity",
    "add_examples",
}


def _next_version_number(session: Session, content_id: UUID) -> int:
    latest = session.scalar(
        select(func.max(ContentVersion.version_number)).where(ContentVersion.content_asset_id == content_id)
    )
    return int(latest or 0) + 1


def create_content_version(
    session: Session,
    *,
    content: ContentAsset,
    user: User,
    body: str,
    change_summary: str | None,
    source: str = "manual",
) -> ContentVersion:
    version = ContentVersion(
        content_asset_id=content.id,
        version_number=_next_version_number(session, content.id),
        content=body,
        change_summary=change_summary,
        source=source,
        created_by=user.id,
    )
    session.add(version)
    session.flush()
    return version


def completeness_checklist(content: ContentAsset, *, links: list[ContentLink], media: list[MediaAsset]) -> list[dict]:
    soup = BeautifulSoup(content.content or "", "html.parser")
    text = soup.get_text(" ", strip=True).lower()
    headings = {tag.name for tag in soup.find_all(["h1", "h2", "h3"])}
    has_table = bool(soup.find("table"))
    has_list = bool(soup.find(["ul", "ol"]))
    has_img = bool(soup.find("img")) or any(m.media_type and "image" in m.media_type for m in media)
    has_video = bool(soup.find("iframe")) or any(m.media_type and "video" in (m.media_type or "") for m in media)
    has_cta = bool(soup.select("[data-cta], .cta-block"))
    imgs = soup.find_all("img")
    alt_ok = all((img.get("alt") or "").strip() for img in imgs) if imgs else False
    target_links = [l for l in links if l.status != LinkStatus.REMOVED.value]
    internal = [l for l in target_links if "internal" in (l.placement_description or "").lower()]
    external = [l for l in target_links if l not in internal]

    def row(key: str, label: str, ok: bool, warn: bool = False) -> dict:
        status = "complete" if ok else ("warning" if warn else "missing")
        return {"key": key, "label": label, "status": status}

    return [
        row("h1", "H1", "h1" in headings),
        row("h2", "H2", "h2" in headings),
        row("h3", "H3", "h3" in headings, warn=True),
        row("intro", "Introduction", bool(soup.find("p"))),
        row("primary_kw", "Primary keyword signal", bool(text), warn=True),
        row("table", "Table", has_table, warn=True),
        row("bullets", "Bullets / lists", has_list, warn=True),
        row("cta", "CTA", has_cta, warn=True),
        row("target_link", "Links", bool(target_links), warn=True),
        row("internal_links", "Internal links", bool(internal), warn=True),
        row("external_refs", "External references", bool(external), warn=True),
        row("images", "Images", has_img, warn=True),
        row("alt_text", "Image alt text", alt_ok if imgs else False, warn=not imgs),
        row("video", "Video", has_video, warn=True),
        row("seo_title", "SEO title", bool(content.seo_title)),
        row("meta_description", "Meta description", bool(content.meta_description)),
    ]


def extract_outline(html: str) -> list[dict]:
    soup = BeautifulSoup(html or "", "html.parser")
    outline = []
    for idx, tag in enumerate(soup.find_all(["h1", "h2", "h3"])):
        text = tag.get_text(" ", strip=True)
        if not text:
            continue
        anchor = f"heading-{idx}-{re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:40]}"
        tag["id"] = tag.get("id") or anchor
        outline.append({"level": int(tag.name[1]), "text": text, "anchor": tag["id"]})
    return outline


def get_studio_payload(session: Session, user: User, content_id: UUID) -> dict:
    content = get_owned_content(session, user, content_id)
    versions = list(
        session.scalars(
            select(ContentVersion)
            .where(ContentVersion.content_asset_id == content.id)
            .order_by(ContentVersion.version_number.desc())
            .limit(50)
        )
    )
    links = list(session.scalars(select(ContentLink).where(ContentLink.content_asset_id == content.id)))
    media = list(session.scalars(select(MediaAsset).where(MediaAsset.content_asset_id == content.id)))
    tags = list(session.scalars(select(ContentTag).where(ContentTag.content_asset_id == content.id)))
    categories = list(
        session.scalars(select(ContentCategory).where(ContentCategory.content_asset_id == content.id))
    )
    metadata = session.scalar(select(ContentMetadata).where(ContentMetadata.content_asset_id == content.id))
    seo = session.scalar(
        select(SEOAnalysisRecord)
        .where(SEOAnalysisRecord.content_asset_id == content.id)
        .order_by(SEOAnalysisRecord.created_at.desc())
        .limit(1)
    )
    keywords = session.scalar(
        select(KeywordAnalysisRecord)
        .where(KeywordAnalysisRecord.content_asset_id == content.id)
        .order_by(KeywordAnalysisRecord.created_at.desc())
        .limit(1)
    )
    quality_rows = list(
        session.scalars(
            select(QualityCheck)
            .where(QualityCheck.content_asset_id == content.id)
            .order_by(QualityCheck.created_at.desc())
            .limit(20)
        )
    )
    research = session.scalar(
        select(ContentResearchBrief)
        .where(ContentResearchBrief.content_asset_id == content.id)
        .order_by(ContentResearchBrief.version_number.desc())
        .limit(1)
    )
    refs = list(
        session.scalars(select(ExternalReference).where(ExternalReference.content_asset_id == content.id))
    )
    media_suggestions = list(
        session.scalars(select(MediaSuggestion).where(MediaSuggestion.content_asset_id == content.id))
    )
    ai_runs = list(
        session.scalars(
            select(AIRun)
            .where(AIRun.content_asset_id == content.id)
            .order_by(AIRun.created_at.desc())
            .limit(50)
        )
    )

    # Never claim published unless a published status is real; UI should not invent publishing.
    status = content.status
    if status == ContentStatus.PUBLISHED.value:
        # Keep as-is only if status already published (Phase 6 will gate this properly).
        pass

    html = content.content or ""
    return {
        "content": ContentRead.model_validate(content).model_dump(mode="json"),
        "metadata": {
            "seo_title": (metadata.seo_title if metadata else None) or content.seo_title,
            "meta_description": (metadata.meta_description if metadata else None) or content.meta_description,
            "slug": (metadata.slug if metadata else None) or content.slug,
            "canonical_url": metadata.canonical_url if metadata else None,
            "og_title": metadata.og_title if metadata else None,
            "og_description": metadata.og_description if metadata else None,
            "og_image": metadata.og_image if metadata else None,
            "twitter_title": metadata.twitter_title if metadata else None,
            "twitter_description": metadata.twitter_description if metadata else None,
            "title_options": metadata.title_options if metadata else [],
            "meta_options": metadata.meta_options if metadata else [],
        },
        "keywords": keywords.payload if keywords else None,
        "tags": [{"id": str(t.id), "name": t.name, "is_accepted": t.is_accepted} for t in tags],
        "categories": [{"id": str(c.id), "name": c.name, "is_accepted": c.is_accepted} for c in categories],
        "links": [
            {
                "id": str(link.id),
                "target_url": link.target_url,
                "anchor_text": link.anchor_text,
                "placement_description": link.placement_description,
                "link_attribute": link.link_attribute,
                "status": link.status,
            }
            for link in links
        ],
        "media": [
            {
                "id": str(m.id),
                "media_type": m.media_type,
                "url": m.url,
                "alt_text": m.alt_text,
                "caption": m.caption,
                "source": m.source,
                "license_information": m.license_information,
                "status": m.status,
                "storage_key": m.storage_key,
            }
            for m in media
        ],
        "media_suggestions": [
            {
                "id": str(s.id),
                "media_type": s.media_type,
                "placement": s.placement,
                "purpose": s.purpose,
                "description": s.description,
                "alt_text": s.alt_text,
                "caption": s.caption,
                "embed_url": s.embed_url,
                "status": s.status,
            }
            for s in media_suggestions
        ],
        "quality": [
            {
                "id": str(q.id),
                "check_type": q.check_type,
                "status": q.status,
                "score": q.score,
                "issues": q.issues,
                "recommendations": q.recommendations,
                "created_at": q.created_at.isoformat() if q.created_at else None,
            }
            for q in quality_rows
        ],
        "seo_analysis": seo.payload if seo else None,
        "research": {
            "exists": research is not None,
            "version_number": research.version_number if research else None,
            "payload": research.payload if research else None,
        },
        "references": [
            {
                "id": str(r.id),
                "title": r.anchor_suggestion,
                "url": r.url,
                "source_type": r.source_type,
                "status": r.status,
                "notes": r.reason,
                "requires_verification": r.requires_verification,
            }
            for r in refs
        ],
        "ai_runs": [
            {
                "id": str(run.id),
                "agent_type": run.agent_type,
                "status": run.status,
                "model": run.model,
                "input_tokens": run.input_tokens,
                "output_tokens": run.output_tokens,
                "total_tokens": run.total_tokens,
                "estimated_cost": float(run.estimated_cost) if run.estimated_cost is not None else None,
                "duration_ms": run.execution_time_ms,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "input_summary": run.input_summary,
            }
            for run in ai_runs
        ],
        "versions": [
            {
                "id": str(v.id),
                "version_number": v.version_number,
                "change_summary": v.change_summary,
                "source": getattr(v, "source", "manual"),
                "created_by": str(v.created_by) if v.created_by else None,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "content_length": len(v.content or ""),
            }
            for v in versions
        ],
        "outline": extract_outline(html),
        "stats": {
            "word_count": content.word_count or count_words(html),
            "character_count": count_characters(html),
            "reading_time_minutes": reading_time_minutes(html),
            "reading_speed_wpm": 200,
        },
        "completeness": completeness_checklist(content, links=links, media=media),
        "status": status,
    }


def save_content_draft(
    session: Session,
    user: User,
    content_id: UUID,
    *,
    title: str | None = None,
    slug: str | None = None,
    content_html: str | None = None,
    seo_title: str | None = None,
    meta_description: str | None = None,
    status: str | None = None,
) -> ContentRead:
    content = get_owned_content(session, user, content_id)
    if title is not None:
        content.title = title.strip()
    if slug is not None:
        clash = session.scalar(
            select(ContentAsset).where(
                ContentAsset.project_id == content.project_id,
                ContentAsset.slug == slug,
                ContentAsset.id != content.id,
            )
        )
        if clash:
            raise ConflictError("A content asset with this slug already exists in the project")
        content.slug = slug
    if content_html is not None:
        content.content = sanitize_html(content_html)
        content.word_count = count_words(content.content)
    if seo_title is not None:
        content.seo_title = seo_title
    if meta_description is not None:
        content.meta_description = meta_description
    if status is not None:
        allowed = {
            ContentStatus.DRAFT.value,
            ContentStatus.REVIEW.value,
            ContentStatus.APPROVED.value,
            ContentStatus.ARCHIVED.value,
            ContentStatus.FAILED.value,
        }
        # Do not allow UI to set published/scheduled in Phase 5.
        if status == ContentStatus.PUBLISHED.value:
            raise BadRequestError("Publishing is not available in Phase 5")
        if status == ContentStatus.SCHEDULED.value:
            raise BadRequestError("Scheduling is not available in Phase 5")
        if status not in allowed and status != content.status:
            # Allow keeping pipeline statuses already set by agents.
            if status not in {s.value for s in ContentStatus}:
                raise BadRequestError("Invalid status")
        content.status = status
    session.flush()
    return ContentRead.model_validate(content)


def restore_version(session: Session, user: User, content_id: UUID, version_id: UUID) -> dict:
    content = get_owned_content(session, user, content_id)
    version = session.get(ContentVersion, version_id)
    if not version or version.content_asset_id != content.id:
        raise NotFoundError("Content version not found")
    # Snapshot current before restore
    create_content_version(
        session,
        content=content,
        user=user,
        body=content.content or "",
        change_summary=f"Pre-restore snapshot (before v{version.version_number})",
        source="manual",
    )
    content.content = version.content
    content.word_count = count_words(version.content)
    if content.status == ContentStatus.ARCHIVED.value:
        content.status = ContentStatus.REVIEW.value
    new_version = create_content_version(
        session,
        content=content,
        user=user,
        body=version.content,
        change_summary=f"Restored from version {version.version_number}",
        source="restore",
    )
    session.flush()
    return {
        "content": ContentRead.model_validate(content).model_dump(mode="json"),
        "restored_from": version.version_number,
        "new_version": ContentVersionRead.model_validate(new_version).model_dump(mode="json"),
    }


def compare_versions(session: Session, user: User, content_id: UUID, left_id: UUID, right_id: UUID) -> dict:
    get_owned_content(session, user, content_id)
    left = session.get(ContentVersion, left_id)
    right = session.get(ContentVersion, right_id)
    if not left or left.content_asset_id != content_id:
        raise NotFoundError("Left version not found")
    if not right or right.content_asset_id != content_id:
        raise NotFoundError("Right version not found")
    left_lines = (left.content or "").splitlines()
    right_lines = (right.content or "").splitlines()
    diff = list(
        difflib.unified_diff(
            left_lines,
            right_lines,
            fromfile=f"v{left.version_number}",
            tofile=f"v{right.version_number}",
            lineterm="",
        )
    )
    matcher = difflib.SequenceMatcher(a=left.content or "", b=right.content or "")
    return {
        "left": {
            "id": str(left.id),
            "version_number": left.version_number,
            "content": left.content,
        },
        "right": {
            "id": str(right.id),
            "version_number": right.version_number,
            "content": right.content,
        },
        "unified_diff": diff,
        "ratio": round(matcher.ratio(), 4),
    }


def duplicate_content(session: Session, user: User, content_id: UUID) -> ContentRead:
    source = get_owned_content(session, user, content_id)
    base_slug = f"{source.slug}-copy"
    slug = base_slug
    n = 1
    while session.scalar(
        select(ContentAsset).where(ContentAsset.project_id == source.project_id, ContentAsset.slug == slug)
    ):
        n += 1
        slug = f"{base_slug}-{n}"
    clone = ContentAsset(
        project_id=source.project_id,
        campaign_id=source.campaign_id,
        prompt_id=None,
        title=f"{source.title} (Copy)",
        slug=slug,
        content=source.content,
        seo_title=source.seo_title,
        meta_description=source.meta_description,
        structured_body=deepcopy(source.structured_body) if source.structured_body else None,
        content_type=source.content_type,
        status=ContentStatus.DRAFT.value,
        word_count=source.word_count,
        seo_score=source.seo_score,
        quality_score=source.quality_score,
    )
    session.add(clone)
    session.flush()
    create_content_version(
        session,
        content=clone,
        user=user,
        body=clone.content or "",
        change_summary=f"Duplicated from {source.id}",
        source="manual",
    )
    # Copy metadata record if present
    meta = session.scalar(select(ContentMetadata).where(ContentMetadata.content_asset_id == source.id))
    if meta:
        session.add(
            ContentMetadata(
                content_asset_id=clone.id,
                seo_title=meta.seo_title,
                meta_description=meta.meta_description,
                slug=clone.slug,
                canonical_url=None,
                og_title=meta.og_title,
                og_description=meta.og_description,
                og_image=meta.og_image,
                twitter_title=meta.twitter_title,
                twitter_description=meta.twitter_description,
                title_options=list(meta.title_options or []),
                meta_options=list(meta.meta_options or []),
            )
        )
    for tag in session.scalars(select(ContentTag).where(ContentTag.content_asset_id == source.id, ContentTag.is_accepted.is_(True))):
        session.add(ContentTag(content_asset_id=clone.id, name=tag.name, source=tag.source, is_accepted=True))
    for link in session.scalars(select(ContentLink).where(ContentLink.content_asset_id == source.id)):
        session.add(
            ContentLink(
                content_asset_id=clone.id,
                target_url=link.target_url,
                anchor_text=link.anchor_text,
                placement_description=link.placement_description,
                link_attribute=link.link_attribute,
                status=LinkStatus.PLANNED.value,
            )
        )
    for media in session.scalars(select(MediaAsset).where(MediaAsset.content_asset_id == source.id)):
        session.add(
            MediaAsset(
                project_id=clone.project_id,
                content_asset_id=clone.id,
                media_type=media.media_type,
                url=media.url,
                storage_key=media.storage_key,
                prompt=media.prompt,
                alt_text=media.alt_text,
                caption=media.caption,
                source=media.source,
                license_information=media.license_information,
                status=media.status,
            )
        )
    session.flush()
    return ContentRead.model_validate(clone)


def apply_section_edit(
    session: Session,
    user: User,
    content_id: UUID,
    *,
    selected_html: str,
    action: str,
    tone: str | None = None,
    instruction: str | None = None,
    accept: bool = True,
    full_html: str | None = None,
    provider: AIProvider | None = None,
) -> dict:
    content = get_owned_content(session, user, content_id)
    action_key = (action or "improve").strip().lower().replace(" ", "_")
    if action_key not in SECTION_ACTIONS:
        raise BadRequestError(f"Unsupported AI action: {action}")
    selected = (selected_html or "").strip()
    if not selected:
        raise BadRequestError("Select content before running an AI section edit")
    if len(selected) > 20_000:
        raise BadRequestError("Selected content is too large for section edit")

    parsed, run = SectionEditAgent(provider=provider).run(
        session,
        project_id=content.project_id,
        content_asset_id=content.id,
        action=action_key,
        selected_html=selected,
        tone=tone,
        instruction=instruction,
    )
    assert isinstance(parsed, SectionEditResult)
    rewritten = sanitize_html(parsed.html)
    result = {
        "selected_html": selected,
        "rewritten_html": rewritten,
        "notes": parsed.notes,
        "ai_run_id": str(run.id),
        "accepted": False,
    }
    if not accept:
        return result

    body = full_html if full_html is not None else (content.content or "")
    if selected not in body:
        # Try sanitized match
        body_sanitized = sanitize_html(body)
        if selected not in body_sanitized:
            raise BadRequestError("Selected HTML was not found in the article — reselect and retry")
        body = body_sanitized
    updated = body.replace(selected, rewritten, 1)
    create_content_version(
        session,
        content=content,
        user=user,
        body=content.content or "",
        change_summary="Pre-AI section edit snapshot",
        source="manual",
    )
    content.content = sanitize_html(updated)
    content.word_count = count_words(content.content)
    new_v = create_content_version(
        session,
        content=content,
        user=user,
        body=content.content,
        change_summary=f"AI section edit: {action_key}",
        source="ai",
    )
    session.flush()
    result["accepted"] = True
    result["content"] = ContentRead.model_validate(content).model_dump(mode="json")
    result["version"] = ContentVersionRead.model_validate(new_v).model_dump(mode="json")
    return result


def search_content(
    session: Session,
    user: User,
    pagination,
    *,
    project_id: UUID | None = None,
    campaign_id: UUID | None = None,
    status: str | None = None,
    content_type: str | None = None,
    q: str | None = None,
) -> tuple[list[ContentRead], int]:
    ids = owned_project_ids(session, user)
    filters = [ContentAsset.project_id.in_(ids)] if ids else [ContentAsset.project_id.is_(None)]
    if project_id:
        from app.services.ownership import get_owned_project

        get_owned_project(session, user, project_id)
        filters = [ContentAsset.project_id == project_id]
    if campaign_id:
        filters.append(ContentAsset.campaign_id == campaign_id)
    if status:
        filters.append(ContentAsset.status == status)
    if content_type:
        filters.append(ContentAsset.content_type == content_type)
    if q:
        like = f"%{q.strip()}%"
        filters.append(
            or_(
                ContentAsset.title.ilike(like),
                ContentAsset.slug.ilike(like),
                ContentAsset.content.ilike(like),
                ContentAsset.seo_title.ilike(like),
            )
        )
    total = session.scalar(select(func.count()).select_from(ContentAsset).where(*filters)) or 0
    stmt = (
        select(ContentAsset)
        .where(*filters)
        .order_by(ContentAsset.updated_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    return [ContentRead.model_validate(row) for row in session.scalars(stmt)], total


def export_content(
    session: Session,
    user: User,
    content_id: UUID,
    *,
    fmt: str,
) -> tuple[bytes, str, str]:
    content = get_owned_content(session, user, content_id)
    basename = export_service.build_export_basename(content.slug, content.title)
    fmt = fmt.lower().strip()
    if fmt == "html":
        data = export_service.export_html_document(
            title=content.title,
            body_html=content.content or "",
            meta_description=content.meta_description,
        ).encode("utf-8")
        filename = f"{basename}.html"
        mime = "text/html; charset=utf-8"
    elif fmt == "markdown" or fmt == "md":
        data = export_service.export_markdown(title=content.title, body_html=content.content or "").encode("utf-8")
        filename = f"{basename}.md"
        mime = "text/markdown; charset=utf-8"
    elif fmt == "txt":
        data = export_service.export_txt(title=content.title, body_html=content.content or "").encode("utf-8")
        filename = f"{basename}.txt"
        mime = "text/plain; charset=utf-8"
    elif fmt == "pdf":
        data = export_service.export_pdf_bytes(title=content.title, body_html=content.content or "")
        filename = f"{basename}.pdf"
        mime = "application/pdf"
    else:
        raise BadRequestError("Unsupported export format")

    storage = get_storage_provider()
    key = f"exports/{content.project_id}/{content.id}/{uuid4().hex}_{safe_filename(filename)}"
    storage.put_bytes(key, data, content_type=mime)
    session.add(
        ContentAssetFile(
            project_id=content.project_id,
            content_asset_id=content.id,
            name=filename,
            asset_type="export",
            mime_type=mime.split(";")[0],
            size_bytes=len(data),
            storage_key=key,
            url=None,
            notes=f"export:{fmt}",
        )
    )
    session.flush()
    return data, filename, mime


def list_asset_library(
    session: Session,
    user: User,
    pagination,
    *,
    project_id: UUID | None = None,
    q: str | None = None,
) -> tuple[list[dict], int]:
    """Unified library of content + media for Asset Library UI."""
    from app.services.ownership import get_owned_project

    ids = owned_project_ids(session, user)
    if project_id:
        get_owned_project(session, user, project_id)
        project_ids = [project_id]
    else:
        project_ids = ids

    content_filters = [ContentAsset.project_id.in_(project_ids)] if project_ids else [ContentAsset.project_id.is_(None)]
    if q:
        like = f"%{q}%"
        content_filters.append(or_(ContentAsset.title.ilike(like), ContentAsset.slug.ilike(like)))
    contents = list(
        session.scalars(
            select(ContentAsset).where(*content_filters).order_by(ContentAsset.updated_at.desc()).limit(200)
        )
    )
    media_filters = [MediaAsset.project_id.in_(project_ids)] if project_ids else [MediaAsset.project_id.is_(None)]
    if q:
        like = f"%{q}%"
        media_filters.append(
            or_(MediaAsset.alt_text.ilike(like), MediaAsset.caption.ilike(like), MediaAsset.url.ilike(like))
        )
    media_rows = list(
        session.scalars(select(MediaAsset).where(*media_filters).order_by(MediaAsset.updated_at.desc()).limit(200))
    )
    items: list[dict] = []
    for c in contents:
        items.append(
            {
                "id": str(c.id),
                "name": c.title,
                "type": "content",
                "subtype": c.content_type,
                "project_id": str(c.project_id),
                "campaign_id": str(c.campaign_id) if c.campaign_id else None,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                "href": f"/content-studio/{c.id}",
            }
        )
    for m in media_rows:
        items.append(
            {
                "id": str(m.id),
                "name": m.alt_text or m.caption or m.url or "Media",
                "type": "media",
                "subtype": m.media_type,
                "project_id": str(m.project_id),
                "campaign_id": None,
                "status": m.status,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None,
                "url": m.url,
                "href": "/media",
            }
        )
    items.sort(key=lambda row: row.get("updated_at") or "", reverse=True)
    total = len(items)
    start = pagination.offset
    end = start + pagination.page_size
    return items[start:end], total
