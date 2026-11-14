
import pytest

from app.experiments.benchmark import BenchmarkRunner


class FakeExperimentRunner:
    def __init__(self, outcomes):
        self.outcomes = outcomes
        self.calls = []

    async def run(self, **kwargs):
        self.calls.append(kwargs)

        outcome = self.outcomes[len(self.calls) - 1]

        return {
            "id": f"exp-{len(self.calls)}",
            "run_group_id": kwargs["run_group_id"],
            "trial_number": kwargs["trial_number"],
            "status": outcome["status"],
            "outcome": outcome["outcome"],
            "duration_seconds": outcome.get("duration_seconds"),
        }


@pytest.mark.anyio
async def test_benchmark_runs_all_trials():
    fake = FakeExperimentRunner([
        {"status": "completed", "outcome": "success", "duration_seconds": 2.0},
        {"status": "completed", "outcome": "success", "duration_seconds": 4.0},
        {"status": "completed", "outcome": "success", "duration_seconds": 3.0},
    ])

    benchmark = BenchmarkRunner(fake)

    result = await benchmark.run(
        "Recovery Benchmark",
        "node-1",
        trials=3,
    )

    assert result["executed_trials"] == 3
    assert result["successful_trials"] == 3
    assert result["success_rate"] == 100
    assert result["average_duration_seconds"] == 3.0
    assert result["stopped_early"] is False
    assert len(fake.calls) == 3


@pytest.mark.anyio
async def test_benchmark_stops_after_failed_trial():
    fake = FakeExperimentRunner([
        {"status": "completed", "outcome": "success", "duration_seconds": 2.0},
        {"status": "failed", "outcome": "failure", "duration_seconds": 1.0},
        {"status": "completed", "outcome": "success", "duration_seconds": 3.0},
    ])

    benchmark = BenchmarkRunner(fake)

    result = await benchmark.run(
        "Failure Benchmark",
        "node-1",
        trials=3,
    )

    assert result["executed_trials"] == 2
    assert result["successful_trials"] == 1
    assert result["failed_trials"] == 1
    assert result["stopped_early"] is True
    assert len(fake.calls) == 2


@pytest.mark.anyio
async def test_benchmark_stops_after_timeout():
    fake = FakeExperimentRunner([
        {"status": "timed_out", "outcome": "timeout", "duration_seconds": 5.0},
    ])

    benchmark = BenchmarkRunner(fake)

    result = await benchmark.run(
        "Timeout Benchmark",
        "node-1",
        trials=5,
    )

    assert result["executed_trials"] == 1
    assert result["timed_out_trials"] == 1
    assert result["success_rate"] == 0
    assert result["stopped_early"] is True


@pytest.mark.anyio
async def test_benchmark_uses_shared_group_id():
    fake = FakeExperimentRunner([
        {"status": "completed", "outcome": "success", "duration_seconds": 1.0},
        {"status": "completed", "outcome": "success", "duration_seconds": 2.0},
    ])

    benchmark = BenchmarkRunner(fake)

    result = await benchmark.run(
        "Group Test",
        "node-1",
        trials=2,
    )

    group_ids = {
        call["run_group_id"]
        for call in fake.calls
    }

    assert len(group_ids) == 1
    assert result["run_group_id"] in group_ids
    assert [call["trial_number"] for call in fake.calls] == [1, 2]


@pytest.mark.anyio
async def test_benchmark_rejects_invalid_trial_count():
    benchmark = BenchmarkRunner(FakeExperimentRunner([]))

    with pytest.raises(ValueError, match="between 1 and 20"):
        await benchmark.run("Invalid", "node-1", trials=21)


@pytest.mark.anyio
async def test_benchmark_rejects_empty_name():
    benchmark = BenchmarkRunner(FakeExperimentRunner([]))

    with pytest.raises(ValueError, match="name"):
        await benchmark.run("   ", "node-1", trials=2)


@pytest.mark.anyio
async def test_benchmark_rejects_non_integer_trial_count():
    benchmark = BenchmarkRunner(FakeExperimentRunner([]))

    with pytest.raises(ValueError, match="integer"):
        await benchmark.run("Invalid", "node-1", trials=2.5)
