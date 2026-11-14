import app.main as main
def test_service_failure_is_recorded_in_logs(client):
    response = client.post("/api/services/api-server/fail")
    assert response.status_code == 200

    logs_response = client.get("/api/logs")

    assert logs_response.status_code == 200

    logs = logs_response.json()
    assert any(
        log["service"] == "api-server"
        and log["event"] == "Service failure detected"
        for log in logs
    )


def test_prometheus_metrics_endpoint(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "resiliencelab_http_requests_total" in response.text
    assert "resiliencelab_http_request_duration_seconds" in response.text


def test_prometheus_updates_node_gauges_for_healthy_cluster(client, monkeypatch):
    monkeypatch.setattr(
        "app.main.get_docker_node_status",
        lambda node_id: "healthy"
    )

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "resiliencelab_active_nodes 3.0" in response.text
    assert "resiliencelab_total_nodes 3.0" in response.text


def test_prometheus_updates_node_gauges_for_degraded_cluster(client, monkeypatch):
    monkeypatch.setattr(
        "app.main.get_docker_node_status",
        lambda node_id: (
            "failed" if node_id == "node-2" else "healthy"
        )
    )

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "resiliencelab_active_nodes 2.0" in response.text
    assert "resiliencelab_total_nodes 3.0" in response.text


from app.recovery.manager import RecoveryManager
from app.recovery.state import RecoveryState


def test_prometheus_exports_recovery_state_gauges(client, monkeypatch):
    manager = RecoveryManager()

    state = RecoveryState(
        item_id="metrics-node",
        item_type="node",
        retry_count=3,
        consecutive_failures=2,
        circuit_state="open",
    )
    manager.register(state)

    monkeypatch.setattr(main, "recovery_manager", manager)

    response = client.get("/metrics")

    assert response.status_code == 200
    metrics = response.text

    assert 'resiliencelab_recovery_retries{node_id="metrics-node"} 3.0' in metrics
    assert 'resiliencelab_recovery_consecutive_failures{node_id="metrics-node"} 2.0' in metrics

    assert 'resiliencelab_circuit_breaker_state{node_id="metrics-node",state="open"} 1.0' in metrics
    assert 'resiliencelab_circuit_breaker_state{node_id="metrics-node",state="closed"} 0.0' in metrics
    assert 'resiliencelab_circuit_breaker_state{node_id="metrics-node",state="half_open"} 0.0' in metrics


def test_prometheus_updates_recovery_gauges_after_state_change(client, monkeypatch):
    manager = RecoveryManager()

    state = RecoveryState(
        item_id="metrics-node-update",
        item_type="node",
        retry_count=2,
        consecutive_failures=1,
        circuit_state="closed",
    )
    manager.register(state)

    monkeypatch.setattr(main, "recovery_manager", manager)

    first_response = client.get("/metrics")
    assert 'resiliencelab_recovery_retries{node_id="metrics-node-update"} 2.0' in first_response.text

    state.retry_count = 4
    state.consecutive_failures = 3
    state.circuit_state = "half_open"

    second_response = client.get("/metrics")
    metrics = second_response.text

    assert 'resiliencelab_recovery_retries{node_id="metrics-node-update"} 4.0' in metrics
    assert 'resiliencelab_recovery_consecutive_failures{node_id="metrics-node-update"} 3.0' in metrics
    assert 'resiliencelab_circuit_breaker_state{node_id="metrics-node-update",state="half_open"} 1.0' in metrics
