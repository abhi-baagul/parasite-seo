"""Phase 6 — Public web page + permanent URL engine tests."""

from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient


def _ok(response):
    assert response.status_code < 400, response.text
    body = response.json()
    assert body.get("success") is True
    return body["data"]


def _seed_ready_job(client: TestClient) -> str:
    projects = _ok(client.get("/api/v1/projects"))
    project_id = projects[0]["id"]
    unique = uuid4().hex[:8]
    prompt = (
        f'As an SEO content writer, write an informative blog post on '
        f'[DIClock Referral Code {unique} "WL1Z375N" - Get 40% Off on Annual Plan] '
        f"of around 1000 words targeting keyword [DIClock Referral Code {unique}]. "
        "Also include H1, H2, H3, bullet points, tables and a clear CTA. "
        f"Primary keywords: DIClock Referral Code For New User, DIClock Referral Code 2026 {unique}."
    )
    job = _ok(
        client.post(
            "/api/v1/parasite-seo/jobs",
            json={
                "project_id": project_id,
                "prompt": prompt,
                "advanced_settings": {"tone": "professional"},
                "target_link": {
                    "target_url": "https://example.com/diclock",
                    "anchor_text": "Get Started",
                    "link_attribute": "sponsored",
                },
            },
        )
    )
    job_id = job["id"]
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    upload = client.post(
        f"/api/v1/parasite-seo/jobs/{job_id}/media",
        files={"file": ("hero.png", BytesIO(png), "image/png")},
    )
    assert upload.status_code == 201, upload.text
    _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/analyze"))
    for stage in ("confirm", "research", "strategy", "outline", "write"):
        _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/generate?stage={stage}"))
    _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/seo-analyze"))
    _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/link-analysis"))
    _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/media-analysis"))
    return job_id


def test_public_page_lifecycle(client: TestClient):
    job_id = _seed_ready_job(client)

    created = _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/web-page", json={}))
    assert created["status"] == "ready"
    assert created["visibility"] == "private"
    assert created["slug"]
    assert "-" not in created["slug"]
    slug = created["slug"]

    # Duplicate create should fail
    clash = client.post(f"/api/v1/parasite-seo/jobs/{job_id}/web-page", json={})
    assert clash.status_code == 400

    # Preview via authenticated get
    preview = _ok(client.get(f"/api/v1/parasite-seo/jobs/{job_id}/web-page?preview=true"))
    assert preview["preview"]["content_html"]
    assert "<script" not in preview["preview"]["content_html"].lower()
    assert preview["preview"]["metadata"]["canonical"]

    # Private page not publicly visible
    hidden = client.get(f"/api/v1/public-pages/{slug}")
    assert hidden.status_code == 404

    published = _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/web-page/publish"))
    assert published["status"] == "published"
    assert published["visibility"] == "public"
    assert published["public_url"]
    assert published["public_url"].endswith(f"/{slug}")
    assert "/p/" not in published["public_url"]
    mirrors = published.get("mirrors") or []
    assert len(mirrors) >= 8
    providers = {m["provider"] for m in mirrors}
    assert {"aws", "vercel", "netlify", "gcp"}.issubset(providers)
    aws = next(m for m in mirrors if m["provider"] == "aws")
    assert aws["status"] == "live"
    assert ".s3-website." in aws["display_host"]
    assert aws["display_host"].endswith(".amazonaws.com")
    assert f"/c/aws/{slug}" in aws["live_url"]
    assert "amazonaws.com" not in aws["live_url"]

    page = _ok(client.get(f"/api/v1/public-pages/{slug}"))
    assert page["title"]
    assert page["content_html"]
    assert page["metadata"]["og"]["title"]
    assert page["structured_data"]
    assert page["structured_data"][0]["@type"] == "Article"
    # XSS protection
    assert "<script" not in page["content_html"].lower()
    assert "javascript:" not in page["content_html"].lower()

    # Legacy public path still works
    legacy = _ok(client.get(f"/api/v1/parasite-seo/public/pages/{slug}"))
    assert legacy["slug"] == slug

    unpublished = _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/web-page/unpublish"))
    assert unpublished["status"] == "unpublished"
    assert all(m["status"] == "unpublished" for m in unpublished.get("mirrors") or [])
    assert client.get(f"/api/v1/public-pages/{slug}").status_code == 404

    republished = _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/web-page/publish"))
    assert republished["status"] == "published"
    assert client.get(f"/api/v1/public-pages/{slug}").status_code == 200

    archived = _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/web-page/archive"))
    assert archived["status"] == "archived"
    assert client.get(f"/api/v1/public-pages/{slug}").status_code == 404

    listing = _ok(client.get("/api/v1/parasite-seo/public-pages"))
    assert any(item["id"] == created["id"] for item in listing["items"])


def test_slug_uniqueness(client: TestClient):
    job_a = _seed_ready_job(client)
    job_b = _seed_ready_job(client)
    token = uuid4().hex[:8]
    base = f"diclock-referral-code-{token}"
    a = _ok(
        client.post(
            f"/api/v1/parasite-seo/jobs/{job_a}/web-page",
            json={"slug": base},
        )
    )
    assert a["slug"] == base
    b = _ok(
        client.post(
            f"/api/v1/parasite-seo/jobs/{job_b}/web-page",
            json={"slug": base},
        )
    )
    assert b["slug"] == f"{base}-2"
    assert a["slug"] != b["slug"]

    reserved = client.patch(
        f"/api/v1/parasite-seo/jobs/{job_a}/web-page",
        json={"slug": "settings"},
    )
    assert reserved.status_code == 400


def test_unsafe_public_access(client: TestClient):
    missing = client.get(f"/api/v1/public-pages/does-not-exist-{uuid4().hex[:8]}")
    assert missing.status_code == 404


def test_legacy_publish_creates_public_page(client: TestClient):
    job_id = _seed_ready_job(client)
    published = _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/publish"))
    assert published["is_public"] is True
    assert published["web_page"]["status"] == "published"
    page = _ok(client.get(f"/api/v1/public-pages/{published['public_slug']}"))
    assert page["title"]
