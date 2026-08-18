from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, DbSession
from app.api.deps_pagination import PaginationParams, pagination_params
from app.schemas.common import ListResponse, PaginationMeta, SuccessResponse
from app.schemas.resources import ProjectCreate, ProjectRead, ProjectUpdate
from app.services import projects as project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ListResponse[ProjectRead])
def list_projects(
    session: DbSession,
    user: CurrentUser,
    pagination: PaginationParams = Depends(pagination_params),
) -> ListResponse[ProjectRead]:
    items, total = project_service.list_projects(session, user, pagination)
    return ListResponse(
        data=items,
        pagination=PaginationMeta(page=pagination.page, page_size=pagination.page_size, total=total),
    )


@router.post("", response_model=SuccessResponse[ProjectRead], status_code=201)
def create_project(payload: ProjectCreate, session: DbSession, user: CurrentUser) -> SuccessResponse[ProjectRead]:
    return SuccessResponse(data=project_service.create_project(session, user, payload))


@router.get("/{project_id}", response_model=SuccessResponse[ProjectRead])
def get_project(project_id: str, session: DbSession, user: CurrentUser) -> SuccessResponse[ProjectRead]:
    from uuid import UUID

    return SuccessResponse(data=project_service.get_project(session, user, UUID(project_id)))


@router.patch("/{project_id}", response_model=SuccessResponse[ProjectRead])
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[ProjectRead]:
    from uuid import UUID

    return SuccessResponse(data=project_service.update_project(session, user, UUID(project_id), payload))


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, session: DbSession, user: CurrentUser) -> None:
    from uuid import UUID

    project_service.delete_project(session, user, UUID(project_id))
