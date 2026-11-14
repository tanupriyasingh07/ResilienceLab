def test_get_nodes_returns_three_nodes(client, monkeypatch):
    import app.main as main

    monkeypatch.setattr(
        main,
        "get_docker_node_status",
        lambda node_id: "healthy"
    )

    response = client.get("/api/nodes")

    assert response.status_code == 200
    assert len(response.json()) == 3
    assert all(
        node["status"] == "healthy"
        for node in response.json().values()
    )


def test_cluster_health_returns_healthy(client, monkeypatch):
    import app.main as main

    monkeypatch.setattr(
        main,
        "get_docker_node_status",
        lambda node_id: "healthy"
    )

    response = client.get("/api/cluster-health")

    assert response.status_code == 200
    assert response.json()["total_nodes"] == 3
    assert response.json()["healthy_nodes"] == 3
    assert response.json()["failed_nodes"] == 0
    assert response.json()["cluster_status"] == "healthy"


def test_cluster_health_returns_degraded(client, monkeypatch):
    import app.main as main

    monkeypatch.setattr(
        main,
        "get_docker_node_status",
        lambda node_id: (
            "failed" if node_id == "node-2" else "healthy"
        )
    )

    response = client.get("/api/cluster-health")

    assert response.status_code == 200
    assert response.json()["healthy_nodes"] == 2
    assert response.json()["failed_nodes"] == 1
    assert response.json()["cluster_status"] == "degraded"

def test_fail_node_stops_running_container(client, monkeypatch):
    import app.main as main
    from unittest.mock import MagicMock

    container = MagicMock()
    container.status = "running"

    docker_mock = MagicMock()
    docker_mock.containers.get.return_value = container

    monkeypatch.setattr(main, "docker_client", docker_mock)

    response = client.post("/api/nodes/node-1/fail")

    assert response.status_code == 200
    container.stop.assert_called_once_with(timeout=2)
    assert main.nodes["node-1"]["status"] == "failed"
    assert main.nodes["node-1"]["failed_at"] is not None


def test_fail_node_returns_404_for_missing_container(client, monkeypatch):
    import app.main as main
    import docker
    from unittest.mock import MagicMock

    docker_mock = MagicMock()
    docker_mock.containers.get.side_effect = docker.errors.NotFound(
        "Container not found"
    )

    monkeypatch.setattr(main, "docker_client", docker_mock)

    response = client.post("/api/nodes/node-1/fail")

    assert response.status_code == 404


def test_fail_node_returns_500_on_docker_error(client, monkeypatch):
    import app.main as main
    import docker
    from unittest.mock import MagicMock

    docker_mock = MagicMock()
    docker_mock.containers.get.side_effect = docker.errors.DockerException(
        "Docker unavailable"
    )

    monkeypatch.setattr(main, "docker_client", docker_mock)

    response = client.post("/api/nodes/node-1/fail")

    assert response.status_code == 500
