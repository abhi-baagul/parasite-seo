from fastapi import APIRouter

from app.api.deps import DbSession
from app.core.config import settings
from app.schemas.common import SuccessResponse
from app.schemas.health import HealthComponent, HealthResponse
from app.services.health import check_database, check_redis

router = APIRouter(tags=["health"])


@router.get("/health", response_model=SuccessResponse[HealthResponse])
def health_v1(session: DbSession) -> SuccessResponse[HealthResponse]:
    db = check_database(session)
    redis = check_redis()
    overall = "ok" if db["status"] == "ok" and redis["status"] == "ok" else "error"
    return SuccessResponse(
        data=HealthResponse(
            status=overall,
            environment=settings.environment,
            database=HealthComponent(status=db["status"]),
            redis=HealthComponent(status=redis["status"]),
        )
    )
