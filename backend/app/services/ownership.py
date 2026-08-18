from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.campaign import Campaign
from app.models.content import ContentAsset, ContentLink
from app.models.media import MediaAsset
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.publishing import PublishedAsset, PublishingChannel
from app.models.user import User


def get_owned_project(session: Session, user: User, project_id: UUID) -> Project:
    project = session.get(Project, project_id)
    if not project:
        raise NotFoundError("Project not found")
    if project.user_id != user.id:
        raise ForbiddenError("You do not own this project")
    return project


def assert_project_owned(session: Session, user: User, project_id: UUID) -> Project:
    return get_owned_project(session, user, project_id)


def get_owned_campaign(session: Session, user: User, campaign_id: UUID) -> Campaign:
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise NotFoundError("Campaign not found")
    get_owned_project(session, user, campaign.project_id)
    return campaign


def get_owned_content(session: Session, user: User, content_id: UUID) -> ContentAsset:
    content = session.get(ContentAsset, content_id)
    if not content:
        raise NotFoundError("Content not found")
    get_owned_project(session, user, content.project_id)
    return content


def get_owned_prompt(session: Session, user: User, prompt_id: UUID) -> Prompt:
    prompt = session.get(Prompt, prompt_id)
    if not prompt:
        raise NotFoundError("Prompt not found")
    get_owned_project(session, user, prompt.project_id)
    return prompt


def get_owned_link(session: Session, user: User, link_id: UUID) -> ContentLink:
    link = session.get(ContentLink, link_id)
    if not link:
        raise NotFoundError("Link not found")
    get_owned_content(session, user, link.content_asset_id)
    return link


def get_owned_media(session: Session, user: User, media_id: UUID) -> MediaAsset:
    media = session.get(MediaAsset, media_id)
    if not media:
        raise NotFoundError("Media asset not found")
    get_owned_project(session, user, media.project_id)
    return media


def get_owned_channel(session: Session, user: User, channel_id: UUID) -> PublishingChannel:
    channel = session.get(PublishingChannel, channel_id)
    if not channel:
        raise NotFoundError("Publishing channel not found")
    get_owned_project(session, user, channel.project_id)
    return channel


def get_owned_published(session: Session, user: User, published_id: UUID) -> PublishedAsset:
    published = session.get(PublishedAsset, published_id)
    if not published:
        raise NotFoundError("Published asset not found")
    get_owned_content(session, user, published.content_asset_id)
    return published


def owned_project_ids(session: Session, user: User) -> list[UUID]:
    stmt = select(Project.id).where(Project.user_id == user.id)
    return list(session.scalars(stmt))
