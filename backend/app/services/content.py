from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps_pagination import PaginationParams
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.content import ContentAsset, ContentVersion
from app.models.user import User
from app.schemas.resources import (
    ContentCreate,
    ContentRead,
    ContentUpdate,
    ContentVersionCreate,
    ContentVersionRead,
)
from app.utils.html_sanitize import count_words, sanitize_html
from app.services.ownership import (
    get_owned_campaign,
    get_owned_content,
    get_owned_project,
    get_owned_prompt,
    owned_project_ids,
)


def _enum_val(value):
    return value.value if hasattr(value, "value") else value


def list_content(
    session: Session,
    user: User,
    pagination: PaginationParams,
    *,
    project_id: UUID | None = None,
) -> tuple[list[ContentRead], int]:
    if project_id:
        get_owned_project(session, user, project_id)
        filters = [ContentAsset.project_id == project_id]
    else:
        ids = owned_project_ids(session, user)
        filters = [ContentAsset.project_id.in_(ids)] if ids else [ContentAsset.project_id.is_(None)]
    total = session.scalar(select(func.count()).select_from(ContentAsset).where(*filters)) or 0
    stmt = (
        select(ContentAsset)
        .where(*filters)
        .order_by(ContentAsset.updated_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    return [ContentRead.model_validate(row) for row in session.scalars(stmt)], total


def create_content(session: Session, user: User, payload: ContentCreate) -> ContentRead:
    get_owned_project(session, user, payload.project_id)
    if payload.campaign_id:
        campaign = get_owned_campaign(session, user, payload.campaign_id)
        if campaign.project_id != payload.project_id:
            from app.core.exceptions import BadRequestError

            raise BadRequestError("Campaign does not belong to the given project")
    if payload.prompt_id:
        prompt = get_owned_prompt(session, user, payload.prompt_id)
        if prompt.project_id != payload.project_id:
            from app.core.exceptions import BadRequestError

            raise BadRequestError("Prompt does not belong to the given project")
    existing = session.scalar(
        select(ContentAsset).where(
            ContentAsset.project_id == payload.project_id,
            ContentAsset.slug == payload.slug,
        )
    )
    if existing:
        raise ConflictError("A content asset with this slug already exists in the project")
    content = ContentAsset(
        project_id=payload.project_id,
        campaign_id=payload.campaign_id,
        prompt_id=payload.prompt_id,
        title=payload.title,
        slug=payload.slug,
        content=payload.content,
        seo_title=payload.seo_title,
        meta_description=payload.meta_description,
        content_type=_enum_val(payload.content_type),
        status=_enum_val(payload.status),
        word_count=payload.word_count or len(payload.content.split()),
        seo_score=payload.seo_score,
        quality_score=payload.quality_score,
    )
    session.add(content)
    session.flush()
    return ContentRead.model_validate(content)


def get_content(session: Session, user: User, content_id: UUID) -> ContentRead:
    return ContentRead.model_validate(get_owned_content(session, user, content_id))


def update_content(session: Session, user: User, content_id: UUID, payload: ContentUpdate) -> ContentRead:
    content = get_owned_content(session, user, content_id)
    data = payload.model_dump(exclude_unset=True)
    if "slug" in data and data["slug"] != content.slug:
        clash = session.scalar(
            select(ContentAsset).where(
                ContentAsset.project_id == content.project_id,
                ContentAsset.slug == data["slug"],
                ContentAsset.id != content.id,
            )
        )
        if clash:
            raise ConflictError("A content asset with this slug already exists in the project")
    for key, value in data.items():
        if key == "content" and value is not None:
            value = sanitize_html(value)
        if key == "status" and value in {"published", "scheduled"}:
            raise BadRequestError("Publishing/scheduling is not available in Phase 5")
        setattr(content, key, _enum_val(value))
    if "content" in data and "word_count" not in data:
        content.word_count = count_words(content.content or "")
    session.flush()
    return ContentRead.model_validate(content)


def delete_content(session: Session, user: User, content_id: UUID) -> None:
    content = get_owned_content(session, user, content_id)
    version_count = session.scalar(
        select(func.count()).select_from(ContentVersion).where(ContentVersion.content_asset_id == content.id)
    )
    if version_count:
        raise ConflictError("Delete is blocked while version history exists; keep history intact")
    session.delete(content)
    session.flush()


def list_versions(
    session: Session,
    user: User,
    content_id: UUID,
    pagination: PaginationParams,
) -> tuple[list[ContentVersionRead], int]:
    get_owned_content(session, user, content_id)
    filters = [ContentVersion.content_asset_id == content_id]
    total = session.scalar(select(func.count()).select_from(ContentVersion).where(*filters)) or 0
    stmt = (
        select(ContentVersion)
        .where(*filters)
        .order_by(ContentVersion.version_number.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    return [ContentVersionRead.model_validate(row) for row in session.scalars(stmt)], total


def create_version(
    session: Session,
    user: User,
    content_id: UUID,
    payload: ContentVersionCreate,
) -> ContentVersionRead:
    content = get_owned_content(session, user, content_id)
    body = (payload.content if payload.content is not None else "").strip() or (content.content or "").strip()
    if not body:
        raise BadRequestError("Nothing to snapshot — generate or write article content first.")
    latest = session.scalar(
        select(func.max(ContentVersion.version_number)).where(ContentVersion.content_asset_id == content.id)
    )
    next_number = int(latest or 0) + 1
    version = ContentVersion(
        content_asset_id=content.id,
        version_number=next_number,
        content=sanitize_html(body),
        change_summary=payload.change_summary,
        source="manual",
        created_by=user.id,
    )
    session.add(version)
    # Snapshot does not overwrite the live content unless the caller also PATCHes content.
    session.flush()
    return ContentVersionRead.model_validate(version)


def get_version(session: Session, user: User, content_id: UUID, version_id: UUID) -> ContentVersionRead:
    get_owned_content(session, user, content_id)
    version = session.get(ContentVersion, version_id)
    if not version or version.content_asset_id != content_id:
        raise NotFoundError("Content version not found")
    return ContentVersionRead.model_validate(version)
