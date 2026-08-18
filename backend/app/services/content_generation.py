from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents import (
    ContentAgent,
    OptimizationAgent,
    OutlineAgent,
    PromptAnalyzerAgent,
    QualityAgent,
    ResearchAgent,
    SeoAgent,
    StrategyAgent,
)
from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.integrations.ai.base import AIProvider
from app.models.content import ContentAsset, ContentVersion
from app.models.enums import ContentStatus, ContentType, PromptStatus, QualityCheckType, QualityStatus, RunStatus
from app.models.pipeline import (
    ContentGenerationJob,
    ContentOutline,
    ContentResearchBrief,
    ContentStrategy,
    PromptAnalysis,
)
from app.models.prompt import Prompt
from app.models.quality import QualityCheck
from app.models.user import User
from app.schemas.ai_pipeline import (
    ConfirmRequirementsRequest,
    ContentOutlineSchema,
    PromptAnalysisSchema,
    dump_schema,
)
from app.services.ownership import get_owned_content, get_owned_project
from app.utils.html_sanitize import count_words, sanitize_html

ACTIVE_JOB_STATUSES = {RunStatus.QUEUED.value, RunStatus.RUNNING.value}


def _map_content_type(value: str | None) -> str:
    if not value:
        return ContentType.ARTICLE.value
    normalized = value.lower().replace(" ", "_")
    mapping = {
        "informational_article": ContentType.ARTICLE.value,
        "article": ContentType.ARTICLE.value,
        "listicle": ContentType.LISTICLE.value,
        "comparison": ContentType.COMPARISON.value,
        "guide": ContentType.GUIDE.value,
        "review": ContentType.REVIEW.value,
        "resource_page": ContentType.RESOURCE_PAGE.value,
    }
    return mapping.get(normalized, ContentType.ARTICLE.value)


def _latest_analysis(session: Session, prompt_id: UUID) -> PromptAnalysis | None:
    return session.scalar(
        select(PromptAnalysis)
        .where(PromptAnalysis.prompt_id == prompt_id)
        .order_by(PromptAnalysis.created_at.desc())
        .limit(1)
    )


def _requirements_for_content(session: Session, content: ContentAsset) -> dict:
    if not content.prompt_id:
        raise BadRequestError("Content has no linked prompt")
    analysis = _latest_analysis(session, content.prompt_id)
    if not analysis:
        raise BadRequestError("Prompt has not been analyzed yet")
    return analysis.confirmed_requirements or analysis.requirements


def _next_version(session: Session, model, content_id: UUID) -> int:
    latest = session.scalar(
        select(func.max(model.version_number)).where(model.content_asset_id == content_id)
    )
    return int(latest or 0) + 1


def _ensure_no_active_job(session: Session, content_id: UUID, stage: str) -> ContentGenerationJob | None:
    existing = session.scalar(
        select(ContentGenerationJob)
        .where(
            ContentGenerationJob.content_asset_id == content_id,
            ContentGenerationJob.stage == stage,
            ContentGenerationJob.status.in_(list(ACTIVE_JOB_STATUSES)),
        )
        .order_by(ContentGenerationJob.created_at.desc())
        .limit(1)
    )
    return existing


def analyze_prompt(
    session: Session,
    user: User,
    *,
    project_id: UUID,
    campaign_id: UUID | None,
    raw_prompt: str,
    provider: AIProvider | None = None,
) -> dict:
    project = get_owned_project(session, user, project_id)
    if campaign_id:
        from app.services.ownership import get_owned_campaign

        campaign = get_owned_campaign(session, user, campaign_id)
        if campaign.project_id != project.id:
            raise BadRequestError("Campaign does not belong to the project")

    prompt = Prompt(
        project_id=project.id,
        campaign_id=campaign_id,
        raw_prompt=raw_prompt,  # store exactly
        status=PromptStatus.DRAFT.value,
    )
    session.add(prompt)
    session.flush()

    agent = PromptAnalyzerAgent(provider=provider)
    parsed, run = agent.run(session, project_id=project.id, content_asset_id=None, raw_prompt=raw_prompt)
    assert isinstance(parsed, PromptAnalysisSchema)
    analysis = PromptAnalysis(
        prompt_id=prompt.id,
        requirements=dump_schema(parsed),
        uncertain_fields=parsed.uncertain_fields,
        is_confirmed=False,
    )
    prompt.status = PromptStatus.ANALYZED.value
    session.add(analysis)
    session.flush()
    return {
        "prompt_id": str(prompt.id),
        "analysis_id": str(analysis.id),
        "ai_run_id": str(run.id),
        "requirements": dump_schema(parsed),
        "uncertain_fields": parsed.uncertain_fields,
    }


