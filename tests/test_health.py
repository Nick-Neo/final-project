def test_health_returns_ok(client):
    resp = client.get("/health")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["status"] == "ok"
    assert data["db"] == "connected"
