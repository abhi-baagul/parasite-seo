"""Phase 8 — Backlink campaign builder + tiered link network."""

from __future__ import annotations

import csv
import io
import json
import re
from collections import Counter
from datetime import UTC, datetime
from urllib.parse import urlparse
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.integrations.publishing_providers import (
    domain_from_url,
    get_publishing_provider,
)
from app.models.backlink_campaign import (
    Backlink,
    BacklinkCampaign,
    BacklinkCheck,
    CampaignAsset,
    CampaignJob,
    CampaignLog,
    CampaignMediaUsage,
    CampaignStrategyTemplate,
    CampaignTask,
    ContentBucket,
    OutreachActivity,
    OutreachProspect,
    PublishingDestination,
)
from app.models.content import ContentAsset, ContentVersion
from app.models.enums import ContentStatus, ContentType
from app.models.media import MediaAsset
from app.models.parasite_seo import ParasiteSEOJob
from app.models.project import Project
from app.models.public_page import PublicPage
from app.models.user import User
from app.services.campaign_intelligence import (
    HYBRID_BLUEPRINT,
    build_asset_html,
    classify_link_kind,
    heading_outline,
    link_groups_for,
    media_snippet,
    recommend_strategy,
    recommended_anchors,
    redact,
    size_reason,
    supporting_topics,
)
from app.services.ownership import get_owned_project, owned_project_ids
from app.storage import get_storage_provider
from app.utils.html_sanitize import count_words, sanitize_html
from app.utils.url_safety import slugify, validate_safe_url

DISCLOSURE = (
    "Link acquisition and SEO metrics are informational. "
    "Search engines independently determine crawling, indexing, ranking, and link treatment."
)

DEFAULT_BLUEPRINTS = {
    "single_asset": {"tier1": 1, "tier2": 0, "cloud": 0, "pr": 0, "outreach": 0, "max_tier_depth": 1},
    "multi_asset": {"tier1": 3, "tier2": 0, "cloud": 0, "pr": 0, "outreach": 0, "max_tier_depth": 1},
    "tiered_network": {"tier1": 5, "tier2": 10, "cloud": 0, "pr": 0, "outreach": 0, "max_tier_depth": 2},
    "cloud_network": {"tier1": 0, "tier2": 0, "cloud": 3, "pr": 0, "outreach": 0, "max_tier_depth": 1},
    "digital_pr": {"tier1": 1, "tier2": 0, "cloud": 0, "pr": 1, "outreach": 0, "max_tier_depth": 1},
    "authorized_outreach": {"tier1": 0, "tier2": 0, "cloud": 0, "pr": 0, "outreach": 10, "max_tier_depth": 1},
    "hybrid": dict(HYBRID_BLUEPRINT),
}

VARIANT_ANGLES = [
    "for students",
    "for remote teams",
    "for developers",
    "for beginners",
    "comparison guide",
    "2026 overview",
    "practical workflows",
    "buying checklist",
    "productivity habits",
    "team collaboration",
    "for computer science students",
    "for AI development",
]


def add_campaign_log(
    session: Session,
    campaign_id: UUID,
    message: str,
    *,
    level: str = "info",
    task_id: UUID | None = None,
    meta: dict | None = None,
) -> None:
    session.add(
        CampaignLog(
            campaign_id=campaign_id,
            task_id=task_id,
            level=level,
            message=redact(message),
            meta=meta or {},
        )
    )


def _group_progress(assets: list[CampaignAsset]) -> list[dict]:
    groups: dict[str, dict] = {}
    for asset in assets:
        name = asset.link_group or asset.asset_type
        row = groups.setdefault(
            name,
            {"id": name, "name": name.replace("_", " ").title(), "tier": asset.tier, "total": 0, "done": 0, "status": "queued"},
        )
        row["total"] += 1
        if asset.status in {"published", "verified", "completed"}:
            row["done"] += 1
        elif asset.status in {"publishing", "running", "generated", "approved"}:
            row["status"] = "running"
        elif asset.status == "failed":
            row["status"] = "failed"
    out = []
    for row in groups.values():
        pct = int(round(100 * row["done"] / max(row["total"], 1)))
        status = "completed" if pct == 100 else row["status"]
        if row["done"] == 0 and status != "failed":
            status = "queued"
        out.append({**row, "progress": pct, "status": status})
    return out


def _owned_campaign(session: Session, user: User, campaign_id: UUID) -> BacklinkCampaign:
    campaign = session.get(BacklinkCampaign, campaign_id)
    if not campaign:
        raise NotFoundError("Campaign not found")
    ids = owned_project_ids(session, user)
    if campaign.project_id not in ids and campaign.user_id != user.id:
        raise ForbiddenError("You do not own this campaign")
    return campaign


def _progress(campaign: BacklinkCampaign, session: Session) -> int:
    assets = list(session.scalars(select(CampaignAsset).where(CampaignAsset.campaign_id == campaign.id)))
    if not assets:
        return min(campaign.wizard_step * 8, 40)
    done = sum(1 for a in assets if a.status in {"published", "verified", "generated", "approved"})
    return min(100, int(round(100 * done / max(len(assets), 1))))


def serialize_campaign(session: Session, campaign: BacklinkCampaign, *, detail: bool = False) -> dict:
    assets = list(session.scalars(select(CampaignAsset).where(CampaignAsset.campaign_id == campaign.id)))
    links = list(session.scalars(select(Backlink).where(Backlink.campaign_id == campaign.id)))
    prospects = list(session.scalars(select(OutreachProspect).where(OutreachProspect.campaign_id == campaign.id)))
    counts = {
        "assets": len(assets),
        "tier1": sum(1 for a in assets if a.tier == 1),
        "tier2": sum(1 for a in assets if a.tier == 2),
        "cloud": sum(1 for a in assets if a.asset_type == "cloud"),
        "pr": sum(1 for a in assets if a.asset_type == "pr"),
        "published": sum(1 for a in assets if a.status in {"published", "verified"}),
        "verified_backlinks": sum(1 for b in links if b.status == "verified"),
        "lost_backlinks": sum(1 for b in links if b.status == "lost"),
        "broken_backlinks": sum(1 for b in links if b.status == "broken"),
        "planned_backlinks": sum(1 for b in links if b.status == "planned"),
        "referring_domains": len({b.source_domain for b in links if b.status == "verified" and b.link_kind != "internal"}),
        "outreach": len(prospects),
        "internal_links": sum(1 for b in links if b.link_kind == "internal"),
        "mock_backlinks": sum(1 for b in links if b.is_mock),
    }
    data = {
        "id": str(campaign.id),
        "project_id": str(campaign.project_id),
        "name": campaign.name,
        "strategy_type": campaign.strategy_type,
        "status": campaign.status,
        "wizard_step": campaign.wizard_step,
        "target_url": campaign.target_url,
        "target_content_id": str(campaign.target_content_id) if campaign.target_content_id else None,
        "target_public_page_id": str(campaign.target_public_page_id) if campaign.target_public_page_id else None,
        "primary_keyword": campaign.primary_keyword,
        "secondary_keywords": campaign.secondary_keywords or [],
        "country": campaign.country,
        "language": campaign.language,
        "niche": campaign.niche,
        "target_audience": campaign.target_audience,
        "blueprint": campaign.blueprint or {},
        "settings": campaign.settings or {},
        "disclosure": campaign.disclosure or DISCLOSURE,
        "bucket_id": str(campaign.bucket_id) if campaign.bucket_id else None,
        "progress_percent": _progress(campaign, session),
        "counts": counts,
        "mock_mode": bool(getattr(campaign, "mock_mode", True)),
        "approved_at": campaign.approved_at.isoformat() if getattr(campaign, "approved_at", None) else None,
        "archived_at": campaign.archived_at.isoformat() if getattr(campaign, "archived_at", None) else None,
        "parasite_job_id": str(campaign.parasite_job_id) if getattr(campaign, "parasite_job_id", None) else None,
        "intelligence": campaign.intelligence or {},
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
    }
    if detail:
        data["assets"] = [serialize_asset(a) for a in assets]
        data["backlinks"] = [serialize_backlink(b) for b in links]
        data["prospects"] = [serialize_prospect(p) for p in prospects]
        data["graph"] = build_graph(campaign, assets, links)
        data["anchor_distribution"] = anchor_distribution(links)
        data["report"] = campaign_report(session, campaign)
        data["link_groups"] = _group_progress(assets)
        data["logs"] = [
            serialize_log(row)
            for row in session.scalars(
                select(CampaignLog).where(CampaignLog.campaign_id == campaign.id).order_by(CampaignLog.created_at.desc()).limit(200)
            )
        ][::-1]
        data["tasks"] = [
            serialize_task(row)
            for row in session.scalars(select(CampaignTask).where(CampaignTask.campaign_id == campaign.id))
        ]
        data["media_usage"] = serialize_media_usage(session, campaign.id)
    return data


