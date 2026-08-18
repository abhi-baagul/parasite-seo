"""Phase 4 SEO enrichment orchestration."""

from __future__ import annotations

import hashlib
import re
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.media_plan_agent import MediaPlanAgent
from app.agents.metadata_agent import MetadataAgent
from app.agents.taxonomy_agent import TaxonomyAgent
from app.core.exceptions import BadRequestError, NotFoundError
from app.integrations.ai.base import AIProvider
from app.models.content import ContentAsset, ContentLink, ContentVersion
from app.models.enums import LinkAttribute, LinkStatus, SuggestionStatus
from app.models.keyword import Keyword
from app.models.media import MediaAsset
from app.models.pipeline import PromptAnalysis
from app.models.seo_enrichment import (
    ContentCategory,
    ContentMetadata,
    ContentTag,
    ExternalReference,
    InternalLinkSuggestion,
    KeywordAnalysisRecord,
    MediaSuggestion,
    SEOAnalysisRecord,
)
from app.models.user import User
from app.schemas.seo_enrichment import (
    InsertLinkRequest,
    SelectMetadataRequest,
    TargetLinkSuggestRequest,
    dump,
)
from app.seo.analyzer import run_full_seo_analysis
from app.seo.keywords import analyze_keywords
from app.seo.metadata import generate_slug_from_keyword
from app.seo.structure import plain_text
from app.services.ownership import get_owned_content
from app.utils.html_sanitize import sanitize_html
from app.utils.url_safety import slugify, validate_safe_url, validate_video_embed_url


def _content_hash(html: str) -> str:
    return hashlib.sha256((html or "").encode("utf-8")).hexdigest()


def _requirements(session: Session, content: ContentAsset) -> dict:
    if not content.prompt_id:
        return {}
    analysis = session.scalar(
        select(PromptAnalysis)
        .where(PromptAnalysis.prompt_id == content.prompt_id)
        .order_by(PromptAnalysis.created_at.desc())
        .limit(1)
    )
    if not analysis:
        return {}
    return analysis.confirmed_requirements or analysis.requirements or {}


def _get_or_create_metadata(session: Session, content_id: UUID) -> ContentMetadata:
    row = session.scalar(select(ContentMetadata).where(ContentMetadata.content_asset_id == content_id))
    if row:
        return row
    row = ContentMetadata(content_asset_id=content_id)
    session.add(row)
    session.flush()
    return row


def _snapshot_version(session: Session, content: ContentAsset, user: User, summary: str) -> None:
    if not content.content:
        return
    latest = session.scalar(
        select(func.max(ContentVersion.version_number)).where(ContentVersion.content_asset_id == content.id)
    )
    session.add(
        ContentVersion(
            content_asset_id=content.id,
            version_number=int(latest or 0) + 1,
            content=content.content,
            change_summary=summary,
            created_by=user.id,
        )
    )
    session.flush()


def analyze_keywords_for_content(session: Session, user: User, content_id: UUID, *, force: bool = False) -> dict:
    content = get_owned_content(session, user, content_id)
    if not content.content:
        raise BadRequestError("Content body is empty")
    digest = _content_hash(content.content)
    if not force:
        existing = session.scalar(
            select(KeywordAnalysisRecord)
            .where(
                KeywordAnalysisRecord.content_asset_id == content.id,
                KeywordAnalysisRecord.content_hash == digest,
            )
            .order_by(KeywordAnalysisRecord.created_at.desc())
            .limit(1)
        )
        if existing:
            return existing.payload

    req = _requirements(session, content)
    result = analyze_keywords(
        content.content,
        title=content.seo_title or content.title,
        primary_keyword=req.get("main_keyword"),
        secondary_keywords=req.get("secondary_keywords") or [],
    )
    payload = result.__dict__
    row = KeywordAnalysisRecord(content_asset_id=content.id, payload=payload, content_hash=digest)
    session.add(row)
    # Persist keyword rows for primary/secondary when missing.
    if result.primary_keyword:
        exists = session.scalar(
            select(Keyword).where(
                Keyword.project_id == content.project_id,
                Keyword.content_asset_id == content.id,
                Keyword.keyword == result.primary_keyword,
            )
        )
        if not exists:
            session.add(
                Keyword(
                    project_id=content.project_id,
                    content_asset_id=content.id,
                    keyword=result.primary_keyword,
                    keyword_type="primary",
                )
            )
    for kw in result.secondary_keywords:
        exists = session.scalar(
            select(Keyword).where(
                Keyword.project_id == content.project_id,
                Keyword.content_asset_id == content.id,
                Keyword.keyword == kw,
            )
        )
        if not exists:
            session.add(
                Keyword(
                    project_id=content.project_id,
                    content_asset_id=content.id,
                    keyword=kw,
                    keyword_type="secondary",
                )
            )
    session.flush()
    return payload


