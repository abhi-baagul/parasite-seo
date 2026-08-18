from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps_pagination import PaginationParams
from app.models.content import ContentAsset
from app.models.publishing import PublishedAsset, PublishingChannel
from app.models.user import User
from app.schemas.resources import (
    PublishedAssetRead,
    PublishingChannelCreate,
    PublishingChannelRead,
    PublishingChannelUpdate,
)
from app.services.ownership import (
    get_owned_channel,
    get_owned_project,
    get_owned_published,
    owned_project_ids,
)


def _enum_val(value):
    return value.value if hasattr(value, "value") else value


def list_channels(
    session: Session,
    user: User,
    pagination: PaginationParams,
    *,
    project_id: UUID | None = None,
) -> tuple[list[PublishingChannelRead], int]:
    if project_id:
        get_owned_project(session, user, project_id)
        filters = [PublishingChannel.project_id == project_id]
    else:
        ids = owned_project_ids(session, user)
        filters = [PublishingChannel.project_id.in_(ids)] if ids else [PublishingChannel.project_id.is_(None)]
    total = session.scalar(select(func.count()).select_from(PublishingChannel).where(*filters)) or 0
    stmt = (
        select(PublishingChannel)
        .where(*filters)
        .order_by(PublishingChannel.updated_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    return [PublishingChannelRead.model_validate(row) for row in session.scalars(stmt)], total


def create_channel(session: Session, user: User, payload: PublishingChannelCreate) -> PublishingChannelRead:
    get_owned_project(session, user, payload.project_id)
    # Never echo secrets — store configuration as provided but responses already exclude password_hash.
    safe_config = dict(payload.configuration or {})
    for key in list(safe_config):
        lowered = key.lower()
        if any(part in lowered for part in ("password", "secret", "token", "api_key", "credential")):
            safe_config[key] = "[redacted-on-write]"
    channel = PublishingChannel(
        project_id=payload.project_id,
        name=payload.name,
        channel_type=_enum_val(payload.channel_type),
        configuration=safe_config,
        is_active=payload.is_active,
    )
    session.add(channel)
    session.flush()
    return PublishingChannelRead.model_validate(channel)


def get_channel(session: Session, user: User, channel_id: UUID) -> PublishingChannelRead:
    return PublishingChannelRead.model_validate(get_owned_channel(session, user, channel_id))


def update_channel(
    session: Session,
    user: User,
    channel_id: UUID,
    payload: PublishingChannelUpdate,
) -> PublishingChannelRead:
    channel = get_owned_channel(session, user, channel_id)
    data = payload.model_dump(exclude_unset=True)
    if "configuration" in data and data["configuration"] is not None:
        cfg = dict(data["configuration"])
        for key in list(cfg):
            lowered = key.lower()
            if any(part in lowered for part in ("password", "secret", "token", "api_key", "credential")):
                cfg[key] = "[redacted-on-write]"
        data["configuration"] = cfg
    for key, value in data.items():
        setattr(channel, key, _enum_val(value))
    session.flush()
    return PublishingChannelRead.model_validate(channel)


def delete_channel(session: Session, user: User, channel_id: UUID) -> None:
    channel = get_owned_channel(session, user, channel_id)
    session.delete(channel)
    session.flush()


def list_publish_history(
    session: Session,
    user: User,
    pagination: PaginationParams,
    *,
    project_id: UUID | None = None,
) -> tuple[list[PublishedAssetRead], int]:
    ids = owned_project_ids(session, user)
    content_q = select(ContentAsset.id).where(ContentAsset.project_id.in_(ids)) if ids else select(ContentAsset.id).where(False)
    if project_id:
        get_owned_project(session, user, project_id)
        content_q = select(ContentAsset.id).where(ContentAsset.project_id == project_id)
    content_ids = list(session.scalars(content_q))
    filters = [PublishedAsset.content_asset_id.in_(content_ids)] if content_ids else [PublishedAsset.id.is_(None)]
    total = session.scalar(select(func.count()).select_from(PublishedAsset).where(*filters)) or 0
    stmt = (
        select(PublishedAsset)
        .where(*filters)
        .order_by(PublishedAsset.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    return [PublishedAssetRead.model_validate(row) for row in session.scalars(stmt)], total


def get_published(session: Session, user: User, published_id: UUID) -> PublishedAssetRead:
    return PublishedAssetRead.model_validate(get_owned_published(session, user, published_id))
