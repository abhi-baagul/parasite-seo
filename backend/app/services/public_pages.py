"""Phase 6 — public web page builder, slug engine, publish lifecycle."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.content import ContentAsset, ContentLink, ContentVersion
from app.models.enums import ContentStatus, LinkStatus, MediaStatus, SuggestionStatus
from app.models.media import MediaAsset
from app.models.parasite_seo import ParasiteSEOJob
from app.models.public_page import PublicPage
from app.models.seo_enrichment import (
    ContentCategory,
    ContentMetadata,
    ContentTag,
    ExternalReference,
)
from app.models.user import User
from app.services.ownership import owned_project_ids
from app.utils.html_sanitize import sanitize_html
from app.utils.url_safety import slugify, validate_safe_url, validate_video_embed_url

PAGE_STATUSES = {"draft", "building", "ready", "published", "unpublished", "archived", "failed"}
VISIBILITIES = {"private", "public"}
MIN_BODY_CHARS = 40


def public_base_url() -> str:
    configured = (settings.public_app_url or "").strip().rstrip("/")
    if configured:
        return configured
    origins = settings.cors_origin_list
    return (origins[0] if origins else "http://localhost:3000").rstrip("/")


def build_public_url(slug: str) -> str:
    return f"{public_base_url()}/p/{slug}"


def _job_or_404(session: Session, user: User, job_id: UUID) -> ParasiteSEOJob:
    job = session.get(ParasiteSEOJob, job_id)
    if not job:
        raise NotFoundError("Parasite SEO job not found")
    ids = owned_project_ids(session, user)
    if job.project_id not in ids and job.user_id != user.id:
        raise ForbiddenError("You do not own this job")
    return job


def _page_for_job(session: Session, job_id: UUID) -> PublicPage | None:
    return session.scalar(select(PublicPage).where(PublicPage.job_id == job_id))


def _latest_version(session: Session, content_id: UUID) -> ContentVersion | None:
    return session.scalar(
        select(ContentVersion)
        .where(ContentVersion.content_asset_id == content_id)
        .order_by(ContentVersion.version_number.desc())
        .limit(1)
    )


def _ensure_snapshot_version(session: Session, content: ContentAsset, user: User) -> ContentVersion:
    latest = _latest_version(session, content.id)
    body = content.content or ""
    if latest and latest.content == body:
        return latest
    next_num = (latest.version_number + 1) if latest else 1
    version = ContentVersion(
        content_asset_id=content.id,
        version_number=next_num,
        content=body,
        change_summary="Public page snapshot",
        source="public_page",
        created_by=user.id,
    )
    session.add(version)
    session.flush()
    return version


def _slug_taken(session: Session, slug: str, *, exclude_page_id: UUID | None = None) -> bool:
    stmt = select(PublicPage.id).where(PublicPage.slug == slug)
    if exclude_page_id:
        stmt = stmt.where(PublicPage.id != exclude_page_id)
    return session.scalar(stmt) is not None


def allocate_unique_slug(
    session: Session,
    base: str,
    *,
    exclude_page_id: UUID | None = None,
) -> str:
    cleaned = slugify(base, max_length=80)
    candidate = cleaned
    n = 1
    while _slug_taken(session, candidate, exclude_page_id=exclude_page_id):
        n += 1
        suffix = f"-{n}"
        candidate = f"{cleaned[: max(1, 80 - len(suffix))]}{suffix}"
    return candidate


def _validate_content_ready(content: ContentAsset) -> None:
    body = (content.content or "").strip()
    if len(body) < MIN_BODY_CHARS:
        raise BadRequestError("Article body is too short to create a public page")
    if not (content.title or "").strip():
        raise BadRequestError("Title is required before creating a public page")
    if not (content.seo_title or content.title):
        raise BadRequestError("SEO title / metadata is required")
    if content.status in {ContentStatus.GENERATING.value, ContentStatus.FAILED.value}:
        raise BadRequestError("Content is still generating or failed; wait until generation finishes")


def _safe_media_url(url: str | None) -> str | None:
    if not url:
        return None
    value = url.strip()
    if value.startswith("/api/v1/"):
        return value
    try:
        return validate_safe_url(value, allow_http=True)
    except BadRequestError:
        return None


def _safe_link_url(url: str) -> str | None:
    try:
        return validate_safe_url(url)
    except BadRequestError:
        return None


def _extract_faq(html: str) -> list[dict[str, str]]:
    """Extract FAQ pairs from approved HTML when an FAQ section exists."""
    text = html or ""
    if not re.search(r"(?i)faq|frequently asked", text):
        return []
    items: list[dict[str, str]] = []
    # Match <h3>Question</h3><p>Answer</p> patterns after an FAQ heading.
    parts = re.split(r"(?i)<h[12][^>]*>[^<]*(?:faq|frequently asked)[^<]*</h[12]>", text, maxsplit=1)
    section = parts[1] if len(parts) > 1 else text
    for match in re.finditer(
        r"(?is)<h3[^>]*>(.*?)</h3>\s*<p[^>]*>(.*?)</p>",
        section,
    ):
        q = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        a = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        if q and a and len(items) < 20:
            items.append({"question": q[:300], "answer": a[:1200]})
    return items


def _sync_job_flags(job: ParasiteSEOJob, page: PublicPage) -> None:
    job.public_slug = page.slug
    job.public_url = page.public_url
    job.is_public = page.status == "published" and page.visibility == "public"
    job.published_at = page.published_at
    if page.status == "published":
        job.status = "published"
        job.current_step = "publish"
    elif page.status in {"unpublished", "archived"}:
        if job.status == "published":
            job.status = "ready"
    elif page.status in {"draft", "ready", "building"}:
        job.current_step = "preview"


def serialize_page(session: Session, page: PublicPage, *, include_preview: bool = False) -> dict:
    content = session.get(ContentAsset, page.content_id)
    latest = _latest_version(session, page.content_id) if content else None
    has_newer = bool(
        page.published_version_id
        and latest
        and latest.id != page.published_version_id
        and page.status == "published"
    )
    data = {
        "id": str(page.id),
        "job_id": str(page.job_id),
        "content_id": str(page.content_id),
        "project_id": str(page.project_id),
        "slug": page.slug,
        "title": page.title,
        "status": page.status,
        "visibility": page.visibility,
        "public_url": page.public_url,
        "canonical_url": page.canonical_url,
        "published_at": page.published_at.isoformat() if page.published_at else None,
        "content_version_id": str(page.content_version_id) if page.content_version_id else None,
        "published_version_id": str(page.published_version_id) if page.published_version_id else None,
        "has_newer_content": has_newer,
        "error_message": page.error_message,
        "seo_score": content.seo_score if content else None,
        "quality_score": content.quality_score if content else None,
        "created_at": page.created_at.isoformat() if page.created_at else None,
        "updated_at": page.updated_at.isoformat() if page.updated_at else None,
    }
    if include_preview and content:
        data["preview"] = build_public_payload(session, page, content, for_public=False)
    return data


def build_public_payload(
    session: Session,
    page: PublicPage,
    content: ContentAsset,
    *,
    for_public: bool,
) -> dict:
    meta = session.scalar(select(ContentMetadata).where(ContentMetadata.content_asset_id == content.id))
    categories = list(
        session.scalars(
            select(ContentCategory).where(
                ContentCategory.content_asset_id == content.id,
                ContentCategory.is_accepted.is_(True),
            )
        )
    )
    tags = list(
        session.scalars(
            select(ContentTag).where(
                ContentTag.content_asset_id == content.id,
                ContentTag.is_accepted.is_(True),
            )
        )
    )
    media_rows = list(
        session.scalars(
            select(MediaAsset).where(
                MediaAsset.content_asset_id == content.id,
                MediaAsset.status.in_(
                    [
                        MediaStatus.APPROVED.value,
                        MediaStatus.ATTACHED.value,
                        MediaStatus.READY.value,
                        MediaStatus.GENERATED.value,
                    ]
                ),
            )
        )
    )
    link_rows = list(
        session.scalars(
            select(ContentLink).where(
                ContentLink.content_asset_id == content.id,
                ContentLink.status.in_(
                    [LinkStatus.PLANNED.value, LinkStatus.INSERTED.value, LinkStatus.VERIFIED.value]
                ),
            )
        )
    )
    refs = list(
        session.scalars(
            select(ExternalReference).where(
                ExternalReference.content_asset_id == content.id,
                ExternalReference.status.in_(
                    [SuggestionStatus.APPROVED.value, SuggestionStatus.INSERTED.value]
                ),
            )
        )
    )

    # Prefer published snapshot body when serving the live public page.
    body_html = content.content or ""
    if for_public and page.published_version_id:
        version = session.get(ContentVersion, page.published_version_id)
        if version:
            body_html = version.content

    clean_html = sanitize_html(body_html)
    faq = _extract_faq(clean_html)

    images = []
    videos = []
    featured = None
    for m in media_rows:
        url = _safe_media_url(m.url)
        if not url:
            continue
        item = {
            "id": str(m.id),
            "media_type": m.media_type,
            "url": url,
            "alt_text": m.alt_text,
            "caption": m.caption,
        }
        is_image = "image" in (m.media_type or "") or (m.url or "").endswith(
            (".jpg", ".jpeg", ".png", ".webp", ".gif")
        )
        is_video = "video" in (m.media_type or "")
        if is_video:
            try:
                if url.startswith("/api/"):
                    videos.append(item)
                else:
                    item["url"] = validate_video_embed_url(url)
                    videos.append(item)
            except BadRequestError:
                continue
        elif is_image:
            images.append(item)
            if featured is None:
                featured = item

    links = []
    for link in link_rows:
        safe = _safe_link_url(link.target_url)
        if not safe:
            continue
        links.append(
            {
                "anchor_text": link.anchor_text,
                "target_url": safe,
                "link_attribute": link.link_attribute,
                "is_internal": safe.startswith(public_base_url()) or "/p/" in safe,
            }
        )

    references = []
    for ref in refs:
        if not ref.url:
            continue
        safe = _safe_link_url(ref.url)
        if not safe:
            continue
        references.append(
            {
                "title": ref.anchor_suggestion,
                "url": safe,
                "source_type": ref.source_type,
            }
        )

    related = []
    if for_public:
        from app.services import content_network as network_service
        from app.models.project import Project as ProjectModel

        project = session.get(ProjectModel, page.project_id)
        limit = 3
        if project:
            limit = int((project.link_settings or {}).get("related_content_limit") or 3)
        related = network_service.related_for_page(session, page, limit=limit)

    job = session.get(ParasiteSEOJob, page.job_id)
    target_link = None
    if job and isinstance(job.target_link, dict):
        raw_url = job.target_link.get("target_url")
        if raw_url:
            safe = _safe_link_url(str(raw_url))
            if safe:
                target_link = {
                    "target_url": safe,
                    "anchor_text": job.target_link.get("anchor_text") or "Learn more",
                    "link_attribute": job.target_link.get("link_attribute") or "sponsored",
                }

    seo_title = (meta.seo_title if meta and meta.seo_title else None) or content.seo_title or content.title
    meta_description = (
        (meta.meta_description if meta and meta.meta_description else None)
        or content.meta_description
        or ""
    )
    og_title = (meta.og_title if meta and meta.og_title else None) or seo_title
    og_description = (meta.og_description if meta and meta.og_description else None) or meta_description
    og_image = (meta.og_image if meta and meta.og_image else None) or (featured["url"] if featured else None)
    if og_image and og_image.startswith("/"):
        og_image = f"{public_base_url()}{og_image}"
    twitter_title = (meta.twitter_title if meta and meta.twitter_title else None) or og_title
    twitter_description = (
        (meta.twitter_description if meta and meta.twitter_description else None) or og_description
    )
    canonical = page.canonical_url or build_public_url(page.slug)

    structured: list[dict] = [
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": seo_title[:110],
            "description": meta_description[:300],
            "datePublished": page.published_at.isoformat() if page.published_at else None,
            "dateModified": page.updated_at.isoformat() if page.updated_at else None,
            "mainEntityOfPage": canonical,
            "image": og_image,
        }
    ]
    if faq:
        structured.append(
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item["question"],
                        "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
                    }
                    for item in faq
                ],
            }
        )
    # Drop nulls from JSON-LD for cleanliness
    for block in structured:
        for key in list(block.keys()):
            if block[key] is None:
                del block[key]

    return {
        "slug": page.slug,
        "title": content.title,
        "seo_title": seo_title,
        "meta_description": meta_description,
        "canonical_url": canonical,
        "content_html": clean_html,
        "published_at": page.published_at.isoformat() if page.published_at else None,
        "word_count": content.word_count,
        "category": categories[0].name if categories else None,
        "tags": [t.name for t in tags[:12]],
        "featured_image": featured,
        "images": images,
        "videos": videos,
        "links": links,
        "references": references,
        "related_pages": related,
        "target_link": target_link,
        "faq": faq,
        "metadata": {
            "title": seo_title,
            "description": meta_description,
            "canonical": canonical,
            "og": {
                "title": og_title,
                "description": og_description,
                "image": og_image,
                "url": canonical,
                "type": "article",
            },
            "twitter": {
                "card": "summary_large_image",
                "title": twitter_title,
                "description": twitter_description,
                "image": og_image,
            },
        },
        "structured_data": structured,
        "public_url": page.public_url or build_public_url(page.slug),
        "status": page.status,
        "visibility": page.visibility,
    }


def create_web_page(
    session: Session,
    user: User,
    job_id: UUID,
    *,
    slug: str | None = None,
) -> dict:
    job = _job_or_404(session, user, job_id)
    existing = _page_for_job(session, job.id)
    if existing and existing.status not in {"archived", "failed"}:
        raise BadRequestError("A web page already exists for this job. Edit or republish it instead.")
    if not job.content_id:
        raise BadRequestError("Generate content before creating a web page")
    content = session.get(ContentAsset, job.content_id)
    if not content:
        raise BadRequestError("Content asset missing")
    _validate_content_ready(content)

    page = existing
    try:
        if page is None:
            page = PublicPage(
                job_id=job.id,
                content_id=content.id,
                project_id=job.project_id,
                slug="pending",
                title=content.title,
                status="building",
                visibility="private",
            )
            session.add(page)
            session.flush()
        else:
            page.status = "building"
            page.error_message = None
            page.title = content.title

        desired = slugify(slug or content.slug or content.title)
        if not desired:
            raise BadRequestError("Unable to generate a valid slug from the title")
        page.slug = allocate_unique_slug(session, desired, exclude_page_id=page.id)
        page.public_url = build_public_url(page.slug)
        page.canonical_url = page.public_url
        version = _ensure_snapshot_version(session, content, user)
        page.content_version_id = version.id
        page.status = "ready"
        page.visibility = "private"
        content.status = ContentStatus.APPROVED.value
        _sync_job_flags(job, page)
        session.flush()
    except IntegrityError as exc:
        page.status = "failed"
        page.error_message = "Slug collision while creating page"
        session.flush()
        raise BadRequestError("Slug collision while creating page; retry with a different slug") from exc
    except Exception as exc:
        if page is not None:
            page.status = "failed"
            page.error_message = str(exc)[:500]
            session.flush()
        raise

    return serialize_page(session, page, include_preview=True)


def get_web_page(session: Session, user: User, job_id: UUID, *, preview: bool = False) -> dict:
    job = _job_or_404(session, user, job_id)
    page = _page_for_job(session, job.id)
    if not page:
        raise NotFoundError("Web page not found. Create one first.")
    return serialize_page(session, page, include_preview=preview)


def update_web_page(
    session: Session,
    user: User,
    job_id: UUID,
    *,
    slug: str | None = None,
    visibility: str | None = None,
    title: str | None = None,
) -> dict:
    job = _job_or_404(session, user, job_id)
    page = _page_for_job(session, job.id)
    if not page:
        raise NotFoundError("Web page not found")
    if page.status == "archived":
        raise BadRequestError("Archived pages cannot be edited; create a new page")
    if slug is not None:
        desired = slugify(slug)
        if not desired:
            raise BadRequestError("Invalid slug")
        if page.status == "published" and desired != page.slug:
            raise BadRequestError("Unpublish before changing the slug of a live page")
        old_slug = page.slug
        page.slug = allocate_unique_slug(session, desired, exclude_page_id=page.id)
        page.public_url = build_public_url(page.slug)
        page.canonical_url = page.public_url
        if old_slug and old_slug != page.slug:
            from app.services import content_network as network_service

            network_service.update_links_for_slug_change(
                session,
                user,
                project_id=page.project_id,
                old_slug=old_slug,
                new_slug=page.slug,
                public_page_id=page.id,
            )
    if visibility is not None:
        if visibility not in VISIBILITIES:
            raise BadRequestError("visibility must be private or public")
        page.visibility = visibility
    if title is not None and title.strip():
        page.title = title.strip()[:300]
    _sync_job_flags(job, page)
    try:
        session.flush()
    except IntegrityError as exc:
        raise BadRequestError("Slug already in use") from exc
    return serialize_page(session, page, include_preview=True)


def publish_web_page(session: Session, user: User, job_id: UUID) -> dict:
    job = _job_or_404(session, user, job_id)
    page = _page_for_job(session, job.id)
    if not page:
        # Convenience: create then publish in one step for legacy UI.
        create_web_page(session, user, job_id)
        page = _page_for_job(session, job.id)
        assert page
    if page.status == "archived":
        raise BadRequestError("Archived pages cannot be published")
    content = session.get(ContentAsset, page.content_id)
    if not content:
        raise BadRequestError("Content missing")
    _validate_content_ready(content)
    if not page.slug:
        raise BadRequestError("Slug is required")
    if _slug_taken(session, page.slug, exclude_page_id=page.id):
        raise BadRequestError("Slug collision; choose another slug")

    page.status = "building"
    session.flush()
    try:
        version = _ensure_snapshot_version(session, content, user)
        page.content_version_id = version.id
        page.published_version_id = version.id
        page.title = content.title
        page.public_url = build_public_url(page.slug)
        page.canonical_url = page.public_url
        page.visibility = "public"
        page.status = "published"
        page.published_at = datetime.now(UTC)
        page.error_message = None
        content.status = ContentStatus.APPROVED.value
        _sync_job_flags(job, page)
        session.flush()
    except IntegrityError as exc:
        page.status = "failed"
        page.error_message = "Slug race collision"
        session.flush()
        raise BadRequestError("Unable to publish due to slug collision; retry") from exc
    except Exception as exc:
        page.status = "failed"
        page.error_message = str(exc)[:500]
        session.flush()
        raise

    data = serialize_page(session, page)
    data["success"] = True
    data["public_url"] = page.public_url
    return data


def unpublish_web_page(session: Session, user: User, job_id: UUID) -> dict:
    job = _job_or_404(session, user, job_id)
    page = _page_for_job(session, job.id)
    if not page:
        raise NotFoundError("Web page not found")
    page.status = "unpublished"
    page.visibility = "private"
    _sync_job_flags(job, page)
    session.flush()
    return serialize_page(session, page)


def archive_web_page(session: Session, user: User, job_id: UUID) -> dict:
    job = _job_or_404(session, user, job_id)
    page = _page_for_job(session, job.id)
    if not page:
        raise NotFoundError("Web page not found")
    page.status = "archived"
    page.visibility = "private"
    _sync_job_flags(job, page)
    session.flush()
    return serialize_page(session, page)


def update_published_page(session: Session, user: User, job_id: UUID) -> dict:
    """Push the latest content version to the live public page."""
    job = _job_or_404(session, user, job_id)
    page = _page_for_job(session, job.id)
    if not page:
        raise NotFoundError("Web page not found")
    if page.status != "published":
        raise BadRequestError("Page is not published")
    content = session.get(ContentAsset, page.content_id)
    if not content:
        raise BadRequestError("Content missing")
    _validate_content_ready(content)
    version = _ensure_snapshot_version(session, content, user)
    page.content_version_id = version.id
    page.published_version_id = version.id
    page.title = content.title
    page.updated_at = datetime.now(UTC)
    session.flush()
    return serialize_page(session, page, include_preview=True)


def delete_web_page(session: Session, user: User, job_id: UUID, *, keep_content: bool = True) -> dict:
    job = _job_or_404(session, user, job_id)
    page = _page_for_job(session, job.id)
    if not page:
        raise NotFoundError("Web page not found")
    session.delete(page)
    job.is_public = False
    job.public_slug = None
    job.public_url = None
    job.published_at = None
    if job.status == "published":
        job.status = "ready"
    session.flush()
    return {"deleted": True, "content_preserved": keep_content, "job_id": str(job.id)}


def get_public_page_by_slug(session: Session, slug: str) -> dict:
    page = session.scalar(select(PublicPage).where(PublicPage.slug == slug))
    if not page or page.status != "published" or page.visibility != "public":
        # Phase 7: follow slug redirects for renamed public pages.
        from app.services import content_network as network_service

        redirected = network_service.resolve_slug_redirect(session, slug)
        if redirected and redirected != slug:
            page = session.scalar(select(PublicPage).where(PublicPage.slug == redirected))
        if not page or page.status != "published" or page.visibility != "public":
            raise NotFoundError("Public page not found")
    content = session.get(ContentAsset, page.content_id)
    if not content:
        raise NotFoundError("Public page not found")
    return build_public_payload(session, page, content, for_public=True)


def list_public_pages_admin(session: Session, user: User, project_id: UUID | None = None) -> list[dict]:
    ids = owned_project_ids(session, user)
    stmt = select(PublicPage).where(PublicPage.project_id.in_(ids)).order_by(PublicPage.updated_at.desc())
    if project_id:
        if project_id not in ids:
            raise ForbiddenError("Project not owned")
        stmt = stmt.where(PublicPage.project_id == project_id)
    pages = list(session.scalars(stmt.limit(200)))
    return [serialize_page(session, p) for p in pages]


def find_job_id_for_content(session: Session, user: User, content_id: UUID) -> UUID | None:
    ids = owned_project_ids(session, user)
    job = session.scalar(
        select(ParasiteSEOJob).where(
            ParasiteSEOJob.content_id == content_id,
            or_(ParasiteSEOJob.project_id.in_(ids), ParasiteSEOJob.user_id == user.id),
        )
    )
    return job.id if job else None
