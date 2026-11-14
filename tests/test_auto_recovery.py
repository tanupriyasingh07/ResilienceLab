import asyncio
import time
from types import SimpleNamespace

import pytest
import app.main as main
from app.recovery.manager import RecoveryManager
from app.recovery.state import RecoveryState

def get_recovery_duration_count(node_id):
    for metric in main.RECOVERY_DURATION.collect():
        for sample in metric.samples:
            if (
                sample.name.endswith("_count")
                and sample.labels.get("node_id") == node_id
            ):
                return sample.value
    return 0

def setup_recovery_manager(node_ids, monkeypatch):
    manager = RecoveryManager()

    for node_id in node_ids:
        state = RecoveryState(
            item_id=node_id,
            item_type="node"
        )
        manager.register(state)
        state.next_retry_at = 0

    main.recovery_manager = manager

    # Prevent tests from modifying the real SQLite database.
    monkeypatch.setattr(
        main,
        "save_recovery_state",
        lambda *args, **kwargs: None
    )

    return manager


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
    setup_recovery_manager(["node-1"], monkeypatch)
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
    assert main.nodes["node-1"]["failed_at"] == original_failed_at

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
    setup_recovery_manager(["node-1"], monkeypatch)
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


def test_auto_recovery_waits_for_node_lock(monkeypatch):
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
                    "failed_at": time.time() - 120,
                    "restarts": 0
                }
            }
        )

        monkeypatch.setattr(main, "services", {})
        setup_recovery_manager(["node-1"], monkeypatch)

        docker_calls = []

        def fake_get(name):
            docker_calls.append(name)
            raise AssertionError("Docker accessed while lock was held")

        monkeypatch.setattr(
            main,
            "docker_client",
            SimpleNamespace(
                containers=SimpleNamespace(get=fake_get)
            )
        )

        await lock.acquire()

        recovery_task = asyncio.create_task(main.auto_recovery())

        await asyncio.sleep(0.05)

        assert docker_calls == []

        recovery_task.cancel()
        lock.release()

        with pytest.raises(asyncio.CancelledError):
            await recovery_task

    asyncio.run(scenario())



def test_auto_recovery_throttles_failed_attempts(monkeypatch):
    original_failed_at = time.time() - 120
    events = []

    async def scenario():
        attempts_before = main.RECOVERY_ATTEMPTS.labels("node-1")._value.get()
        failures_before = main.RECOVERY_RESULTS.labels("node-1", "failure")._value.get()
        duration_count_before = get_recovery_duration_count("node-1")

        monkeypatch.setattr(
            main,
            "node_recovery_locks",
            {"node-1": asyncio.Lock()}
        )

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
        setup_recovery_manager(["node-1"], monkeypatch)

        def failing_get(name):
            raise main.docker.errors.DockerException(
                "Docker daemon unavailable"
            )

        monkeypatch.setattr(
            main,
            "docker_client",
            SimpleNamespace(
                containers=SimpleNamespace(get=failing_get)
            )
        )

        monkeypatch.setattr(
            main,
            "get_docker_node_status",
            lambda node_id: "failed"
        )

        monkeypatch.setattr(
            main,
            "log_event",
            lambda service, event: events.append(event)
        )

        monkeypatch.setattr(main, "save_states", lambda: None)

        async def stop_loop(delay):
            raise asyncio.CancelledError

        monkeypatch.setattr(main.asyncio, "sleep", stop_loop)

        try:
            await main.auto_recovery()
        except asyncio.CancelledError:
            pass

        assert main.nodes["node-1"]["failed_at"] == original_failed_at
        assert any("Automatic recovery failed" in event for event in events)

        # Verify recovery metrics
        assert main.RECOVERY_ATTEMPTS.labels("node-1")._value.get() == attempts_before + 1
        assert main.RECOVERY_RESULTS.labels("node-1", "failure")._value.get() == failures_before + 1
        assert get_recovery_duration_count("node-1") == duration_count_before + 1

    asyncio.run(scenario())



def test_auto_recovery_executes_probe_after_circuit_cooldown(monkeypatch):
    async def scenario():
        attempts_before = main.RECOVERY_ATTEMPTS.labels("node-1")._value.get()
        successes_before = main.RECOVERY_RESULTS.labels("node-1", "success")._value.get()
        failures_before = main.RECOVERY_RESULTS.labels("node-1", "failure")._value.get()
        duration_count_before = get_recovery_duration_count("node-1")

        current_time = [1029.0]
        manager = RecoveryManager(clock=lambda: current_time[0])

        state = RecoveryState(
            "node-1",
            "node",
            retry_count=5,
            consecutive_failures=3,
            circuit_state="open",
            circuit_opened_at=1000.0,
        )
        manager.register(state)
        manager.schedule_retry("node-1")

        assert state.next_retry_at == 1030.0

        main.recovery_manager = manager
        monkeypatch.setattr(main, "services", {})

        monkeypatch.setattr(
            main,
            "nodes",
            {
                "node-1": {
                    "name": "Server Node 1",
                    "status": "failed",
                    "requests": 0,
                    "failed_at": 900.0,
                    "restarts": 0,
                }
            },
        )

        monkeypatch.setattr(
            main,
            "node_recovery_locks",
            {"node-1": asyncio.Lock()},
        )

        started = []

        class FakeContainer:
            status = "exited"

            def reload(self):
                pass

            def start(self):
                started.append(True)

        container = FakeContainer()

        monkeypatch.setattr(
            main,
            "docker_client",
            SimpleNamespace(
                containers=SimpleNamespace(
                    get=lambda name: container
                )
            ),
        )

        status_calls = []

        def fake_node_status(node_id):
            status_calls.append(node_id)

            # Failed before recovery; healthy after container start.
            if len(status_calls) <= 2:
                return "failed"

            return "healthy"

        monkeypatch.setattr(
            main,
            "get_docker_node_status",
            fake_node_status,
        )

        monkeypatch.setattr(main, "log_event", lambda *args: None)
        monkeypatch.setattr(main, "save_states", lambda: None)
        monkeypatch.setattr(
            main,
            "save_recovery_state",
            lambda *args, **kwargs: None,
        )

        async def fake_log(*args):
            pass

        async def fake_save():
            pass

        monkeypatch.setattr(main, "async_log_event", fake_log)
        monkeypatch.setattr(main, "async_save_states", fake_save)

        sleep_calls = 0

        async def controlled_sleep(delay):
            nonlocal sleep_calls
            sleep_calls += 1

            if sleep_calls == 1:
                # Advance exactly to the cooldown deadline.
                current_time[0] = 1030.0
                return

            raise asyncio.CancelledError

        monkeypatch.setattr(main.asyncio, "sleep", controlled_sleep)

        with pytest.raises(asyncio.CancelledError):
            await main.auto_recovery()

        assert started == [True]
        assert state.circuit_state == "closed"
        assert state.retry_count == 0
        assert state.consecutive_failures == 0
        assert state.next_retry_at is None
        assert main.nodes["node-1"]["status"] == "healthy"

        assert main.RECOVERY_ATTEMPTS.labels("node-1")._value.get() == attempts_before + 1
        assert main.RECOVERY_RESULTS.labels("node-1", "success")._value.get() == successes_before + 1
        assert main.RECOVERY_RESULTS.labels("node-1", "failure")._value.get() == failures_before
        assert get_recovery_duration_count("node-1") == duration_count_before + 1

    asyncio.run(scenario())
