"""Phase 7 — Content network + internal link APIs under Parasite SEO."""

from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import SuccessResponse
from app.services import content_network as service

router = APIRouter(prefix="/parasite-seo/link-network", tags=["content-network"])


class AnalyzeRequest(BaseModel):
    project_id: UUID
    use_ai: bool = True


class SettingsUpdateRequest(BaseModel):
    automatic_internal_linking: bool | None = None
    min_relevance_score: int | None = Field(default=None, ge=50, le=99)
    max_new_links_per_article: int | None = Field(default=None, ge=1, le=20)
    max_links_to_same_target: int | None = Field(default=None, ge=1, le=5)
    max_links_per_section: int | None = Field(default=None, ge=1, le=5)
    related_content_limit: int | None = Field(default=None, ge=1, le=8)


class SuggestionPatchRequest(BaseModel):
    anchor_text: str | None = None
    placement: str | None = None
    context: str | None = None


class OrphanSuggestionRequest(BaseModel):
    project_id: UUID
    source_content_id: UUID
    target_content_id: UUID
    anchor_text: str | None = None


class SlugUpdateLinksRequest(BaseModel):
    project_id: UUID
    old_slug: str
    new_slug: str
    public_page_id: UUID | None = None


@router.post("/analyze", response_model=SuccessResponse[dict])
def analyze_network(payload: AnalyzeRequest, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=service.analyze_network(session, user, payload.project_id, use_ai=payload.use_ai)
    )


@router.get("", response_model=SuccessResponse[dict])
def get_network(
    session: DbSession,
    user: CurrentUser,
    project_id: UUID = Query(...),
) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.network_overview(session, user, project_id))


@router.post("/suggestions", response_model=SuccessResponse[dict])
def create_orphan_suggestion(
    payload: OrphanSuggestionRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=service.create_suggestion_from_opportunity(
            session,
            user,
            project_id=payload.project_id,
            source_content_id=payload.source_content_id,
            target_content_id=payload.target_content_id,
            anchor_text=payload.anchor_text,
        )
    )


@router.get("/orphans/{content_id}/opportunities", response_model=SuccessResponse[list])
def orphan_opportunities(
    content_id: UUID,
    session: DbSession,
    user: CurrentUser,
    project_id: UUID = Query(...),
) -> SuccessResponse[list]:
    return SuccessResponse(data=service.orphan_opportunities(session, user, project_id, content_id))


@router.post("/slug-redirects/apply", response_model=SuccessResponse[dict])
def apply_slug_redirects(
    payload: SlugUpdateLinksRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=service.update_links_for_slug_change(
            session,
            user,
            project_id=payload.project_id,
            old_slug=payload.old_slug,
            new_slug=payload.new_slug,
            public_page_id=payload.public_page_id,
        )
    )


@router.get("/{project_id}/settings", response_model=SuccessResponse[dict])
def get_settings(project_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.get_link_settings(session, user, project_id))


@router.patch("/{project_id}/settings", response_model=SuccessResponse[dict])
def patch_settings(
    project_id: UUID,
    payload: SettingsUpdateRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    data = payload.model_dump(exclude_none=True)
    return SuccessResponse(data=service.update_link_settings(session, user, project_id, data))


@router.get("/{project_id}", response_model=SuccessResponse[dict])
def get_network_by_project(
    project_id: UUID,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.network_overview(session, user, project_id))


suggestions_router = APIRouter(prefix="/parasite-seo/link-suggestions", tags=["content-network"])


@suggestions_router.get("", response_model=SuccessResponse[dict])
def list_suggestions(
    session: DbSession,
    user: CurrentUser,
    project_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
) -> SuccessResponse[dict]:
    items = service.list_suggestions(session, user, project_id=project_id, status=status)
    return SuccessResponse(data={"items": items})


@suggestions_router.post("/{suggestion_id}/approve", response_model=SuccessResponse[dict])
def approve_suggestion(
    suggestion_id: UUID,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.approve_and_insert(session, user, suggestion_id))


@suggestions_router.post("/{suggestion_id}/reject", response_model=SuccessResponse[dict])
def reject_suggestion(
    suggestion_id: UUID,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.reject_suggestion(session, user, suggestion_id))


@suggestions_router.patch("/{suggestion_id}", response_model=SuccessResponse[dict])
def patch_suggestion(
    suggestion_id: UUID,
    payload: SuggestionPatchRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=service.update_suggestion(
            session,
            user,
            suggestion_id,
            anchor_text=payload.anchor_text,
            placement=payload.placement,
            context=payload.context,
        )
    )


@suggestions_router.delete("/broken/{link_id}", response_model=SuccessResponse[dict])
def remove_broken(link_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.remove_broken_link(session, user, link_id))