def confirm_requirements(
    session: Session,
    user: User,
    prompt_id: UUID,
    payload: ConfirmRequirementsRequest,
) -> dict:
    prompt = session.get(Prompt, prompt_id)
    if not prompt:
        raise NotFoundError("Prompt not found")
    get_owned_project(session, user, prompt.project_id)
    analysis = _latest_analysis(session, prompt.id)
    if not analysis:
        raise BadRequestError("No analysis found for this prompt")
    analysis.confirmed_requirements = dump_schema(payload.requirements)
    analysis.is_confirmed = True
    analysis.uncertain_fields = payload.requirements.uncertain_fields
    session.flush()

    # Create draft content shell linked to the prompt.
    title = payload.requirements.topic or payload.requirements.main_keyword or "Untitled draft"
    slug_base = (payload.requirements.main_keyword or title).lower().replace(" ", "-")[:60]
    slug = f"{slug_base}-{str(prompt.id)[:8]}"
    existing = session.scalar(
        select(ContentAsset).where(ContentAsset.project_id == prompt.project_id, ContentAsset.slug == slug)
    )
    if existing:
        content = existing
        content.prompt_id = prompt.id
        content.title = title
        content.content_type = _map_content_type(payload.requirements.content_type)
        content.status = ContentStatus.DRAFT.value
    else:
        content = ContentAsset(
            project_id=prompt.project_id,
            campaign_id=prompt.campaign_id,
            prompt_id=prompt.id,
            title=title,
            slug=slug,
            content="",
            content_type=_map_content_type(payload.requirements.content_type),
            status=ContentStatus.DRAFT.value,
            word_count=0,
        )
        session.add(content)
        session.flush()
    analysis.content_asset_id = content.id
    prompt.status = PromptStatus.USED.value
    session.flush()
    return {
        "prompt_id": str(prompt.id),
        "content_id": str(content.id),
        "requirements": analysis.confirmed_requirements,
    }


def run_research(session: Session, user: User, content_id: UUID, provider: AIProvider | None = None) -> dict:
    content = get_owned_content(session, user, content_id)
    active = _ensure_no_active_job(session, content.id, "research")
    if active:
        return {"status": active.status, "job_id": str(active.id), "message": "Research already in progress"}
    job = ContentGenerationJob(content_asset_id=content.id, stage="research", status=RunStatus.RUNNING.value)
    session.add(job)
    content.status = ContentStatus.RESEARCHING.value
    session.flush()
    try:
        requirements = _requirements_for_content(session, content)
        parsed, run = ResearchAgent(provider=provider).run(
            session,
            project_id=content.project_id,
            content_asset_id=content.id,
            requirements=requirements,
        )
        brief = ContentResearchBrief(
            content_asset_id=content.id,
            version_number=_next_version(session, ContentResearchBrief, content.id),
            payload=dump_schema(parsed),
            source_note="No live SERP provider configured in Phase 3; verify claims before publishing.",
        )
        session.add(brief)
        job.status = RunStatus.COMPLETED.value
        job.ai_run_id = run.id
        content.status = ContentStatus.DRAFT.value
        session.flush()
        return {"research": brief.payload, "version_number": brief.version_number, "ai_run_id": str(run.id)}
    except Exception as exc:
        job.status = RunStatus.FAILED.value
        job.error_message = str(exc)[:500]
        content.status = ContentStatus.FAILED.value
        session.flush()
        raise