def serialize_asset(asset: CampaignAsset) -> dict:
    return {
        "id": str(asset.id),
        "campaign_id": str(asset.campaign_id),
        "content_id": str(asset.content_id) if asset.content_id else None,
        "master_content_id": str(asset.master_content_id) if asset.master_content_id else None,
        "destination_id": str(asset.destination_id) if asset.destination_id else None,
        "title": asset.title,
        "asset_type": asset.asset_type,
        "link_group": asset.link_group,
        "tier": asset.tier,
        "topic": asset.topic,
        "variant_angle": asset.variant_angle,
        "relevance_score": asset.relevance_score,
        "is_mock": bool(asset.is_mock),
        "status": asset.status,
        "source_url": asset.source_url,
        "target_url": asset.target_url,
        "parent_asset_id": str(asset.parent_asset_id) if asset.parent_asset_id else None,
        "anchor_text": asset.anchor_text,
        "link_attribute": asset.link_attribute,
        "placement": asset.placement,
        "quality_score": asset.quality_score,
        "seo_score": asset.seo_score,
        "meta": asset.meta or {},
    }


def serialize_backlink(link: Backlink) -> dict:
    return {
        "id": str(link.id),
        "campaign_id": str(link.campaign_id),
        "asset_id": str(link.asset_id) if link.asset_id else None,
        "source_url": link.source_url,
        "source_domain": link.source_domain,
        "target_url": link.target_url,
        "target_content_id": str(link.target_content_id) if link.target_content_id else None,
        "anchor_text": link.anchor_text,
        "attribute": link.attribute,
        "tier": link.tier,
        "source_type": link.source_type,
        "link_kind": link.link_kind,
        "is_mock": bool(link.is_mock),
        "indexed_status": link.indexed_status,
        "status": link.status,
        "first_seen": link.first_seen.isoformat() if link.first_seen else None,
        "last_seen": link.last_seen.isoformat() if link.last_seen else None,
        "last_checked_at": link.last_checked_at.isoformat() if link.last_checked_at else None,
        "notes": link.notes,
    }


def serialize_prospect(p: OutreachProspect) -> dict:
    return {
        "id": str(p.id),
        "campaign_id": str(p.campaign_id),
        "website": p.website,
        "contact_name": p.contact_name,
        "email": p.email,
        "topic": p.topic,
        "relevance_score": p.relevance_score,
        "status": p.status,
        "draft_subject": p.draft_subject,
        "draft_body": p.draft_body,
        "notes": p.notes,
    }


def serialize_destination(d: PublishingDestination) -> dict:
    return {
        "id": str(d.id),
        "project_id": str(d.project_id),
        "name": d.name,
        "provider_type": d.provider_type,
        "base_url": d.base_url,
        "configuration": {k: v for k, v in (d.configuration or {}).items() if k != "secret"},
        "is_active": d.is_active,
        "test_status": d.test_status,
        "authorization_status": d.authorization_status,
        "last_tested_at": d.last_tested_at.isoformat() if d.last_tested_at else None,
        # credentials_ref never exposed
    }


def serialize_log(row: CampaignLog) -> dict:
    return {
        "id": str(row.id),
        "campaign_id": str(row.campaign_id),
        "task_id": str(row.task_id) if row.task_id else None,
        "level": row.level,
        "message": row.message,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def serialize_task(row: CampaignTask) -> dict:
    return {
        "id": str(row.id),
        "campaign_id": str(row.campaign_id),
        "asset_id": str(row.asset_id) if row.asset_id else None,
        "group": row.group_name,
        "tier": row.tier,
        "task_type": row.task_type,
        "status": row.status,
        "progress": row.progress,
        "error": row.error_message,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
    }


def serialize_media_usage(session: Session, campaign_id: UUID) -> list[dict]:
    rows = list(session.scalars(select(CampaignMediaUsage).where(CampaignMediaUsage.campaign_id == campaign_id)))
    by_media: dict[str, dict] = {}
    for row in rows:
        key = str(row.media_id)
        item = by_media.setdefault(key, {"media_id": key, "usage_count": 0, "asset_ids": []})
        item["usage_count"] += row.usage_count or 1
        if row.asset_id:
            item["asset_ids"].append(str(row.asset_id))
    return list(by_media.values())


def list_campaigns(
    session: Session,
    user: User,
    project_id: UUID | None = None,
    *,
    include_archived: bool = False,
) -> list[dict]:
    ids = owned_project_ids(session, user)
    stmt = select(BacklinkCampaign).where(BacklinkCampaign.project_id.in_(ids)).order_by(BacklinkCampaign.updated_at.desc())
    if not include_archived:
        stmt = stmt.where(BacklinkCampaign.archived_at.is_(None))
    if project_id:
        if project_id not in ids:
            raise ForbiddenError("Project not owned")
        stmt = stmt.where(BacklinkCampaign.project_id == project_id)
    return [serialize_campaign(session, c) for c in session.scalars(stmt.limit(100))]


def create_campaign(
    session: Session,
    user: User,
    *,
    project_id: UUID,
    name: str,
    strategy_type: str = "tiered_network",
    target_url: str | None = None,
    target_public_page_id: UUID | None = None,
    primary_keyword: str | None = None,
    secondary_keywords: list[str] | None = None,
    country: str | None = None,
    language: str | None = None,
    niche: str | None = None,
    target_audience: str | None = None,
    blueprint: dict | None = None,
    parasite_job_id: UUID | None = None,
    mock_mode: bool = True,
    intelligence: dict | None = None,
) -> dict:
    get_owned_project(session, user, project_id)
    if strategy_type not in DEFAULT_BLUEPRINTS:
        raise BadRequestError("Unknown strategy type")
    target_content_id = None
    resolved_url = target_url
    if target_public_page_id:
        page = session.get(PublicPage, target_public_page_id)
        if not page or page.project_id != project_id:
            raise BadRequestError("Target public page not found in this project")
        if page.status != "published" or page.visibility != "public":
            raise BadRequestError("Target must be a published public page")
        target_content_id = page.content_id
        resolved_url = page.public_url or f"/p/{page.slug}"
    elif target_url:
        try:
            validate_safe_url(target_url, allow_http=True)
        except BadRequestError:
            if not target_url.startswith("/p/"):
                raise
    bp = dict(DEFAULT_BLUEPRINTS[strategy_type])
    if blueprint:
        bp.update(blueprint)
    bp["max_tier_depth"] = int(bp.get("max_tier_depth") or 2)
    if bp["max_tier_depth"] not in {1, 2, 3}:
        raise BadRequestError("max_tier_depth must be 1, 2, or 3")

    campaign = BacklinkCampaign(
        project_id=project_id,
        user_id=user.id,
        name=name.strip()[:200],
        strategy_type=strategy_type,
        status="draft",
        wizard_step=1,
        target_url=resolved_url,
        target_content_id=target_content_id,
        target_public_page_id=target_public_page_id,
        primary_keyword=primary_keyword,
        secondary_keywords=secondary_keywords or [],
        country=country,
        language=language,
        niche=niche,
        target_audience=target_audience,
        blueprint=bp,
        settings={"automatic_publish": False},
        disclosure=DISCLOSURE,
        parasite_job_id=parasite_job_id,
        mock_mode=mock_mode,
        intelligence=intelligence or {},
    )
    session.add(campaign)
    session.flush()
    return serialize_campaign(session, campaign, detail=True)


def update_campaign(session: Session, user: User, campaign_id: UUID, payload: dict) -> dict:
    campaign = _owned_campaign(session, user, campaign_id)
    allowed = {
        "name",
        "primary_keyword",
        "secondary_keywords",
        "country",
        "language",
        "niche",
        "target_audience",
        "wizard_step",
        "status",
        "blueprint",
        "settings",
        "bucket_id",
        "target_url",
        "target_public_page_id",
        "strategy_type",
    }
    for key, value in payload.items():
        if key not in allowed:
            continue
        if key == "target_public_page_id" and value:
            page = session.get(PublicPage, UUID(str(value)))
            if not page or page.project_id != campaign.project_id:
                raise BadRequestError("Invalid target page")
            campaign.target_public_page_id = page.id
            campaign.target_content_id = page.content_id
            campaign.target_url = page.public_url or f"/p/{page.slug}"
        elif key == "bucket_id":
            campaign.bucket_id = UUID(str(value)) if value else None
        elif key == "blueprint" and isinstance(value, dict):
            bp = dict(campaign.blueprint or {})
            bp.update(value)
            campaign.blueprint = bp
        elif key == "status" and value == "paused":
            campaign.status = "paused"
        else:
            setattr(campaign, key, value)
    session.flush()
    return serialize_campaign(session, campaign, detail=True)


def get_campaign(session: Session, user: User, campaign_id: UUID) -> dict:
    return serialize_campaign(session, _owned_campaign(session, user, campaign_id), detail=True)


def list_strategy_templates(session: Session, user: User, project_id: UUID) -> list[dict]:
    get_owned_project(session, user, project_id)
    # Ensure system templates exist
    _ensure_system_templates(session)
    rows = session.scalars(
        select(CampaignStrategyTemplate).where(
            (CampaignStrategyTemplate.is_system.is_(True))
            | (CampaignStrategyTemplate.project_id == project_id)
        )
    )
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "strategy_type": r.strategy_type,
            "blueprint": r.blueprint,
            "is_system": r.is_system,
        }
        for r in rows
    ]


