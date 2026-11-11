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
