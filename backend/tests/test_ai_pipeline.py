"""Phase 3 AI agent and content generation pipeline tests."""

import pytest
from sqlalchemy import select
from uuid import uuid4

from app.agents.prompt_analyzer import PromptAnalyzerAgent
from app.core.exceptions import ConflictError, ServiceUnavailableError, UnprocessableError
from app.integrations.ai.base import AICompletionResult, AIProvider
from app.integrations.ai.mock import MockAIProvider
from app.models.ai_run import AIRun
from app.models.content import ContentAsset, ContentVersion
from app.models.enums import ContentStatus, RunStatus
from app.models.pipeline import ContentGenerationJob, PromptAnalysis
from app.models.project import Project
from app.models.quality import QualityCheck
from app.models.user import User
from app.schemas.ai_pipeline import ConfirmRequirementsRequest, PromptAnalysisSchema
from app.services import content_generation as gen


SAMPLE_PROMPT = """As an SEO-content writer, write an informative blog post on

[DIClock Referral Code "WL1Z375N" - Get 40% Off on Annual Plan]

of around 1000 words targeting keyword [DIClock Referral Code].

Also include H1, H2, H3, bullet points, tables, and a clear CTA.

Primary keywords:
DIClock Referral Code For New User
DIClock Referral Code 2026
DIClock Referral Code Latest
DIClock Referral Code Signup"""


class BrokenJSONProvider(AIProvider):
    name = "broken"

    def complete(self, messages, *, model=None, temperature=None, max_tokens=None, response_format_json=True):
        return AICompletionResult(content="not-json", model="broken", input_tokens=1, output_tokens=1, total_tokens=2)


class EmptyProvider(AIProvider):
    name = "empty"

    def complete(self, messages, *, model=None, temperature=None, max_tokens=None, response_format_json=True):
        return AICompletionResult(content="", model="empty", input_tokens=1, output_tokens=0, total_tokens=1)


class TimeoutProvider(AIProvider):
    name = "timeout"

    def complete(self, messages, *, model=None, temperature=None, max_tokens=None, response_format_json=True):
        raise TimeoutError("provider timeout")


