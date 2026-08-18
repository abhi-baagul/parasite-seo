"""Parasite SEO AI feature endpoints (includes Phase 6 web pages)."""

from uuid import UUID

from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import BadRequestError, NotFoundError
from app.schemas.common import SuccessResponse
from app.services import parasite_seo as service
from app.services import public_pages as public_page_service

router = APIRouter(prefix="/parasite-seo", tags=["parasite-seo"])


class CreateJobRequest(BaseModel):
    project_id: UUID
    prompt: str = Field(min_length=20)
    advanced_settings: dict | None = None
    target_link: dict | None = None


class RequirementsUpdateRequest(BaseModel):
    requirements: dict


class OptimizeDecisionRequest(BaseModel):
    accept: bool = True


class CreateWebPageRequest(BaseModel):
    slug: str | None = None


class UpdateWebPageRequest(BaseModel):
    slug: str | None = None
    visibility: str | None = None
    title: str | None = None


@router.get("", response_model=SuccessResponse[dict])
def list_jobs(
    session: DbSession,
    user: CurrentUser,
    project_id: UUID | None = Query(default=None),
) -> SuccessResponse[dict]:
    items, stats = service.list_jobs(session, user, project_id=project_id)
    return SuccessResponse(data={"items": items, "stats": stats})


@router.get("/public-pages", response_model=SuccessResponse[dict])
def list_web_pages(
    session: DbSession,
    user: CurrentUser,
    project_id: UUID | None = Query(default=None),
) -> SuccessResponse[dict]:
    items = public_page_service.list_public_pages_admin(session, user, project_id=project_id)
    return SuccessResponse(data={"items": items})


@router.post("/jobs", response_model=SuccessResponse[dict], status_code=201)
def create_job(payload: CreateJobRequest, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=service.create_job(
            session,
            user,
            project_id=payload.project_id,
            prompt=payload.prompt,
            advanced_settings=payload.advanced_settings,
            target_link=payload.target_link,
        )
    )


@router.get("/jobs/by-content/{content_id}", response_model=SuccessResponse[dict])
def job_by_content(content_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    job_id = public_page_service.find_job_id_for_content(session, user, content_id)
    if not job_id:
        raise NotFoundError("No Parasite SEO job is linked to this content")
    return SuccessResponse(data=service.get_job(session, user, job_id))


@router.get("/jobs/{job_id}", response_model=SuccessResponse[dict])
def get_job(job_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.get_job(session, user, job_id))


@router.post("/jobs/{job_id}/analyze", response_model=SuccessResponse[dict])
def analyze_job(job_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.analyze_job(session, user, job_id))


@router.patch("/jobs/{job_id}/requirements", response_model=SuccessResponse[dict])
def update_requirements(
    job_id: UUID,
    payload: RequirementsUpdateRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.update_requirements(session, user, job_id, payload.requirements))


@router.post("/jobs/{job_id}/generate", response_model=SuccessResponse[dict])
def generate_job(
    job_id: UUID,
    session: DbSession,
    user: CurrentUser,
    stage: str | None = Query(default=None, description="confirm | research | strategy | outline | write | all"),
) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.generate_job(session, user, job_id, stage=stage))


@router.post("/jobs/{job_id}/seo-analyze", response_model=SuccessResponse[dict])
def seo_analyze(job_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.seo_analyze_job(session, user, job_id))


@router.post("/jobs/{job_id}/optimize", response_model=SuccessResponse[dict])
def optimize(job_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.optimize_job(session, user, job_id))


@router.post("/jobs/{job_id}/optimize/decision", response_model=SuccessResponse[dict])
def optimize_decision(
    job_id: UUID,
    payload: OptimizeDecisionRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.accept_optimize(session, user, job_id, accept=payload.accept))


@router.post("/jobs/{job_id}/link-analysis", response_model=SuccessResponse[dict])
def link_analysis(job_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.link_analysis_job(session, user, job_id))


@router.post("/jobs/{job_id}/media-analysis", response_model=SuccessResponse[dict])
def media_analysis(job_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.media_analysis_job(session, user, job_id))


