"""Phase 8 — Backlink campaign APIs."""

from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import BadRequestError
from app.schemas.common import SuccessResponse
from app.services import backlink_campaigns as service

router = APIRouter(prefix="/parasite-seo/backlink-campaigns", tags=["backlink-campaigns"])


class CreateCampaignRequest(BaseModel):
    project_id: UUID
    name: str = Field(min_length=3, max_length=200)
    strategy_type: str = "tiered_network"
    target_url: str | None = None
    target_public_page_id: UUID | None = None
    primary_keyword: str | None = None
    secondary_keywords: list[str] | None = None
    country: str | None = None
    language: str | None = None
    niche: str | None = None
    target_audience: str | None = None
    blueprint: dict | None = None
    parasite_job_id: UUID | None = None
    mock_mode: bool = True


class UpdateCampaignRequest(BaseModel):
    name: str | None = None
    primary_keyword: str | None = None
    secondary_keywords: list[str] | None = None
    country: str | None = None
    language: str | None = None
    niche: str | None = None
    target_audience: str | None = None
    wizard_step: int | None = None
    status: str | None = None
    blueprint: dict | None = None
    settings: dict | None = None
    bucket_id: UUID | None = None
    target_url: str | None = None
    target_public_page_id: UUID | None = None
    strategy_type: str | None = None


class BucketRequest(BaseModel):
    project_id: UUID
    name: str
    topics: list[str] | None = None
    keywords: list[str] | None = None
    niche: str | None = None


class DestinationRequest(BaseModel):
    project_id: UUID
    name: str
    provider_type: str = "mock_local"
    base_url: str | None = None
    configuration: dict | None = None


class PublishRequest(BaseModel):
    asset_ids: list[UUID] | None = None
    destination_id: UUID | None = None


class VerifyRequest(BaseModel):
    backlink_ids: list[UUID] | None = None


class StrategyTemplateRequest(BaseModel):
    project_id: UUID
    name: str
    strategy_type: str
    blueprint: dict


class AutoCreateRequest(BaseModel):
    project_id: UUID
    job_id: UUID | None = None
    public_page_id: UUID | None = None
    blueprint: dict | None = None
    generate: bool = True
    mock_mode: bool = True


class ProspectUpdateRequest(BaseModel):
    status: str | None = None
    contact_name: str | None = None
    email: str | None = None
    topic: str | None = None
    draft_subject: str | None = None
    draft_body: str | None = None
    notes: str | None = None
    relevance_score: int | None = None


@router.get("", response_model=SuccessResponse[dict])
def list_campaigns(
    session: DbSession,
    user: CurrentUser,
    project_id: UUID | None = Query(default=None),
    include_archived: bool = Query(default=False),
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data={"items": service.list_campaigns(session, user, project_id, include_archived=include_archived)}
    )


@router.post("", response_model=SuccessResponse[dict], status_code=201)
def create_campaign(payload: CreateCampaignRequest, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=service.create_campaign(
            session,
            user,
            project_id=payload.project_id,
            name=payload.name,
            strategy_type=payload.strategy_type,
            target_url=payload.target_url,
            target_public_page_id=payload.target_public_page_id,
            primary_keyword=payload.primary_keyword,
            secondary_keywords=payload.secondary_keywords,
            country=payload.country,
            language=payload.language,
            niche=payload.niche,
            target_audience=payload.target_audience,
            blueprint=payload.blueprint,
            parasite_job_id=payload.parasite_job_id,
            mock_mode=payload.mock_mode,
        )
    )


@router.get("/analyze", response_model=SuccessResponse[dict])
def analyze(
    session: DbSession,
    user: CurrentUser,
    project_id: UUID = Query(...),
    job_id: UUID | None = Query(default=None),
    public_page_id: UUID | None = Query(default=None),
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=service.analyze_project(
            session, user, project_id=project_id, job_id=job_id, public_page_id=public_page_id
        )
    )


@router.post("/auto", response_model=SuccessResponse[dict], status_code=201)
def auto_create(payload: AutoCreateRequest, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=service.auto_create_campaign(
            session,
            user,
            project_id=payload.project_id,
            job_id=payload.job_id,
            public_page_id=payload.public_page_id,
            blueprint=payload.blueprint,
            generate=payload.generate,
            mock_mode=payload.mock_mode,
        )
    )


@router.get("/project-backlinks", response_model=SuccessResponse[dict])
def project_backlinks(
    session: DbSession,
    user: CurrentUser,
    project_id: UUID = Query(...),
    status: str | None = Query(default=None),
    tier: int | None = Query(default=None),
    source_type: str | None = Query(default=None),
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=service.list_project_backlinks(
            session, user, project_id, status=status, tier=tier, source_type=source_type
        )
    )


@router.get("/project-report", response_model=SuccessResponse[dict])
def project_report(
    session: DbSession,
    user: CurrentUser,
    project_id: UUID = Query(...),
) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.project_backlink_report(session, user, project_id))


@router.get("/targets", response_model=SuccessResponse[dict])
def list_targets(
    session: DbSession,
    user: CurrentUser,
    project_id: UUID = Query(...),
) -> SuccessResponse[dict]:
    return SuccessResponse(data={"items": service.list_target_options(session, user, project_id)})


@router.get("/strategies", response_model=SuccessResponse[dict])
def list_strategies(
    session: DbSession,
    user: CurrentUser,
    project_id: UUID = Query(...),
) -> SuccessResponse[dict]:
    return SuccessResponse(data={"items": service.list_strategy_templates(session, user, project_id)})