def get_keyword_analysis(session: Session, user: User, content_id: UUID) -> dict:
    content = get_owned_content(session, user, content_id)
    row = session.scalar(
        select(KeywordAnalysisRecord)
        .where(KeywordAnalysisRecord.content_asset_id == content.id)
        .order_by(KeywordAnalysisRecord.created_at.desc())
        .limit(1)
    )
    if not row:
        raise NotFoundError("Keyword analysis not found")
    return row.payload


def analyze_seo(session: Session, user: User, content_id: UUID, *, force: bool = False) -> dict:
    content = get_owned_content(session, user, content_id)
    if not content.content:
        raise BadRequestError("Content body is empty")
    digest = _content_hash(content.content)
    if not force:
        existing = session.scalar(
            select(SEOAnalysisRecord)
            .where(SEOAnalysisRecord.content_asset_id == content.id, SEOAnalysisRecord.content_hash == digest)
            .order_by(SEOAnalysisRecord.created_at.desc())
            .limit(1)
        )
        if existing:
            return existing.payload

    req = _requirements(session, content)
    links = session.scalars(select(ContentLink).where(ContentLink.content_asset_id == content.id)).all()
    media_suggestions = session.scalars(
        select(MediaSuggestion).where(MediaSuggestion.content_asset_id == content.id)
    ).all()
    media_assets = session.scalars(select(MediaAsset).where(MediaAsset.content_asset_id == content.id)).all()
    media_count = len(media_suggestions) + len(media_assets)
    with_alt = sum(1 for m in media_suggestions if m.alt_text) + sum(1 for m in media_assets if m.alt_text)

    meta = session.scalar(select(ContentMetadata).where(ContentMetadata.content_asset_id == content.id))
    payload = run_full_seo_analysis(
        html=content.content,
        title=content.title,
        seo_title=(meta.seo_title if meta and meta.seo_title else content.seo_title),
        meta_description=(meta.meta_description if meta and meta.meta_description else content.meta_description),
        slug=(meta.slug if meta and meta.slug else content.slug),
        primary_keyword=req.get("main_keyword"),
        secondary_keywords=req.get("secondary_keywords") or [],
        target_word_count=req.get("word_count"),
        planned_links=[
            {"status": link.status, "url": link.target_url, "anchor": link.anchor_text} for link in links
        ],
        media_count=media_count,
        media_with_alt=with_alt,
    )
    row = SEOAnalysisRecord(
        content_asset_id=content.id,
        payload=payload,
        overall_score=payload.get("overall_score"),
        content_hash=digest,
    )
    session.add(row)
    content.seo_score = payload.get("overall_score")
    session.flush()
    return payload


def get_seo(session: Session, user: User, content_id: UUID) -> dict:
    content = get_owned_content(session, user, content_id)
    row = session.scalar(
        select(SEOAnalysisRecord)
        .where(SEOAnalysisRecord.content_asset_id == content.id)
        .order_by(SEOAnalysisRecord.created_at.desc())
        .limit(1)
    )
    if not row:
        raise NotFoundError("SEO analysis not found")
    return row.payload


def generate_metadata(
    session: Session, user: User, content_id: UUID, provider: AIProvider | None = None
) -> dict:
    content = get_owned_content(session, user, content_id)
    req = _requirements(session, content)
    parsed, run = MetadataAgent(provider=provider).run(
        session,
        project_id=content.project_id,
        content_asset_id=content.id,
        topic=req.get("topic") or content.title,
        primary_keyword=req.get("main_keyword"),
        intent=req.get("intent"),
        audience=req.get("audience"),
        title=content.title,
        html=content.content,
    )
    meta = _get_or_create_metadata(session, content.id)
    meta.title_options = [dump(o) if hasattr(o, "model_dump") else o for o in parsed.title_options]
    # pydantic objects already validated
    meta.title_options = [o.model_dump() for o in parsed.title_options]
    meta.meta_options = [o.model_dump() for o in parsed.meta_options]
    meta.slug = parsed.slug or generate_slug_from_keyword(req.get("main_keyword"), content.title)
    meta.og_title = parsed.og_title
    meta.og_description = parsed.og_description
    meta.twitter_title = parsed.twitter_title
    meta.twitter_description = parsed.twitter_description
    session.flush()
    return {
        "metadata": {
            "title_options": meta.title_options,
            "meta_options": meta.meta_options,
            "slug": meta.slug,
            "og_title": meta.og_title,
            "og_description": meta.og_description,
            "twitter_title": meta.twitter_title,
            "twitter_description": meta.twitter_description,
            "selected_seo_title": meta.seo_title,
            "selected_meta_description": meta.meta_description,
        },
        "ai_run_id": str(run.id),
    }


