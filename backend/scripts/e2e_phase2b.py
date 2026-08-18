import uuid

import httpx

base = "http://127.0.0.1:8000"


def main() -> None:
    client = httpx.Client(base_url=base, timeout=30.0)

    def show(name: str, response: httpx.Response):
        print(name, response.status_code, response.text[:240])
        response.raise_for_status()
        if response.status_code == 204:
            return None
        return response.json()["data"]

    project = show(
        "project",
        client.post(
            "/api/v1/projects",
            json={
                "name": "E2E Solar Project",
                "niche": "Residential solar",
                "country": "United States",
                "language": "English",
            },
        ),
    )
    campaign = show(
        "campaign",
        client.post(
            f"/api/v1/projects/{project['id']}/campaigns",
            json={"name": "E2E Campaign", "default_content_type": "comparison", "default_word_count": 1600},
        ),
    )
    prompt = show(
        "prompt",
        client.post(
            "/api/v1/prompts",
            json={
                "project_id": project["id"],
                "campaign_id": campaign["id"],
                "raw_prompt": "Exact E2E prompt text",
            },
        ),
    )
    assert prompt["raw_prompt"] == "Exact E2E prompt text"
    content = show(
        "content",
        client.post(
            "/api/v1/content",
            json={
                "project_id": project["id"],
                "campaign_id": campaign["id"],
                "prompt_id": prompt["id"],
                "title": "E2E Article",
                "slug": f"e2e-article-{uuid.uuid4().hex[:8]}",
                "content": "<p>Hello E2E</p>",
                "content_type": "comparison",
            },
        ),
    )
    edited = show(
        "edit",
        client.patch(
            f"/api/v1/content/{content['id']}",
            json={"title": "E2E Article Edited", "content": "<p>Hello E2E edited</p>"},
        ),
    )
    version = show(
        "version",
        client.post(
            f"/api/v1/content/{content['id']}/versions",
            json={"content": "<p>Version body</p>", "change_summary": "e2e snapshot"},
        ),
    )
    link = show(
        "link",
        client.post(
            "/api/v1/links",
            json={
                "content_asset_id": content["id"],
                "target_url": "https://example.com/offer",
                "anchor_text": "Authorized offer",
                "link_attribute": "sponsored",
            },
        ),
    )
    media = show(
        "media",
        client.post(
            "/api/v1/media",
            json={
                "project_id": project["id"],
                "content_asset_id": content["id"],
                "media_type": "generated_image",
                "alt_text": "Diagram",
                "prompt": "Neutral diagram",
            },
        ),
    )
    channel = show(
        "channel",
        client.post(
            "/api/v1/publishing/channels",
            json={
                "project_id": project["id"],
                "name": "E2E WordPress",
                "channel_type": "wordpress",
                "configuration": {"site_url": "https://example.com", "api_key": "secret"},
            },
        ),
    )
    assert channel["configuration"]["api_key"] == "[redacted-on-write]"
    history = client.get("/api/v1/publishing/history").json()
    runs = client.get("/api/v1/ai/runs").json()
    keyword = show(
        "keyword",
        client.post(
            "/api/v1/keywords",
            json={"project_id": project["id"], "keyword": "e2e keyword", "keyword_type": "primary"},
        ),
    )
    analytics = client.get("/api/v1/analytics/overview").json()
    print(
        "OK",
        {
            "project": project["id"],
            "prompt": prompt["raw_prompt"],
            "title": edited["title"],
            "version": version["version_number"],
            "link": link["link_attribute"],
            "media": media["id"],
            "history_total": history["pagination"]["total"],
            "runs_total": runs["pagination"]["total"],
            "keyword": keyword["keyword"],
            "analytics": analytics["data"]["metric_count"],
        },
    )


if __name__ == "__main__":
    main()
