from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession
from app.api.deps_pagination import PaginationParams, pagination_params
from app.schemas.common import ListResponse, PaginationMeta, SuccessResponse
from app.schemas.resources import LinkCreate, LinkRead, LinkUpdate
from app.services import links as link_service

router = APIRouter(prefix="/links", tags=["links"])


@router.get("", response_model=ListResponse[LinkRead])
def list_links(
    session: DbSession,
    user: CurrentUser,
    pagination: PaginationParams = Depends(pagination_params),
    project_id: UUID | None = Query(default=None),
    content_asset_id: UUID | None = Query(default=None),
) -> ListResponse[LinkRead]:
    items, total = link_service.list_links(
        session,
        user,
        pagination,
        project_id=project_id,
        content_asset_id=content_asset_id,
    )
    return ListResponse(
        data=items,
        pagination=PaginationMeta(page=pagination.page, page_size=pagination.page_size, total=total),
    )


@router.post("", response_model=SuccessResponse[LinkRead], status_code=201)
def create_link(payload: LinkCreate, session: DbSession, user: CurrentUser) -> SuccessResponse[LinkRead]:
    return SuccessResponse(data=link_service.create_link(session, user, payload))


@router.get("/{link_id}", response_model=SuccessResponse[LinkRead])
def get_link(link_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[LinkRead]:
    return SuccessResponse(data=link_service.get_link(session, user, link_id))


@router.patch("/{link_id}", response_model=SuccessResponse[LinkRead])
def update_link(
    link_id: UUID,
    payload: LinkUpdate,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[LinkRead]:
    return SuccessResponse(data=link_service.update_link(session, user, link_id, payload))


@router.delete("/{link_id}", status_code=204)
def delete_link(link_id: UUID, session: DbSession, user: CurrentUser) -> None:
    link_service.delete_link(session, user, link_id)
