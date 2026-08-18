from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps_pagination import PaginationParams
from app.models.analytics import AnalyticsMetric
from app.models.user import User
from app.schemas.resources import AnalyticsMetricRead, AnalyticsOverview
from app.services.ownership import get_owned_project, owned_project_ids


def list_metrics(
    session: Session,
    user: User,
    pagination: PaginationParams,
    *,
    project_id: UUID | None = None,
) -> tuple[list[AnalyticsMetricRead], int]:
    if project_id:
        get_owned_project(session, user, project_id)
        filters = [AnalyticsMetric.project_id == project_id]
    else:
        ids = owned_project_ids(session, user)
        filters = [AnalyticsMetric.project_id.in_(ids)] if ids else [AnalyticsMetric.project_id.is_(None)]
    total = session.scalar(select(func.count()).select_from(AnalyticsMetric).where(*filters)) or 0
    stmt = (
        select(AnalyticsMetric)
        .where(*filters)
        .order_by(AnalyticsMetric.metric_date.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    return [_to_read(row) for row in session.scalars(stmt)], total


def overview(session: Session, user: User, *, project_id: UUID | None = None) -> AnalyticsOverview:
    if project_id:
        get_owned_project(session, user, project_id)
        filters = [AnalyticsMetric.project_id == project_id]
    else:
        ids = owned_project_ids(session, user)
        filters = [AnalyticsMetric.project_id.in_(ids)] if ids else [AnalyticsMetric.project_id.is_(None)]

    rows = list(session.scalars(select(AnalyticsMetric).where(*filters)))
    totals: dict[str, float] = {}
    for row in rows:
        totals[row.metric_type] = totals.get(row.metric_type, 0.0) + float(row.metric_value)
    return AnalyticsOverview(
        impressions=totals.get("impressions", 0.0),
        clicks=totals.get("clicks", 0.0),
        ctr=totals.get("ctr", 0.0),
        traffic=totals.get("traffic", 0.0),
        average_position=totals.get("average_position", 0.0),
        conversions=totals.get("conversions", 0.0),
        revenue=totals.get("revenue", 0.0),
        metric_count=len(rows),
    )


def _to_read(row: AnalyticsMetric) -> AnalyticsMetricRead:
    return AnalyticsMetricRead(
        id=row.id,
        project_id=row.project_id,
        content_asset_id=row.content_asset_id,
        metric_type=row.metric_type,
        metric_value=float(row.metric_value),
        metric_date=row.metric_date.isoformat(),
        source=row.source,
        created_at=row.created_at,
    )
