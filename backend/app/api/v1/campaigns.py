from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, DbSession
from app.api.deps_pagination import PaginationParams, pagination_params
from app.schemas.common import ListResponse, PaginationMeta, SuccessResponse
from app.schemas.resources import CampaignCreate, CampaignRead, CampaignUpdate
from app.services import campaigns as campaign_service

router = APIRouter(tags=["campaigns"])


@router.get("/projects/{project_id}/campaigns", response_model=ListResponse[CampaignRead])
def list_campaigns(
    project_id: UUID,
    session: DbSession,
    user: CurrentUser,
    pagination: PaginationParams = Depends(pagination_params),
) -> ListResponse[CampaignRead]:
    items, total = campaign_service.list_campaigns(session, user, project_id, pagination)
    return ListResponse(
        data=items,
        pagination=PaginationMeta(page=pagination.page, page_size=pagination.page_size, total=total),
    )


@router.post("/projects/{project_id}/campaigns", response_model=SuccessResponse[CampaignRead], status_code=201)
def create_campaign(
    project_id: UUID,
    payload: CampaignCreate,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[CampaignRead]:
    return SuccessResponse(data=campaign_service.create_campaign(session, user, project_id, payload))


@router.get("/campaigns/{campaign_id}", response_model=SuccessResponse[CampaignRead])
def get_campaign(campaign_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[CampaignRead]:
    return SuccessResponse(data=campaign_service.get_campaign(session, user, campaign_id))


@router.patch("/campaigns/{campaign_id}", response_model=SuccessResponse[CampaignRead])
def update_campaign(
    campaign_id: UUID,
    payload: CampaignUpdate,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[CampaignRead]:
    return SuccessResponse(data=campaign_service.update_campaign(session, user, campaign_id, payload))


@router.delete("/campaigns/{campaign_id}", status_code=204)
def delete_campaign(campaign_id: UUID, session: DbSession, user: CurrentUser) -> None:
    campaign_service.delete_campaign(session, user, campaign_id)
