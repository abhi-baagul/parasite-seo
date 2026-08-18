"""Phase 7 — Content network + internal link automation."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.agents.link_intelligence_agent import LinkIntelligenceAgent
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.content import ContentAsset, ContentLink, ContentVersion
from app.models.content_network import ContentNetworkRun, PublicSlugRedirect
from app.models.enums import LinkAttribute, LinkStatus, SuggestionStatus
from app.models.project import Project
from app.models.public_page import PublicPage
from app.models.seo_enrichment import ContentTag, InternalLinkSuggestion
from app.models.user import User
from app.services import public_pages as public_page_service
from app.services import seo_enrichment
from app.services.ownership import get_owned_project, owned_project_ids
from app.utils.html_sanitize import count_words, sanitize_html
from app.utils.url_safety import slugify

DEFAULT_LINK_SETTINGS = {
    "automatic_internal_linking": False,
    "min_relevance_score": 85,
    "max_new_links_per_article": 5,
    "max_links_to_same_target": 1,
    "max_links_per_section": 2,
    "related_content_limit": 3,
}

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "your",
    "into",
    "about",
    "using",
    "tools",
    "best",
    "guide",
    "complete",
}


def _settings(project: Project) -> dict:
    raw = dict(project.link_settings or {})
    merged = dict(DEFAULT_LINK_SETTINGS)
    merged.update({k: v for k, v in raw.items() if v is not None})
    return merged


def _tokens(text: str) -> set[str]:
    parts = re.findall(r"[a-z0-9]{3,}", (text or "").lower())
    return {p for p in parts if p not in STOPWORDS}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _plain(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html or "")


def _eligible_pages(session: Session, project_id: UUID) -> list[tuple[PublicPage, ContentAsset]]:
    pages = list(
        session.scalars(
            select(PublicPage).where(
                PublicPage.project_id == project_id,
                PublicPage.status == "published",
                PublicPage.visibility == "public",
            )
        )
    )
    out: list[tuple[PublicPage, ContentAsset]] = []
    for page in pages:
        content = session.get(ContentAsset, page.content_id)
        if not content or not (content.content or "").strip() or not page.slug:
            continue
        out.append((page, content))
    return out


def _page_blob(content: ContentAsset, page: PublicPage) -> str:
    tags = session_tags = ""  # filled by caller when needed
    return f"{content.title} {page.slug} {content.seo_title or ''} {content.meta_description or ''} {_plain(content.content)[:1200]}"


def _internal_path(slug: str) -> str:
    return f"/p/{slug}"


def _resolve_slug_from_url(url: str) -> str | None:
    value = (url or "").strip()
    if value.startswith("/p/"):
        return value.split("/p/", 1)[1].split("?", 1)[0].strip("/")
    try:
        parsed = urlparse(value)
        if "/p/" in parsed.path:
            return parsed.path.split("/p/", 1)[1].strip("/")
    except Exception:
        return None
    return None


def serialize_suggestion(session: Session, row: InternalLinkSuggestion) -> dict:
    source = session.get(ContentAsset, row.content_asset_id)
    target = session.get(ContentAsset, row.target_content_id)
    return {
        "id": str(row.id),
        "project_id": str(row.project_id) if row.project_id else None,
        "source_content_id": str(row.content_asset_id),
        "target_content_id": str(row.target_content_id),
        "source_title": source.title if source else None,
        "target_title": target.title if target else None,
        "anchor_text": row.anchor_text,
        "target_path": row.target_path,
        "reason": row.reason,
        "relevance_score": row.relevance_score,
        "confidence_score": row.confidence_score,
        "placement": row.placement or row.source_section,
        "context": row.context,
        "suggestion_type": row.suggestion_type,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def get_link_settings(session: Session, user: User, project_id: UUID) -> dict:
    project = get_owned_project(session, user, project_id)
    return _settings(project)


def update_link_settings(session: Session, user: User, project_id: UUID, payload: dict) -> dict:
    project = get_owned_project(session, user, project_id)
    current = _settings(project)
    allowed = set(DEFAULT_LINK_SETTINGS.keys())
    for key, value in payload.items():
        if key not in allowed:
            continue
        current[key] = value
    if not isinstance(current["min_relevance_score"], int) or not 50 <= current["min_relevance_score"] <= 99:
        raise BadRequestError("min_relevance_score must be an integer between 50 and 99")
    project.link_settings = current
    session.flush()
    return current


def analyze_network(session: Session, user: User, project_id: UUID, *, use_ai: bool = True) -> dict:
    project = get_owned_project(session, user, project_id)
    settings = _settings(project)
    run = ContentNetworkRun(
        project_id=project.id,
        status="analyzing",
        started_at=datetime.now(UTC),
        summary={},
    )
    session.add(run)
    session.flush()

    try:
        pages = _eligible_pages(session, project.id)
        created = 0
        overlap_flags: list[dict] = []

        # Precompute tokens
        page_meta: list[dict] = []
        for page, content in pages:
            tags = list(
                session.scalars(
                    select(ContentTag.name).where(
                        ContentTag.content_asset_id == content.id,
                        ContentTag.is_accepted.is_(True),
                    )
                )
            )
            blob = f"{content.title} {' '.join(tags)} {content.seo_title or ''} {_plain(content.content)[:1500]}"
            page_meta.append(
                {
                    "page": page,
                    "content": content,
                    "tags": tags,
                    "tokens": _tokens(blob),
                    "title": content.title,
                    "slug": page.slug,
                }
            )

        # Near-duplicate detection
        for i, left in enumerate(page_meta):
            for right in page_meta[i + 1 :]:
                sim = _jaccard(left["tokens"], right["tokens"])
                if sim >= 0.72:
                    overlap_flags.append(
                        {
                            "left_content_id": str(left["content"].id),
                            "right_content_id": str(right["content"].id),
                            "left_title": left["title"],
                            "right_title": right["title"],
                            "similarity": round(sim, 3),
                            "message": "Potentially overlapping content — review, consolidate, or differentiate.",
                        }
                    )

        agent = LinkIntelligenceAgent() if use_ai else None

        for source in page_meta:
            # Candidate filter: similarity score, exclude self, prefer useful overlap
            candidates = []
            for other in page_meta:
                if other["content"].id == source["content"].id:
                    continue
                score = int(round(_jaccard(source["tokens"], other["tokens"]) * 100))
                # Soft boost shared title tokens
                title_overlap = _jaccard(_tokens(source["title"]), _tokens(other["title"]))
                score = min(100, score + int(title_overlap * 20))
                if score < 25:
                    continue
                candidates.append((score, other))
            candidates.sort(key=lambda x: x[0], reverse=True)
            candidates = candidates[:8]

            if not candidates:
                continue

            ai_items = []
            if agent and len(candidates) > 0:
                try:
                    parsed, _run = agent.run(
                        session,
                        project_id=project.id,
                        content_asset_id=source["content"].id,
                        source={
                            "title": source["title"],
                            "slug": source["slug"],
                            "excerpt": _plain(source["content"].content)[:800],
                            "tags": source["tags"],
                        },
                        candidates=[
                            {
                                "title": c["title"],
                                "slug": c["slug"],
                                "excerpt": _plain(c["content"].content)[:400],
                                "heuristic_score": score,
                            }
                            for score, c in candidates
                        ],
                    )
                    ai_items = list(parsed.suggestions)
                except Exception:
                    ai_items = []

            # Merge AI + heuristic
            planned: list[dict] = []
            if ai_items:
                by_title = {c["title"].lower(): (score, c) for score, c in candidates}
                for item in ai_items:
                    match = by_title.get(item.target_title.lower())
                    if not match:
                        # fuzzy: title contained
                        match = next(
                            (
                                (score, c)
                                for score, c in candidates
                                if item.target_title.lower() in c["title"].lower()
                                or c["title"].lower() in item.target_title.lower()
                            ),
                            None,
                        )
                    if not match:
                        continue
                    score, target = match
                    planned.append(
                        {
                            "target": target,
                            "anchor": item.anchor_text.strip()[:120],
                            "reason": item.reason,
                            "relevance": max(score, item.relevance_score),
                            "confidence": item.confidence_score,
                            "placement": item.placement or "Contextual paragraph",
                            "context": item.context,
                        }
                    )
            else:
                for score, target in candidates[:3]:
                    if score < 40:
                        continue
                    anchor = target["title"][:80]
                    # diversify: shorter natural form
                    words = target["title"].split()
                    if len(words) > 4:
                        anchor = " ".join(words[:4])
                    planned.append(
                        {
                            "target": target,
                            "anchor": anchor,
                            "reason": (
                                f"{target['title']} is topically related and can help readers "
                                f"explore a closely connected subject from {source['title']}."
                            ),
                            "relevance": score,
                            "confidence": min(95, score + 5),
                            "placement": "After an introductory section covering related topics",
                            "context": None,
                        }
                    )

            existing_targets = {
                r.target_content_id
                for r in session.scalars(
                    select(InternalLinkSuggestion).where(
                        InternalLinkSuggestion.content_asset_id == source["content"].id,
                        InternalLinkSuggestion.status.in_(
                            [SuggestionStatus.SUGGESTED.value, SuggestionStatus.APPROVED.value, SuggestionStatus.INSERTED.value]
                        ),
                    )
                )
            }
            outgoing = list(
                session.scalars(
                    select(ContentLink).where(ContentLink.content_asset_id == source["content"].id)
                )
            )
            max_new = int(settings["max_new_links_per_article"])
            added_for_source = 0
            for plan in planned:
                if added_for_source >= max_new:
                    break
                target = plan["target"]
                if target["content"].id in existing_targets:
                    continue
                if any(
                    (_resolve_slug_from_url(link.target_url) == target["slug"]) or link.target_content_id == target["content"].id
                    for link in outgoing
                ):
                    continue
                if plan["relevance"] < 35:
                    continue
                suggestion = InternalLinkSuggestion(
                    content_asset_id=source["content"].id,
                    target_content_id=target["content"].id,
                    project_id=project.id,
                    source_section=plan["placement"],
                    anchor_text=plan["anchor"],
                    target_path=_internal_path(target["slug"]),
                    reason=plan["reason"],
                    relevance_score=int(plan["relevance"]),
                    confidence_score=int(plan["confidence"]),
                    placement=plan["placement"],
                    context=plan["context"],
                    suggestion_type="contextual",
                    status=SuggestionStatus.SUGGESTED.value,
                )
                session.add(suggestion)
                session.flush()
                created += 1
                added_for_source += 1
                existing_targets.add(target["content"].id)

                # Auto-insert only when enabled and high confidence
                if (
                    settings["automatic_internal_linking"]
                    and int(plan["confidence"]) >= int(settings["min_relevance_score"])
                ):
                    try:
                        approve_and_insert(session, user, suggestion.id, auto=True)
                    except Exception:
                        pass

        run.status = "completed"
        run.pages_analyzed = len(pages)
        run.suggestions_created = created
        run.completed_at = datetime.now(UTC)
        run.summary = {
            "overlap_flags": overlap_flags[:20],
            "settings": settings,
        }
        session.flush()
        return {
            "run": serialize_run(run),
            "overview": network_overview(session, user, project_id),
        }
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)[:500]
        run.completed_at = datetime.now(UTC)
        session.flush()
        raise


def serialize_run(run: ContentNetworkRun) -> dict:
    return {
        "id": str(run.id),
        "project_id": str(run.project_id),
        "status": run.status,
        "pages_analyzed": run.pages_analyzed,
        "suggestions_created": run.suggestions_created,
        "error_message": run.error_message,
        "summary": run.summary or {},
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


def list_suggestions(
    session: Session,
    user: User,
    *,
    project_id: UUID | None = None,
    status: str | None = None,
) -> list[dict]:
    ids = owned_project_ids(session, user)
    stmt = select(InternalLinkSuggestion).where(
        or_(
            InternalLinkSuggestion.project_id.in_(ids),
            InternalLinkSuggestion.content_asset_id.in_(
                select(ContentAsset.id).where(ContentAsset.project_id.in_(ids))
            ),
        )
    )
    if project_id:
        if project_id not in ids:
            raise ForbiddenError("Project not owned")
        stmt = stmt.where(
            or_(
                InternalLinkSuggestion.project_id == project_id,
                InternalLinkSuggestion.content_asset_id.in_(
                    select(ContentAsset.id).where(ContentAsset.project_id == project_id)
                ),
            )
        )
    if status:
        stmt = stmt.where(InternalLinkSuggestion.status == status)
    rows = list(session.scalars(stmt.order_by(InternalLinkSuggestion.created_at.desc()).limit(300)))
    return [serialize_suggestion(session, r) for r in rows]


def update_suggestion(
    session: Session,
    user: User,
    suggestion_id: UUID,
    *,
    anchor_text: str | None = None,
    placement: str | None = None,
    context: str | None = None,
) -> dict:
    row = _owned_suggestion(session, user, suggestion_id)
    if row.status not in {SuggestionStatus.SUGGESTED.value, SuggestionStatus.APPROVED.value}:
        raise BadRequestError("Only suggested/approved suggestions can be edited")
    if anchor_text is not None:
        cleaned = anchor_text.strip()
        if len(cleaned) < 2:
            raise BadRequestError("Anchor text is too short")
        row.anchor_text = cleaned[:500]
    if placement is not None:
        row.placement = placement[:300]
        row.source_section = placement[:300]
    if context is not None:
        row.context = context
    session.flush()
    return serialize_suggestion(session, row)


def reject_suggestion(session: Session, user: User, suggestion_id: UUID) -> dict:
    row = _owned_suggestion(session, user, suggestion_id)
    row.status = SuggestionStatus.REJECTED.value
    session.flush()
    return serialize_suggestion(session, row)


def _owned_suggestion(session: Session, user: User, suggestion_id: UUID) -> InternalLinkSuggestion:
    row = session.get(InternalLinkSuggestion, suggestion_id)
    if not row:
        raise NotFoundError("Link suggestion not found")
    source = session.get(ContentAsset, row.content_asset_id)
    if not source:
        raise NotFoundError("Source content missing")
    ids = owned_project_ids(session, user)
    if source.project_id not in ids:
        raise ForbiddenError("You do not own this suggestion")
    return row


def approve_and_insert(session: Session, user: User, suggestion_id: UUID, *, auto: bool = False) -> dict:
    row = _owned_suggestion(session, user, suggestion_id)
    if row.status == SuggestionStatus.INSERTED.value:
        return {"suggestion": serialize_suggestion(session, row), "already_inserted": True}
    if row.status == SuggestionStatus.REJECTED.value:
        raise BadRequestError("Rejected suggestions cannot be inserted")

    source = session.get(ContentAsset, row.content_asset_id)
    target = session.get(ContentAsset, row.target_content_id)
    assert source and target
    if source.project_id != target.project_id:
        raise ForbiddenError("Cross-project internal links are not allowed")

    target_page = session.scalar(
        select(PublicPage).where(
            PublicPage.content_id == target.id,
            PublicPage.status == "published",
            PublicPage.visibility == "public",
        )
    )
    if not target_page:
        raise BadRequestError("Target must be a published public page before linking")

    path = _internal_path(target_page.slug)
    # Absolute public URL preferred for public pages, keep path-safe internal
    public_url = target_page.public_url or public_page_service.build_public_url(target_page.slug)

    # Duplicate guard
    existing = session.scalar(
        select(ContentLink).where(
            ContentLink.content_asset_id == source.id,
            or_(
                ContentLink.target_content_id == target.id,
                ContentLink.target_url.in_([path, public_url, f"/p/{target_page.slug}"]),
            ),
        )
    )
    if existing:
        row.status = SuggestionStatus.INSERTED.value
        row.target_path = path
        session.flush()
        return {"suggestion": serialize_suggestion(session, row), "already_inserted": True, "link_id": str(existing.id)}

    settings = _settings(get_owned_project(session, user, source.project_id))
    outgoing_count = session.scalar(
        select(func.count()).select_from(ContentLink).where(ContentLink.content_asset_id == source.id)
    ) or 0
    if outgoing_count >= int(settings["max_new_links_per_article"]) + 10:
        raise BadRequestError("This article already has many outgoing links — review link density first")

    seo_before = source.seo_score
    seo_enrichment._snapshot_version(session, source, user, "Pre-internal-link insertion")

    anchor = row.anchor_text.strip()
    link_html = f'<a href="{path}">{anchor}</a>'
    html = source.content or ""
    # Avoid duplicate anchors already linked
    if f'href="{path}"' in html or f"href='{path}'" in html:
        pass
    elif anchor.lower() in _plain(html).lower() and anchor in html:
        html = html.replace(anchor, link_html, 1)
    elif row.context and row.context in html:
        html = html.replace(row.context, row.context.replace(anchor, link_html) if anchor in row.context else f"{row.context} {link_html}", 1)
    else:
        # Insert near end of first suitable paragraph
        paras = list(re.finditer(r"(?is)(<p[^>]*>)(.*?)(</p>)", html))
        inserted = False
        if paras:
            idx = min(2, len(paras) - 1)
            m = paras[idx]
            inner = m.group(2)
            if anchor.lower() in inner.lower():
                new_inner = re.sub(re.escape(anchor), link_html, inner, count=1, flags=re.I)
            else:
                new_inner = f"{inner.rstrip()} {link_html}"
            html = html[: m.start()] + f"{m.group(1)}{new_inner}{m.group(3)}" + html[m.end() :]
            inserted = True
        if not inserted:
            html = html + f"<p>{link_html}</p>"

    source.content = sanitize_html(html)
    source.word_count = count_words(source.content)

    link = ContentLink(
        content_asset_id=source.id,
        target_url=path,
        target_content_id=target.id,
        anchor_text=anchor,
        placement_description=row.placement or row.source_section or "Internal contextual link",
        link_attribute=LinkAttribute.STANDARD.value,
        status=LinkStatus.INSERTED.value,
    )
    session.add(link)
    seo_enrichment._snapshot_version(session, source, user, "Internal link inserted")
    row.status = SuggestionStatus.INSERTED.value
    row.target_path = path
    session.flush()

    seo_after = None
    try:
        result = seo_enrichment.analyze_seo(session, user, source.id, force=True)
        seo_after = result.get("overall_score") or source.seo_score
    except Exception:
        seo_after = source.seo_score

    # Touch public page updated_at via content; published version not auto-updated (Phase 6 rule).
    # Offer flag for newer content on source page.
    source_page = session.scalar(select(PublicPage).where(PublicPage.content_id == source.id))
    if source_page and source_page.status == "published":
        source_page.updated_at = datetime.now(UTC)

    return {
        "suggestion": serialize_suggestion(session, row),
        "link": {
            "id": str(link.id),
            "target_url": link.target_url,
            "anchor_text": link.anchor_text,
            "target_content_id": str(target.id),
        },
        "seo_before": seo_before,
        "seo_after": seo_after,
        "auto": auto,
        "note": "Internal link inserted. SEO rechecked. Live public page uses published version until explicitly updated.",
    }


def network_overview(session: Session, user: User, project_id: UUID) -> dict:
    get_owned_project(session, user, project_id)
    pages = _eligible_pages(session, project_id)
    content_ids = [c.id for _, c in pages]
    slug_by_content = {c.id: p.slug for p, c in pages}
    content_by_slug = {p.slug: c.id for p, c in pages}

    links = []
    if content_ids:
        links = list(
            session.scalars(select(ContentLink).where(ContentLink.content_asset_id.in_(content_ids)))
        )

    internal_edges = []
    broken = []
    incoming: dict[UUID, int] = {cid: 0 for cid in content_ids}
    outgoing: dict[UUID, int] = {cid: 0 for cid in content_ids}
    anchors_by_target: dict[UUID, list[str]] = {cid: [] for cid in content_ids}

    for link in links:
        slug = _resolve_slug_from_url(link.target_url)
        target_id = link.target_content_id
        if not target_id and slug:
            target_id = content_by_slug.get(slug)
        if target_id and target_id in incoming:
            outgoing[link.content_asset_id] = outgoing.get(link.content_asset_id, 0) + 1
            incoming[target_id] = incoming.get(target_id, 0) + 1
            anchors_by_target[target_id].append(link.anchor_text)
            internal_edges.append(
                {
                    "id": str(link.id),
                    "source_content_id": str(link.content_asset_id),
                    "target_content_id": str(target_id),
                    "anchor_text": link.anchor_text,
                    "target_url": link.target_url,
                    "status": "valid",
                }
            )
        elif slug or (link.target_url or "").startswith("/p/"):
            src = session.get(ContentAsset, link.content_asset_id)
            broken.append(
                {
                    "id": str(link.id),
                    "source_content_id": str(link.content_asset_id),
                    "source_title": src.title if src else None,
                    "target_url": link.target_url,
                    "anchor_text": link.anchor_text,
                    "status": "broken",
                    "reason": "Target public page missing, unpublished, or invalid slug",
                }
            )

    orphans = []
    nodes = []
    seo_scores = []
    for page, content in pages:
        inc = incoming.get(content.id, 0)
        out = outgoing.get(content.id, 0)
        words = content.word_count or count_words(content.content or "")
        density = "healthy"
        if words and out > 0 and (out / max(words / 250, 1)) > 8:
            density = "excessive"
        elif out == 0 and inc == 0:
            density = "isolated"
        if content.seo_score is not None:
            seo_scores.append(content.seo_score)
        node = {
            "content_id": str(content.id),
            "page_id": str(page.id),
            "title": content.title,
            "slug": page.slug,
            "public_url": page.public_url or public_page_service.build_public_url(page.slug),
            "seo_score": content.seo_score,
            "incoming_links": inc,
            "outgoing_links": out,
            "orphan": inc == 0,
            "link_density": density,
            "status": page.status,
        }
        nodes.append(node)
        if inc == 0:
            orphans.append(node)

    # Anchor diversity
    diversity = []
    for tid, anchors in anchors_by_target.items():
        if len(anchors) < 2:
            continue
        unique = len({a.lower().strip() for a in anchors})
        diversity.append(
            {
                "target_content_id": str(tid),
                "target_title": (session.get(ContentAsset, tid).title if session.get(ContentAsset, tid) else None),
                "anchor_count": len(anchors),
                "unique_anchors": unique,
                "recommendation": "Diversify anchors" if unique / max(len(anchors), 1) < 0.5 else "Healthy diversity",
            }
        )

    health_score = 100
    health_score -= min(30, len(orphans) * 8)
    health_score -= min(25, len(broken) * 10)
    excessive = sum(1 for n in nodes if n["link_density"] == "excessive")
    health_score -= min(20, excessive * 5)
    health_score = max(0, health_score)

    suggested = session.scalar(
        select(func.count()).select_from(InternalLinkSuggestion).where(
            InternalLinkSuggestion.project_id == project_id,
            InternalLinkSuggestion.status == SuggestionStatus.SUGGESTED.value,
        )
    ) or 0

    return {
        "project_id": str(project_id),
        "total_pages": len(nodes),
        "total_internal_links": len(internal_edges),
        "orphan_pages": len(orphans),
        "broken_links": len(broken),
        "pending_suggestions": int(suggested),
        "link_health_score": health_score,
        "average_seo_score": int(round(sum(seo_scores) / len(seo_scores))) if seo_scores else None,
        "nodes": nodes,
        "edges": internal_edges,
        "orphans": orphans,
        "broken": broken,
        "anchor_diversity": diversity[:30],
        "terminology": {
            "internal_link": "Same-domain link between your public pages.",
            "backlink": "A link from another website/domain to your website.",
            "external_link": "A link from your page to another website.",
            "target_link": "User-provided external destination URL.",
        },
    }


def orphan_opportunities(session: Session, user: User, project_id: UUID, content_id: UUID) -> list[dict]:
    overview = network_overview(session, user, project_id)
    orphan = next((n for n in overview["orphans"] if n["content_id"] == str(content_id)), None)
    if not orphan:
        raise BadRequestError("Content is not an orphan published page in this project")
    target = session.get(ContentAsset, content_id)
    assert target
    target_tokens = _tokens(f"{target.title} {_plain(target.content)[:800]}")
    ideas = []
    for node in overview["nodes"]:
        if node["content_id"] == str(content_id):
            continue
        source = session.get(ContentAsset, UUID(node["content_id"]))
        if not source:
            continue
        score = int(_jaccard(target_tokens, _tokens(f"{source.title} {_plain(source.content)[:800]}")) * 100)
        if score < 30:
            continue
        ideas.append(
            {
                "source_content_id": node["content_id"],
                "source_title": node["title"],
                "target_content_id": str(content_id),
                "target_title": target.title,
                "relevance_score": score,
                "recommended_anchor": target.title[:80],
            }
        )
    ideas.sort(key=lambda x: x["relevance_score"], reverse=True)
    return ideas[:10]


def create_suggestion_from_opportunity(
    session: Session,
    user: User,
    *,
    project_id: UUID,
    source_content_id: UUID,
    target_content_id: UUID,
    anchor_text: str | None = None,
) -> dict:
    get_owned_project(session, user, project_id)
    source = session.get(ContentAsset, source_content_id)
    target = session.get(ContentAsset, target_content_id)
    if not source or not target:
        raise NotFoundError("Content not found")
    if source.project_id != project_id or target.project_id != project_id:
        raise ForbiddenError("Cross-project linking is not allowed")
    target_page = session.scalar(
        select(PublicPage).where(
            PublicPage.content_id == target.id,
            PublicPage.status == "published",
            PublicPage.visibility == "public",
        )
    )
    if not target_page:
        raise BadRequestError("Target must be published")
    row = InternalLinkSuggestion(
        content_asset_id=source.id,
        target_content_id=target.id,
        project_id=project_id,
        source_section="Recommended for orphan recovery",
        anchor_text=(anchor_text or target.title)[:500],
        target_path=_internal_path(target_page.slug),
        reason="Suggested to reduce orphan status with a relevant contextual internal link.",
        relevance_score=75,
        confidence_score=80,
        placement="Related paragraph",
        suggestion_type="contextual",
        status=SuggestionStatus.SUGGESTED.value,
    )
    session.add(row)
    session.flush()
    return serialize_suggestion(session, row)


def remove_broken_link(session: Session, user: User, link_id: UUID) -> dict:
    from app.services.ownership import get_owned_link

    link = get_owned_link(session, user, link_id)
    link.status = LinkStatus.REMOVED.value
    session.flush()
    return {"id": str(link.id), "status": link.status}


def update_links_for_slug_change(
    session: Session,
    user: User,
    *,
    project_id: UUID,
    old_slug: str,
    new_slug: str,
    public_page_id: UUID | None = None,
) -> dict:
    get_owned_project(session, user, project_id)
    old_path = _internal_path(old_slug)
    new_path = _internal_path(new_slug)
    redirect = session.scalar(select(PublicSlugRedirect).where(PublicSlugRedirect.old_slug == old_slug))
    if redirect:
        redirect.new_slug = new_slug
        redirect.public_page_id = public_page_id
    else:
        session.add(
            PublicSlugRedirect(
                project_id=project_id,
                public_page_id=public_page_id,
                old_slug=old_slug,
                new_slug=new_slug,
            )
        )
    updated = 0
    links = list(
        session.scalars(
            select(ContentLink).where(
                or_(
                    ContentLink.target_url == old_path,
                    ContentLink.target_url.like(f"%/p/{old_slug}"),
                )
            )
        )
    )
    for link in links:
        content = session.get(ContentAsset, link.content_asset_id)
        if not content or content.project_id != project_id:
            continue
        ids = owned_project_ids(session, user)
        if content.project_id not in ids:
            continue
        html = content.content or ""
        content.content = sanitize_html(html.replace(old_path, new_path).replace(f"/p/{old_slug}", new_path))
        link.target_url = new_path
        updated += 1
    # Update suggestion paths
    suggestions = list(
        session.scalars(
            select(InternalLinkSuggestion).where(InternalLinkSuggestion.target_path == old_path)
        )
    )
    for s in suggestions:
        s.target_path = new_path
    session.flush()
    return {"updated_links": updated, "old_slug": old_slug, "new_slug": new_slug, "redirect_created": True}


def resolve_slug_redirect(session: Session, slug: str) -> str | None:
    row = session.scalar(select(PublicSlugRedirect).where(PublicSlugRedirect.old_slug == slug))
    return row.new_slug if row else None


def related_for_page(session: Session, page: PublicPage, *, limit: int = 3) -> list[dict]:
    """Related published pages for public rendering (cards)."""
    content = session.get(ContentAsset, page.content_id)
    if not content:
        return []
    # Prefer approved/inserted suggestions as related cards
    rows = list(
        session.scalars(
            select(InternalLinkSuggestion)
            .where(
                InternalLinkSuggestion.content_asset_id == content.id,
                InternalLinkSuggestion.status.in_(
                    [
                        SuggestionStatus.APPROVED.value,
                        SuggestionStatus.INSERTED.value,
                        SuggestionStatus.SUGGESTED.value,
                    ]
                ),
            )
            .order_by(InternalLinkSuggestion.relevance_score.desc())
            .limit(limit * 2)
        )
    )
    out = []
    seen = set()
    for row in rows:
        target_page = session.scalar(
            select(PublicPage).where(
                PublicPage.content_id == row.target_content_id,
                PublicPage.status == "published",
                PublicPage.visibility == "public",
            )
        )
        if not target_page or target_page.id == page.id or target_page.slug in seen:
            continue
        seen.add(target_page.slug)
        out.append(
            {
                "title": target_page.title,
                "slug": target_page.slug,
                "public_url": target_page.public_url or public_page_service.build_public_url(target_page.slug),
                "relevance_score": row.relevance_score,
            }
        )
        if len(out) >= limit:
            break
    if len(out) >= limit:
        return out
    # Fallback: overview similarity among published
    others = _eligible_pages(session, page.project_id)
    src_tokens = _tokens(f"{content.title} {_plain(content.content)[:600]}")
    ranked = []
    for other_page, other_content in others:
        if other_page.id == page.id or other_page.slug in seen:
            continue
        score = int(_jaccard(src_tokens, _tokens(f"{other_content.title} {_plain(other_content.content)[:600]}")) * 100)
        if score < 20:
            continue
        ranked.append((score, other_page))
    ranked.sort(key=lambda x: x[0], reverse=True)
    for score, other_page in ranked:
        out.append(
            {
                "title": other_page.title,
                "slug": other_page.slug,
                "public_url": other_page.public_url or public_page_service.build_public_url(other_page.slug),
                "relevance_score": score,
            }
        )
        if len(out) >= limit:
            break
    return out