def _ensure_system_templates(session: Session) -> None:
    existing = {
        r.strategy_type
        for r in session.scalars(select(CampaignStrategyTemplate).where(CampaignStrategyTemplate.is_system.is_(True)))
    }
    names = {
        "single_asset": "Single Asset",
        "multi_asset": "Multi-Asset",
        "tiered_network": "Standard Tiered Campaign",
        "cloud_network": "Cloud Content Network",
        "digital_pr": "Digital PR",
        "authorized_outreach": "Authorized Outreach",
        "hybrid": "Hybrid Tiered Content Network",
    }
    for key, bp in DEFAULT_BLUEPRINTS.items():
        if key in existing:
            continue
        session.add(
            CampaignStrategyTemplate(
                project_id=None,
                name=names[key],
                strategy_type=key,
                blueprint=bp,
                is_system=True,
            )
        )
    session.flush()


def save_strategy_template(
    session: Session, user: User, project_id: UUID, *, name: str, strategy_type: str, blueprint: dict
) -> dict:
    get_owned_project(session, user, project_id)
    row = CampaignStrategyTemplate(
        project_id=project_id,
        name=name[:200],
        strategy_type=strategy_type,
        blueprint=blueprint,
        is_system=False,
    )
    session.add(row)
    session.flush()
    return {"id": str(row.id), "name": row.name, "strategy_type": row.strategy_type, "blueprint": row.blueprint}


def create_bucket(
    session: Session,
    user: User,
    project_id: UUID,
    *,
    name: str,
    topics: list[str] | None = None,
    keywords: list[str] | None = None,
    niche: str | None = None,
) -> dict:
    get_owned_project(session, user, project_id)
    bucket = ContentBucket(
        project_id=project_id,
        name=name[:200],
        niche=niche,
        topics=topics or [],
        keywords=keywords or [],
    )
    session.add(bucket)
    session.flush()
    return {
        "id": str(bucket.id),
        "name": bucket.name,
        "topics": bucket.topics,
        "keywords": bucket.keywords,
        "niche": bucket.niche,
    }


def list_buckets(session: Session, user: User, project_id: UUID) -> list[dict]:
    get_owned_project(session, user, project_id)
    rows = session.scalars(select(ContentBucket).where(ContentBucket.project_id == project_id))
    return [
        {"id": str(b.id), "name": b.name, "topics": b.topics, "keywords": b.keywords, "niche": b.niche}
        for b in rows
    ]


def create_destination(
    session: Session,
    user: User,
    project_id: UUID,
    *,
    name: str,
    provider_type: str = "mock_local",
    base_url: str | None = None,
    configuration: dict | None = None,
) -> dict:
    get_owned_project(session, user, project_id)
    try:
        get_publishing_provider(provider_type)
    except ValueError as exc:
        raise BadRequestError(str(exc)) from exc
    dest = PublishingDestination(
        project_id=project_id,
        name=name[:200],
        provider_type=provider_type,
        base_url=base_url,
        configuration=configuration or {},
        credentials_ref=None,
        is_active=True,
        authorization_status="authorized" if provider_type in {"mock_local", "cloud_static", "aws_s3", "azure_blob", "gcs"} else "pending",
    )
    session.add(dest)
    session.flush()
    return serialize_destination(dest)


def list_destinations(session: Session, user: User, project_id: UUID) -> list[dict]:
    get_owned_project(session, user, project_id)
    rows = session.scalars(select(PublishingDestination).where(PublishingDestination.project_id == project_id))
    return [serialize_destination(d) for d in rows]


def test_destination(session: Session, user: User, destination_id: UUID) -> dict:
    dest = session.get(PublishingDestination, destination_id)
    if not dest:
        raise NotFoundError("Destination not found")
    get_owned_project(session, user, dest.project_id)
    provider = get_publishing_provider(dest.provider_type)
    result = provider.test(dest.configuration or {})
    dest.last_tested_at = datetime.now(UTC)
    dest.test_status = "ok" if result.get("ok") else "failed"
    session.flush()
    return {**serialize_destination(dest), "test_result": result}


def _attach_task(session: Session, campaign_id: UUID, asset: CampaignAsset) -> CampaignTask:
    task = CampaignTask(
        campaign_id=campaign_id,
        asset_id=asset.id,
        group_name=asset.link_group,
        tier=asset.tier,
        task_type="generate",
        status="completed",
        progress=100,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )
    session.add(task)
    session.flush()
    return task


def _generate_asset_html(*, title: str, keyword: str, target_url: str, anchor: str, angle: str) -> str:
    return sanitize_html(
        f"<h1>{title}</h1>"
        f"<p>This guide explores {keyword} {angle} with practical, verifiable recommendations.</p>"
        f"<h2>Why {keyword} matters</h2>"
        f"<p>Teams evaluating {keyword} should compare features, privacy, and workflow fit — not hype.</p>"
        f"<h2>Practical workflow</h2>"
        "<ul><li>Define the job to be done</li><li>Shortlist tools</li><li>Pilot claims before buying</li></ul>"
        f"<h2>Related reading</h2>"
        f"<p>For a deeper overview, see {anchor} and confirm details on the official page.</p>"
        f"<h2>FAQ</h2>"
        f"<h3>Is this a ranking guarantee?</h3>"
        "<p>No. Search engines independently determine crawling, indexing, and ranking.</p>"
        f"<p><a href=\"{target_url}\">{anchor}</a></p>"
    )


