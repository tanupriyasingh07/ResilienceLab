import asyncio
import pytest
from fastapi.testclient import TestClient
import app.main as main


async def idle_recovery():
    await asyncio.Event().wait()


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB", str(tmp_path / "test.db"))
    monkeypatch.setattr(main, "auto_recovery", idle_recovery)

    with TestClient(main.app) as test_client:
        yield test_client


def test_health_endpoint_returns_running_status(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "running",
        "project": "ResilienceLab"
    }
