from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps_pagination import PaginationParams
from app.core.exceptions import ConflictError
from app.models.campaign import Campaign
from app.models.content import ContentAsset
from app.models.project import Project
from app.models.user import User
from app.schemas.resources import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.ownership import get_owned_project


def _to_read(session: Session, project: Project) -> ProjectRead:
    campaign_count = session.scalar(
        select(func.count()).select_from(Campaign).where(Campaign.project_id == project.id)
    ) or 0
    content_count = session.scalar(
        select(func.count()).select_from(ContentAsset).where(ContentAsset.project_id == project.id)
    ) or 0
    data = ProjectRead.model_validate(project)
    return data.model_copy(update={"campaign_count": campaign_count, "content_count": content_count})


def list_projects(
    session: Session,
    user: User,
    pagination: PaginationParams,
) -> tuple[list[ProjectRead], int]:
    filters = [Project.user_id == user.id]
    total = session.scalar(select(func.count()).select_from(Project).where(*filters)) or 0
    stmt = (
        select(Project)
        .where(*filters)
        .order_by(Project.updated_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    rows = list(session.scalars(stmt))
    return [_to_read(session, row) for row in rows], total


def create_project(session: Session, user: User, payload: ProjectCreate) -> ProjectRead:
    project = Project(user_id=user.id, **payload.model_dump())
    session.add(project)
    session.flush()
    return _to_read(session, project)


def get_project(session: Session, user: User, project_id: UUID) -> ProjectRead:
    return _to_read(session, get_owned_project(session, user, project_id))


def update_project(session: Session, user: User, project_id: UUID, payload: ProjectUpdate) -> ProjectRead:
    project = get_owned_project(session, user, project_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, key, value.value if hasattr(value, "value") else value)
    session.flush()
    return _to_read(session, project)


def delete_project(session: Session, user: User, project_id: UUID) -> None:
    project = get_owned_project(session, user, project_id)
    has_campaigns = session.scalar(
        select(func.count()).select_from(Campaign).where(Campaign.project_id == project.id)
    )
    has_content = session.scalar(
        select(func.count()).select_from(ContentAsset).where(ContentAsset.project_id == project.id)
    )
    if has_campaigns or has_content:
        raise ConflictError("Delete related campaigns and content before deleting the project")
    session.delete(project)
    session.flush()