@router.post("/jobs/{job_id}/preview", response_model=SuccessResponse[dict])
def preview(job_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    data = service.get_job(session, user, job_id)
    data["preview"] = True
    return SuccessResponse(data=data)


@router.post("/jobs/{job_id}/web-page", response_model=SuccessResponse[dict], status_code=201)
def create_web_page(
    job_id: UUID,
    session: DbSession,
    user: CurrentUser,
    payload: CreateWebPageRequest | None = None,
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=public_page_service.create_web_page(
            session,
            user,
            job_id,
            slug=(payload.slug if payload else None),
        )
    )


@router.get("/jobs/{job_id}/web-page", response_model=SuccessResponse[dict])
def get_web_page(
    job_id: UUID,
    session: DbSession,
    user: CurrentUser,
    preview: bool = Query(default=False),
) -> SuccessResponse[dict]:
    return SuccessResponse(data=public_page_service.get_web_page(session, user, job_id, preview=preview))


@router.patch("/jobs/{job_id}/web-page", response_model=SuccessResponse[dict])
def update_web_page(
    job_id: UUID,
    payload: UpdateWebPageRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=public_page_service.update_web_page(
            session,
            user,
            job_id,
            slug=payload.slug,
            visibility=payload.visibility,
            title=payload.title,
        )
    )


@router.post("/jobs/{job_id}/web-page/publish", response_model=SuccessResponse[dict])
def publish_web_page(job_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    data = public_page_service.publish_web_page(session, user, job_id)
    job = service._job_or_404(session, user, job_id)
    service._set_step(job, "publication", "completed")
    service._set_step(job, "web_page", "completed")
    session.flush()
    return SuccessResponse(data=data)


@router.post("/jobs/{job_id}/web-page/unpublish", response_model=SuccessResponse[dict])
def unpublish_web_page(job_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=public_page_service.unpublish_web_page(session, user, job_id))


@router.post("/jobs/{job_id}/web-page/archive", response_model=SuccessResponse[dict])
def archive_web_page(job_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=public_page_service.archive_web_page(session, user, job_id))


@router.post("/jobs/{job_id}/web-page/update-published", response_model=SuccessResponse[dict])
def update_published(job_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=public_page_service.update_published_page(session, user, job_id))


@router.delete("/jobs/{job_id}/web-page", response_model=SuccessResponse[dict])
def delete_web_page(
    job_id: UUID,
    session: DbSession,
    user: CurrentUser,
    keep_content: bool = Query(default=True),
) -> SuccessResponse[dict]:
    return SuccessResponse(
        data=public_page_service.delete_web_page(session, user, job_id, keep_content=keep_content)
    )


@router.post("/jobs/{job_id}/publish", response_model=SuccessResponse[dict])
def publish(job_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.publish_job(session, user, job_id))


@router.get("/jobs/{job_id}/public-url", response_model=SuccessResponse[dict])
def public_url(job_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    job = service.get_job(session, user, job_id)
    return SuccessResponse(
        data={
            "public_url": job.get("public_url"),
            "public_slug": job.get("public_slug"),
            "is_public": job.get("is_public"),
            "web_page": job.get("web_page"),
        }
    )


@router.post("/jobs/{job_id}/media", response_model=SuccessResponse[dict], status_code=201)
async def upload_media(
    job_id: UUID,
    session: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
) -> SuccessResponse[dict]:
    raw = await file.read()
    content_type = file.content_type or "application/octet-stream"
    return SuccessResponse(
        data=service.upload_media(
            session,
            user,
            job_id,
            filename=file.filename or "upload.bin",
            content_type=content_type,
            data=raw,
        )
    )


@router.get("/media-file/{file_path:path}")
def serve_media_file(file_path: str, session: DbSession) -> Response:
    if not (file_path.startswith("uploads/") or file_path.startswith("exports/")):
        raise BadRequestError("Invalid media path")
    data, mime = service.get_stored_media_bytes(session, file_path)
    return Response(content=data, media_type=mime)


@router.get("/public/pages/{slug}", response_model=SuccessResponse[dict])
def public_page_legacy(slug: str, session: DbSession) -> SuccessResponse[dict]:
    return SuccessResponse(data=service.get_public_page(session, slug))
