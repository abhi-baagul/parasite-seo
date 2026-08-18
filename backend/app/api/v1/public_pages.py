"""Public-safe page endpoints (no auth)."""

from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.common import SuccessResponse
from app.services import public_pages as public_page_service

router = APIRouter(prefix="/public-pages", tags=["public-pages"])


@router.get("/{slug}", response_model=SuccessResponse[dict])
def get_public_page(slug: str, session: DbSession) -> SuccessResponse[dict]:
    return SuccessResponse(data=public_page_service.get_public_page_by_slug(session, slug))
