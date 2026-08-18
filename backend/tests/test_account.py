def test_me_and_notifications(client):
    me = client.get("/api/v1/me")
    assert me.status_code == 200
    profile = me.json()["data"]
    assert profile["email"]
    assert "notification_prefs" in profile

    updated = client.patch("/api/v1/me", json={"organization": "Northstar Lab", "job_title": "Designer"})
    assert updated.status_code == 200
    assert updated.json()["data"]["organization"] == "Northstar Lab"

    notes = client.get("/api/v1/me/notifications")
    assert notes.status_code == 200
    items = notes.json()["data"]
    assert isinstance(items, list)
    assert any(item["source_key"] == "welcome" for item in items)

    marked = client.post("/api/v1/me/notifications/read-all")
    assert marked.status_code == 200
    assert marked.json()["data"]["updated"] >= 1
