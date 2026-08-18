from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps_pagination import PaginationParams
from app.models.campaign import Campaign
from app.models.user import User
from app.schemas.resources import CampaignCreate, CampaignRead, CampaignUpdate
from app.services.ownership import get_owned_campaign, get_owned_project


def list_campaigns(
    session: Session,
    user: User,
    project_id: UUID,
    pagination: PaginationParams,
) -> tuple[list[CampaignRead], int]:
    get_owned_project(session, user, project_id)
    filters = [Campaign.project_id == project_id]
    total = session.scalar(select(func.count()).select_from(Campaign).where(*filters)) or 0
    stmt = (
        select(Campaign)
        .where(*filters)
        .order_by(Campaign.updated_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    return [CampaignRead.model_validate(row) for row in session.scalars(stmt)], total


def create_campaign(
    session: Session,
    user: User,
    project_id: UUID,
    payload: CampaignCreate,
) -> CampaignRead:
    get_owned_project(session, user, project_id)
    data = payload.model_dump()
    for key in ("status", "default_content_type"):
        if hasattr(data[key], "value"):
            data[key] = data[key].value
    campaign = Campaign(project_id=project_id, **data)
    session.add(campaign)
    session.flush()
    return CampaignRead.model_validate(campaign)


def get_campaign(session: Session, user: User, campaign_id: UUID) -> CampaignRead:
    return CampaignRead.model_validate(get_owned_campaign(session, user, campaign_id))


def update_campaign(
    session: Session,
    user: User,
    campaign_id: UUID,
    payload: CampaignUpdate,
) -> CampaignRead:
    campaign = get_owned_campaign(session, user, campaign_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(campaign, key, value.value if hasattr(value, "value") else value)
    session.flush()
    return CampaignRead.model_validate(campaign)


def delete_campaign(session: Session, user: User, campaign_id: UUID) -> None:
    campaign = get_owned_campaign(session, user, campaign_id)
    session.delete(campaign)
    session.flush()