@pytest.fixture
def user_project(db) -> tuple[User, Project]:
    user = User(
        email=f"phase3-{uuid4().hex[:8]}@example.com",
        password_hash="x",
        name="Phase3 Tester",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.flush()
    project = Project(user_id=user.id, name="Phase3 Project", status="active")
    db.add(project)
    db.flush()
    return user, project


def test_prompt_analyzer_valid_json(db, user_project):
    user, project = user_project
    result = gen.analyze_prompt(
        db,
        user,
        project_id=project.id,
        campaign_id=None,
        raw_prompt=SAMPLE_PROMPT,
        provider=MockAIProvider(),
    )
    assert result["requirements"]["main_keyword"] == "DIClock Referral Code"
    assert result["requirements"]["word_count"] == 1000
    assert "table" in [e.lower() for e in result["requirements"]["required_elements"]] or "CTA" in result[
        "requirements"
    ]["required_elements"]
    analysis = db.get(PromptAnalysis, result["analysis_id"])
    assert analysis is not None
    run = db.scalar(select(AIRun).where(AIRun.id == result["ai_run_id"]))
    assert run is not None
    assert run.status == RunStatus.COMPLETED.value


def test_prompt_analyzer_invalid_json_fails(db, user_project):
    user, project = user_project
    with pytest.raises((UnprocessableError, ServiceUnavailableError)):
        gen.analyze_prompt(
            db,
            user,
            project_id=project.id,
            campaign_id=None,
            raw_prompt=SAMPLE_PROMPT,
            provider=BrokenJSONProvider(),
        )


def test_prompt_analyzer_empty_response_fails(db, user_project):
    user, project = user_project
    with pytest.raises((UnprocessableError, ServiceUnavailableError)):
        gen.analyze_prompt(
            db,
            user,
            project_id=project.id,
            campaign_id=None,
            raw_prompt=SAMPLE_PROMPT,
            provider=EmptyProvider(),
        )


def test_provider_timeout_marks_failed_run(db, user_project):
    user, project = user_project
    with pytest.raises(ServiceUnavailableError):
        gen.analyze_prompt(
            db,
            user,
            project_id=project.id,
            campaign_id=None,
            raw_prompt=SAMPLE_PROMPT,
            provider=TimeoutProvider(),
        )
    failed = db.scalars(select(AIRun).where(AIRun.project_id == project.id)).all()
    assert failed
    assert any(run.status == RunStatus.FAILED.value for run in failed)


def _seed_pipeline(db, user, project, provider=None):
    provider = provider or MockAIProvider()
    analyzed = gen.analyze_prompt(
        db,
        user,
        project_id=project.id,
        campaign_id=None,
        raw_prompt=SAMPLE_PROMPT,
        provider=provider,
    )
    confirmed = gen.confirm_requirements(
        db,
        user,
        analyzed["prompt_id"],
        ConfirmRequirementsRequest(requirements=PromptAnalysisSchema.model_validate(analyzed["requirements"])),
    )
    content_id = confirmed["content_id"]
    gen.run_research(db, user, content_id, provider=provider)
    gen.run_strategy(db, user, content_id, provider=provider)
    gen.run_outline(db, user, content_id, provider=provider)
    gen.approve_outline(db, user, content_id)
    return content_id


def test_full_pipeline_persistence(db, user_project):
    user, project = user_project
    provider = MockAIProvider()
    content_id = _seed_pipeline(db, user, project, provider=provider)
    generated = gen.generate_content(db, user, content_id, provider=provider)
    assert generated["word_count"] > 0
    assert "<h1>" in generated["content"].lower() or "<H1>" in generated["content"]

    content = db.get(ContentAsset, content_id)
    assert content is not None
    assert content.status == ContentStatus.REVIEW.value
    assert content.seo_title
    versions = db.scalars(select(ContentVersion).where(ContentVersion.content_asset_id == content.id)).all()
    assert versions

    seo = gen.run_seo_check(db, user, content_id, provider=provider)
    quality = gen.run_quality_check(db, user, content_id, provider=provider)
    assert seo["report"]["overall_score"] >= 0
    assert quality["report"]["status"] in {"passed", "needs_review", "failed"}
    checks = db.scalars(select(QualityCheck).where(QualityCheck.content_asset_id == content.id)).all()
    assert len(checks) >= 2
    runs = db.scalars(select(AIRun).where(AIRun.content_asset_id == content.id)).all()
    assert runs


def test_duplicate_generation_prevention(db, user_project):
    user, project = user_project
    provider = MockAIProvider()
    content_id = _seed_pipeline(db, user, project, provider=provider)
    job = ContentGenerationJob(
        content_asset_id=content_id,
        stage="generate",
        status=RunStatus.RUNNING.value,
    )
    db.add(job)
    db.flush()
    with pytest.raises(ConflictError):
        gen.generate_content(db, user, content_id, provider=provider)


def test_base_agent_missing_fields_retry_then_fail(db, user_project):
    user, project = user_project

    class InvalidThenStillInvalid(AIProvider):
        name = "invalid"

        def complete(self, messages, *, model=None, temperature=None, max_tokens=None, response_format_json=True):
            return AICompletionResult(
                content="{not-valid-json",
                model="invalid",
                input_tokens=1,
                output_tokens=1,
                total_tokens=2,
            )

    agent = PromptAnalyzerAgent(provider=InvalidThenStillInvalid())
    with pytest.raises((UnprocessableError, ServiceUnavailableError)):
        agent.run(db, project_id=project.id, content_asset_id=None, raw_prompt=SAMPLE_PROMPT)


def test_analyze_prompt_api(client):
    # Ensure seed user exists via a bootstrap call that creates the default principal.
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    projects = client.get("/api/v1/projects")
    assert projects.status_code == 200
    project_id = projects.json()["data"][0]["id"] if projects.json()["data"] else None
    if not project_id:
        created = client.post(
            "/api/v1/projects",
            json={"name": "Phase3 API Project", "status": "active"},
        )
        assert created.status_code == 201
        project_id = created.json()["data"]["id"]
    response = client.post(
        "/api/v1/content/analyze-prompt",
        json={"project_id": project_id, "prompt": SAMPLE_PROMPT},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["requirements"]["main_keyword"] == "DIClock Referral Code"
