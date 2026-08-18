from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession
from app.api.deps_pagination import PaginationParams, pagination_params
from app.schemas.common import ListResponse, PaginationMeta, SuccessResponse
from app.schemas.resources import AnalyticsMetricRead, AnalyticsOverview
from app.services import analytics as analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=ListResponse[AnalyticsMetricRead])
def list_analytics(
    session: DbSession,
    user: CurrentUser,
    pagination: PaginationParams = Depends(pagination_params),
    project_id: UUID | None = Query(default=None),
) -> ListResponse[AnalyticsMetricRead]:
    items, total = analytics_service.list_metrics(session, user, pagination, project_id=project_id)
    return ListResponse(
        data=items,
        pagination=PaginationMeta(page=pagination.page, page_size=pagination.page_size, total=total),
    )


@router.get("/overview", response_model=SuccessResponse[AnalyticsOverview])
def analytics_overview(
    session: DbSession,
    user: CurrentUser,
    project_id: UUID | None = Query(default=None),
) -> SuccessResponse[AnalyticsOverview]:
    return SuccessResponse(data=analytics_service.overview(session, user, project_id=project_id))
