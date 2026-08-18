"""Phase 8 — Backlink campaign builder tests."""

from fastapi.testclient import TestClient


def _ok(response):
    assert response.status_code < 400, response.text
    body = response.json()
    assert body.get("success") is True
    return body["data"]


def test_backlink_campaign_flow(client: TestClient):
    projects = _ok(client.get("/api/v1/projects"))
    project_id = projects[0]["id"]

    dest = _ok(
        client.post(
            "/api/v1/parasite-seo/backlink-campaigns/destinations",
            json={
                "project_id": project_id,
                "name": "Test Mock Local",
                "provider_type": "mock_local",
                "configuration": {"path_prefix": "test-campaigns"},
            },
        )
    )
    assert dest["provider_type"] == "mock_local"
    assert "secret" not in (dest.get("configuration") or {})

    tested = _ok(client.post(f"/api/v1/parasite-seo/backlink-campaigns/destinations/{dest['id']}/test"))
    assert tested["test_result"]["ok"] is True

    bucket = _ok(
        client.post(
            "/api/v1/parasite-seo/backlink-campaigns/buckets",
            json={
                "project_id": project_id,
                "name": "AI Productivity",
                "topics": ["AI productivity tools", "AI tools for students"],
                "keywords": ["AI Productivity Tools"],
            },
        )
    )

    campaign = _ok(
        client.post(
            "/api/v1/parasite-seo/backlink-campaigns",
            json={
                "project_id": project_id,
                "name": "AI Productivity Tools 2026",
                "strategy_type": "tiered_network",
                "target_url": "https://example.com/p/ai-productivity-tools",
                "primary_keyword": "AI Productivity Tools",
                "secondary_keywords": ["AI Tools for Students", "AI Productivity Apps"],
                "blueprint": {
                    "tier1": 2,
                    "tier2": 2,
                    "cloud": 1,
                    "pr": 1,
                    "outreach": 3,
                    "max_tier_depth": 2,
                },
            },
        )
    )
    campaign_id = campaign["id"]
    assert campaign["disclosure"]
    assert "Guaranteed" not in campaign["disclosure"]

    _ok(
        client.patch(
            f"/api/v1/parasite-seo/backlink-campaigns/{campaign_id}",
            json={"bucket_id": bucket["id"], "wizard_step": 7, "status": "planning"},
        )
    )

    generated = _ok(client.post(f"/api/v1/parasite-seo/backlink-campaigns/{campaign_id}/generate-assets"))
    assert generated["created"] >= 5
    detail = generated["campaign"]
    assert detail["graph"]["nodes"]
    assert any(a["tier"] == 1 for a in detail["assets"])
    assert any(a["tier"] == 2 for a in detail["assets"])
    assert any(a["asset_type"] == "cloud" for a in detail["assets"])
    assert len(detail["prospects"]) >= 3
    # variants differ
    titles = [a["title"] for a in detail["assets"]]
    assert len(set(titles)) == len(titles)

    asset_ids = [a["id"] for a in detail["assets"] if a["asset_type"] != "pr"][:4]
    published = _ok(
        client.post(
            f"/api/v1/parasite-seo/backlink-campaigns/{campaign_id}/publish",
            json={"asset_ids": asset_ids, "destination_id": dest["id"]},
        )
    )
    assert published["published"] >= 1
    assert any(b["status"] == "published" for b in published["campaign"]["backlinks"])

    # duplicate protection: republish same assets should not duplicate identical backlinks
    before = len(published["campaign"]["backlinks"])
    again = _ok(
        client.post(
            f"/api/v1/parasite-seo/backlink-campaigns/{campaign_id}/publish",
            json={"asset_ids": asset_ids, "destination_id": dest["id"]},
        )
    )
    # assets already published are skipped by status filter
    assert again["published"] == 0
    assert len(again["campaign"]["backlinks"]) == before

    verified = _ok(client.post(f"/api/v1/parasite-seo/backlink-campaigns/{campaign_id}/verify"))
    assert verified["verified"] >= 1
    assert any(b["status"] == "verified" for b in verified["campaign"]["backlinks"])
    assert verified["campaign"]["counts"]["referring_domains"] >= 1

    report = client.get(f"/api/v1/parasite-seo/backlink-campaigns/{campaign_id}/report?format=json")
    assert report.status_code == 200
    assert b"referring_domains" in report.content

    csv_report = client.get(f"/api/v1/parasite-seo/backlink-campaigns/{campaign_id}/report?format=csv")
    assert csv_report.status_code == 200
    assert b"metric" in csv_report.content

    # published mock file is readable via stored HTML key
    source = next(b["source_url"] for b in verified["campaign"]["backlinks"] if b["status"] == "verified")
    assert "mock-source-" in source or "/published-file/" in source
    asset = next(a for a in verified["campaign"]["assets"] if a.get("source_url") == source)
    key = (asset.get("meta") or {}).get("storage_key") or (asset.get("meta") or {}).get("external_id")
    assert key
    html = client.get(f"/api/v1/parasite-seo/backlink-campaigns/published-file/{key}")
    assert html.status_code == 200
    assert b"href=" in html.content

    demo = _ok(client.post(f"/api/v1/parasite-seo/backlink-campaigns/demo?project_id={project_id}"))
    assert demo["name"] == "AI Productivity Tools 2026"
    assert demo["blueprint"]["tier1"] == 5


