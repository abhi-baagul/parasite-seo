from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession
from app.api.deps_pagination import PaginationParams, pagination_params
from app.schemas.common import ListResponse, PaginationMeta, SuccessResponse
from app.schemas.resources import (
    PublishedAssetRead,
    PublishingChannelCreate,
    PublishingChannelRead,
    PublishingChannelUpdate,
)
from app.services import publishing as publishing_service

router = APIRouter(prefix="/publishing", tags=["publishing"])


@router.get("/channels", response_model=ListResponse[PublishingChannelRead])
def list_channels(
    session: DbSession,
    user: CurrentUser,
    pagination: PaginationParams = Depends(pagination_params),
    project_id: UUID | None = Query(default=None),
) -> ListResponse[PublishingChannelRead]:
    items, total = publishing_service.list_channels(session, user, pagination, project_id=project_id)
    return ListResponse(
        data=items,
        pagination=PaginationMeta(page=pagination.page, page_size=pagination.page_size, total=total),
    )


@router.post("/channels", response_model=SuccessResponse[PublishingChannelRead], status_code=201)
def create_channel(
    payload: PublishingChannelCreate,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[PublishingChannelRead]:
    return SuccessResponse(data=publishing_service.create_channel(session, user, payload))


@router.get("/channels/{channel_id}", response_model=SuccessResponse[PublishingChannelRead])
def get_channel(
    channel_id: UUID,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[PublishingChannelRead]:
    return SuccessResponse(data=publishing_service.get_channel(session, user, channel_id))


@router.patch("/channels/{channel_id}", response_model=SuccessResponse[PublishingChannelRead])
def update_channel(
    channel_id: UUID,
    payload: PublishingChannelUpdate,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[PublishingChannelRead]:
    return SuccessResponse(data=publishing_service.update_channel(session, user, channel_id, payload))


@router.delete("/channels/{channel_id}", status_code=204)
def delete_channel(channel_id: UUID, session: DbSession, user: CurrentUser) -> None:
    publishing_service.delete_channel(session, user, channel_id)


@router.get("/history", response_model=ListResponse[PublishedAssetRead])
def publish_history(
    session: DbSession,
    user: CurrentUser,
    pagination: PaginationParams = Depends(pagination_params),
    project_id: UUID | None = Query(default=None),
) -> ListResponse[PublishedAssetRead]:
    items, total = publishing_service.list_publish_history(session, user, pagination, project_id=project_id)
    return ListResponse(
        data=items,
        pagination=PaginationMeta(page=pagination.page, page_size=pagination.page_size, total=total),
    )


@router.get("/{published_id}", response_model=SuccessResponse[PublishedAssetRead])
def get_published(
    published_id: UUID,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[PublishedAssetRead]:
    return SuccessResponse(data=publishing_service.get_published(session, user, published_id))
