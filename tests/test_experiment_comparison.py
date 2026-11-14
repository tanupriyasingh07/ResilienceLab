
import pytest

from app import main


def make_experiment(experiment_id, duration, outcome="success"):
    return {
        "id": experiment_id,
        "run_group_id": None,
        "trial_number": 1,
        "name": "Comparison Test",
        "target_node": "node-1",
        "strategy": "fixed_retry",
        "status": "completed" if outcome == "success" else "failed",
        "started_at": 1000.0,
        "completed_at": 1000.0 + duration,
        "duration_seconds": duration,
        "outcome": outcome,
        "error": None,
        "config": {},
        "result": {},
    }



def seed_experiments(repository):
    experiments = [
        make_experiment("exp-001", 2.0),
        make_experiment("exp-002", 4.0),
    ]

    for experiment in experiments:
        repository.create(experiment)

        repository.update(
            experiment["id"],
            {
                "status": experiment["status"],
                "completed_at": experiment["completed_at"],
                "duration_seconds": experiment["duration_seconds"],
                "outcome": experiment["outcome"],
                "error": experiment["error"],
                "result": experiment["result"],
            },
        )



def test_compare_experiments_success(client):
    repository = main.experiment_runner.repository
    seed_experiments(repository)

    response = client.get(
        "/api/experiments/compare?ids=exp-001,exp-002"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_experiments"] == 2
    assert data["successful_experiments"] == 2
    assert data["success_rate"] == 100
    assert data["average_duration_seconds"] == 3.0
    assert len(data["experiments"]) == 2


def test_compare_experiments_rejects_duplicate_ids(client):
    response = client.get(
        "/api/experiments/compare?ids=exp-001,exp-001"
    )

    assert response.status_code == 400
    assert "Duplicate" in response.json()["detail"]


def test_compare_experiments_rejects_insufficient_ids(client):
    response = client.get(
        "/api/experiments/compare?ids=exp-001"
    )

    assert response.status_code == 400


def test_compare_experiments_returns_404_for_missing_id(client):
    repository = main.experiment_runner.repository
    repository.create(make_experiment("exp-001", 2.0))

    response = client.get(
        "/api/experiments/compare?ids=exp-001,missing-id"
    )

    assert response.status_code == 404


def test_compare_experiments_returns_503_when_runner_unavailable(
    client,
    monkeypatch
):
    monkeypatch.setattr(main, "experiment_runner", None)

    response = client.get(
        "/api/experiments/compare?ids=exp-001,exp-002"
    )

    assert response.status_code == 503
