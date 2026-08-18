from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession
from app.api.deps_pagination import PaginationParams, pagination_params
from app.schemas.common import ListResponse, PaginationMeta, SuccessResponse
from app.schemas.resources import AIRunRead
from app.services import ai_runs as ai_run_service

router = APIRouter(prefix="/ai", tags=["ai-runs"])


@router.get("/runs", response_model=ListResponse[AIRunRead])
def list_runs(
    session: DbSession,
    user: CurrentUser,
    pagination: PaginationParams = Depends(pagination_params),
    project_id: UUID | None = Query(default=None),
) -> ListResponse[AIRunRead]:
    items, total = ai_run_service.list_ai_runs(session, user, pagination, project_id=project_id)
    return ListResponse(
        data=items,
        pagination=PaginationMeta(page=pagination.page, page_size=pagination.page_size, total=total),
    )


@router.get("/runs/{run_id}", response_model=SuccessResponse[AIRunRead])
def get_run(run_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[AIRunRead]:
    return SuccessResponse(data=ai_run_service.get_ai_run(session, user, run_id))