def run_strategy(session: Session, user: User, content_id: UUID, provider: AIProvider | None = None) -> dict:
    content = get_owned_content(session, user, content_id)
    active = _ensure_no_active_job(session, content.id, "strategy")
    if active:
        return {"status": active.status, "job_id": str(active.id), "message": "Strategy already in progress"}
    research = session.scalar(
        select(ContentResearchBrief)
        .where(ContentResearchBrief.content_asset_id == content.id)
        .order_by(ContentResearchBrief.version_number.desc())
        .limit(1)
    )
    if not research:
        raise BadRequestError("Research brief is required before strategy")
    job = ContentGenerationJob(content_asset_id=content.id, stage="strategy", status=RunStatus.RUNNING.value)
    session.add(job)
    content.status = ContentStatus.STRATEGIZING.value
    session.flush()
    try:
        requirements = _requirements_for_content(session, content)
        parsed, run = StrategyAgent(provider=provider).run(
            session,
            project_id=content.project_id,
            content_asset_id=content.id,
            requirements=requirements,
            research=research.payload,
        )
        row = ContentStrategy(
            content_asset_id=content.id,
            version_number=_next_version(session, ContentStrategy, content.id),
            payload=dump_schema(parsed),
        )
        session.add(row)
        job.status = RunStatus.COMPLETED.value
        job.ai_run_id = run.id
        content.status = ContentStatus.DRAFT.value
        session.flush()
        return {"strategy": row.payload, "version_number": row.version_number, "ai_run_id": str(run.id)}
    except Exception as exc:
        job.status = RunStatus.FAILED.value
        job.error_message = str(exc)[:500]
        content.status = ContentStatus.FAILED.value
        session.flush()
        raise


def run_outline(session: Session, user: User, content_id: UUID, provider: AIProvider | None = None) -> dict:
    content = get_owned_content(session, user, content_id)
    active = _ensure_no_active_job(session, content.id, "outline")
    if active:
        return {"status": active.status, "job_id": str(active.id), "message": "Outline already in progress"}
    strategy = session.scalar(
        select(ContentStrategy)
        .where(ContentStrategy.content_asset_id == content.id)
        .order_by(ContentStrategy.version_number.desc())
        .limit(1)
    )
    if not strategy:
        raise BadRequestError("Strategy is required before outline")
    job = ContentGenerationJob(content_asset_id=content.id, stage="outline", status=RunStatus.RUNNING.value)
    session.add(job)
    content.status = ContentStatus.OUTLINING.value
    session.flush()
    try:
        requirements = _requirements_for_content(session, content)
        parsed, run = OutlineAgent(provider=provider).run(
            session,
            project_id=content.project_id,
            content_asset_id=content.id,
            requirements=requirements,
            strategy=strategy.payload,
        )
        row = ContentOutline(
            content_asset_id=content.id,
            version_number=_next_version(session, ContentOutline, content.id),
            payload=dump_schema(parsed),
            is_approved=False,
        )
        session.add(row)
        job.status = RunStatus.COMPLETED.value
        job.ai_run_id = run.id
        content.status = ContentStatus.DRAFT.value
        session.flush()
        return {"outline": row.payload, "version_number": row.version_number, "ai_run_id": str(run.id)}
    except Exception as exc:
        job.status = RunStatus.FAILED.value
        job.error_message = str(exc)[:500]
        content.status = ContentStatus.FAILED.value
        session.flush()
        raise


def approve_outline(session: Session, user: User, content_id: UUID, outline: ContentOutlineSchema | None = None) -> dict:
    content = get_owned_content(session, user, content_id)
    row = session.scalar(
        select(ContentOutline)
        .where(ContentOutline.content_asset_id == content.id)
        .order_by(ContentOutline.version_number.desc())
        .limit(1)
    )
    if not row:
        raise BadRequestError("No outline to approve")
    if outline is not None:
        row.payload = dump_schema(outline)
    row.is_approved = True
    session.flush()
    return {"outline": row.payload, "is_approved": True, "version_number": row.version_number}


