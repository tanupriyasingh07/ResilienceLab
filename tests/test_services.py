def test_get_services_returns_all_services(client):
    response = client.get("/api/services")

    assert response.status_code == 200

    data = response.json()
    assert "api-server" in data
    assert "database" in data
    assert "worker" in data


def test_fail_valid_service(client):
    response = client.post("/api/services/api-server/fail")

    assert response.status_code == 200
    assert "failure detected" in response.json()["message"].lower()

    services_response = client.get("/api/services")
    assert services_response.json()["api-server"]["status"] == "failed"


def test_fail_invalid_service_returns_404(client):
    response = client.post("/api/services/invalid-service/fail")

    assert response.status_code == 404
