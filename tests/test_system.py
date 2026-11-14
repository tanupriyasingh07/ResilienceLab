def test_system_metrics_returns_expected_fields(client, monkeypatch):
    import app.main as main
    from unittest.mock import MagicMock

    memory = MagicMock()
    memory.percent = 65.0

    disk = MagicMock()
    disk.percent = 72.0

    monkeypatch.setattr(
        main.psutil,
        "cpu_percent",
        lambda interval: 25.0
    )
    monkeypatch.setattr(
        main.psutil,
        "virtual_memory",
        lambda: memory
    )
    monkeypatch.setattr(
        main.psutil,
        "disk_usage",
        lambda path: disk
    )
    monkeypatch.setattr(main.time, "time", lambda: 10000)
    monkeypatch.setattr(main.psutil, "boot_time", lambda: 9000)

    response = client.get("/api/system")

    assert response.status_code == 200

    data = response.json()

    assert data["cpu"] == 25.0
    assert data["memory"] == 65.0
    assert data["disk"] == 72.0
    assert data["uptime"] == 1000


def test_dashboard_endpoint_returns_html(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]