
import asyncio
from types import SimpleNamespace

import app.main as main


def test_manual_recovery_waits_for_node_lock(monkeypatch):
    async def scenario():
        lock = asyncio.Lock()
        monkeypatch.setattr(
            main,
            "node_recovery_locks",
            {"node-1": lock}
        )

        monkeypatch.setattr(
            main,
            "nodes",
            {
                "node-1": {
                    "name": "Server Node 1",
                    "status": "failed",
                    "requests": 0,
                    "failed_at": 123.0,
                    "restarts": 0
                }
            }
        )

        container_calls = []

        class FakeContainer:
            status = "running"

            def reload(self):
                pass

        fake_container = FakeContainer()

        def fake_get(name):
            container_calls.append(name)
            return fake_container

        monkeypatch.setattr(
            main,
            "docker_client",
            SimpleNamespace(
                containers=SimpleNamespace(get=fake_get)
            )
        )

        monkeypatch.setattr(
            main,
            "get_docker_node_status",
            lambda node_id: "healthy"
        )
        monkeypatch.setattr(main, "log_event", lambda *args: None)
        monkeypatch.setattr(main, "save_states", lambda: None)

        await lock.acquire()

        recovery_task = asyncio.create_task(
            main.recover_node("node-1")
        )

        # Give the recovery task an opportunity to attempt the lock.
        await asyncio.sleep(0.05)

        # Recovery must not access Docker while the lock is held.
        assert container_calls == []

        lock.release()

        result = await recovery_task

        assert result["status"] == "healthy"
        assert len(container_calls) == 1
        assert main.nodes["node-1"]["status"] == "healthy"

    asyncio.run(scenario())


def test_routing_holds_node_lock_during_request(monkeypatch):
    async def scenario():
        lock = asyncio.Lock()

        monkeypatch.setattr(
            main,
            "node_recovery_locks",
            {"node-1": lock}
        )

        monkeypatch.setattr(
            main,
            "nodes",
            {
                "node-1": {
                    "name": "Server Node 1",
                    "status": "healthy",
                    "requests": 0,
                    "failed_at": None,
                    "restarts": 0
                }
            }
        )

        monkeypatch.setattr(main, "rr_index", 0)

        monkeypatch.setattr(
            main,
            "get_docker_node_status",
            lambda node_id: "healthy"
        )

        request_started = asyncio.Event()
        allow_request_to_finish = asyncio.Event()

        def fake_urlopen(*args, **kwargs):
            class FakeResponse:
                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

                def read(self):
                    return b'{"node_id":"node-1"}'

            request_started.set()
            return FakeResponse()

        async def fake_send_request():
            request_started.set()
            await allow_request_to_finish.wait()
            return {"node_id": "node-1"}

        # Use a controllable async replacement for the worker request.
        original_to_thread = main.asyncio.to_thread

        async def controlled_to_thread(func, *args, **kwargs):
            if func.__name__ == "send_request":
                return await fake_send_request()
            return await original_to_thread(func, *args, **kwargs)

        monkeypatch.setattr(
            main.asyncio,
            "to_thread",
            controlled_to_thread
        )

        monkeypatch.setattr(main, "log_event", lambda *args: None)
        monkeypatch.setattr(main, "save_states", lambda: None)

        route_task = asyncio.create_task(main.route_request())

        await request_started.wait()

        assert lock.locked()

        recovery_task = asyncio.create_task(lock.acquire())

        await asyncio.sleep(0.05)
        assert not recovery_task.done()

        allow_request_to_finish.set()

        result = await route_task

        assert result["selected_node"] == "node-1"

        await recovery_task
        lock.release()

    asyncio.run(scenario())
