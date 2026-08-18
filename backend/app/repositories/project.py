from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    model = Project

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def list_for_user(self, user_id: UUID) -> list[Project]:
        stmt = select(Project).where(Project.user_id == user_id)
        return list(self.session.scalars(stmt))
