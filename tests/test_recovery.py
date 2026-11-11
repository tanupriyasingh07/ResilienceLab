def test_recover_failed_service(client):
    client.post("/api/services/api-server/fail")

    response = client.post("/api/services/api-server/recover")

    assert response.status_code == 200
    assert "recovered" in response.json()["message"].lower()

    services_response = client.get("/api/services")
    assert services_response.json()["api-server"]["status"] == "healthy"


def test_recover_invalid_service_returns_404(client):
    response = client.post("/api/services/invalid-service/recover")

    assert response.status_code == 404


def test_recovery_increments_restart_count(client):
    before = client.get("/api/services").json()["api-server"]["restarts"]

    client.post("/api/services/api-server/fail")
    client.post("/api/services/api-server/recover")

    after = client.get("/api/services").json()["api-server"]["restarts"]

    assert after == before + 1