def generate_assets(session: Session, user: User, campaign_id: UUID) -> dict:
    campaign = _owned_campaign(session, user, campaign_id)
    if not campaign.target_url and campaign.strategy_type != "authorized_outreach":
        raise BadRequestError("Select a target URL or public page before generating assets")
    job = CampaignJob(
        campaign_id=campaign.id,
        job_type="campaign_generation",
        status="running",
        started_at=datetime.now(UTC),
        progress=5,
    )
    session.add(job)
    session.flush()

    try:
        campaign.status = "generating"
        add_campaign_log(session, campaign.id, "Project analysis / asset generation started", level="info")
        bp = dict(campaign.blueprint or DEFAULT_BLUEPRINTS.get(campaign.strategy_type, {}))
        # Hard caps — never auto-create thousands of low-quality pages
        for key, cap in (("tier1", 20), ("tier2", 40), ("cloud", 10), ("pr", 5), ("outreach", 50)):
            bp[key] = max(0, min(int(bp.get(key) or 0), cap))
        keyword = campaign.primary_keyword or campaign.name
        secondary = list(campaign.secondary_keywords or [])
        intel = campaign.intelligence or {}
        bucket = session.get(ContentBucket, campaign.bucket_id) if campaign.bucket_id else None
        topics = list(intel.get("supporting_topics") or [])
        if bucket and bucket.topics:
            for item in bucket.topics:
                if item not in topics:
                    topics.append(item)
        for item in secondary:
            if item not in topics:
                topics.append(item)
        if not topics:
            topics = supporting_topics(keyword=keyword, secondary=secondary, prompt=str(intel.get("prompt") or ""))
        if not topics:
            topics = [keyword]
        anchors = list(intel.get("recommended_anchor_terms") or recommended_anchors(keyword))
        add_campaign_log(session, campaign.id, f"Primary keyword identified: {keyword}", level="success")
        add_campaign_log(session, campaign.id, f"Campaign strategy generated: {campaign.strategy_type}", level="success")
        target = campaign.target_url or ""
        created: list[CampaignAsset] = []
        media_rows = list(
            session.scalars(select(MediaAsset).where(MediaAsset.project_id == campaign.project_id).limit(12))
        )

        # Clear planned-only assets on regen
        for old in session.scalars(
            select(CampaignAsset).where(
                CampaignAsset.campaign_id == campaign.id,
                CampaignAsset.status == "planned",
            )
        ):
            session.delete(old)
        session.flush()

        content_types = ["article", "guide", "comparison", "listicle", "faq"]
        used_titles: set[str] = set()
        tier1_assets: list[CampaignAsset] = []
        for i in range(int(bp.get("tier1") or 0)):
            topic = topics[i % len(topics)]
            title = str(topic)[:300]
            if title.lower() in used_titles:
                title = f"{title} ({i + 1})"[:300]
            used_titles.add(title.lower())
            angle = VARIANT_ANGLES[i % len(VARIANT_ANGLES)]
            ctype = content_types[i % len(content_types)]
            anchor = anchors[i % len(anchors)]
            media_html = ""
            used_media = None
            if media_rows and i % 2 == 0:
                used_media = media_rows[i % len(media_rows)]
                media_html = media_snippet(
                    {"url": used_media.url, "media_type": used_media.media_type},
                    alt=used_media.alt_text or f"{title} illustration",
                )
            html = build_asset_html(
                title=title,
                topic=str(topic),
                keyword=keyword,
                angle=angle,
                content_type=ctype,
                target_url=target,
                anchor=anchor,
                media_html=media_html,
            )
            content = _create_content(session, campaign, title=title, html=html, keyword=keyword)
            asset = CampaignAsset(
                campaign_id=campaign.id,
                content_id=content.id,
                master_content_id=None,
                title=title,
                asset_type="tier1",
                link_group="web_content",
                tier=1,
                topic=str(topic),
                variant_angle=ctype,
                relevance_score=88 + (i % 8),
                status="generated",
                target_url=target,
                anchor_text=anchor,
                link_attribute="standard",
                placement=f"Section 3 related to {keyword}",
                seo_score=content.seo_score,
                quality_score=78,
                meta={"generated": True, "content_type": ctype},
            )
            session.add(asset)
            session.flush()
            _attach_task(session, campaign.id, asset)
            if used_media:
                session.add(
                    CampaignMediaUsage(
                        campaign_id=campaign.id, media_id=used_media.id, asset_id=asset.id, usage_count=1
                    )
                )
            tier1_assets.append(asset)
            created.append(asset)
        add_campaign_log(session, campaign.id, f"Tier 1 assets generated ({len(tier1_assets)})", level="success")

        for i in range(int(bp.get("tier2") or 0)):
            parent = tier1_assets[i % max(len(tier1_assets), 1)] if tier1_assets else None
            topic = topics[(i + 3) % len(topics)]
            title = f"Supporting notes: {topic}"[:300]
            if title.lower() in used_titles:
                title = f"{title} ({i + 1})"[:300]
            used_titles.add(title.lower())
            angle = VARIANT_ANGLES[(i + 3) % len(VARIANT_ANGLES)]
            ctype = content_types[(i + 2) % len(content_types)]
            parent_url = parent.target_url if parent else target
            anchor = (parent.title[:80] if parent else anchors[i % len(anchors)])
            if parent and parent.source_url:
                planned_target = parent.source_url
            elif parent:
                planned_target = f"tier1:{parent.id}"
            else:
                planned_target = target
            html = build_asset_html(
                title=title,
                topic=str(topic),
                keyword=keyword,
                angle=angle,
                content_type=ctype,
                target_url=parent_url or target,
                anchor=anchor,
            )
            content = _create_content(session, campaign, title=title, html=html, keyword=keyword)
            asset = CampaignAsset(
                campaign_id=campaign.id,
                content_id=content.id,
                master_content_id=parent.content_id if parent else None,
                title=title,
                asset_type="tier2",
                link_group="supporting",
                tier=2,
                topic=str(topic),
                variant_angle=ctype,
                relevance_score=70 + (i % 15),
                status="generated",
                target_url=planned_target if isinstance(planned_target, str) else target,
                parent_asset_id=parent.id if parent else None,
                anchor_text=anchor,
                link_attribute="standard",
                placement="Supporting context for the parent Tier 1 asset",
                seo_score=content.seo_score,
                quality_score=75,
                meta={"generated": True, "links_to_tier1": True, "content_type": ctype},
            )
            session.add(asset)
            session.flush()
            _attach_task(session, campaign.id, asset)
            created.append(asset)
        if int(bp.get("tier2") or 0):
            add_campaign_log(session, campaign.id, "Tier 2 assets generated", level="success")

        for i in range(int(bp.get("cloud") or 0)):
            topic = topics[i % len(topics)]
            title = f"Cloud page: {topic}"[:300]
            if title.lower() in used_titles:
                title = f"{title} ({i + 1})"[:300]
            used_titles.add(title.lower())
            ctype = "guide"
            anchor = anchors[(i + 2) % len(anchors)]
            html = build_asset_html(
                title=title,
                topic=str(topic),
                keyword=keyword,
                angle="cloud static page",
                content_type=ctype,
                target_url=target,
                anchor=anchor,
            )
            content = _create_content(session, campaign, title=title, html=html, keyword=keyword)
            asset = CampaignAsset(
                campaign_id=campaign.id,
                content_id=content.id,
                title=title,
                asset_type="cloud",
                link_group="cloud_content",
                tier=1,
                topic=str(topic),
                variant_angle=ctype,
                relevance_score=80,
                status="generated",
                target_url=target,
                anchor_text=anchor,
                link_attribute="standard",
                placement="Cloud article CTA",
                seo_score=content.seo_score,
                quality_score=76,
                meta={"generated": True, "cloud": True},
            )
            session.add(asset)
            session.flush()
            _attach_task(session, campaign.id, asset)
            created.append(asset)

        for i in range(int(bp.get("pr") or 0)):
            title = f"{keyword}: Research notes (requires verification)"
            html = sanitize_html(
                f"<h1>{title}</h1>"
                "<p>This research asset is a template. Do not invent statistics.</p>"
                "<h2>Methodology</h2>"
                "<p>Document sampling method, date range, and verification status before publication.</p>"
                "<h2>Findings</h2>"
                "<p>Replace placeholders with verified data and cite sources.</p>"
                f"<p>Related: <a href=\"{target}\">{keyword}</a></p>"
            )
            content = _create_content(session, campaign, title=title, html=html, keyword=keyword)
            asset = CampaignAsset(
                campaign_id=campaign.id,
                content_id=content.id,
                title=title,
                asset_type="pr",
                link_group="research",
                tier=1,
                topic=keyword,
                variant_angle="research",
                relevance_score=75,
                status="generated",
                target_url=target,
                anchor_text=keyword,
                link_attribute="standard",
                meta={"requires_verification": True, "fabricated_stats": False},
            )
            session.add(asset)
            session.flush()
            _attach_task(session, campaign.id, asset)
            created.append(asset)

        # Outreach prospects (planning only — no auto-send)
        existing_prospects = session.scalar(
            select(func.count()).select_from(OutreachProspect).where(OutreachProspect.campaign_id == campaign.id)
        ) or 0
        for i in range(int(bp.get("outreach") or 0)):
            if existing_prospects + i >= int(bp.get("outreach") or 0) and existing_prospects:
                break
            prospect = OutreachProspect(
                campaign_id=campaign.id,
                website=f"https://example-publisher-{i + 1}.example",
                contact_name=None,
                email=None,
                topic=keyword,
                relevance_score=60 + (i % 30),
                status="prospect",
                draft_subject=f"Research on {keyword}",
                draft_body=(
                    f"Hello,\n\nI put together a practical overview of {keyword} that may be useful for your readers.\n"
                    "Happy to share a draft for your editorial review — no obligation.\n\nThanks"
                ),
                notes="Outreach requires explicit user approval before sending.",
            )
            session.add(prospect)

        campaign.status = "review"
        campaign.wizard_step = max(campaign.wizard_step, 7)
        job.status = "completed"
        job.progress = 100
        job.completed_at = datetime.now(UTC)
        job.result = {"created_assets": len(created)}
        add_campaign_log(session, campaign.id, f"Campaign assets ready for review ({len(created)})", level="success")
        session.flush()
        return {
            "job": {"id": str(job.id), "status": job.status},
            "campaign": serialize_campaign(session, campaign, detail=True),
            "created": len(created),
        }
    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)[:500]
        job.completed_at = datetime.now(UTC)
        campaign.status = "failed"
        campaign.error_message = str(exc)[:500]
        session.flush()
        raise


def _diverse_anchor(keyword: str, index: int) -> str:
    variants = [
        keyword,
        f"{keyword} overview",
        f"guide to {keyword}",
        f"best {keyword}",
        f"{keyword} explained",
        f"using {keyword}",
    ]
    return variants[index % len(variants)][:120]


def _create_content(session: Session, campaign: BacklinkCampaign, *, title: str, html: str, keyword: str) -> ContentAsset:
    slug = slugify(f"{title}-{uuid4().hex[:6]}")
    content = ContentAsset(
        project_id=campaign.project_id,
        campaign_id=None,
        title=title[:300],
        slug=slug,
        content=html,
        seo_title=title[:300],
        meta_description=f"Practical guide related to {keyword}"[:300],
        content_type=ContentType.ARTICLE.value,
        status=ContentStatus.REVIEW.value,
        word_count=count_words(html),
        seo_score=80,
        quality_score=78,
    )
    session.add(content)
    session.flush()
    session.add(
        ContentVersion(
            content_asset_id=content.id,
            version_number=1,
            content=html,
            change_summary="Campaign asset generated",
            source="campaign",
            created_by=campaign.user_id,
        )
    )
    session.flush()
    return content