def select_metadata(session: Session, user: User, content_id: UUID, payload: SelectMetadataRequest) -> dict:
    content = get_owned_content(session, user, content_id)
    meta = _get_or_create_metadata(session, content.id)
    data = payload.model_dump(exclude_unset=True)
    if "slug" in data and data["slug"]:
        data["slug"] = slugify(data["slug"])
    if data.get("canonical_url"):
        data["canonical_url"] = validate_safe_url(data["canonical_url"])
    if data.get("og_image"):
        data["og_image"] = validate_safe_url(data["og_image"])
    for key, value in data.items():
        setattr(meta, key, value)
    # Mirror selected fields onto content asset for Phase 3 compatibility.
    if meta.seo_title:
        content.seo_title = meta.seo_title
    if meta.meta_description:
        content.meta_description = meta.meta_description
    if meta.slug:
        content.slug = meta.slug[:320]
    session.flush()
    return {
        "seo_title": meta.seo_title,
        "meta_description": meta.meta_description,
        "slug": meta.slug,
        "canonical_url": meta.canonical_url,
        "og_title": meta.og_title,
        "og_description": meta.og_description,
        "og_image": meta.og_image,
        "twitter_title": meta.twitter_title,
        "twitter_description": meta.twitter_description,
    }


def generate_tags(session: Session, user: User, content_id: UUID, provider: AIProvider | None = None) -> dict:
    content = get_owned_content(session, user, content_id)
    req = _requirements(session, content)
    keywords = [req.get("main_keyword")] + list(req.get("secondary_keywords") or [])
    parsed, run = TaxonomyAgent(provider=provider).run(
        session,
        project_id=content.project_id,
        content_asset_id=content.id,
        topic=req.get("topic") or content.title,
        keywords=[k for k in keywords if k],
        html=content.content,
    )
    # Replace previous AI suggestions that were not manually marked differently — keep accepted set refreshed.
    for name in parsed.tags[:8]:
        clean = name.strip()
        if not clean:
            continue
        exists = session.scalar(
            select(ContentTag).where(ContentTag.content_asset_id == content.id, ContentTag.name == clean)
        )
        if not exists:
            session.add(ContentTag(content_asset_id=content.id, name=clean, source="ai", is_accepted=False))
    for name in parsed.categories[:4]:
        clean = name.strip()
        if not clean:
            continue
        exists = session.scalar(
            select(ContentCategory).where(
                ContentCategory.content_asset_id == content.id, ContentCategory.name == clean
            )
        )
        if not exists:
            session.add(
                ContentCategory(content_asset_id=content.id, name=clean, source="ai", is_accepted=False)
            )
    session.flush()
    return {"tags": list_tags(session, user, content_id), "categories": list_categories(session, user, content_id), "ai_run_id": str(run.id)}


def list_tags(session: Session, user: User, content_id: UUID) -> list[dict]:
    content = get_owned_content(session, user, content_id)
    rows = session.scalars(select(ContentTag).where(ContentTag.content_asset_id == content.id))
    return [
        {"id": str(r.id), "name": r.name, "source": r.source, "is_accepted": r.is_accepted}
        for r in rows
    ]


def list_categories(session: Session, user: User, content_id: UUID) -> list[dict]:
    content = get_owned_content(session, user, content_id)
    rows = session.scalars(select(ContentCategory).where(ContentCategory.content_asset_id == content.id))
    return [
        {"id": str(r.id), "name": r.name, "source": r.source, "is_accepted": r.is_accepted}
        for r in rows
    ]


def set_tag_acceptance(session: Session, user: User, content_id: UUID, tag_id: UUID, accepted: bool) -> dict:
    content = get_owned_content(session, user, content_id)
    tag = session.get(ContentTag, tag_id)
    if not tag or tag.content_asset_id != content.id:
        raise NotFoundError("Tag not found")
    tag.is_accepted = accepted
    session.flush()
    return {"id": str(tag.id), "name": tag.name, "is_accepted": tag.is_accepted}