def generate_content(
    session: Session,
    user: User,
    content_id: UUID,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
    provider: AIProvider | None = None,
) -> dict:
    content = get_owned_content(session, user, content_id)
    active = _ensure_no_active_job(session, content.id, "generate")
    if active:
        raise ConflictError("Content generation is already running for this asset")
    outline = session.scalar(
        select(ContentOutline)
        .where(ContentOutline.content_asset_id == content.id, ContentOutline.is_approved.is_(True))
        .order_by(ContentOutline.version_number.desc())
        .limit(1)
    )
    if not outline:
        raise BadRequestError("Approve an outline before generating content")
    research = session.scalar(
        select(ContentResearchBrief)
        .where(ContentResearchBrief.content_asset_id == content.id)
        .order_by(ContentResearchBrief.version_number.desc())
        .limit(1)
    )
    strategy = session.scalar(
        select(ContentStrategy)
        .where(ContentStrategy.content_asset_id == content.id)
        .order_by(ContentStrategy.version_number.desc())
        .limit(1)
    )
    if not research or not strategy:
        raise BadRequestError("Research and strategy are required before generation")
    if not content.prompt_id:
        raise BadRequestError("Content is missing its original prompt")
    prompt = session.get(Prompt, content.prompt_id)
    if not prompt:
        raise BadRequestError("Original prompt not found")

    job = ContentGenerationJob(content_asset_id=content.id, stage="generate", status=RunStatus.RUNNING.value)
    session.add(job)
    content.status = ContentStatus.GENERATING.value
    session.flush()
    try:
        requirements = _requirements_for_content(session, content)
        parsed, run = ContentAgent(provider=provider).run(
            session,
            project_id=content.project_id,
            content_asset_id=content.id,
            temperature=temperature,
            max_tokens=max_tokens or max(settings.ai_max_tokens, 8192),
            raw_prompt=prompt.raw_prompt,
            requirements=requirements,
            research=research.payload,
            strategy=strategy.payload,
            outline=outline.payload,
        )
        html = sanitize_html(parsed.html)
        if len(html) > 200_000:
            raise BadRequestError("Generated content exceeds safe size limits")
        # Snapshot previous content if present.
        if content.content:
            version_number = session.scalar(
                select(func.max(ContentVersion.version_number)).where(
                    ContentVersion.content_asset_id == content.id
                )
            )
            session.add(
                ContentVersion(
                    content_asset_id=content.id,
                    version_number=int(version_number or 0) + 1,
                    content=content.content,
                    change_summary="Pre-generation snapshot",
                    created_by=user.id,
                )
            )
        content.title = parsed.title
        content.seo_title = parsed.seo_title
        content.meta_description = parsed.meta_description
        desired_slug = (parsed.slug or content.slug or "content")[:320]
        unique_slug = desired_slug
        n = 1
        while True:
            clash = session.scalar(
                select(ContentAsset.id).where(
                    ContentAsset.project_id == content.project_id,
                    ContentAsset.slug == unique_slug,
                    ContentAsset.id != content.id,
                )
            )
            if not clash:
                break
            n += 1
            unique_slug = f"{desired_slug[:300]}-{n}"
        content.slug = unique_slug
        content.content = html
        content.structured_body = dump_schema(parsed)
        content.word_count = parsed.word_count or count_words(html)
        content.status = ContentStatus.REVIEW.value
        session.add(
            ContentVersion(
                content_asset_id=content.id,
                version_number=int(
                    session.scalar(
                        select(func.max(ContentVersion.version_number)).where(
                            ContentVersion.content_asset_id == content.id
                        )
                    )
                    or 0
                )
                + 1,
                content=html,
                change_summary="AI generated article",
                created_by=user.id,
            )
        )
        job.status = RunStatus.COMPLETED.value
        job.ai_run_id = run.id
        session.flush()
        return {
            "content_id": str(content.id),
            "title": content.title,
            "seo_title": content.seo_title,
            "meta_description": content.meta_description,
            "slug": content.slug,
            "content": content.content,
            "word_count": content.word_count,
            "generation_status": content.status,
            "ai_run_id": str(run.id),
        }
    except Exception as exc:
        job.status = RunStatus.FAILED.value
        job.error_message = str(exc)[:500]
        content.status = ContentStatus.FAILED.value
        session.flush()
        raise


