from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps_pagination import PaginationParams
from app.models.keyword import Keyword
from app.models.user import User
from app.schemas.resources import KeywordCreate, KeywordRead, KeywordUpdate
from app.services.ownership import get_owned_content, get_owned_project, owned_project_ids
from app.core.exceptions import NotFoundError


def _enum_val(value):
    return value.value if hasattr(value, "value") else value


def list_keywords(
    session: Session,
    user: User,
    pagination: PaginationParams,
    *,
    project_id: UUID | None = None,
) -> tuple[list[KeywordRead], int]:
    if project_id:
        get_owned_project(session, user, project_id)
        filters = [Keyword.project_id == project_id]
    else:
        ids = owned_project_ids(session, user)
        filters = [Keyword.project_id.in_(ids)] if ids else [Keyword.project_id.is_(None)]
    total = session.scalar(select(func.count()).select_from(Keyword).where(*filters)) or 0
    stmt = (
        select(Keyword)
        .where(*filters)
        .order_by(Keyword.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    return [_to_read(row) for row in session.scalars(stmt)], total


def create_keyword(session: Session, user: User, payload: KeywordCreate) -> KeywordRead:
    get_owned_project(session, user, payload.project_id)
    if payload.content_asset_id:
        content = get_owned_content(session, user, payload.content_asset_id)
        if content.project_id != payload.project_id:
            from app.core.exceptions import BadRequestError

            raise BadRequestError("Content does not belong to the given project")
    keyword = Keyword(
        project_id=payload.project_id,
        content_asset_id=payload.content_asset_id,
        keyword=payload.keyword.strip(),
        keyword_type=_enum_val(payload.keyword_type),
        search_volume=payload.search_volume,
        difficulty=payload.difficulty,
        cpc=Decimal(str(payload.cpc)) if payload.cpc is not None else None,
        intent=_enum_val(payload.intent) if payload.intent else None,
        country=payload.country,
        language=payload.language,
        opportunity_score=Decimal(str(payload.opportunity_score))
        if payload.opportunity_score is not None
        else None,
    )
    session.add(keyword)
    session.flush()
    return _to_read(keyword)


def get_keyword(session: Session, user: User, keyword_id: UUID) -> KeywordRead:
    keyword = session.get(Keyword, keyword_id)
    if not keyword:
        raise NotFoundError("Keyword not found")
    get_owned_project(session, user, keyword.project_id)
    return _to_read(keyword)


def update_keyword(session: Session, user: User, keyword_id: UUID, payload: KeywordUpdate) -> KeywordRead:
    keyword = session.get(Keyword, keyword_id)
    if not keyword:
        raise NotFoundError("Keyword not found")
    get_owned_project(session, user, keyword.project_id)
    data = payload.model_dump(exclude_unset=True)
    if "keyword" in data and isinstance(data["keyword"], str):
        data["keyword"] = data["keyword"].strip()
    if "cpc" in data and data["cpc"] is not None:
        data["cpc"] = Decimal(str(data["cpc"]))
    if "opportunity_score" in data and data["opportunity_score"] is not None:
        data["opportunity_score"] = Decimal(str(data["opportunity_score"]))
    for key, value in data.items():
        setattr(keyword, key, _enum_val(value))
    session.flush()
    return _to_read(keyword)


def delete_keyword(session: Session, user: User, keyword_id: UUID) -> None:
    keyword = session.get(Keyword, keyword_id)
    if not keyword:
        raise NotFoundError("Keyword not found")
    get_owned_project(session, user, keyword.project_id)
    session.delete(keyword)
    session.flush()


def _to_read(row: Keyword) -> KeywordRead:
    return KeywordRead(
        id=row.id,
        project_id=row.project_id,
        content_asset_id=row.content_asset_id,
        keyword=row.keyword,
        keyword_type=row.keyword_type,
        search_volume=row.search_volume,
        difficulty=row.difficulty,
        cpc=float(row.cpc) if row.cpc is not None else None,
        intent=row.intent,
        country=row.country,
        language=row.language,
        opportunity_score=float(row.opportunity_score) if row.opportunity_score is not None else None,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