def set_category_acceptance(
    session: Session, user: User, content_id: UUID, category_id: UUID, accepted: bool
) -> dict:
    content = get_owned_content(session, user, content_id)
    row = session.get(ContentCategory, category_id)
    if not row or row.content_asset_id != content.id:
        raise NotFoundError("Category not found")
    row.is_accepted = accepted
    session.flush()
    return {"id": str(row.id), "name": row.name, "is_accepted": row.is_accepted}


def suggest_internal_links(session: Session, user: User, content_id: UUID) -> dict:
    content = get_owned_content(session, user, content_id)
    req = _requirements(session, content)
    primary = (req.get("main_keyword") or content.title or "").lower()
    others = session.scalars(
        select(ContentAsset).where(
            ContentAsset.project_id == content.project_id,
            ContentAsset.id != content.id,
        )
    ).all()
    created = []
    for other in others:
        blob = f"{other.title} {other.slug} {plain_text(other.content)[:500]}".lower()
        # Simple topical overlap heuristic — no fabricated pages.
        overlap = any(token and token in blob for token in re.split(r"\W+", primary) if len(token) > 3)
        if not overlap and primary and primary[:12] not in blob:
            continue
        exists = session.scalar(
            select(InternalLinkSuggestion).where(
                InternalLinkSuggestion.content_asset_id == content.id,
                InternalLinkSuggestion.target_content_id == other.id,
                InternalLinkSuggestion.status == SuggestionStatus.SUGGESTED.value,
            )
        )
        if exists:
            continue
        suggestion = InternalLinkSuggestion(
            content_asset_id=content.id,
            target_content_id=other.id,
            source_section="Related reading",
            anchor_text=other.title[:500],
            target_path=f"/{other.slug}",
            reason="Related project content that may help readers explore the topic further.",
            status=SuggestionStatus.SUGGESTED.value,
        )
        session.add(suggestion)
        created.append(suggestion)
    session.flush()
    return {"suggestions": list_internal_link_suggestions(session, user, content_id), "created": len(created)}


def list_internal_link_suggestions(session: Session, user: User, content_id: UUID) -> list[dict]:
    content = get_owned_content(session, user, content_id)
    rows = session.scalars(
        select(InternalLinkSuggestion)
        .where(InternalLinkSuggestion.content_asset_id == content.id)
        .order_by(InternalLinkSuggestion.created_at.desc())
    )
    return [
        {
            "id": str(r.id),
            "target_content_id": str(r.target_content_id),
            "source_section": r.source_section,
            "anchor_text": r.anchor_text,
            "target_path": r.target_path,
            "reason": r.reason,
            "status": r.status,
        }
        for r in rows
    ]


def decide_internal_link(
    session: Session, user: User, content_id: UUID, suggestion_id: UUID, status: str
) -> dict:
    content = get_owned_content(session, user, content_id)
    row = session.get(InternalLinkSuggestion, suggestion_id)
    if not row or row.content_asset_id != content.id:
        raise NotFoundError("Internal link suggestion not found")
    row.status = status
    session.flush()
    return {"id": str(row.id), "status": row.status}


def suggest_external_references(session: Session, user: User, content_id: UUID) -> dict:
    content = get_owned_content(session, user, content_id)
    req = _requirements(session, content)
    topic = req.get("topic") or content.title
    # Do not invent URLs — store verification-required placeholders.
    templates = [
        {
            "url": None,
            "anchor_suggestion": f"Official {topic} documentation",
            "reason": "Prefer the vendor’s official help/docs pages when a verified URL is available.",
            "source_type": "official_documentation",
            "requires_verification": True,
        },
        {
            "url": None,
            "anchor_suggestion": f"{topic} pricing or checkout",
            "reason": "Readers should confirm offers on an official checkout page.",
            "source_type": "official_product",
            "requires_verification": True,
        },
    ]
    for item in templates:
        exists = session.scalar(
            select(ExternalReference).where(
                ExternalReference.content_asset_id == content.id,
                ExternalReference.anchor_suggestion == item["anchor_suggestion"],
            )
        )
        if exists:
            continue
        session.add(ExternalReference(content_asset_id=content.id, **item))
    session.flush()
    return {"references": list_external_references(session, user, content_id)}


