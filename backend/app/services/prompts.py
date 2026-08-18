from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps_pagination import PaginationParams
from app.models.prompt import Prompt
from app.models.user import User
from app.schemas.resources import PromptCreate, PromptRead
from app.services.ownership import get_owned_campaign, get_owned_project, get_owned_prompt, owned_project_ids


def list_prompts(
    session: Session,
    user: User,
    pagination: PaginationParams,
    *,
    project_id: UUID | None = None,
) -> tuple[list[PromptRead], int]:
    if project_id:
        get_owned_project(session, user, project_id)
        filters = [Prompt.project_id == project_id]
    else:
        ids = owned_project_ids(session, user)
        filters = [Prompt.project_id.in_(ids)] if ids else [Prompt.project_id.is_(None)]
    total = session.scalar(select(func.count()).select_from(Prompt).where(*filters)) or 0
    stmt = (
        select(Prompt)
        .where(*filters)
        .order_by(Prompt.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    return [PromptRead.model_validate(row) for row in session.scalars(stmt)], total


def create_prompt(session: Session, user: User, payload: PromptCreate) -> PromptRead:
    get_owned_project(session, user, payload.project_id)
    if payload.campaign_id:
        campaign = get_owned_campaign(session, user, payload.campaign_id)
        if campaign.project_id != payload.project_id:
            from app.core.exceptions import BadRequestError

            raise BadRequestError("Campaign does not belong to the given project")
    # Store the original raw prompt exactly — do not normalize whitespace beyond stripping edges for emptiness.
    prompt = Prompt(
        project_id=payload.project_id,
        campaign_id=payload.campaign_id,
        raw_prompt=payload.raw_prompt,
        status=payload.status.value if hasattr(payload.status, "value") else payload.status,
    )
    session.add(prompt)
    session.flush()
    return PromptRead.model_validate(prompt)


def get_prompt(session: Session, user: User, prompt_id: UUID) -> PromptRead:
    return PromptRead.model_validate(get_owned_prompt(session, user, prompt_id))
