"""API integration tests for Phase 2B."""

from uuid import uuid4


def _ok(response):
    assert response.status_code < 400, response.text
    body = response.json()
    assert body["success"] is True
    return body


def test_v1_health(client):
    body = _ok(client.get("/api/v1/health"))
    assert body["data"]["database"]["status"] == "ok"
    assert body["data"]["redis"]["status"] == "ok"


def test_project_campaign_content_flow(client):
    project = _ok(
        client.post(
            "/api/v1/projects",
            json={
                "name": f"API Project {uuid4().hex[:6]}",
                "niche": "Testing",
                "country": "United States",
                "language": "English",
            },
        )
    )["data"]
    project_id = project["id"]

    listed = _ok(client.get("/api/v1/projects"))
    assert any(item["id"] == project_id for item in listed["data"])
    assert "pagination" in listed

    campaign = _ok(
        client.post(
            f"/api/v1/projects/{project_id}/campaigns",
            json={"name": "Campaign A", "default_word_count": 1400},
        )
    )["data"]

    prompt = _ok(
        client.post(
            "/api/v1/prompts",
            json={
                "project_id": project_id,
                "campaign_id": campaign["id"],
                "raw_prompt": "  Keep exact spacing  ",
            },
        )
    )["data"]
    assert prompt["raw_prompt"] == "  Keep exact spacing  "

    content = _ok(
        client.post(
            "/api/v1/content",
            json={
                "project_id": project_id,
                "campaign_id": campaign["id"],
                "prompt_id": prompt["id"],
                "title": "Draft Title",
                "slug": f"draft-{uuid4().hex[:6]}",
                "content": "<p>Hello world</p>",
                "content_type": "article",
            },
        )
    )["data"]

    updated = _ok(
        client.patch(
            f"/api/v1/content/{content['id']}",
            json={"title": "Edited Title", "content": "<p>Hello world edited</p>"},
        )
    )["data"]
    assert updated["title"] == "Edited Title"

    version = _ok(
        client.post(
            f"/api/v1/content/{content['id']}/versions",
            json={"content": "<p>Version snapshot</p>", "change_summary": "first snapshot"},
        )
    )["data"]
    assert version["version_number"] == 1

    versions = _ok(client.get(f"/api/v1/content/{content['id']}/versions"))
    assert versions["pagination"]["total"] >= 1

    link = _ok(
        client.post(
            "/api/v1/links",
            json={
                "content_asset_id": content["id"],
                "target_url": "https://example.com/offer",
                "anchor_text": "Authorized offer",
                "link_attribute": "sponsored",
            },
        )
    )["data"]
    assert link["link_attribute"] == "sponsored"

    media = _ok(
        client.post(
            "/api/v1/media",
            json={
                "project_id": project_id,
                "content_asset_id": content["id"],
                "media_type": "generated_image",
                "alt_text": "Diagram",
                "prompt": "Neutral diagram",
            },
        )
    )["data"]

    channel = _ok(
        client.post(
            "/api/v1/publishing/channels",
            json={
                "project_id": project_id,
                "name": "Test WordPress",
                "channel_type": "wordpress",
                "configuration": {"site_url": "https://example.com", "api_key": "secret"},
            },
        )
    )["data"]
    assert channel["configuration"]["api_key"] == "[redacted-on-write]"

    history = _ok(client.get("/api/v1/publishing/history"))
    assert "data" in history

    runs = _ok(client.get("/api/v1/ai/runs"))
    assert "data" in runs

    keyword = _ok(
        client.post(
            "/api/v1/keywords",
            json={"project_id": project_id, "keyword": "hybrid inverter", "keyword_type": "primary"},
        )
    )["data"]
    assert keyword["keyword"] == "hybrid inverter"

    analytics = _ok(client.get("/api/v1/analytics/overview"))
    assert "impressions" in analytics["data"]

    # invalid link attribute
    bad = client.post(
        "/api/v1/links",
        json={
            "content_asset_id": content["id"],
            "target_url": "https://example.com",
            "anchor_text": "x",
            "link_attribute": "spam",
        },
    )
    assert bad.status_code == 422
    assert bad.json()["success"] is False

    missing = client.get(f"/api/v1/projects/{uuid4()}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    # cleanup-ish: delete link and media
    assert client.delete(f"/api/v1/links/{link['id']}").status_code == 204
    assert client.delete(f"/api/v1/media/{media['id']}").status_code == 204
