from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.health import HealthComponent, HealthResponse
from app.services.health import check_database, check_redis

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(session: Session = Depends(get_db)) -> HealthResponse:
    db = check_database(session)
    redis = check_redis()
    overall = "ok" if db["status"] == "ok" and redis["status"] == "ok" else "error"
    return HealthResponse(
        status=overall,
        environment=settings.environment,
        database=HealthComponent(status=db["status"]),
        redis=HealthComponent(status=redis["status"]),
    )


@router.get("/health/db")
def health_db(session: Session = Depends(get_db)) -> dict[str, str]:
    return check_database(session)


@router.get("/health/redis")
def health_redis() -> dict[str, str]:
    return check_redis()


@router.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok"}
