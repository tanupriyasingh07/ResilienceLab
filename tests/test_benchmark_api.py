
from app import main


def test_create_benchmark_success(client, monkeypatch):
    class FakeBenchmarkRunner:
        async def run(self, **kwargs):
            return {
                "run_group_id": "group-001",
                "name": kwargs["name"],
                "target_node": kwargs["target_node"],
                "requested_trials": kwargs["trials"],
                "executed_trials": 2,
                "successful_trials": 2,
                "failed_trials": 0,
                "timed_out_trials": 0,
                "success_rate": 100.0,
                "average_duration_seconds": 2.5,
                "stopped_early": False,
                "trials": [],
            }

    monkeypatch.setattr(
        main,
        "benchmark_runner",
        FakeBenchmarkRunner()
    )

    response = client.post(
        "/api/experiments/benchmark",
        json={
            "name": "Recovery Benchmark",
            "target_node": "node-1",
            "trials": 2,
        },
    )

    assert response.status_code == 200
    assert response.json()["executed_trials"] == 2
    assert response.json()["success_rate"] == 100.0


def test_benchmark_rejects_invalid_trial_count(client):
    response = client.post(
        "/api/experiments/benchmark",
        json={
            "name": "Invalid Benchmark",
            "target_node": "node-1",
            "trials": 21,
        },
    )

    assert response.status_code == 422


def test_benchmark_rejects_missing_name(client):
    response = client.post(
        "/api/experiments/benchmark",
        json={
            "target_node": "node-1",
            "trials": 2,
        },
    )

    assert response.status_code == 422


def test_benchmark_returns_503_when_runner_unavailable(
    client,
    monkeypatch
):
    monkeypatch.setattr(main, "benchmark_runner", None)

    response = client.post(
        "/api/experiments/benchmark",
        json={
            "name": "Unavailable Benchmark",
            "target_node": "node-1",
            "trials": 2,
        },
    )

    assert response.status_code == 503


def test_benchmark_returns_409_on_concurrent_run(
    client,
    monkeypatch
):
    class FakeBenchmarkRunner:
        async def run(self, **kwargs):
            raise RuntimeError("Another experiment is already running")

    monkeypatch.setattr(
        main,
        "benchmark_runner",
        FakeBenchmarkRunner()
    )

    response = client.post(
        "/api/experiments/benchmark",
        json={
            "name": "Concurrent Benchmark",
            "target_node": "node-1",
            "trials": 2,
        },
    )

    assert response.status_code == 409
