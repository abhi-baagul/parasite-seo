"""Phase 7 — Content network + internal link automation tests."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.content import ContentAsset, ContentLink
from app.models.enums import ContentStatus, LinkAttribute, LinkStatus
from app.models.parasite_seo import ParasiteSEOJob
from app.models.public_page import PublicPage
from app.models.user import User


def _ok(response):
    assert response.status_code < 400, response.text
    body = response.json()
    assert body.get("success") is True
    return body["data"]


def _publish_pages(project_id: UUID, user_id: UUID, titles: list[str]):
    session = SessionLocal()
    out = []
    try:
        for title in titles:
            slug = f"{title.lower().replace(' ', '-')}-{uuid4().hex[:6]}"
            content = ContentAsset(
                project_id=project_id,
                title=title,
                slug=slug,
                content=(
                    f"<h1>{title}</h1>"
                    "<p>Students are increasingly using AI for research, writing and productivity.</p>"
                    f"<p>Learn more about {title} and how teams compare AI productivity apps.</p>"
                    "<p>Developers and remote workers also rely on related AI tools.</p>"
                ),
                seo_title=title,
                meta_description=f"Overview of {title}",
                status=ContentStatus.APPROVED.value,
                word_count=90,
                seo_score=90,
            )
            session.add(content)
            session.flush()
            job = ParasiteSEOJob(
                project_id=project_id,
                user_id=user_id,
                original_prompt=f"Write about {title}",
                advanced_settings={},
                step_state={},
                status="published",
                current_step="publish",
                content_id=content.id,
                public_slug=slug,
                public_url=f"http://localhost:3000/p/{slug}",
                is_public=True,
                published_at=datetime.now(UTC),
            )
            session.add(job)
            session.flush()
            page = PublicPage(
                job_id=job.id,
                content_id=content.id,
                project_id=project_id,
                slug=slug,
                title=title,
                status="published",
                visibility="public",
                public_url=f"http://localhost:3000/p/{slug}",
                canonical_url=f"http://localhost:3000/p/{slug}",
                published_at=datetime.now(UTC),
            )
            session.add(page)
            session.flush()
            out.append(
                {
                    "content_id": str(content.id),
                    "page_id": str(page.id),
                    "slug": slug,
                    "title": title,
                }
            )
        session.commit()
        return out
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_content_network_analyze_and_insert(client: TestClient):
    projects = _ok(client.get("/api/v1/projects"))
    project_id = UUID(projects[0]["id"])

    session = SessionLocal()
    try:
        user = session.query(User).first()
        assert user
        user_id = user.id
    finally:
        session.close()

    titles = [
        "Best AI Productivity Tools",
        "AI Tools for Students",
        "AI Tools for Developers",
        "AI Productivity Apps",
        "Remote Work Productivity Tools",
    ]
    seeded = _publish_pages(project_id, user_id, titles)
    assert len(seeded) == 5

    analyzed = _ok(
        client.post(
            "/api/v1/parasite-seo/link-network/analyze",
            json={"project_id": str(project_id), "use_ai": False},
        )
    )
    assert analyzed["run"]["status"] == "completed"
    assert analyzed["overview"]["total_pages"] >= 5

    overview = _ok(client.get(f"/api/v1/parasite-seo/link-network?project_id={project_id}"))
    assert "terminology" in overview
    assert "internal_link" in overview["terminology"]

    suggestions = _ok(
        client.get(f"/api/v1/parasite-seo/link-suggestions?project_id={project_id}&status=suggested")
    )
    assert len(suggestions["items"]) >= 1
    first = suggestions["items"][0]

    patched = _ok(
        client.patch(
            f"/api/v1/parasite-seo/link-suggestions/{first['id']}",
            json={"anchor_text": "AI tools for students"},
        )
    )
    assert patched["anchor_text"] == "AI tools for students"

    inserted = _ok(client.post(f"/api/v1/parasite-seo/link-suggestions/{first['id']}/approve"))
    assert inserted["suggestion"]["status"] == "inserted"
    assert inserted["link"]["target_url"].startswith("/p/")

    session = SessionLocal()
    try:
        source = session.get(ContentAsset, UUID(first["source_content_id"]))
        assert source
        assert "/p/" in (source.content or "")
    finally:
        session.close()

    suggestions2 = _ok(
        client.get(f"/api/v1/parasite-seo/link-suggestions?project_id={project_id}&status=suggested")
    )
    if suggestions2["items"]:
        rejected = _ok(
            client.post(f"/api/v1/parasite-seo/link-suggestions/{suggestions2['items'][0]['id']}/reject")
        )
        assert rejected["status"] == "rejected"

    # Broken link
    session = SessionLocal()
    try:
        orphan_id = UUID(seeded[-1]["content_id"])
        bad = ContentLink(
            content_asset_id=orphan_id,
            target_url="/p/does-not-exist-xyz",
            anchor_text="missing page",
            link_attribute=LinkAttribute.STANDARD.value,
            status=LinkStatus.INSERTED.value,
        )
        session.add(bad)
        session.commit()
    finally:
        session.close()

    overview2 = _ok(client.get(f"/api/v1/parasite-seo/link-network/{project_id}"))
    assert overview2["broken_links"] >= 1
    broken_id = overview2["broken"][0]["id"]
    removed = _ok(client.delete(f"/api/v1/parasite-seo/link-suggestions/broken/{broken_id}"))
    assert removed["status"] == "removed"

    orphans = overview2["orphans"]
    if orphans:
        opp = _ok(
            client.get(
                f"/api/v1/parasite-seo/link-network/orphans/{orphans[0]['content_id']}/opportunities"
                f"?project_id={project_id}"
            )
        )
        assert isinstance(opp, list)

    settings = _ok(client.get(f"/api/v1/parasite-seo/link-network/{project_id}/settings"))
    assert settings["automatic_internal_linking"] is False
    updated = _ok(
        client.patch(
            f"/api/v1/parasite-seo/link-network/{project_id}/settings",
            json={"min_relevance_score": 90, "related_content_limit": 4},
        )
    )
    assert updated["min_relevance_score"] == 90

    old_slug = seeded[0]["slug"]
    result = _ok(
        client.post(
            "/api/v1/parasite-seo/link-network/slug-redirects/apply",
            json={
                "project_id": str(project_id),
                "old_slug": old_slug,
                "new_slug": f"{old_slug}-renamed",
                "public_page_id": seeded[0]["page_id"],
            },
        )
    )
    assert result["redirect_created"] is True


def test_cross_project_blocked(client: TestClient):
    missing = client.get(f"/api/v1/parasite-seo/link-network?project_id={uuid4()}")
    assert missing.status_code in {403, 404}
