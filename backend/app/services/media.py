from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps_pagination import PaginationParams
from app.core.exceptions import BadRequestError
from app.models.media import MediaAsset
from app.models.user import User
from app.schemas.resources import MediaCreate, MediaRead, MediaUpdate
from app.services.ownership import get_owned_content, get_owned_media, get_owned_project, owned_project_ids
from app.utils.url_safety import validate_safe_url, validate_video_embed_url


def _enum_val(value):
    return value.value if hasattr(value, "value") else value


def list_media(
    session: Session,
    user: User,
    pagination: PaginationParams,
    *,
    project_id: UUID | None = None,
    content_asset_id: UUID | None = None,
    media_type: str | None = None,
) -> tuple[list[MediaRead], int]:
    if content_asset_id:
        get_owned_content(session, user, content_asset_id)
        filters = [MediaAsset.content_asset_id == content_asset_id]
    elif project_id:
        get_owned_project(session, user, project_id)
        filters = [MediaAsset.project_id == project_id]
    else:
        ids = owned_project_ids(session, user)
        filters = [MediaAsset.project_id.in_(ids)] if ids else [MediaAsset.project_id.is_(None)]
    if media_type:
        filters.append(MediaAsset.media_type == media_type)
    total = session.scalar(select(func.count()).select_from(MediaAsset).where(*filters)) or 0
    stmt = (
        select(MediaAsset)
        .where(*filters)
        .order_by(MediaAsset.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    return [MediaRead.model_validate(row) for row in session.scalars(stmt)], total


def create_media(session: Session, user: User, payload: MediaCreate) -> MediaRead:
    get_owned_project(session, user, payload.project_id)
    if payload.content_asset_id:
        content = get_owned_content(session, user, payload.content_asset_id)
        if content.project_id != payload.project_id:
            raise BadRequestError("Content does not belong to the given project")
    url = payload.url
    if url:
        if _enum_val(payload.media_type) in {"video", "video_embed"}:
            url = validate_video_embed_url(url)
        else:
            url = validate_safe_url(url)
    media = MediaAsset(
        project_id=payload.project_id,
        content_asset_id=payload.content_asset_id,
        media_type=_enum_val(payload.media_type),
        url=url,
        storage_key=payload.storage_key,
        prompt=payload.prompt,
        alt_text=payload.alt_text,
        caption=payload.caption,
        source=payload.source,
        license_information=payload.license_information,
        status=_enum_val(payload.status),
    )
    session.add(media)
    session.flush()
    return MediaRead.model_validate(media)


def get_media(session: Session, user: User, media_id: UUID) -> MediaRead:
    return MediaRead.model_validate(get_owned_media(session, user, media_id))


def update_media(session: Session, user: User, media_id: UUID, payload: MediaUpdate) -> MediaRead:
    media = get_owned_media(session, user, media_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(media, key, _enum_val(value))
    session.flush()
    return MediaRead.model_validate(media)


def delete_media(session: Session, user: User, media_id: UUID) -> None:
    media = get_owned_media(session, user, media_id)
    session.delete(media)
    session.flush()
