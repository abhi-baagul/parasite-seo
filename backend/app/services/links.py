from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps_pagination import PaginationParams
from app.core.exceptions import BadRequestError
from app.models.content import ContentAsset, ContentLink
from app.models.user import User
from app.schemas.resources import LinkCreate, LinkRead, LinkUpdate
from app.services.ownership import get_owned_content, get_owned_link, owned_project_ids
from app.utils.url_safety import validate_safe_url


def _enum_val(value):
    return value.value if hasattr(value, "value") else value


def list_links(
    session: Session,
    user: User,
    pagination: PaginationParams,
    *,
    project_id: UUID | None = None,
    content_asset_id: UUID | None = None,
) -> tuple[list[LinkRead], int]:
    if content_asset_id:
        get_owned_content(session, user, content_asset_id)
        filters = [ContentLink.content_asset_id == content_asset_id]
    else:
        ids = owned_project_ids(session, user)
        if project_id:
            from app.services.ownership import get_owned_project

            get_owned_project(session, user, project_id)
            content_ids = list(
                session.scalars(select(ContentAsset.id).where(ContentAsset.project_id == project_id))
            )
        else:
            content_ids = list(
                session.scalars(select(ContentAsset.id).where(ContentAsset.project_id.in_(ids)))
            ) if ids else []
        filters = [ContentLink.content_asset_id.in_(content_ids)] if content_ids else [ContentLink.id.is_(None)]
    total = session.scalar(select(func.count()).select_from(ContentLink).where(*filters)) or 0
    stmt = (
        select(ContentLink)
        .where(*filters)
        .order_by(ContentLink.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    return [LinkRead.model_validate(row) for row in session.scalars(stmt)], total


def create_link(session: Session, user: User, payload: LinkCreate) -> LinkRead:
    get_owned_content(session, user, payload.content_asset_id)
    url = validate_safe_url(str(payload.target_url))
    # Duplicate protection
    dup = session.scalar(
        select(ContentLink).where(
            ContentLink.content_asset_id == payload.content_asset_id,
            ContentLink.target_url == url,
            ContentLink.anchor_text == payload.anchor_text.strip(),
        )
    )
    if dup:
        raise BadRequestError("Duplicate link already exists for this content")
    link = ContentLink(
        content_asset_id=payload.content_asset_id,
        target_url=url,
        anchor_text=payload.anchor_text.strip(),
        placement_description=payload.placement_description,
        link_attribute=_enum_val(payload.link_attribute),
        status=_enum_val(payload.status),
    )
    session.add(link)
    session.flush()
    return LinkRead.model_validate(link)


def get_link(session: Session, user: User, link_id: UUID) -> LinkRead:
    return LinkRead.model_validate(get_owned_link(session, user, link_id))


def update_link(session: Session, user: User, link_id: UUID, payload: LinkUpdate) -> LinkRead:
    link = get_owned_link(session, user, link_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "anchor_text" and isinstance(value, str):
            value = value.strip()
        if key == "target_url" and value is not None:
            value = validate_safe_url(str(value))
        setattr(link, key, _enum_val(value))
    session.flush()
    return LinkRead.model_validate(link)


def delete_link(session: Session, user: User, link_id: UUID) -> None:
    link = get_owned_link(session, user, link_id)
    session.delete(link)
    session.flush()
