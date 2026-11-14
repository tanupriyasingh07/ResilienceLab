import json
import app.main as main


class MockResponse:
    def __init__(self, node_id):
        self.node_id = node_id

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return json.dumps({
            "message": "Request processed successfully",
            "node_id": self.node_id,
            "total_requests": 1
        }).encode("utf-8")


def mock_node_response(request, timeout=None):
    url = request.full_url if hasattr(request, "full_url") else request

    for node_id, container_name in main.NODE_CONTAINER_NAMES.items():
        if container_name in url:
            return MockResponse(node_id)

    raise ValueError(f"Unknown node URL: {url}")


def test_round_robin_routes_to_different_healthy_nodes(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "get_docker_node_status",
        lambda node_id: "healthy"
    )
    monkeypatch.setattr(
        main.urllib.request,
        "urlopen",
        mock_node_response
    )

    first = client.post("/api/route")
    second = client.post("/api/route")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["selected_node"] == "node-1"
    assert second.json()["selected_node"] == "node-2"


def test_routing_skips_failed_node(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "get_docker_node_status",
        lambda node_id: (
            "failed" if node_id == "node-2" else "healthy"
        )
    )
    monkeypatch.setattr(
        main.urllib.request,
        "urlopen",
        mock_node_response
    )

    main.rr_index = 1

    response = client.post("/api/route")

    assert response.status_code == 200
    assert response.json()["selected_node"] == "node-3"


def test_routing_returns_503_when_all_nodes_fail(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "get_docker_node_status",
        lambda node_id: "failed"
    )

    response = client.post("/api/route")

    assert response.status_code == 503
    assert "No healthy servers" in response.json()["detail"]


def test_routing_failure_updates_node_state(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "get_docker_node_status",
        lambda node_id: "failed"
    )

    def failed_request(request, timeout=None):
        raise ConnectionError("Node connection failed")

    monkeypatch.setattr(
        main.urllib.request,
        "urlopen",
        failed_request
    )

    response = client.post("/api/route")

    assert response.status_code == 503

    failed_nodes = [
        node for node in main.nodes.values()
        if node["status"] == "failed"
    ]

    assert len(failed_nodes) == 3

    for node in failed_nodes:
        assert node["failed_at"] is not None

def test_routing_initializes_missing_failed_at(client, monkeypatch):
    import time

    node = main.nodes["node-1"]
    node["status"] = "failed"
    node["failed_at"] = None

    monkeypatch.setattr(
        main,
        "get_docker_node_status",
        lambda node_id: "failed"
    )

    before = time.time()

    response = client.post("/api/route")

    after = time.time()

    assert response.status_code == 503
    assert node["status"] == "failed"
    assert node["failed_at"] is not None
    assert before <= node["failed_at"] <= after
