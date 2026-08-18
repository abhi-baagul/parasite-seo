from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.api.deps_pagination import PaginationParams, pagination_params
from app.schemas.ai_pipeline import (
    AnalyzePromptRequest,
    ApproveOutlineRequest,
    ConfirmRequirementsRequest,
    GenerateContentRequest,
    OptimizeContentRequest,
)
from app.schemas.common import ListResponse, PaginationMeta, SuccessResponse
from app.schemas.resources import (
    ContentCreate,
    ContentRead,
    ContentUpdate,
    ContentVersionCreate,
    ContentVersionRead,
)
from app.services import content as content_service
from app.services import content_generation as generation_service
from app.services import content_studio as studio_service
from app.services import seo_enrichment
from app.schemas.seo_enrichment import (
    ExternalReferenceDecisionRequest,
    InsertLinkRequest,
    SelectMetadataRequest,
    SuggestionDecisionRequest,
    TargetLinkSuggestRequest,
)

router = APIRouter(prefix="/content", tags=["content"])


class SectionEditRequest(BaseModel):
    selected_html: str = Field(min_length=1)
    action: str = Field(min_length=1)
    tone: str | None = None
    instruction: str | None = None
    accept: bool = True
    full_html: str | None = None


class VersionCompareRequest(BaseModel):
    left_version_id: UUID
    right_version_id: UUID


@router.get("", response_model=ListResponse[ContentRead])
def list_content(
    session: DbSession,
    user: CurrentUser,
    pagination: PaginationParams = Depends(pagination_params),
    project_id: UUID | None = Query(default=None),
    campaign_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    content_type: str | None = Query(default=None),
    q: str | None = Query(default=None),
) -> ListResponse[ContentRead]:
    items, total = studio_service.search_content(
        session,
        user,
        pagination,
        project_id=project_id,
        campaign_id=campaign_id,
        status=status,
        content_type=content_type,
        q=q,
    )
    return ListResponse(
        data=items,
        pagination=PaginationMeta(page=pagination.page, page_size=pagination.page_size, total=total),
    )


@router.post("", response_model=SuccessResponse[ContentRead], status_code=201)
def create_content(payload: ContentCreate, session: DbSession, user: CurrentUser) -> SuccessResponse[ContentRead]:
    return SuccessResponse(data=content_service.create_content(session, user, payload))