def test_strategy_templates_and_targets(client: TestClient):
    projects = _ok(client.get("/api/v1/projects"))
    project_id = projects[0]["id"]
    strategies = _ok(client.get(f"/api/v1/parasite-seo/backlink-campaigns/strategies?project_id={project_id}"))
    assert len(strategies["items"]) >= 6
    saved = _ok(
        client.post(
            "/api/v1/parasite-seo/backlink-campaigns/strategies",
            json={
                "project_id": project_id,
                "name": "My Standard Campaign",
                "strategy_type": "tiered_network",
                "blueprint": {"tier1": 5, "tier2": 10, "cloud": 3, "pr": 2, "outreach": 20, "max_tier_depth": 2},
            },
        )
    )
    assert saved["name"] == "My Standard Campaign"
    targets = _ok(client.get(f"/api/v1/parasite-seo/backlink-campaigns/targets?project_id={project_id}"))
    assert "items" in targets


def test_automatic_project_campaign_engine(client: TestClient):
    projects = _ok(client.get("/api/v1/projects"))
    project_id = projects[0]["id"]

    plan = _ok(client.get(f"/api/v1/parasite-seo/backlink-campaigns/analyze?project_id={project_id}"))
    assert plan["strategy"]["strategy_type"]
    assert plan["blueprint"]["tier1"] >= 1
    assert plan["intelligence"]["primary_keyword"]
    assert plan["size_reason"]

    created = _ok(
        client.post(
            "/api/v1/parasite-seo/backlink-campaigns/auto",
            json={
                "project_id": project_id,
                "blueprint": {"tier1": 2, "tier2": 2, "cloud": 1, "pr": 0, "outreach": 2, "max_tier_depth": 2},
                "generate": True,
                "mock_mode": True,
            },
        )
    )
    campaign = created["campaign"]
    campaign_id = campaign["id"]
    assert campaign["mock_mode"] is True
    assert created["created"] >= 4
    assert any(a["link_group"] for a in campaign["assets"])
    assert campaign["logs"]
    titles = [a["title"] for a in campaign["assets"]]
    assert len(set(titles)) == len(titles)

    approved = _ok(client.post(f"/api/v1/parasite-seo/backlink-campaigns/{campaign_id}/approve"))
    assert approved["status"] == "approved"

    started = _ok(client.post(f"/api/v1/parasite-seo/backlink-campaigns/{campaign_id}/start"))
    assert started["published"] >= 1
    assert started["verified"] >= 1
    assert any(b["is_mock"] for b in started["campaign"]["backlinks"])
    assert started["campaign"]["counts"]["referring_domains"] <= started["campaign"]["counts"]["verified_backlinks"]
    assert all(b["indexed_status"] == "unknown" for b in started["campaign"]["backlinks"])

    logs = _ok(client.get(f"/api/v1/parasite-seo/backlink-campaigns/{campaign_id}/logs"))
    assert logs["items"]
    assert not any("password" in (row["message"] or "").lower() for row in logs["items"])

    copy = _ok(client.post(f"/api/v1/parasite-seo/backlink-campaigns/{campaign_id}/duplicate"))
    assert copy["id"] != campaign_id
    assert not copy.get("backlinks")

    project_links = _ok(client.get(f"/api/v1/parasite-seo/backlink-campaigns/project-backlinks?project_id={project_id}"))
    assert project_links["referring_domains"] <= project_links["verified"] or project_links["verified"] == 0
    report = _ok(client.get(f"/api/v1/parasite-seo/backlink-campaigns/project-report?project_id={project_id}"))
    assert "referring_domains" in report

