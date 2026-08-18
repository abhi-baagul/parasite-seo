from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession
from app.api.deps_pagination import PaginationParams, pagination_params
from app.schemas.common import ListResponse, PaginationMeta, SuccessResponse
from app.schemas.resources import PromptCreate, PromptRead
from app.services import prompts as prompt_service

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("", response_model=ListResponse[PromptRead])
def list_prompts(
    session: DbSession,
    user: CurrentUser,
    pagination: PaginationParams = Depends(pagination_params),
    project_id: UUID | None = Query(default=None),
) -> ListResponse[PromptRead]:
    items, total = prompt_service.list_prompts(session, user, pagination, project_id=project_id)
    return ListResponse(
        data=items,
        pagination=PaginationMeta(page=pagination.page, page_size=pagination.page_size, total=total),
    )


@router.post("", response_model=SuccessResponse[PromptRead], status_code=201)
def create_prompt(payload: PromptCreate, session: DbSession, user: CurrentUser) -> SuccessResponse[PromptRead]:
    return SuccessResponse(data=prompt_service.create_prompt(session, user, payload))


@router.get("/{prompt_id}", response_model=SuccessResponse[PromptRead])
def get_prompt(prompt_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[PromptRead]:
    return SuccessResponse(data=prompt_service.get_prompt(session, user, prompt_id))