@router.post("/analyze-prompt", response_model=SuccessResponse[dict])
def analyze_prompt(
    payload: AnalyzePromptRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    data = generation_service.analyze_prompt(
        session,
        user,
        project_id=UUID(payload.project_id),
        campaign_id=UUID(payload.campaign_id) if payload.campaign_id else None,
        raw_prompt=payload.prompt,
    )
    return SuccessResponse(data=data)


@router.post("/prompts/{prompt_id}/confirm-requirements", response_model=SuccessResponse[dict])
def confirm_requirements(
    prompt_id: UUID,
    payload: ConfirmRequirementsRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(data=generation_service.confirm_requirements(session, user, prompt_id, payload))


@router.post("/generate", response_model=SuccessResponse[dict])
def generate_content(
    payload: GenerateContentRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    data = generation_service.generate_content(
        session,
        user,
        UUID(payload.content_id),
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
    )
    return SuccessResponse(data=data)


@router.post("/{content_id}/research", response_model=SuccessResponse[dict])
def run_research(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=generation_service.run_research(session, user, content_id))


@router.get("/{content_id}/research", response_model=SuccessResponse[dict])
def get_research(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=generation_service.get_research(session, user, content_id))


@router.post("/{content_id}/strategy", response_model=SuccessResponse[dict])
def run_strategy(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=generation_service.run_strategy(session, user, content_id))


@router.get("/{content_id}/strategy", response_model=SuccessResponse[dict])
def get_strategy(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=generation_service.get_strategy(session, user, content_id))


@router.post("/{content_id}/outline", response_model=SuccessResponse[dict])
def run_outline(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=generation_service.run_outline(session, user, content_id))


@router.get("/{content_id}/outline", response_model=SuccessResponse[dict])
def get_outline(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=generation_service.get_outline(session, user, content_id))


@router.post("/{content_id}/outline/approve", response_model=SuccessResponse[dict])
def approve_outline(
    content_id: UUID,
    payload: ApproveOutlineRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=generation_service.approve_outline(session, user, content_id, outline=payload.outline)
    )


@router.post("/{content_id}/seo-check", response_model=SuccessResponse[dict])
def seo_check(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=generation_service.run_seo_check(session, user, content_id))


@router.post("/{content_id}/quality-check", response_model=SuccessResponse[dict])
def quality_check(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=generation_service.run_quality_check(session, user, content_id))


@router.get("/{content_id}/quality-checks", response_model=SuccessResponse[list])
def list_quality_checks(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[list]:
    return SuccessResponse(data=generation_service.list_quality_checks(session, user, content_id))


@router.post("/{content_id}/optimize", response_model=SuccessResponse[dict])
def optimize_content(
    content_id: UUID,
    payload: OptimizeContentRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=generation_service.run_optimize(session, user, content_id, instructions=payload.instructions)
    )


# ---- Phase 4: SEO + links + media enrichment ----


@router.post("/{content_id}/keyword-analysis", response_model=SuccessResponse[dict])
def run_keyword_analysis(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=seo_enrichment.analyze_keywords_for_content(session, user, content_id, force=True))


@router.get("/{content_id}/keyword-analysis", response_model=SuccessResponse[dict])
def get_keyword_analysis(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=seo_enrichment.get_keyword_analysis(session, user, content_id))


@router.post("/{content_id}/seo/analyze", response_model=SuccessResponse[dict])
def seo_analyze(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=seo_enrichment.analyze_seo(session, user, content_id, force=True))


@router.get("/{content_id}/seo", response_model=SuccessResponse[dict])
def get_seo_analysis(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=seo_enrichment.get_seo(session, user, content_id))


@router.post("/{content_id}/seo/generate-metadata", response_model=SuccessResponse[dict])
def seo_generate_metadata(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=seo_enrichment.generate_metadata(session, user, content_id))


@router.post("/{content_id}/seo/select-metadata", response_model=SuccessResponse[dict])
def seo_select_metadata(
    content_id: UUID,
    payload: SelectMetadataRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(data=seo_enrichment.select_metadata(session, user, content_id, payload))


@router.post("/{content_id}/seo/generate-tags", response_model=SuccessResponse[dict])
def seo_generate_tags(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=seo_enrichment.generate_tags(session, user, content_id))


@router.post("/{content_id}/tags/generate", response_model=SuccessResponse[dict])
def tags_generate(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=seo_enrichment.generate_tags(session, user, content_id))


@router.get("/{content_id}/tags", response_model=SuccessResponse[list])
def get_tags(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[list]:
    return SuccessResponse(data=seo_enrichment.list_tags(session, user, content_id))


@router.post("/{content_id}/tags/{tag_id}/decision", response_model=SuccessResponse[dict])
def tag_decision(
    content_id: UUID,
    tag_id: UUID,
    payload: SuggestionDecisionRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    accepted = payload.status == "approved"
    return SuccessResponse(data=seo_enrichment.set_tag_acceptance(session, user, content_id, tag_id, accepted))


@router.get("/{content_id}/categories", response_model=SuccessResponse[list])
def get_categories(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[list]:
    return SuccessResponse(data=seo_enrichment.list_categories(session, user, content_id))


@router.post("/{content_id}/categories/{category_id}/decision", response_model=SuccessResponse[dict])
def category_decision(
    content_id: UUID,
    category_id: UUID,
    payload: SuggestionDecisionRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    accepted = payload.status == "approved"
    return SuccessResponse(
        data=seo_enrichment.set_category_acceptance(session, user, content_id, category_id, accepted)
    )


@router.post("/{content_id}/internal-link-suggestions", response_model=SuccessResponse[dict])
def create_internal_link_suggestions(
    content_id: UUID, session: DbSession, user: CurrentUser
) -> SuccessResponse[dict]:
    return SuccessResponse(data=seo_enrichment.suggest_internal_links(session, user, content_id))


@router.get("/{content_id}/internal-link-suggestions", response_model=SuccessResponse[list])
def get_internal_link_suggestions(
    content_id: UUID, session: DbSession, user: CurrentUser
) -> SuccessResponse[list]:
    return SuccessResponse(data=seo_enrichment.list_internal_link_suggestions(session, user, content_id))


@router.post("/{content_id}/internal-link-suggestions/{suggestion_id}/decision", response_model=SuccessResponse[dict])
def internal_link_decision(
    content_id: UUID,
    suggestion_id: UUID,
    payload: SuggestionDecisionRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=seo_enrichment.decide_internal_link(session, user, content_id, suggestion_id, payload.status)
    )


@router.post("/{content_id}/external-references", response_model=SuccessResponse[dict])
def create_external_references(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=seo_enrichment.suggest_external_references(session, user, content_id))


@router.get("/{content_id}/external-references", response_model=SuccessResponse[list])
def get_external_references(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[list]:
    return SuccessResponse(data=seo_enrichment.list_external_references(session, user, content_id))


@router.post("/{content_id}/external-references/{ref_id}/decision", response_model=SuccessResponse[dict])
def external_reference_decision(
    content_id: UUID,
    ref_id: UUID,
    payload: ExternalReferenceDecisionRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=seo_enrichment.decide_external_reference(
            session, user, content_id, ref_id, payload.status, url=payload.url
        )
    )


@router.post("/{content_id}/links/analyze", response_model=SuccessResponse[dict])
def links_analyze(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=seo_enrichment.analyze_links(session, user, content_id))


@router.post("/{content_id}/links/suggest", response_model=SuccessResponse[dict])
def links_suggest(
    content_id: UUID,
    payload: TargetLinkSuggestRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(data=seo_enrichment.suggest_target_link_placement(session, user, content_id, payload))


@router.post("/{content_id}/links/insert", response_model=SuccessResponse[dict])
def links_insert(
    content_id: UUID,
    payload: InsertLinkRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(data=seo_enrichment.insert_link(session, user, content_id, payload))


@router.post("/{content_id}/seo/generate-media-plan", response_model=SuccessResponse[dict])
def seo_generate_media_plan(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=seo_enrichment.generate_media_plan(session, user, content_id))


@router.post("/{content_id}/media/video-suggestions", response_model=SuccessResponse[dict])
def media_video_suggestions(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=seo_enrichment.video_suggestions(session, user, content_id))


@router.get("/{content_id}/media", response_model=SuccessResponse[list])
def content_media(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[list]:
    return SuccessResponse(data=seo_enrichment.list_media_suggestions(session, user, content_id))


@router.post("/{content_id}/media/{suggestion_id}/decision", response_model=SuccessResponse[dict])
def media_suggestion_decision(
    content_id: UUID,
    suggestion_id: UUID,
    payload: SuggestionDecisionRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=seo_enrichment.decide_media_suggestion(session, user, content_id, suggestion_id, payload.status)
    )


@router.post("/{content_id}/seo/generate-all", response_model=SuccessResponse[dict])
def seo_generate_all(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=seo_enrichment.generate_all(session, user, content_id))


@router.get("/{content_id}", response_model=SuccessResponse[ContentRead])
def get_content(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[ContentRead]:
    return SuccessResponse(data=content_service.get_content(session, user, content_id))


@router.patch("/{content_id}", response_model=SuccessResponse[ContentRead])
def update_content(
    content_id: UUID,
    payload: ContentUpdate,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[ContentRead]:
    return SuccessResponse(data=content_service.update_content(session, user, content_id, payload))


@router.delete("/{content_id}", status_code=204)
def delete_content(content_id: UUID, session: DbSession, user: CurrentUser) -> None:
    content_service.delete_content(session, user, content_id)


@router.get("/{content_id}/versions", response_model=ListResponse[ContentVersionRead])
def list_versions(
    content_id: UUID,
    session: DbSession,
    user: CurrentUser,
    pagination: PaginationParams = Depends(pagination_params),
) -> ListResponse[ContentVersionRead]:
    items, total = content_service.list_versions(session, user, content_id, pagination)
    return ListResponse(
        data=items,
        pagination=PaginationMeta(page=pagination.page, page_size=pagination.page_size, total=total),
    )


@router.post("/{content_id}/versions", response_model=SuccessResponse[ContentVersionRead], status_code=201)
def create_version(
    content_id: UUID,
    payload: ContentVersionCreate,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[ContentVersionRead]:
    return SuccessResponse(data=content_service.create_version(session, user, content_id, payload))


@router.get("/{content_id}/versions/{version_id}", response_model=SuccessResponse[ContentVersionRead])
def get_version(
    content_id: UUID,
    version_id: UUID,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[ContentVersionRead]:
    return SuccessResponse(data=content_service.get_version(session, user, content_id, version_id))


@router.get("/{content_id}/studio", response_model=SuccessResponse[dict])
def get_studio(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=studio_service.get_studio_payload(session, user, content_id))


@router.post("/{content_id}/duplicate", response_model=SuccessResponse[ContentRead], status_code=201)
def duplicate_content(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[ContentRead]:
    return SuccessResponse(data=studio_service.duplicate_content(session, user, content_id))


@router.post("/{content_id}/versions/{version_id}/restore", response_model=SuccessResponse[dict])
def restore_version(
    content_id: UUID,
    version_id: UUID,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(data=studio_service.restore_version(session, user, content_id, version_id))


@router.post("/{content_id}/versions/compare", response_model=SuccessResponse[dict])
def compare_versions(
    content_id: UUID,
    payload: VersionCompareRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=studio_service.compare_versions(
            session,
            user,
            content_id,
            payload.left_version_id,
            payload.right_version_id,
        )
    )


@router.post("/{content_id}/ai/section-edit", response_model=SuccessResponse[dict])
def section_edit(
    content_id: UUID,
    payload: SectionEditRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=studio_service.apply_section_edit(
            session,
            user,
            content_id,
            selected_html=payload.selected_html,
            action=payload.action,
            tone=payload.tone,
            instruction=payload.instruction,
            accept=payload.accept,
            full_html=payload.full_html,
        )
    )


@router.get("/{content_id}/ai-runs", response_model=SuccessResponse[list])
def content_ai_runs(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[list]:
    data = studio_service.get_studio_payload(session, user, content_id)
    return SuccessResponse(data=data["ai_runs"])


@router.get("/{content_id}/references", response_model=SuccessResponse[list])
def content_references(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[list]:
    data = studio_service.get_studio_payload(session, user, content_id)
    return SuccessResponse(data=data["references"])


def _export_response(session: DbSession, user, content_id: UUID, fmt: str) -> Response:
    data, filename, mime = studio_service.export_content(session, user, content_id, fmt=fmt)
    return Response(
        content=data,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{content_id}/export/html")
def export_html(content_id: UUID, session: DbSession, user: CurrentUser) -> Response:
    return _export_response(session, user, content_id, "html")


@router.get("/{content_id}/export/markdown")
def export_markdown(content_id: UUID, session: DbSession, user: CurrentUser) -> Response:
    return _export_response(session, user, content_id, "markdown")


@router.get("/{content_id}/export/txt")
def export_txt(content_id: UUID, session: DbSession, user: CurrentUser) -> Response:
    return _export_response(session, user, content_id, "txt")


@router.get("/{content_id}/export/pdf")
def export_pdf(content_id: UUID, session: DbSession, user: CurrentUser) -> Response:
    return _export_response(session, user, content_id, "pdf")
