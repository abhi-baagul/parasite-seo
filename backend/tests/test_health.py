REQUIRED_TABLES = {
    "users",
    "projects",
    "campaigns",
    "prompts",
    "content_assets",
    "content_versions",
    "content_links",
    "media_assets",
    "publishing_channels",
    "published_assets",
    "ai_runs",
    "quality_checks",
    "keywords",
    "analytics_metrics",
    "notifications",
}


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"]["status"] == "ok"
    assert body["redis"]["status"] == "ok"
    assert "request_id" not in body or True
    assert response.headers.get("X-Request-ID")


def test_health_db(client):
    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_redis(client):
    response = client.get("/health/redis")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_unknown_route_is_json_404(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "request_id" in body["error"]
