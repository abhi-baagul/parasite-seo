from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession
from app.api.deps_pagination import PaginationParams, pagination_params
from app.schemas.common import ListResponse, PaginationMeta, SuccessResponse
from app.schemas.resources import MediaCreate, MediaRead, MediaUpdate
from app.services import media as media_service

router = APIRouter(prefix="/media", tags=["media"])


@router.get("", response_model=ListResponse[MediaRead])
def list_media(
    session: DbSession,
    user: CurrentUser,
    pagination: PaginationParams = Depends(pagination_params),
    project_id: UUID | None = Query(default=None),
    content_asset_id: UUID | None = Query(default=None),
    media_type: str | None = Query(default=None),
) -> ListResponse[MediaRead]:
    items, total = media_service.list_media(
        session,
        user,
        pagination,
        project_id=project_id,
        content_asset_id=content_asset_id,
        media_type=media_type,
    )
    return ListResponse(
        data=items,
        pagination=PaginationMeta(page=pagination.page, page_size=pagination.page_size, total=total),
    )


@router.post("", response_model=SuccessResponse[MediaRead], status_code=201)
def create_media(payload: MediaCreate, session: DbSession, user: CurrentUser) -> SuccessResponse[MediaRead]:
    return SuccessResponse(data=media_service.create_media(session, user, payload))


@router.get("/{media_id}", response_model=SuccessResponse[MediaRead])
def get_media(media_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[MediaRead]:
    return SuccessResponse(data=media_service.get_media(session, user, media_id))


@router.patch("/{media_id}", response_model=SuccessResponse[MediaRead])
def update_media(
    media_id: UUID,
    payload: MediaUpdate,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[MediaRead]:
    return SuccessResponse(data=media_service.update_media(session, user, media_id, payload))


@router.delete("/{media_id}", status_code=204)
def delete_media(media_id: UUID, session: DbSession, user: CurrentUser) -> None:
    media_service.delete_media(session, user, media_id)
