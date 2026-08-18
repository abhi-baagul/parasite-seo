"""Parasite SEO AI feature tests."""

from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient


def _ok(response):
    assert response.status_code < 400, response.text
    body = response.json()
    assert body.get("success") is True
    return body["data"]


def test_parasite_seo_workflow(client: TestClient):
    projects = _ok(client.get("/api/v1/projects"))
    project_id = projects[0]["id"]
    prompt = (
        'As an SEO content writer, write an informative blog post on '
        '[DIClock Referral Code "WL1Z375N" - Get 40% Off on Annual Plan] '
        "of around 1000 words targeting keyword [DIClock Referral Code]. "
        "Also include H1, H2, H3, bullet points, tables and a clear CTA. "
        "Primary keywords: DIClock Referral Code For New User, DIClock Referral Code 2026."
    )
    job = _ok(
        client.post(
            "/api/v1/parasite-seo/jobs",
            json={
                "project_id": project_id,
                "prompt": prompt,
                "advanced_settings": {"tone": "professional", "language": "English"},
                "target_link": {
                    "target_url": "https://example.com/diclock",
                    "anchor_text": "DIClock Referral Code",
                    "link_attribute": "sponsored",
                },
            },
        )
    )
    job_id = job["id"]

    # optional media upload
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    upload = client.post(
        f"/api/v1/parasite-seo/jobs/{job_id}/media",
        files={"file": ("test.png", BytesIO(png), "image/png")},
    )
    assert upload.status_code == 201, upload.text

    analyzed = _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/analyze"))
    assert analyzed["requirements"]
    assert analyzed["step_state"]["prompt_analysis"] == "completed"

    generated = None
    for stage in ("confirm", "research", "strategy", "outline", "write"):
        generated = _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/generate?stage={stage}"))
    assert generated["content_id"]
    assert generated["content"]["content"]
    assert generated["step_state"]["content_generation"] == "completed"

    seo = _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/seo-analyze"))
    assert seo["step_state"]["seo_analysis"] == "completed"

    links = _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/link-analysis"))
    assert links["step_state"]["link_analysis"] == "completed"

    media = _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/media-analysis"))
    assert media["status"] == "ready"

    published = _ok(client.post(f"/api/v1/parasite-seo/jobs/{job_id}/publish"))
    assert published["is_public"] is True
    assert published["public_slug"]
    assert published["public_url"]
    assert published["status"] == "published"

    page = _ok(client.get(f"/api/v1/parasite-seo/public/pages/{published['public_slug']}"))
    assert page["title"]
    assert "<script" not in page["content_html"].lower()

    # draft slug must not be public
    missing = client.get(f"/api/v1/parasite-seo/public/pages/does-not-exist-{uuid4().hex[:6]}")
    assert missing.status_code == 404

    listing = _ok(client.get("/api/v1/parasite-seo"))
    assert listing["stats"]["total_generated_pages"] >= 1
