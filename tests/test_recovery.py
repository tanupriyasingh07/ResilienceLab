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

def test_manual_recovery_starts_stopped_container(client, monkeypatch):
    import app.main as main
    from unittest.mock import MagicMock

    container = MagicMock()
    container.status = "exited"

    monkeypatch.setattr(
        main.docker_client.containers,
        "get",
        lambda name: container
    )
    monkeypatch.setattr(
        main,
        "get_docker_node_status",
        lambda node_id: "healthy"
    )

    response = client.post("/api/nodes/node-1/recover")

    assert response.status_code == 200
    container.start.assert_called_once()
    container.restart.assert_not_called()
    assert main.nodes["node-1"]["status"] == "healthy"


def test_manual_recovery_restarts_running_unhealthy_container(client, monkeypatch):
    import app.main as main
    from unittest.mock import MagicMock

    container = MagicMock()
    container.status = "running"

    docker_mock = MagicMock()
    docker_mock.containers.get.return_value = container

    health_checks = iter(["unhealthy", "healthy"])

    monkeypatch.setattr(main, "docker_client", docker_mock)
    monkeypatch.setattr(
        main,
        "get_docker_node_status",
        lambda node_id: next(health_checks)
    )

    response = client.post("/api/nodes/node-1/recover")

    assert response.status_code == 200
    container.restart.assert_called_once()
    container.start.assert_not_called()
    assert main.nodes["node-1"]["status"] == "healthy"