def run_seo_check(session: Session, user: User, content_id: UUID, provider: AIProvider | None = None) -> dict:
    content = get_owned_content(session, user, content_id)
    if not content.content:
        raise BadRequestError("Generate content before SEO check")
    # Reuse latest SEO check if content unchanged since last check — simple reuse by matching content hash in summary.
    requirements = _requirements_for_content(session, content)
    parsed, run = SeoAgent(provider=provider).run(
        session,
        project_id=content.project_id,
        content_asset_id=content.id,
        requirements=requirements,
        title=content.title,
        html=content.content,
    )
    check = QualityCheck(
        content_asset_id=content.id,
        check_type=QualityCheckType.SEO.value,
        score=parsed.overall_score,
        status=QualityStatus.PASSED.value if parsed.overall_score >= 70 else QualityStatus.NEEDS_REVIEW.value,
        issues=parsed.issues,
        recommendations=parsed.recommendations
        + ["Editorial diagnostic only — not a guaranteed ranking score."],
    )
    content.seo_score = parsed.overall_score
    session.add(check)
    session.flush()
    return {"report": dump_schema(parsed), "quality_check_id": str(check.id), "ai_run_id": str(run.id)}


def run_quality_check(session: Session, user: User, content_id: UUID, provider: AIProvider | None = None) -> dict:
    content = get_owned_content(session, user, content_id)
    if not content.content:
        raise BadRequestError("Generate content before quality check")
    requirements = _requirements_for_content(session, content)
    parsed, run = QualityAgent(provider=provider).run(
        session,
        project_id=content.project_id,
        content_asset_id=content.id,
        requirements=requirements,
        html=content.content,
    )
    check = QualityCheck(
        content_asset_id=content.id,
        check_type=QualityCheckType.QUALITY.value,
        score=parsed.score,
        status=parsed.status,
        issues=parsed.issues,
        recommendations=parsed.recommendations,
    )
    content.quality_score = parsed.score
    session.add(check)
    session.flush()
    return {"report": dump_schema(parsed), "quality_check_id": str(check.id), "ai_run_id": str(run.id)}


def run_optimize(
    session: Session,
    user: User,
    content_id: UUID,
    *,
    instructions: str | None = None,
    provider: AIProvider | None = None,
) -> dict:
    content = get_owned_content(session, user, content_id)
    if not content.content:
        raise BadRequestError("Generate content before optimization")
    parsed, run = OptimizationAgent(provider=provider).run(
        session,
        project_id=content.project_id,
        content_asset_id=content.id,
        html=content.content,
        instructions=instructions,
    )
    return {"suggestions": dump_schema(parsed)["suggestions"], "ai_run_id": str(run.id)}


def get_research(session: Session, user: User, content_id: UUID) -> dict:
    content = get_owned_content(session, user, content_id)
    row = session.scalar(
        select(ContentResearchBrief)
        .where(ContentResearchBrief.content_asset_id == content.id)
        .order_by(ContentResearchBrief.version_number.desc())
        .limit(1)
    )
    if not row:
        return {"research": None, "version_number": None, "source_note": None, "exists": False}
    return {
        "research": row.payload,
        "version_number": row.version_number,
        "source_note": row.source_note,
        "exists": True,
    }


def get_outline(session: Session, user: User, content_id: UUID) -> dict:
    content = get_owned_content(session, user, content_id)
    row = session.scalar(
        select(ContentOutline)
        .where(ContentOutline.content_asset_id == content.id)
        .order_by(ContentOutline.version_number.desc())
        .limit(1)
    )
    if not row:
        return {"outline": None, "version_number": None, "is_approved": False, "exists": False}
    return {
        "outline": row.payload,
        "version_number": row.version_number,
        "is_approved": row.is_approved,
        "exists": True,
    }


def get_strategy(session: Session, user: User, content_id: UUID) -> dict:
    content = get_owned_content(session, user, content_id)
    row = session.scalar(
        select(ContentStrategy)
        .where(ContentStrategy.content_asset_id == content.id)
        .order_by(ContentStrategy.version_number.desc())
        .limit(1)
    )
    if not row:
        return {"strategy": None, "version_number": None, "exists": False}
    return {"strategy": row.payload, "version_number": row.version_number, "exists": True}


def list_quality_checks(session: Session, user: User, content_id: UUID) -> list[dict]:
    content = get_owned_content(session, user, content_id)
    rows = session.scalars(
        select(QualityCheck)
        .where(QualityCheck.content_asset_id == content.id)
        .order_by(QualityCheck.created_at.desc())
    )
    return [
        {
            "id": str(row.id),
            "check_type": row.check_type,
            "score": row.score,
            "status": row.status,
            "issues": row.issues,
            "recommendations": row.recommendations,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]
