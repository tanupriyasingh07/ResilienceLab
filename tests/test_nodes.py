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