def list_external_references(session: Session, user: User, content_id: UUID) -> list[dict]:
    content = get_owned_content(session, user, content_id)
    rows = session.scalars(select(ExternalReference).where(ExternalReference.content_asset_id == content.id))
    return [
        {
            "id": str(r.id),
            "url": r.url,
            "anchor_suggestion": r.anchor_suggestion,
            "reason": r.reason,
            "source_type": r.source_type,
            "requires_verification": r.requires_verification,
            "status": r.status,
        }
        for r in rows
    ]


def decide_external_reference(
    session: Session, user: User, content_id: UUID, ref_id: UUID, status: str, url: str | None = None
) -> dict:
    content = get_owned_content(session, user, content_id)
    row = session.get(ExternalReference, ref_id)
    if not row or row.content_asset_id != content.id:
        raise NotFoundError("External reference not found")
    if url is not None:
        if url:
            row.url = validate_safe_url(url)
            row.requires_verification = False
        else:
            row.url = None
            row.requires_verification = True
    row.status = status
    session.flush()
    return {"id": str(row.id), "status": row.status, "url": row.url}


def analyze_links(session: Session, user: User, content_id: UUID) -> dict:
    content = get_owned_content(session, user, content_id)
    from app.seo.links import analyze_links as engine_links

    links = session.scalars(select(ContentLink).where(ContentLink.content_asset_id == content.id)).all()
    report = engine_links(
        content.content or "",
        planned_links=[{"status": l.status, "url": l.target_url} for l in links],
    )
    return report.__dict__


def suggest_target_link_placement(
    session: Session, user: User, content_id: UUID, payload: TargetLinkSuggestRequest
) -> dict:
    content = get_owned_content(session, user, content_id)
    url = validate_safe_url(payload.target_url)
    anchor = payload.anchor_text.strip()
    text = plain_text(content.content or "")
    # Suggest a contextual sentence without inserting yet.
    if anchor.lower() in text.lower():
        phrase = f'Existing mention of "{anchor}" can become the link anchor.'
    else:
        phrase = (
            f'Users looking for the latest {anchor} can review the offer details and confirm them before purchasing.'
        )
    return {
        "target_url": url,
        "anchor_text": anchor,
        "link_attribute": payload.link_attribute,
        "suggested_phrase": phrase,
        "note": "Review before insertion. Attribute should match the commercial relationship honestly.",
    }


def insert_link(session: Session, user: User, content_id: UUID, payload: InsertLinkRequest) -> dict:
    content = get_owned_content(session, user, content_id)
    url = validate_safe_url(payload.target_url)
    anchor = payload.anchor_text.strip()
    # Duplicate URL check
    existing = session.scalar(
        select(ContentLink).where(ContentLink.content_asset_id == content.id, ContentLink.target_url == url)
    )
    if existing and existing.anchor_text.lower() == anchor.lower():
        raise BadRequestError("Duplicate target URL + anchor already exists for this content")

    # Excessive same-anchor check
    same_anchor = session.scalars(
        select(ContentLink).where(ContentLink.content_asset_id == content.id, ContentLink.anchor_text == anchor)
    ).all()
    if len(list(same_anchor)) >= 3:
        raise BadRequestError("Excessive repeated anchors for the same text")

    _snapshot_version(session, content, user, "Pre-link-insertion snapshot")
    phrase = payload.placement_phrase or anchor
    href_attr = url
    rel_bits = []
    if payload.link_attribute == LinkAttribute.NOFOLLOW.value:
        rel_bits.append("nofollow")
    if payload.link_attribute == LinkAttribute.SPONSORED.value:
        rel_bits.append("sponsored")
    if payload.link_attribute == LinkAttribute.UGC.value:
        rel_bits.append("ugc")
    rel = f' rel="{" ".join(rel_bits)}"' if rel_bits else ""
    link_html = f'<a href="{href_attr}"{rel}>{anchor}</a>'

    html = content.content or ""
    if phrase in html:
        html = html.replace(phrase, link_html if phrase == anchor else phrase.replace(anchor, link_html), 1)
    elif anchor in html:
        html = html.replace(anchor, link_html, 1)
    else:
        html = html + f"<p>{link_html}</p>"
    content.content = sanitize_html(html)

    link = ContentLink(
        content_asset_id=content.id,
        target_url=url,
        anchor_text=anchor,
        placement_description=payload.placement_phrase or "Contextual insertion",
        link_attribute=payload.link_attribute,
        status=LinkStatus.INSERTED.value,
    )
    session.add(link)
    _snapshot_version(session, content, user, "Inserted target link")
    session.flush()
    return {
        "link": {
            "id": str(link.id),
            "target_url": link.target_url,
            "anchor_text": link.anchor_text,
            "link_attribute": link.link_attribute,
            "status": link.status,
        },
        "content": content.content,
    }