def publish_assets(
    session: Session,
    user: User,
    campaign_id: UUID,
    *,
    asset_ids: list[UUID] | None = None,
    destination_id: UUID | None = None,
) -> dict:
    campaign = _owned_campaign(session, user, campaign_id)
    if not campaign.target_url:
        raise BadRequestError("Campaign target URL is required before publishing")

    dest = None
    if destination_id:
        dest = session.get(PublishingDestination, destination_id)
        if not dest or dest.project_id != campaign.project_id:
            raise BadRequestError("Invalid destination")
    else:
        dest = session.scalar(
            select(PublishingDestination).where(
                PublishingDestination.project_id == campaign.project_id,
                PublishingDestination.is_active.is_(True),
                PublishingDestination.authorization_status == "authorized",
            )
        )
        if not dest:
            dest = PublishingDestination(
                project_id=campaign.project_id,
                name="Mock Local Destination",
                provider_type="mock_local",
                configuration={"path_prefix": f"campaigns/{campaign.id}"},
                is_active=True,
                authorization_status="authorized",
            )
            session.add(dest)
            session.flush()

    if dest.authorization_status != "authorized":
        raise BadRequestError("Destination is not authorized. Connect and authorize it before publishing.")

    provider = get_publishing_provider(dest.provider_type)
    q = select(CampaignAsset).where(
        CampaignAsset.campaign_id == campaign.id,
        CampaignAsset.status.in_(["generated", "approved", "failed"]),
    )
    if asset_ids:
        q = q.where(CampaignAsset.id.in_(asset_ids))
    assets = list(session.scalars(q.order_by(CampaignAsset.tier.asc())))
    published = 0
    failed = 0
    add_campaign_log(session, campaign.id, "Publishing queued assets to authorized destinations", level="info")
    for asset in assets:
        content = session.get(ContentAsset, asset.content_id) if asset.content_id else None
        html = content.content if content else f"<p>{asset.title}</p>"
        # Resolve tier2 target to parent source URL when available
        target = campaign.target_url
        if asset.tier == 2 and asset.parent_asset_id:
            parent = session.get(CampaignAsset, asset.parent_asset_id)
            if parent and parent.source_url:
                target = parent.source_url
            elif parent:
                # publish parents first already ordered by tier
                target = parent.source_url or campaign.target_url
        cfg = dict(dest.configuration or {})
        if dest.provider_type == "mock_local":
            cfg["mock_index"] = int(cfg.get("mock_index") or 1)
        result = provider.publish(
            configuration=cfg,
            title=asset.title,
            html=html,
            slug=slugify(asset.title) + "-" + str(asset.id)[:8],
            target_url=target or campaign.target_url,
            anchor_text=asset.anchor_text or campaign.primary_keyword or asset.title,
            link_attribute=asset.link_attribute or "standard",
        )
        if dest.provider_type == "mock_local":
            cfg["mock_index"] = int(cfg.get("mock_index") or 1) + 1
            dest.configuration = cfg
        if not result.success:
            asset.status = "failed"
            asset.meta = {**(asset.meta or {}), "publish_error": result.error}
            failed += 1
            add_campaign_log(session, campaign.id, f"Asset failed: {asset.title}", level="error")
            continue
        asset.destination_id = dest.id
        asset.source_url = result.source_url
        asset.target_url = target
        asset.status = "published"
        asset.is_mock = campaign.mock_mode or dest.provider_type == "mock_local"
        asset.meta = {**(asset.meta or {}), "external_id": result.external_id, "storage_key": result.external_id}
        if content and result.html_snapshot:
            content.content = sanitize_html(
                re.sub(r"(?is)^.*?<body[^>]*>|</body>.*$", "", result.html_snapshot)
            ) or content.content

        # Create backlink record (external backlink only when source domain differs conceptually)
        source_domain = domain_from_url(result.source_url or "")
        if result.source_url and "mock-source-" in (result.source_url or ""):
            source_domain = domain_from_url(result.source_url)
        elif result.source_url and result.source_url.startswith("/api/"):
            source_domain = f"mock-local-{dest.provider_type}"
        kind = classify_link_kind(result.source_url or "", target or campaign.target_url or "")
        exists = session.scalar(
            select(Backlink).where(
                Backlink.campaign_id == campaign.id,
                Backlink.source_url == result.source_url,
                Backlink.target_url == (target or ""),
                Backlink.anchor_text == (asset.anchor_text or ""),
            )
        )
        if not exists:
            link = Backlink(
                campaign_id=campaign.id,
                asset_id=asset.id,
                source_url=result.source_url or "",
                source_domain=source_domain,
                target_url=target or campaign.target_url or "",
                target_content_id=campaign.target_content_id,
                anchor_text=asset.anchor_text or campaign.primary_keyword or "learn more",
                attribute=asset.link_attribute or "standard",
                tier=asset.tier,
                source_type=dest.provider_type,
                link_kind=kind,
                is_mock=asset.is_mock,
                indexed_status="unknown",
                status="published" if kind == "external" else "published",
                first_seen=datetime.now(UTC),
                last_seen=datetime.now(UTC),
            )
            session.add(link)
        published += 1
        add_campaign_log(session, campaign.id, f"Publication completed: {asset.title}", level="success")

    if failed and published:
        campaign.status = "partially_completed"
    elif failed and not published:
        campaign.status = "failed"
    else:
        campaign.status = "monitoring" if published else campaign.status
    campaign.wizard_step = max(campaign.wizard_step, 9)
    session.flush()
    return {"published": published, "failed": failed, "campaign": serialize_campaign(session, campaign, detail=True)}


def verify_backlinks(session: Session, user: User, campaign_id: UUID, *, backlink_ids: list[UUID] | None = None) -> dict:
    campaign = _owned_campaign(session, user, campaign_id)
    add_campaign_log(session, campaign.id, "Backlink verification started", level="info")
    q = select(Backlink).where(Backlink.campaign_id == campaign.id)
    if backlink_ids:
        q = q.where(Backlink.id.in_(backlink_ids))
    links = list(session.scalars(q))
    verified = 0
    lost = 0
    broken = 0
    for link in links:
        result = _verify_one(session, link)
        check = BacklinkCheck(
            backlink_id=link.id,
            status=result["status"],
            source_ok=result["source_ok"],
            target_ok=result["target_ok"],
            anchor_found=result["anchor_found"],
            attribute_match=result["attribute_match"],
            http_status=result.get("http_status"),
            details=result.get("details") or {},
            checked_at=datetime.now(UTC),
        )
        session.add(check)
        link.last_checked_at = check.checked_at
        link.status = result["status"]
        if result["status"] == "verified":
            link.last_seen = check.checked_at
            verified += 1
        elif result["status"] == "lost":
            lost += 1
        elif result["status"] == "broken":
            broken += 1
        add_campaign_log(
            session,
            campaign.id,
            f"Backlink {result['status']}: {link.source_domain}",
            level="success" if result["status"] == "verified" else "warning",
        )
    session.flush()
    return {
        "verified": verified,
        "lost": lost,
        "broken": broken,
        "campaign": serialize_campaign(session, campaign, detail=True),
    }


