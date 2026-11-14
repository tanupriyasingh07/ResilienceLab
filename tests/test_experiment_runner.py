
import asyncio
import pytest

from app.experiments.runner import ExperimentRunner


class FakeRepository:
    def __init__(self):
        self.records = {}

    def create(self, experiment):
        self.records[experiment["id"]] = experiment.copy()

    def update(self, experiment_id, updates):
        if experiment_id not in self.records:
            return False

        self.records[experiment_id].update(updates)
        return True

    def get(self, experiment_id):
        return self.records.get(experiment_id)


class FakeRecoveryManager:
    def __init__(self):
        self.states = {
            "node-1": type(
                "State",
                (),
                {"strategy": "fixed_retry"}
            )()
        }

    def get_state(self, node_id):
        return self.states.get(node_id)


@pytest.mark.anyio
async def test_experiment_success():
    repository = FakeRepository()
    manager = FakeRecoveryManager()
    statuses = iter(["healthy", "failed", "healthy"])

    async def inject_failure(node_id):
        return {"status": "failed"}

    def get_status(node_id):
        return next(statuses)

    runner = ExperimentRunner(
        repository,
        manager,
        inject_failure,
        get_status,
        recovery_timeout=2,
        poll_interval=0.01,
    )

    result = await runner.run("Recovery Test", "node-1")

    assert result["status"] == "completed"
    assert result["outcome"] == "success"
    assert result["result"]["recovered"] is True
    assert result["duration_seconds"] >= 0


@pytest.mark.anyio
async def test_experiment_timeout():
    repository = FakeRepository()
    manager = FakeRecoveryManager()

    async def inject_failure(node_id):
        return {"status": "failed"}

    status_calls = 0

    def get_status(node_id):
        nonlocal status_calls
        status_calls += 1

        if status_calls == 1:
            return "healthy"

        return "failed"

    runner = ExperimentRunner(
        repository,
        manager,
        inject_failure,
        get_status,
        recovery_timeout=0.05,
        poll_interval=0.01,
    )

    result = await runner.run("Timeout Test", "node-1")

    assert result["status"] == "timed_out"
    assert result["outcome"] == "timeout"


@pytest.mark.anyio
async def test_experiment_failure_is_recorded():
    repository = FakeRepository()
    manager = FakeRecoveryManager()

    async def inject_failure(node_id):
        raise RuntimeError("Docker unavailable")

    statuses = iter(["healthy"])
    runner = ExperimentRunner(
        repository,
        manager,
        inject_failure,
        lambda node_id: next(statuses),
    )

    result = await runner.run("Failure Test", "node-1")

    assert result["status"] == "failed"
    assert "Docker unavailable" in result["error"]


@pytest.mark.anyio
async def test_unknown_node_is_rejected():
    runner = ExperimentRunner(
        FakeRepository(),
        FakeRecoveryManager(),
        lambda node_id: asyncio.sleep(0),
        lambda node_id: "healthy",
    )

    with pytest.raises(ValueError, match="Unknown recovery node"):
        await runner.run("Invalid Test", "node-99")


@pytest.mark.anyio
async def test_empty_experiment_name_is_rejected():
    runner = ExperimentRunner(
        FakeRepository(),
        FakeRecoveryManager(),
        lambda node_id: asyncio.sleep(0),
        lambda node_id: "healthy",
    )

    with pytest.raises(ValueError, match="name"):
        await runner.run("   ", "node-1")


@pytest.mark.anyio
async def test_invalid_trial_number_is_rejected():
    runner = ExperimentRunner(
        FakeRepository(),
        FakeRecoveryManager(),
        lambda node_id: asyncio.sleep(0),
        lambda node_id: "healthy",
    )

    with pytest.raises(ValueError, match="trial_number"):
        await runner.run("Invalid Trial", "node-1", trial_number=0)


@pytest.mark.anyio
async def test_unhealthy_node_is_rejected_before_experiment_creation():
    repository = FakeRepository()
    manager = FakeRecoveryManager()

    async def inject_failure(node_id):
        raise AssertionError("Failure injection should not run")

    runner = ExperimentRunner(
        repository,
        manager,
        inject_failure,
        lambda node_id: "failed",
    )

    with pytest.raises(RuntimeError, match="healthy before experiment"):
        await runner.run("Unhealthy Node Test", "node-1")

    assert repository.records == {}


@pytest.mark.anyio
async def test_concurrent_experiment_is_rejected():
    repository = FakeRepository()
    manager = FakeRecoveryManager()

    injection_started = asyncio.Event()
    release_injection = asyncio.Event()
    statuses = iter(["healthy", "failed", "healthy"])

    async def inject_failure(node_id):
        injection_started.set()
        await release_injection.wait()
        return {"status": "failed"}

    def get_status(node_id):
        return next(statuses)

    runner = ExperimentRunner(
        repository,
        manager,
        inject_failure,
        get_status,
        recovery_timeout=2,
        poll_interval=0.01,
    )

    first_task = asyncio.create_task(
        runner.run("First Experiment", "node-1")
    )

    try:
        await asyncio.wait_for(injection_started.wait(), timeout=2)

        with pytest.raises(RuntimeError, match="Another experiment"):
            await runner.run("Second Experiment", "node-1")

    finally:
        release_injection.set()

    result = await first_task

    assert result["status"] == "completed"
    assert len(repository.records) == 1


@pytest.mark.anyio
async def test_cancelled_experiment_is_recorded_and_cancellation_propagates():
    repository = FakeRepository()
    manager = FakeRecoveryManager()

    injection_started = asyncio.Event()

    async def inject_failure(node_id):
        injection_started.set()
        await asyncio.Event().wait()

    runner = ExperimentRunner(
        repository,
        manager,
        inject_failure,
        lambda node_id: "healthy",
    )

    task = asyncio.create_task(
        runner.run("Cancellation Test", "node-1")
    )

    await asyncio.wait_for(injection_started.wait(), timeout=2)

    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert len(repository.records) == 1

    experiment = next(iter(repository.records.values()))

    assert experiment["status"] == "failed"
    assert experiment["outcome"] == "cancelled"
    assert experiment["completed_at"] is not None
    assert "cancel" in experiment["error"].lower()
    assert runner._running is False