def generate_media_plan(
    session: Session, user: User, content_id: UUID, provider: AIProvider | None = None
) -> dict:
    content = get_owned_content(session, user, content_id)
    req = _requirements(session, content)
    parsed, run = MediaPlanAgent(provider=provider).run(
        session,
        project_id=content.project_id,
        content_asset_id=content.id,
        topic=req.get("topic") or content.title,
        html=content.content,
    )
    created = []
    for item in list(parsed.items) + list(parsed.video_suggestions):
        row = MediaSuggestion(
            content_asset_id=content.id,
            media_type=item.media_type,
            placement=item.placement,
            purpose=item.purpose,
            description=item.description,
            generation_prompt=item.generation_prompt,
            alt_text=item.alt_text,
            caption=item.caption,
            suggested_filename=item.suggested_filename,
            status=SuggestionStatus.SUGGESTED.value,
        )
        session.add(row)
        created.append(row)
    session.flush()
    return {"media": list_media_suggestions(session, user, content_id), "ai_run_id": str(run.id), "created": len(created)}


def list_media_suggestions(session: Session, user: User, content_id: UUID) -> list[dict]:
    content = get_owned_content(session, user, content_id)
    rows = session.scalars(
        select(MediaSuggestion)
        .where(MediaSuggestion.content_asset_id == content.id)
        .order_by(MediaSuggestion.created_at.desc())
    )
    return [
        {
            "id": str(r.id),
            "content_id": str(r.content_asset_id),
            "media_type": r.media_type,
            "placement": r.placement,
            "purpose": r.purpose,
            "description": r.description,
            "generation_prompt": r.generation_prompt,
            "alt_text": r.alt_text,
            "caption": r.caption,
            "suggested_filename": r.suggested_filename,
            "status": r.status,
            "embed_url": r.embed_url,
        }
        for r in rows
    ]


def decide_media_suggestion(
    session: Session,
    user: User,
    content_id: UUID,
    suggestion_id: UUID,
    status: str,
    *,
    embed_url: str | None = None,
    alt_text: str | None = None,
) -> dict:
    content = get_owned_content(session, user, content_id)
    row = session.get(MediaSuggestion, suggestion_id)
    if not row or row.content_asset_id != content.id:
        raise NotFoundError("Media suggestion not found")
    if embed_url is not None:
        row.embed_url = validate_video_embed_url(embed_url) if embed_url else None
    if alt_text is not None:
        row.alt_text = alt_text
    row.status = status
    # Promote approved suggestions into MediaAsset library metadata (no binary generation yet).
    if status == SuggestionStatus.APPROVED.value:
        session.add(
            MediaAsset(
                project_id=content.project_id,
                content_asset_id=content.id,
                media_type=row.media_type if row.media_type in {"image", "video", "diagram", "infographic"} else "image",
                url=row.embed_url,
                prompt=row.generation_prompt,
                alt_text=row.alt_text,
                caption=row.caption,
                source="media_plan",
                status="approved",
            )
        )
    session.flush()
    return {"id": str(row.id), "status": row.status}


def video_suggestions(session: Session, user: User, content_id: UUID, provider: AIProvider | None = None) -> dict:
    # Reuse media plan agent but filter to video items; if none exist, generate plan.
    existing = [
        m for m in list_media_suggestions(session, user, content_id) if m["media_type"] == "video"
    ]
    if existing:
        return {"videos": existing}
    plan = generate_media_plan(session, user, content_id, provider=provider)
    videos = [m for m in plan["media"] if m["media_type"] == "video"]
    return {"videos": videos, "ai_run_id": plan.get("ai_run_id")}


def generate_all(session: Session, user: User, content_id: UUID, provider: AIProvider | None = None) -> dict:
    """Controlled enrichment sequence — avoids redundant AI where cached analysis exists."""
    keywords = analyze_keywords_for_content(session, user, content_id)
    metadata = generate_metadata(session, user, content_id, provider=provider)
    tags = generate_tags(session, user, content_id, provider=provider)
    internal = suggest_internal_links(session, user, content_id)
    external = suggest_external_references(session, user, content_id)
    media = generate_media_plan(session, user, content_id, provider=provider)
    seo = analyze_seo(session, user, content_id, force=True)
    return {
        "keywords": keywords,
        "metadata": metadata,
        "tags": tags,
        "internal_links": internal,
        "external_references": external,
        "media": media,
        "seo": seo,
    }
