"""Phase 4 SEO / link / media enrichment tests."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.exceptions import BadRequestError
from app.integrations.ai.mock import MockAIProvider
from app.models.content import ContentAsset, ContentVersion
from app.models.project import Project
from app.models.seo_enrichment import MediaSuggestion, SEOAnalysisRecord
from app.models.user import User
from app.schemas.seo_enrichment import InsertLinkRequest, TargetLinkSuggestRequest
from app.services import seo_enrichment as enrich
from app.utils.url_safety import validate_safe_url, validate_video_embed_url


SAMPLE_HTML = """
<h1>DIClock Referral Code: How It Works</h1>
<h2>Introduction</h2>
<p>DIClock Referral Code offers should be verified before purchase.</p>
<h2>How it works</h2>
<p>Enter the code at checkout and confirm the discount.</p>
<ul><li>Open checkout</li><li>Enter code</li></ul>
<table><tr><th>Item</th><th>Check</th></tr><tr><td>Discount</td><td>Checkout</td></tr></table>
<div class="cta-block">Confirm on the official checkout.</div>
"""


@pytest.fixture
def user_project_content(db):
    user = User(
        email=f"p4-{uuid4().hex[:8]}@example.com",
        password_hash="x",
        name="Phase4",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.flush()
    project = Project(user_id=user.id, name="P4 Project", status="active")
    db.add(project)
    db.flush()
    content = ContentAsset(
        project_id=project.id,
        title="DIClock Referral Code Guide",
        slug=f"diclock-{uuid4().hex[:6]}",
        content=SAMPLE_HTML,
        seo_title="DIClock Referral Code Guide",
        meta_description="Learn how referral codes work and verify offers.",
        content_type="article",
        status="review",
        word_count=80,
    )
    db.add(content)
    db.flush()
    # Sibling article for internal links
    other = ContentAsset(
        project_id=project.id,
        title="Best Productivity Tools",
        slug=f"best-productivity-{uuid4().hex[:6]}",
        content="<h1>Best Productivity Tools</h1><p>Software and time tracking tools.</p>",
        content_type="article",
        status="draft",
        word_count=20,
    )
    db.add(other)
    db.flush()
    return user, project, content


def test_unsafe_urls_rejected():
    for bad in ("javascript:alert(1)", "data:text/html,hi", "file:///etc/passwd"):
        with pytest.raises(BadRequestError):
            validate_safe_url(bad)


def test_http_rejected_by_default():
    with pytest.raises(BadRequestError):
        validate_safe_url("http://example.com/x")


def test_https_allowed():
    assert validate_safe_url("https://example.com/diclock").startswith("https://")


def test_invalid_video_host_rejected():
    with pytest.raises(BadRequestError):
        validate_video_embed_url("https://evil.example/video")


def test_seo_analyze_and_cache(db, user_project_content):
    user, _, content = user_project_content
    first = enrich.analyze_seo(db, user, content.id, force=True)
    assert first["overall_score"] >= 0
    assert first["label"] == "Content SEO Score"
    second = enrich.analyze_seo(db, user, content.id, force=False)
    assert second["overall_score"] == first["overall_score"]
    rows = db.scalars(select(SEOAnalysisRecord).where(SEOAnalysisRecord.content_asset_id == content.id)).all()
    assert len(rows) >= 1


def test_keyword_analysis(db, user_project_content):
    user, _, content = user_project_content
    # Monkeypatch requirements via empty prompt — analysis still runs with None primary
    result = enrich.analyze_keywords_for_content(db, user, content.id, force=True)
    assert "primary_keyword_present" in result
    assert "recommendations" in result


def test_metadata_tags_media(db, user_project_content):
    user, _, content = user_project_content
    provider = MockAIProvider()
    meta = enrich.generate_metadata(db, user, content.id, provider=provider)
    assert meta["metadata"]["title_options"]
    tags = enrich.generate_tags(db, user, content.id, provider=provider)
    assert tags["tags"]
    media = enrich.generate_media_plan(db, user, content.id, provider=provider)
    assert media["created"] >= 1
    suggestions = db.scalars(select(MediaSuggestion).where(MediaSuggestion.content_asset_id == content.id)).all()
    assert suggestions


def test_internal_and_external(db, user_project_content):
    user, _, content = user_project_content
    internal = enrich.suggest_internal_links(db, user, content.id)
    assert "suggestions" in internal
    external = enrich.suggest_external_references(db, user, content.id)
    assert external["references"]
    assert all(ref["requires_verification"] for ref in external["references"])


def test_target_link_insert_creates_version(db, user_project_content):
    user, _, content = user_project_content
    suggest = enrich.suggest_target_link_placement(
        db,
        user,
        content.id,
        TargetLinkSuggestRequest(
            target_url="https://example.com/diclock",
            anchor_text="DIClock Referral Code",
            link_attribute="sponsored",
        ),
    )
    assert "suggested_phrase" in suggest
    before_versions = list(
        db.scalars(select(ContentVersion).where(ContentVersion.content_asset_id == content.id))
    )
    inserted = enrich.insert_link(
        db,
        user,
        content.id,
        InsertLinkRequest(
            target_url="https://example.com/diclock",
            anchor_text="DIClock Referral Code",
            link_attribute="sponsored",
        ),
    )
    assert inserted["link"]["status"] == "inserted"
    after_versions = list(
        db.scalars(select(ContentVersion).where(ContentVersion.content_asset_id == content.id))
    )
    assert len(after_versions) > len(before_versions)


def test_duplicate_link_blocked(db, user_project_content):
    user, _, content = user_project_content
    payload = InsertLinkRequest(
        target_url="https://example.com/diclock",
        anchor_text="DIClock Referral Code",
        link_attribute="standard",
    )
    enrich.insert_link(db, user, content.id, payload)
    with pytest.raises(BadRequestError):
        enrich.insert_link(db, user, content.id, payload)


def test_generate_all_and_api(client, db, user_project_content):
    user, project, content = user_project_content
    # Persist via client ownership: create through API with seed user is easier
    projects = client.get("/api/v1/projects")
    assert projects.status_code == 200
    # Use enrichment service path already covered; API smoke:
    # Need content owned by seed user — create one
    created = client.post(
        "/api/v1/content",
        json={
            "project_id": projects.json()["data"][0]["id"],
            "title": "DIClock Referral Code API",
            "slug": f"diclock-api-{uuid4().hex[:6]}",
            "content": SAMPLE_HTML,
            "status": "review",
        },
    )
    assert created.status_code == 201
    cid = created.json()["data"]["id"]
    seo = client.post(f"/api/v1/content/{cid}/seo/analyze")
    assert seo.status_code == 200
    assert seo.json()["data"]["overall_score"] >= 0
    bad = client.post(
        f"/api/v1/content/{cid}/links/suggest",
        json={"target_url": "javascript:alert(1)", "anchor_text": "x"},
    )
    assert bad.status_code == 400