@router.post("/strategies", response_model=SuccessResponse[dict], status_code=201)
def save_strategy(payload: StrategyTemplateRequest, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=service.save_strategy_template(
            session,
            user,
            payload.project_id,
            name=payload.name,
            strategy_type=payload.strategy_type,
            blueprint=payload.blueprint,
        )
    )


@router.get("/buckets", response_model=SuccessResponse[dict])
def list_buckets(
    session: DbSession,
    user: CurrentUser,
    project_id: UUID = Query(...),
) -> SuccessResponse[dict]:
    return SuccessResponse(data={"items": service.list_buckets(session, user, project_id)})


@router.post("/buckets", response_model=SuccessResponse[dict], status_code=201)
def create_bucket(payload: BucketRequest, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=service.create_bucket(
            session,
            user,
            payload.project_id,
            name=payload.name,
            topics=payload.topics,
            keywords=payload.keywords,
            niche=payload.niche,
        )
    )


@router.get("/destinations", response_model=SuccessResponse[dict])
def list_destinations(
    session: DbSession,
    user: CurrentUser,
    project_id: UUID = Query(...),
) -> SuccessResponse[dict]:
    return SuccessResponse(data={"items": service.list_destinations(session, user, project_id)})


@router.post("/destinations", response_model=SuccessResponse[dict], status_code=201)
def create_destination(payload: DestinationRequest, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=service.create_destination(
            session,
            user,
            payload.project_id,
            name=payload.name,
            provider_type=payload.provider_type,
            base_url=payload.base_url,
            configuration=payload.configuration,
        )
    )


@router.post("/destinations/{destination_id}/test", response_model=SuccessResponse[dict])
def test_destination(destination_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.test_destination(session, user, destination_id))


@router.get("/published-file/{file_path:path}")
def published_file(file_path: str) -> Response:
    data, mime = service.get_published_file_bytes(file_path)
    return Response(content=data, media_type=mime)


@router.post("/demo", response_model=SuccessResponse[dict], status_code=201)
def create_demo(
    session: DbSession,
    user: CurrentUser,
    project_id: UUID = Query(...),
) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.create_demo_campaign(session, user, project_id))


@router.get("/{campaign_id}", response_model=SuccessResponse[dict])
def get_campaign(campaign_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.get_campaign(session, user, campaign_id))


@router.patch("/{campaign_id}", response_model=SuccessResponse[dict])
def patch_campaign(
    campaign_id: UUID,
    payload: UpdateCampaignRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=service.update_campaign(session, user, campaign_id, payload.model_dump(exclude_none=True))
    )


@router.post("/{campaign_id}/generate-assets", response_model=SuccessResponse[dict])
def generate_assets(campaign_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.generate_assets(session, user, campaign_id))


@router.post("/{campaign_id}/publish", response_model=SuccessResponse[dict])
def publish(
    campaign_id: UUID,
    session: DbSession,
    user: CurrentUser,
    payload: PublishRequest | None = None,
) -> SuccessResponse[dict]:
    body = payload or PublishRequest()
    return SuccessResponse(
        data=service.publish_assets(
            session,
            user,
            campaign_id,
            asset_ids=body.asset_ids,
            destination_id=body.destination_id,
        )
    )


@router.post("/{campaign_id}/verify", response_model=SuccessResponse[dict])
def verify(
    campaign_id: UUID,
    session: DbSession,
    user: CurrentUser,
    payload: VerifyRequest | None = None,
) -> SuccessResponse[dict]:
    body = payload or VerifyRequest()
    return SuccessResponse(
        data=service.verify_backlinks(session, user, campaign_id, backlink_ids=body.backlink_ids)
    )


@router.post("/{campaign_id}/approve", response_model=SuccessResponse[dict])
def approve(campaign_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.approve_campaign(session, user, campaign_id))


@router.post("/{campaign_id}/start", response_model=SuccessResponse[dict])
def start(
    campaign_id: UUID,
    session: DbSession,
    user: CurrentUser,
    payload: PublishRequest | None = None,
) -> SuccessResponse[dict]:
    body = payload or PublishRequest()
    return SuccessResponse(
        data=service.start_campaign(session, user, campaign_id, destination_id=body.destination_id)
    )


@router.post("/{campaign_id}/retry-failed", response_model=SuccessResponse[dict])
def retry_failed(campaign_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.retry_failed_assets(session, user, campaign_id))


@router.post("/{campaign_id}/duplicate", response_model=SuccessResponse[dict], status_code=201)
def duplicate(campaign_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.duplicate_campaign(session, user, campaign_id))


@router.post("/{campaign_id}/archive", response_model=SuccessResponse[dict])
def archive(campaign_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.archive_campaign(session, user, campaign_id))


@router.get("/{campaign_id}/logs", response_model=SuccessResponse[dict])
def logs(
    campaign_id: UUID,
    session: DbSession,
    user: CurrentUser,
    level: str | None = Query(default=None),
) -> SuccessResponse[dict]:
    return SuccessResponse(data={"items": service.list_campaign_logs(session, user, campaign_id, level=level)})


@router.get("/{campaign_id}/report")
def report(
    campaign_id: UUID,
    session: DbSession,
    user: CurrentUser,
    format: str = Query(default="json"),
) -> Response:
    if format not in {"json", "csv", "pdf"}:
        raise BadRequestError("format must be json, csv, or pdf")
    data, mime, filename = service.export_report(session, user, campaign_id, fmt=format)
    return Response(
        content=data,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/prospects/{prospect_id}", response_model=SuccessResponse[dict])
def patch_prospect(
    prospect_id: UUID,
    payload: ProspectUpdateRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=service.update_prospect(session, user, prospect_id, payload.model_dump(exclude_none=True))
    )
