"""Phase 5 Content Studio API tests."""

from uuid import uuid4

from fastapi.testclient import TestClient


def _ok(response):
    assert response.status_code < 400, response.text
    body = response.json()
    assert body.get("success") is True
    return body["data"]


def _seed_content(client: TestClient) -> dict:
    projects = _ok(client.get("/api/v1/projects"))
    assert projects, "seed project required"
    project_id = projects[0]["id"]
    slug = f"phase5-{uuid4().hex[:8]}"
    return _ok(
        client.post(
            "/api/v1/content",
            json={
                "project_id": project_id,
                "title": "Phase 5 Studio Article",
                "slug": slug,
                "content": (
                    "<h1>Phase 5 Title</h1>"
                    "<h2>Intro</h2>"
                    "<p>Hello paragraph for editing.</p>"
                    "<ul><li>One</li><li>Two</li></ul>"
                    "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></td></table>"
                    '<section class="cta-block" data-cta="1"><p>Try it</p>'
                    '<p><a href="https://example.com/offer">Get Started</a></p></section>'
                ),
                "seo_title": "Phase 5 SEO Title",
                "meta_description": "Meta for phase 5 tests",
                "status": "draft",
            },
        )
    )


def test_studio_payload_versions_export_duplicate(client: TestClient):
    content = _seed_content(client)
    cid = content["id"]

    studio = _ok(client.get(f"/api/v1/content/{cid}/studio"))
    assert studio["content"]["id"] == cid
    assert studio["stats"]["word_count"] > 0
    assert isinstance(studio["outline"], list)
    assert studio["completeness"]

    v1 = _ok(
        client.post(
            f"/api/v1/content/{cid}/versions",
            json={"content": content["content"], "change_summary": "manual v1"},
        )
    )
    assert v1["version_number"] >= 1
    assert v1.get("source") == "manual"

    patched = _ok(
        client.patch(
            f"/api/v1/content/{cid}",
            json={"content": content["content"] + "<p>Extra line for version 2.</p>"},
        )
    )
    assert "Extra line" in patched["content"]

    v2 = _ok(
        client.post(
            f"/api/v1/content/{cid}/versions",
            json={"change_summary": "after edit"},
        )
    )

    compare = _ok(
        client.post(
            f"/api/v1/content/{cid}/versions/compare",
            json={"left_version_id": v1["id"], "right_version_id": v2["id"]},
        )
    )
    assert "unified_diff" in compare

    restored = _ok(client.post(f"/api/v1/content/{cid}/versions/{v1['id']}/restore"))
    assert restored["restored_from"] == v1["version_number"]
    assert restored["new_version"]["source"] == "restore"

    for fmt in ("html", "markdown", "txt", "pdf", "doc", "csv"):
        resp = client.get(f"/api/v1/content/{cid}/export/{fmt}")
        assert resp.status_code == 200, resp.text
        assert resp.content
        assert "attachment" in resp.headers.get("content-disposition", "").lower()
    csv_resp = client.get(f"/api/v1/content/{cid}/export/csv")
    assert b"title" in csv_resp.content
    assert b"Phase 5 Studio Article" in csv_resp.content

    dup = _ok(client.post(f"/api/v1/content/{cid}/duplicate"))
    assert dup["id"] != cid
    assert dup["status"] == "draft"
    assert "(Copy)" in dup["title"]

    # XSS should be stripped on save
    dirty = _ok(
        client.patch(
            f"/api/v1/content/{cid}",
            json={"content": '<p>Safe</p><script>alert(1)</script><a href="javascript:alert(1)">x</a>'},
        )
    )
    assert "<script" not in dirty["content"].lower()
    assert "javascript:" not in dirty["content"].lower()

    # published status blocked
    blocked = client.patch(f"/api/v1/content/{cid}", json={"status": "published"})
    assert blocked.status_code == 400

    library = client.get("/api/v1/assets/library")
    assert library.status_code == 200
    assert library.json()["success"] is True


def test_section_edit_and_search(client: TestClient):
    content = _seed_content(client)
    cid = content["id"]
    selected = "<p>Hello paragraph for editing.</p>"
    edited = _ok(
        client.post(
            f"/api/v1/content/{cid}/ai/section-edit",
            json={
                "selected_html": selected,
                "action": "improve",
                "accept": True,
                "full_html": content["content"],
            },
        )
    )
    assert edited["accepted"] is True
    assert edited["rewritten_html"]

    found = client.get("/api/v1/content", params={"q": "Phase 5 Studio"})
    assert found.status_code == 200
    assert found.json()["pagination"]["total"] >= 1
