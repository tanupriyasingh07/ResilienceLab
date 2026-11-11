import asyncio
import time
from types import SimpleNamespace

import pytest
import app.main as main


def test_auto_recovery_restarts_running_unhealthy_container(monkeypatch):
    restart_called = []
    original_failed_at = time.time() - 120

    class FakeContainer:
        status = "running"

        def reload(self):
            pass

        def restart(self):
            restart_called.append(True)

    fake_container = FakeContainer()

    fake_docker = SimpleNamespace(
        containers=SimpleNamespace(
            get=lambda name: fake_container
        )
    )

    monkeypatch.setattr(main, "docker_client", fake_docker)
    monkeypatch.setattr(
        main,
        "nodes",
        {
            "node-1": {
                "name": "Server Node 1",
                "status": "failed",
                "requests": 0,
                "failed_at": original_failed_at,
                "restarts": 0
            }
        }
    )
    monkeypatch.setattr(main, "services", {})
    monkeypatch.setattr(
        main,
        "get_docker_node_status",
        lambda node_id: "failed"
    )
    monkeypatch.setattr(main, "log_event", lambda *args: None)
    monkeypatch.setattr(main, "save_states", lambda: None)

    async def stop_loop(delay):
        raise asyncio.CancelledError

    monkeypatch.setattr(main.asyncio, "sleep", stop_loop)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(main.auto_recovery())

    assert restart_called, "Unhealthy running container was not restarted"
    assert main.nodes["node-1"]["failed_at"] > original_failed_at

def test_auto_recovery_starts_stopped_container(monkeypatch):
    start_called = []
    restart_called = []

    class FakeContainer:
        status = "exited"

        def reload(self):
            pass

        def start(self):
            start_called.append(True)

        def restart(self):
            restart_called.append(True)

    fake_container = FakeContainer()

    fake_docker = SimpleNamespace(
        containers=SimpleNamespace(
            get=lambda name: fake_container
        )
    )

    monkeypatch.setattr(main, "docker_client", fake_docker)
    monkeypatch.setattr(
        main,
        "nodes",
        {
            "node-1": {
                "name": "Server Node 1",
                "status": "failed",
                "requests": 0,
                "failed_at": time.time() - 120,
                "restarts": 0
            }
        }
    )
    monkeypatch.setattr(main, "services", {})
    monkeypatch.setattr(
        main,
        "get_docker_node_status",
        lambda node_id: "failed"
    )
    monkeypatch.setattr(main, "log_event", lambda *args: None)
    monkeypatch.setattr(main, "save_states", lambda: None)

    async def stop_loop(delay):
        raise asyncio.CancelledError

    monkeypatch.setattr(main.asyncio, "sleep", stop_loop)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(main.auto_recovery())

    assert start_called, "Stopped container was not started"
    assert not restart_called, "Stopped container should use start(), not restart()"

