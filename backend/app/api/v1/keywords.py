from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession
from app.api.deps_pagination import PaginationParams, pagination_params
from app.schemas.common import ListResponse, PaginationMeta, SuccessResponse
from app.schemas.resources import KeywordCreate, KeywordRead, KeywordUpdate
from app.services import keywords as keyword_service

router = APIRouter(prefix="/keywords", tags=["keywords"])


@router.get("", response_model=ListResponse[KeywordRead])
def list_keywords(
    session: DbSession,
    user: CurrentUser,
    pagination: PaginationParams = Depends(pagination_params),
    project_id: UUID | None = Query(default=None),
) -> ListResponse[KeywordRead]:
    items, total = keyword_service.list_keywords(session, user, pagination, project_id=project_id)
    return ListResponse(
        data=items,
        pagination=PaginationMeta(page=pagination.page, page_size=pagination.page_size, total=total),
    )


@router.post("", response_model=SuccessResponse[KeywordRead], status_code=201)
def create_keyword(payload: KeywordCreate, session: DbSession, user: CurrentUser) -> SuccessResponse[KeywordRead]:
    return SuccessResponse(data=keyword_service.create_keyword(session, user, payload))


@router.get("/{keyword_id}", response_model=SuccessResponse[KeywordRead])
def get_keyword(keyword_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[KeywordRead]:
    return SuccessResponse(data=keyword_service.get_keyword(session, user, keyword_id))


@router.patch("/{keyword_id}", response_model=SuccessResponse[KeywordRead])
def update_keyword(
    keyword_id: UUID,
    payload: KeywordUpdate,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[KeywordRead]:
    return SuccessResponse(data=keyword_service.update_keyword(session, user, keyword_id, payload))


@router.delete("/{keyword_id}", status_code=204)
def delete_keyword(keyword_id: UUID, session: DbSession, user: CurrentUser) -> None:
    keyword_service.delete_keyword(session, user, keyword_id)
