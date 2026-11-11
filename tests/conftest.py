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

    fresh_services = {
        "api-server": {
            "name": "API Server",
            "status": "healthy",
            "restarts": 0,
            "failed_at": None
        },
        "database": {
            "name": "Database",
            "status": "healthy",
            "restarts": 0,
            "failed_at": None
        },
        "worker": {
            "name": "Background Worker",
            "status": "healthy",
            "restarts": 0,
            "failed_at": None
        }
    }

    fresh_nodes = {
        "node-1": {
            "name": "Server Node 1",
            "status": "healthy",
            "requests": 0,
            "failed_at": None,
            "restarts": 0
        },
        "node-2": {
            "name": "Server Node 2",
            "status": "healthy",
            "requests": 0,
            "failed_at": None,
            "restarts": 0
        },
        "node-3": {
            "name": "Server Node 3",
            "status": "healthy",
            "requests": 0,
            "failed_at": None,
            "restarts": 0
        }
    }

    monkeypatch.setattr(main, "services", fresh_services)
    monkeypatch.setattr(main, "nodes", fresh_nodes)
    monkeypatch.setattr(main, "rr_index", 0)

    with TestClient(main.app) as test_client:
        yield test_client
