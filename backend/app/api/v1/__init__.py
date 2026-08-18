from fastapi import APIRouter

from app.api.v1.account import router as account_router
from app.api.v1.ai_runs import router as ai_runs_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.assets import router as assets_router
from app.api.v1.backlink_campaigns import router as backlink_campaigns_router
from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.content import router as content_router
from app.api.v1.health import router as health_router
from app.api.v1.keywords import router as keywords_router
from app.api.v1.link_network import router as link_network_router
from app.api.v1.link_network import suggestions_router as link_suggestions_router
from app.api.v1.links import router as links_router
from app.api.v1.media import router as media_router
from app.api.v1.parasite_seo import router as parasite_seo_router
from app.api.v1.projects import router as projects_router
from app.api.v1.prompts import router as prompts_router
from app.api.v1.public_pages import router as public_pages_router
from app.api.v1.publishing import router as publishing_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router)
api_v1_router.include_router(account_router)
api_v1_router.include_router(projects_router)
api_v1_router.include_router(campaigns_router)
api_v1_router.include_router(prompts_router)
api_v1_router.include_router(content_router)
api_v1_router.include_router(parasite_seo_router)
api_v1_router.include_router(backlink_campaigns_router)
api_v1_router.include_router(link_network_router)
api_v1_router.include_router(link_suggestions_router)
api_v1_router.include_router(public_pages_router)
api_v1_router.include_router(assets_router)
api_v1_router.include_router(links_router)
api_v1_router.include_router(media_router)
api_v1_router.include_router(publishing_router)
api_v1_router.include_router(ai_runs_router)
api_v1_router.include_router(keywords_router)
api_v1_router.include_router(analytics_router)
