
import pytest

from app import main


def make_experiment(experiment_id="exp-001"):
    return {
        "id": experiment_id,
        "run_group_id": None,
        "trial_number": 1,
        "name": "API Recovery Test",
        "target_node": "node-1",
        "strategy": "fixed_retry",
        "status": "completed",
        "started_at": 1000.0,
        "completed_at": 1002.0,
        "duration_seconds": 2.0,
        "outcome": "success",
        "error": None,
        "config": {},
        "result": {"recovered": True}
    }


class FakeExperimentRunner:
    def __init__(self, repository, result=None, error=None):
        self.repository = repository
        self.result = result
        self.error = error
        self.calls = []

    async def run(self, **kwargs):
        self.calls.append(kwargs)

        if self.error:
            raise self.error

        return self.result


def install_fake_runner(repository, monkeypatch, result=None, error=None):
    runner = FakeExperimentRunner(
        repository=repository,
        result=result,
        error=error
    )
    monkeypatch.setattr(main, "experiment_runner", runner)
    return runner


def test_create_experiment_success(client, monkeypatch):
    experiment = make_experiment()

    runner = install_fake_runner(
        main.experiment_runner.repository,
        monkeypatch,
        result=experiment
    )

    response = client.post(
        "/api/experiments",
        json={
            "name": "API Recovery Test",
            "target_node": "node-1"
        }
    )

    assert response.status_code == 200
    assert response.json()["id"] == "exp-001"
    assert runner.calls == [{
        "name": "API Recovery Test",
        "target_node": "node-1"
    }]


def test_create_experiment_rejects_invalid_node(client, monkeypatch):
    install_fake_runner(
        main.experiment_runner.repository,
        monkeypatch,
        error=ValueError("Unknown recovery node: node-99")
    )

    response = client.post(
        "/api/experiments",
        json={
            "name": "Invalid Node Test",
            "target_node": "node-99"
        }
    )

    assert response.status_code == 400
    assert "Unknown recovery node" in response.json()["detail"]


def test_create_experiment_rejects_concurrent_run(client, monkeypatch):
    install_fake_runner(
        main.experiment_runner.repository,
        monkeypatch,
        error=RuntimeError("Another experiment is already running")
    )

    response = client.post(
        "/api/experiments",
        json={
            "name": "Concurrent Test",
            "target_node": "node-1"
        }
    )

    assert response.status_code == 409


def test_list_experiments_with_pagination(client):
    repository = main.experiment_runner.repository

    repository.create(make_experiment("exp-001"))

    second = make_experiment("exp-002")
    second["started_at"] = 2000.0
    repository.create(second)

    response = client.get("/api/experiments?limit=1&offset=0")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == "exp-002"


def test_get_experiment_by_id(client):
    repository = main.experiment_runner.repository
    repository.create(make_experiment("exp-detail"))

    response = client.get("/api/experiments/exp-detail")

    assert response.status_code == 200
    assert response.json()["id"] == "exp-detail"
    assert response.json()["result"]["recovered"] is True


def test_get_missing_experiment_returns_404(client):
    response = client.get("/api/experiments/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment not found"


def test_experiment_api_returns_503_when_runner_unavailable(client, monkeypatch):
    monkeypatch.setattr(main, "experiment_runner", None)

    response = client.get("/api/experiments")

    assert response.status_code == 503
    assert response.json()["detail"] == "Experiment runner is not initialized"
