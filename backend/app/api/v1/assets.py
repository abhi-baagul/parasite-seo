from fastapi import APIRouter, Depends, Query
from uuid import UUID

from app.api.deps import CurrentUser, DbSession
from app.api.deps_pagination import PaginationParams, pagination_params
from app.schemas.common import ListResponse, PaginationMeta
from app.services import content_studio as studio_service

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/library", response_model=ListResponse[dict])
def asset_library(
    session: DbSession,
    user: CurrentUser,
    pagination: PaginationParams = Depends(pagination_params),
    project_id: UUID | None = Query(default=None),
    q: str | None = Query(default=None),
) -> ListResponse[dict]:
    items, total = studio_service.list_asset_library(
        session, user, pagination, project_id=project_id, q=q
    )
    return ListResponse(
        data=items,
        pagination=PaginationMeta(page=pagination.page, page_size=pagination.page_size, total=total),
    )