def _verify_one(session: Session, link: Backlink) -> dict:
    source_ok = False
    anchor_found = False
    attribute_match = False
    http_status = None
    details: dict = {}
    html = ""

    url = link.source_url or ""
    asset = session.get(CampaignAsset, link.asset_id) if link.asset_id else None
    storage_key = (asset.meta or {}).get("storage_key") or (asset.meta or {}).get("external_id") if asset else None
    if "mock-source-" in url or (link.is_mock and storage_key):
        key = str(storage_key or "")
        try:
            html = get_storage_provider().get_bytes(key).decode("utf-8", errors="ignore")
            source_ok = True
            http_status = 200
            details["mock"] = True
        except Exception as exc:
            details["error"] = str(exc)[:200]
            http_status = 404
    elif url.startswith("/api/v1/parasite-seo/backlink-campaigns/published-file/"):
        key = url.split("/published-file/", 1)[-1]
        try:
            html = get_storage_provider().get_bytes(key).decode("utf-8", errors="ignore")
            source_ok = True
            http_status = 200
        except Exception as exc:
            details["error"] = str(exc)[:200]
            http_status = 404
    elif url.startswith("http://") or url.startswith("https://"):
        # Live fetch only for explicitly configured public URLs — best effort.
        try:
            import urllib.request

            req = urllib.request.Request(url, headers={"User-Agent": "ParasiteSEO-LinkVerifier/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:  # noqa: S310 — user-authorized verification
                http_status = getattr(resp, "status", 200)
                html = resp.read(500_000).decode("utf-8", errors="ignore")
                source_ok = http_status < 400
        except Exception as exc:
            details["error"] = str(exc)[:200]
            http_status = 0
    else:
        details["error"] = "Unsupported source URL scheme for verification"
        http_status = 0

    target_ok = bool(link.target_url)
    if link.target_url and link.target_url.startswith("/p/"):
        slug = link.target_url.split("/p/", 1)[-1].strip("/")
        page = session.scalar(
            select(PublicPage).where(
                PublicPage.slug == slug,
                PublicPage.status == "published",
                PublicPage.visibility == "public",
            )
        )
        target_ok = page is not None
    elif link.target_url and link.target_url.startswith("http"):
        target_ok = True  # do not fabricate failure for external authorized targets

    if source_ok and html:
        anchor_found = (link.anchor_text or "").lower() in html.lower() and (link.target_url or "") in html
        if link.attribute == "standard":
            attribute_match = True
        else:
            attribute_match = link.attribute in html
        # Also accept href present even if anchor text drifted slightly
        if (link.target_url or "") in html and not anchor_found:
            anchor_found = True
            details["note"] = "Target href found; anchor text may have minor variation"

    if source_ok and target_ok and anchor_found:
        status = "verified"
    elif http_status == 404 or (not source_ok and http_status in {0, 404}):
        status = "broken" if link.status in {"verified", "published"} else "broken"
        if link.status == "verified":
            status = "lost"
    elif source_ok and not anchor_found:
        status = "lost" if link.status == "verified" else "broken"
    else:
        status = "broken"

    return {
        "status": status,
        "source_ok": source_ok,
        "target_ok": target_ok,
        "anchor_found": anchor_found,
        "attribute_match": attribute_match,
        "http_status": http_status,
        "details": details,
    }


def build_graph(campaign: BacklinkCampaign, assets: list[CampaignAsset], links: list[Backlink]) -> dict:
    nodes = [
        {
            "id": "target",
            "label": campaign.target_url or "Target",
            "type": "target",
            "status": "target",
        }
    ]
    edges = []
    for asset in assets:
        nodes.append(
            {
                "id": str(asset.id),
                "label": asset.title,
                "type": asset.asset_type,
                "tier": asset.tier,
                "status": asset.status,
                "source_url": asset.source_url,
                "domain": domain_from_url(asset.source_url or "") if asset.source_url else None,
            }
        )
        if asset.tier == 1 or asset.asset_type in {"cloud", "pr"}:
            edges.append({"from": str(asset.id), "to": "target", "label": asset.anchor_text, "kind": "backlink_plan"})
        if asset.parent_asset_id:
            edges.append(
                {
                    "from": str(asset.id),
                    "to": str(asset.parent_asset_id),
                    "label": asset.anchor_text,
                    "kind": "tier_support",
                }
            )
    for link in links:
        edges.append(
            {
                "from": str(link.asset_id) if link.asset_id else link.source_domain,
                "to": "target",
                "label": link.anchor_text,
                "kind": "backlink",
                "status": link.status,
            }
        )
    return {"nodes": nodes, "edges": edges}


def anchor_distribution(links: list[Backlink]) -> list[dict]:
    if not links:
        return []
    counts = Counter((b.anchor_text or "").strip().lower() for b in links)
    total = sum(counts.values()) or 1
    return [
        {"anchor": anchor, "count": count, "percent": round(100 * count / total, 1)}
        for anchor, count in counts.most_common(20)
    ]


def campaign_report(session: Session, campaign: BacklinkCampaign) -> dict:
    links = list(session.scalars(select(Backlink).where(Backlink.campaign_id == campaign.id)))
    assets = list(session.scalars(select(CampaignAsset).where(CampaignAsset.campaign_id == campaign.id)))
    return {
        "campaign": campaign.name,
        "target": campaign.target_url,
        "strategy": campaign.strategy_type,
        "disclosure": campaign.disclosure,
        "assets": len(assets),
        "published_assets": sum(1 for a in assets if a.status in {"published", "verified"}),
        "backlinks": len(links),
        "verified": sum(1 for b in links if b.status == "verified"),
        "lost": sum(1 for b in links if b.status == "lost"),
        "broken": sum(1 for b in links if b.status == "broken"),
        "referring_domains": len({b.source_domain for b in links if b.status == "verified" and b.link_kind != "internal"}),
        "internal_links": sum(1 for b in links if b.link_kind == "internal"),
        "mock_mode": campaign.mock_mode,
        "indexed_unknown": sum(1 for b in links if b.indexed_status == "unknown"),
        "tier_distribution": {
            "tier1": sum(1 for b in links if b.tier == 1),
            "tier2": sum(1 for b in links if b.tier == 2),
        },
        "anchor_distribution": anchor_distribution(links),
        "source_types": dict(Counter(b.source_type for b in links)),
    }


def export_report(session: Session, user: User, campaign_id: UUID, fmt: str = "json") -> tuple[bytes, str, str]:
    campaign = _owned_campaign(session, user, campaign_id)
    report = campaign_report(session, campaign)
    report["exported_at"] = datetime.now(UTC).isoformat()
    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["metric", "value"])
        for key, value in report.items():
            if isinstance(value, (dict, list)):
                writer.writerow([key, json.dumps(value)])
            else:
                writer.writerow([key, value])
        return buf.getvalue().encode("utf-8"), "text/csv", f"campaign-{campaign.id}.csv"
    if fmt == "pdf":
        from app.services.export import export_pdf

        lines = [
            f"<h1>{campaign.name}</h1>",
            f"<p>Target: {campaign.target_url}</p>",
            f"<p>Verified: {report['verified']} / {report['backlinks']}</p>",
            f"<p>Referring domains: {report['referring_domains']}</p>",
            f"<p>{DISCLOSURE}</p>",
        ]
        data = export_pdf(title=campaign.name, body_html="".join(lines))
        return data, "application/pdf", f"campaign-{campaign.id}.pdf"
    payload = json.dumps(report, indent=2).encode("utf-8")
    return payload, "application/json", f"campaign-{campaign.id}.json"


DEMO_BLUEPRINT = {
    "tier1": 5,
    "tier2": 10,
    "cloud": 3,
    "pr": 1,
    "outreach": 10,
    "max_tier_depth": 2,
}


def create_demo_campaign(session: Session, user: User, project_id: UUID) -> dict:
    """Create the Phase 8 demo campaign (mock publishing only)."""
    get_owned_project(session, user, project_id)
    page = session.scalar(
        select(PublicPage)
        .where(
            PublicPage.project_id == project_id,
            PublicPage.status == "published",
            PublicPage.visibility == "public",
        )
        .order_by(PublicPage.published_at.desc())
        .limit(1)
    )
    bucket = session.scalar(
        select(ContentBucket).where(ContentBucket.project_id == project_id, ContentBucket.name == "AI Productivity")
    )
    if not bucket:
        bucket_data = create_bucket(
            session,
            user,
            project_id,
            name="AI Productivity",
            topics=[
                "AI productivity tools",
                "AI tools for students",
                "AI tools for developers",
                "AI automation",
                "AI work tools",
            ],
            keywords=["AI Productivity Tools", "AI Tools for Students", "AI Productivity Apps", "Best AI Tools 2026"],
            niche="productivity",
        )
        bucket_id = UUID(bucket_data["id"])
    else:
        bucket_id = bucket.id

    dest = session.scalar(
        select(PublishingDestination).where(
            PublishingDestination.project_id == project_id,
            PublishingDestination.provider_type == "mock_local",
        )
    )
    if not dest:
        create_destination(
            session,
            user,
            project_id,
            name="Demo Mock Local",
            provider_type="mock_local",
            configuration={"path_prefix": "demo-campaigns"},
        )
    cloud = session.scalar(
        select(PublishingDestination).where(
            PublishingDestination.project_id == project_id,
            PublishingDestination.provider_type == "cloud_static",
        )
    )
    if not cloud:
        create_destination(
            session,
            user,
            project_id,
            name="Demo Cloud Static",
            provider_type="cloud_static",
            configuration={"bucket": "demo-cloud-pages"},
        )

    campaign = create_campaign(
        session,
        user,
        project_id=project_id,
        name="AI Productivity Tools 2026",
        strategy_type="tiered_network",
        target_url=None if page else "https://yourdomain.com/p/ai-productivity-tools",
        target_public_page_id=page.id if page else None,
        primary_keyword="AI Productivity Tools",
        secondary_keywords=["AI Tools for Students", "AI Productivity Apps", "Best AI Tools 2026"],
        country="Global",
        language="English",
        niche="AI Productivity",
        target_audience="Students, remote teams, and developers",
        blueprint=DEMO_BLUEPRINT,
    )
    update_campaign(session, user, UUID(campaign["id"]), {"bucket_id": str(bucket_id), "wizard_step": 6, "status": "planning"})
    return get_campaign(session, user, UUID(campaign["id"]))


def list_target_options(session: Session, user: User, project_id: UUID) -> list[dict]:
    get_owned_project(session, user, project_id)
    pages = session.scalars(
        select(PublicPage).where(
            PublicPage.project_id == project_id,
            PublicPage.status == "published",
            PublicPage.visibility == "public",
        )
    )
    out = []
    for page in pages:
        content = session.get(ContentAsset, page.content_id)
        out.append(
            {
                "public_page_id": str(page.id),
                "content_id": str(page.content_id),
                "title": page.title,
                "url": page.public_url or f"/p/{page.slug}",
                "slug": page.slug,
                "seo_score": content.seo_score if content else None,
                "quality_score": content.quality_score if content else None,
                "status": page.status,
                "published_at": page.published_at.isoformat() if page.published_at else None,
            }
        )
    return out


def update_prospect(session: Session, user: User, prospect_id: UUID, payload: dict) -> dict:
    prospect = session.get(OutreachProspect, prospect_id)
    if not prospect:
        raise NotFoundError("Prospect not found")
    _owned_campaign(session, user, prospect.campaign_id)
    for key in ("status", "contact_name", "email", "topic", "draft_subject", "draft_body", "notes", "relevance_score"):
        if key in payload:
            setattr(prospect, key, payload[key])
    if payload.get("status") == "sent":
        # Explicit approval gate — never auto-send emails.
        session.add(
            OutreachActivity(
                prospect_id=prospect.id,
                activity_type="sent_marked",
                summary="User marked outreach as sent (no automatic email delivery).",
            )
        )
    session.flush()
    return serialize_prospect(prospect)


def get_published_file_bytes(key: str) -> tuple[bytes, str]:
    cleaned = (key or "").lstrip("/")
    if ".." in cleaned or cleaned.startswith("\\") or not cleaned:
        raise BadRequestError("Invalid path")
    # Allow mock/cloud campaign HTML keys written by authorized providers only
    allowed_prefixes = ("campaigns/", "cloud/", "demo-campaigns/", "test-campaigns/")
    if not cleaned.endswith(".html") and not cleaned.endswith(".css"):
        raise BadRequestError("Invalid published file type")
    if not any(cleaned.startswith(p) for p in allowed_prefixes):
        # Still allow provider-configured path_prefix folders that look like storage keys
        if "/" not in cleaned or not re.match(r"^[a-zA-Z0-9._/-]+$", cleaned):
            raise BadRequestError("Invalid published file path")
    data = get_storage_provider().get_bytes(cleaned)
    mime = "text/css; charset=utf-8" if cleaned.endswith(".css") else "text/html; charset=utf-8"
    return data, mime


def analyze_project(
    session: Session,
    user: User,
    *,
    project_id: UUID,
    job_id: UUID | None = None,
    public_page_id: UUID | None = None,
) -> dict:
    project = get_owned_project(session, user, project_id)
    job = None
    if job_id:
        job = session.get(ParasiteSEOJob, job_id)
        if not job or job.project_id != project_id:
            raise BadRequestError("Parasite SEO job not found in this project")
    page = session.get(PublicPage, public_page_id) if public_page_id else None
    if page and page.project_id != project_id:
        raise BadRequestError("Target page is not in this project")
    if not page and job:
        page = session.scalar(select(PublicPage).where(PublicPage.job_id == job.id))
    if not page:
        page = session.scalar(
            select(PublicPage)
            .where(PublicPage.project_id == project_id, PublicPage.status == "published", PublicPage.visibility == "public")
            .order_by(PublicPage.published_at.desc())
            .limit(1)
        )
    content = None
    if page:
        content = session.get(ContentAsset, page.content_id)
    elif job and job.content_id:
        content = session.get(ContentAsset, job.content_id)
    reqs = (job.requirements if job else None) or {}
    html = (content.content if content else "") or ""
    headings = heading_outline(html)
    keyword = (
        (reqs.get("main_keyword") if isinstance(reqs, dict) else None)
        or (content.seo_title if content else None)
        or project.name
    )
    secondary = list((reqs.get("secondary_keywords") if isinstance(reqs, dict) else None) or [])
    prompt = job.original_prompt if job else (project.description or project.name)
    topics = supporting_topics(keyword=str(keyword), secondary=secondary, prompt=prompt or "")
    dests = list(session.scalars(select(PublishingDestination).where(PublishingDestination.project_id == project_id)))
    dest_types = {d.provider_type for d in dests}
    has_cloud = bool(dest_types & {"cloud_static", "aws_s3", "azure_blob", "gcs"}) or True
    existing_links = session.scalar(
        select(func.count()).select_from(Backlink).join(BacklinkCampaign).where(BacklinkCampaign.project_id == project_id)
    ) or 0
    strategy = recommend_strategy(
        topic_count=len(topics), dest_types=dest_types, has_cloud=has_cloud, existing_links=int(existing_links)
    )
    intel = {
        "topic": reqs.get("topic") if isinstance(reqs, dict) else project.name,
        "primary_keyword": keyword,
        "secondary_keywords": secondary,
        "search_intent": (reqs.get("intent") if isinstance(reqs, dict) else None) or "commercial",
        "content_category": (reqs.get("content_type") if isinstance(reqs, dict) else None) or "article",
        "audience": (reqs.get("audience") if isinstance(reqs, dict) else None) or project.target_audience,
        "country": (reqs.get("country") if isinstance(reqs, dict) else None) or project.country,
        "language": (reqs.get("language") if isinstance(reqs, dict) else None) or project.language,
        "recommended_anchor_terms": recommended_anchors(str(keyword)),
        "supporting_topics": topics,
        "recommended_content_types": ["article", "guide", "comparison", "listicle", "faq", "research"],
        "campaign_strategy": strategy["strategy_type"],
        "entities": [w for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", str(keyword))[:12]],
        "prompt": (prompt or "")[:4000],
        "headings": headings,
        "seo_score": content.seo_score if content else None,
        "content_quality_score": content.quality_score if content else None,
        "media_count": session.scalar(
            select(func.count()).select_from(MediaAsset).where(MediaAsset.project_id == project_id)
        )
        or 0,
    }
    try:
        from app.agents.project_intelligence_agent import ProjectIntelligenceAgent
        from app.agents.campaign_strategy_agent import CampaignStrategyAgent

        parsed, _run = ProjectIntelligenceAgent().run(
            session, project_id=project_id, content_asset_id=content.id if content else None, context=intel
        )
        dumped = parsed.model_dump()
        for key, value in dumped.items():
            if value:
                intel[key] = value
        strat, _srun = CampaignStrategyAgent().run(
            session,
            project_id=project_id,
            content_asset_id=content.id if content else None,
            intelligence=intel,
            destinations=[{"provider_type": d.provider_type, "authorized": d.authorization_status} for d in dests],
        )
        if strat.strategy_type in DEFAULT_BLUEPRINTS:
            strategy["strategy_type"] = strat.strategy_type
            strategy["label"] = strat.label or strategy["label"]
            strategy["reason"] = strat.reason or strategy["reason"]
            if strat.blueprint and isinstance(strat.blueprint, dict):
                bp = dict(DEFAULT_BLUEPRINTS[strat.strategy_type])
                for key in ("tier1", "tier2", "cloud", "pr", "outreach", "max_tier_depth"):
                    raw = strat.blueprint.get(key)
                    try:
                        bp[key] = int(raw)
                    except (TypeError, ValueError):
                        continue
                strategy["blueprint"] = bp
    except Exception:
        pass

    groups = link_groups_for(strategy["blueprint"], dest_types)
    target = None
    if page:
        target = {
            "public_page_id": str(page.id),
            "title": page.title,
            "url": page.public_url or f"/p/{page.slug}",
            "primary_keyword": intel["primary_keyword"],
            "seo_score": intel["seo_score"],
            "content_score": intel["content_quality_score"],
            "status": page.status,
        }
    elif job and job.public_url:
        target = {
            "public_page_id": None,
            "title": content.title if content else project.name,
            "url": job.public_url,
            "primary_keyword": intel["primary_keyword"],
            "seo_score": intel["seo_score"],
            "content_score": intel["content_quality_score"],
            "status": job.status,
        }
    else:
        from app.utils.url_safety import slugify as _slug

        target = {
            "public_page_id": None,
            "title": content.title if content else project.name,
            "url": f"https://example.com/p/{_slug(project.name)}",
            "primary_keyword": intel["primary_keyword"],
            "seo_score": intel["seo_score"],
            "content_score": intel["content_quality_score"],
            "status": "planned",
        }
    return {
        "project": {"id": str(project.id), "name": project.name},
        "job_id": str(job.id) if job else None,
        "target": target,
        "intelligence": intel,
        "strategy": strategy,
        "blueprint": strategy["blueprint"],
        "size_reason": size_reason(strategy["blueprint"]),
        "link_groups": groups,
        "destinations": [serialize_destination(d) for d in dests],
        "disclosure": DISCLOSURE,
    }


def auto_create_campaign(
    session: Session,
    user: User,
    *,
    project_id: UUID,
    job_id: UUID | None = None,
    public_page_id: UUID | None = None,
    blueprint: dict | None = None,
    generate: bool = True,
    mock_mode: bool = True,
) -> dict:
    plan = analyze_project(session, user, project_id=project_id, job_id=job_id, public_page_id=public_page_id)
    intel = plan["intelligence"]
    strategy = plan["strategy"]
    bp = dict(strategy["blueprint"])
    if blueprint:
        bp.update(blueprint)
    target = plan.get("target") or {}
    page_id = UUID(target["public_page_id"]) if target.get("public_page_id") else None
    dests = list(session.scalars(select(PublishingDestination).where(PublishingDestination.project_id == project_id)))
    if not any(d.provider_type == "mock_local" for d in dests):
        create_destination(
            session,
            user,
            project_id,
            name="Mock Local (development)",
            provider_type="mock_local",
            configuration={"path_prefix": f"campaigns/{project_id}"},
        )
    campaign = create_campaign(
        session,
        user,
        project_id=project_id,
        name=f"{intel.get('primary_keyword') or plan['project']['name']} Backlink Campaign"[:200],
        strategy_type=strategy["strategy_type"] if strategy["strategy_type"] in DEFAULT_BLUEPRINTS else "hybrid",
        target_url=None if page_id else target.get("url"),
        target_public_page_id=page_id,
        primary_keyword=intel.get("primary_keyword"),
        secondary_keywords=list(intel.get("secondary_keywords") or []),
        country=intel.get("country"),
        language=intel.get("language"),
        niche=intel.get("content_category"),
        target_audience=intel.get("audience"),
        blueprint=bp,
        parasite_job_id=UUID(plan["job_id"]) if plan.get("job_id") else None,
        mock_mode=mock_mode,
        intelligence=intel,
    )
    cid = UUID(campaign["id"])
    add_campaign_log(session, cid, "Automatic campaign created from project intelligence", level="success")
    topics = list(intel.get("supporting_topics") or [])
    if topics:
        bucket = create_bucket(
            session,
            user,
            project_id,
            name=str(intel.get("topic") or intel.get("primary_keyword") or "Campaign topics")[:200],
            topics=topics,
            keywords=[k for k in [intel.get("primary_keyword"), *(intel.get("secondary_keywords") or [])] if k][:12],
            niche=intel.get("content_category"),
        )
        update_campaign(session, user, cid, {"bucket_id": bucket["id"], "status": "review"})
    if generate:
        generated = generate_assets(session, user, cid)
        return {"plan": plan, **generated}
    return {"plan": plan, "created": 0, "campaign": get_campaign(session, user, cid)}


def approve_campaign(session: Session, user: User, campaign_id: UUID) -> dict:
    campaign = _owned_campaign(session, user, campaign_id)
    campaign.status = "approved"
    campaign.approved_at = datetime.now(UTC)
    add_campaign_log(session, campaign.id, "Campaign approved. External publishing may now start.", level="success")
    session.flush()
    return serialize_campaign(session, campaign, detail=True)


def start_campaign(session: Session, user: User, campaign_id: UUID, *, destination_id: UUID | None = None) -> dict:
    campaign = _owned_campaign(session, user, campaign_id)
    if not campaign.approved_at and campaign.status not in {"approved", "review", "generating"}:
        raise BadRequestError("Approve the campaign before starting publication")
    if campaign.status == "review" and not campaign.approved_at:
        raise BadRequestError("Approve the campaign before starting publication")
    add_campaign_log(session, campaign.id, "Campaign execution started", level="info")
    published = publish_assets(session, user, campaign_id, destination_id=destination_id)
    verified = verify_backlinks(session, user, campaign_id)
    return {
        "published": published.get("published"),
        "failed": published.get("failed"),
        "verified": verified.get("verified"),
        "campaign": verified["campaign"],
    }


def retry_failed_assets(session: Session, user: User, campaign_id: UUID) -> dict:
    campaign = _owned_campaign(session, user, campaign_id)
    failed = list(
        session.scalars(
            select(CampaignAsset).where(CampaignAsset.campaign_id == campaign.id, CampaignAsset.status == "failed")
        )
    )
    for asset in failed:
        asset.status = "generated"
    session.flush()
    add_campaign_log(session, campaign.id, f"Retrying {len(failed)} failed assets", level="warning")
    return publish_assets(session, user, campaign_id, asset_ids=[a.id for a in failed])


def duplicate_campaign(session: Session, user: User, campaign_id: UUID) -> dict:
    source = _owned_campaign(session, user, campaign_id)
    copy = create_campaign(
        session,
        user,
        project_id=source.project_id,
        name=f"{source.name} (copy)"[:200],
        strategy_type=source.strategy_type,
        target_url=source.target_url,
        target_public_page_id=source.target_public_page_id,
        primary_keyword=source.primary_keyword,
        secondary_keywords=list(source.secondary_keywords or []),
        country=source.country,
        language=source.language,
        niche=source.niche,
        target_audience=source.target_audience,
        blueprint=dict(source.blueprint or {}),
        parasite_job_id=source.parasite_job_id,
        mock_mode=True,
        intelligence=dict(source.intelligence or {}),
    )
    row = session.get(BacklinkCampaign, UUID(copy["id"]))
    assert row
    row.duplicated_from_id = source.id
    row.bucket_id = source.bucket_id
    row.status = "draft"
    add_campaign_log(session, row.id, "Campaign duplicated without published URLs or backlinks", level="info")
    session.flush()
    return serialize_campaign(session, row, detail=True)


def archive_campaign(session: Session, user: User, campaign_id: UUID) -> dict:
    campaign = _owned_campaign(session, user, campaign_id)
    campaign.archived_at = datetime.now(UTC)
    campaign.status = "archived"
    session.flush()
    return serialize_campaign(session, campaign)


def list_campaign_logs(
    session: Session, user: User, campaign_id: UUID, *, level: str | None = None
) -> list[dict]:
    _owned_campaign(session, user, campaign_id)
    stmt = select(CampaignLog).where(CampaignLog.campaign_id == campaign_id).order_by(CampaignLog.created_at.asc())
    if level:
        stmt = stmt.where(CampaignLog.level == level)
    return [serialize_log(row) for row in session.scalars(stmt.limit(500))]


def list_project_backlinks(
    session: Session,
    user: User,
    project_id: UUID,
    *,
    status: str | None = None,
    tier: int | None = None,
    source_type: str | None = None,
) -> dict:
    get_owned_project(session, user, project_id)
    ids = session.scalars(select(BacklinkCampaign.id).where(BacklinkCampaign.project_id == project_id))
    campaign_ids = list(ids)
    if not campaign_ids:
        return {"items": [], "total_backlinks": 0, "referring_domains": 0, "verified": 0}
    stmt = select(Backlink).where(Backlink.campaign_id.in_(campaign_ids))
    if status:
        stmt = stmt.where(Backlink.status == status)
    if tier is not None:
        stmt = stmt.where(Backlink.tier == tier)
    if source_type:
        stmt = stmt.where(Backlink.source_type == source_type)
    links = list(session.scalars(stmt.order_by(Backlink.created_at.desc()).limit(500)))
    verified = [b for b in links if b.status == "verified" and b.link_kind != "internal"]
    return {
        "items": [serialize_backlink(b) for b in links],
        "total_backlinks": len(links),
        "verified": len(verified),
        "referring_domains": len({b.source_domain for b in verified}),
    }


def project_backlink_report(session: Session, user: User, project_id: UUID) -> dict:
    project = get_owned_project(session, user, project_id)
    campaigns = list(
        session.scalars(
            select(BacklinkCampaign).where(
                BacklinkCampaign.project_id == project_id, BacklinkCampaign.archived_at.is_(None)
            )
        )
    )
    links: list[Backlink] = []
    assets: list[CampaignAsset] = []
    for campaign in campaigns:
        links.extend(session.scalars(select(Backlink).where(Backlink.campaign_id == campaign.id)))
        assets.extend(session.scalars(select(CampaignAsset).where(CampaignAsset.campaign_id == campaign.id)))
    verified = [b for b in links if b.status == "verified" and b.link_kind != "internal"]
    page = session.scalar(
        select(PublicPage)
        .where(PublicPage.project_id == project_id, PublicPage.status == "published")
        .order_by(PublicPage.published_at.desc())
        .limit(1)
    )
    content = session.get(ContentAsset, page.content_id) if page else None
    return {
        "project": project.name,
        "target": page.public_url if page else None,
        "seo_score": content.seo_score if content else None,
        "campaigns": len(campaigns),
        "planned": sum(1 for a in assets),
        "published": sum(1 for a in assets if a.status in {"published", "verified"}),
        "verified": len(verified),
        "lost": sum(1 for b in links if b.status == "lost"),
        "broken": sum(1 for b in links if b.status == "broken"),
        "referring_domains": len({b.source_domain for b in verified}),
        "tier1_planned": sum(1 for a in assets if a.tier == 1),
        "tier1_verified": sum(1 for b in verified if b.tier == 1),
        "tier2_planned": sum(1 for a in assets if a.tier == 2),
        "tier2_verified": sum(1 for b in verified if b.tier == 2),
        "cloud_planned": sum(1 for a in assets if a.asset_type == "cloud"),
        "disclosure": DISCLOSURE,
    }
