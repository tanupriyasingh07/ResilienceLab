
import pytest

from app import main


def make_experiment(
    experiment_id,
    trial_number=1,
    duration=5.0,
    outcome="success",
):
    return {
        "id": experiment_id,
        "run_group_id": "group-001",
        "trial_number": trial_number,
        "name": "Report Test",
        "target_node": "node-1",
        "strategy": "fixed_retry",
        "status": "completed" if outcome == "success" else "failed",
        "started_at": 1000.0,
        "completed_at": 1000.0 + duration,
        "duration_seconds": duration,
        "outcome": outcome,
        "error": None,
        "config": {},
        "result": {
            "failure_observed": True,
            "recovered": True,
            "final_node_status": "healthy",
            "recovery_strategy": "fixed_retry",
        },
    }


def seed_experiment(repository, experiment):
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


def test_individual_experiment_report_success(client):
    repository = main.experiment_runner.repository
    seed_experiment(repository, make_experiment("exp-001"))

    response = client.get("/api/experiments/exp-001/report")

    assert response.status_code == 200

    data = response.json()

    assert data["report_type"] == "individual_experiment"
    assert data["experiment"]["id"] == "exp-001"
    assert data["execution"]["outcome"] == "success"
    assert data["recovery"]["recovered"] is True


def test_individual_experiment_report_returns_404(client):
    response = client.get("/api/experiments/missing-id/report")

    assert response.status_code == 404


def test_individual_experiment_report_returns_503(
    client,
    monkeypatch
):
    monkeypatch.setattr(main, "experiment_runner", None)

    response = client.get("/api/experiments/exp-001/report")

    assert response.status_code == 503


def test_benchmark_group_report_success(client):
    repository = main.experiment_runner.repository

    seed_experiment(
        repository,
        make_experiment("exp-001", trial_number=1, duration=4.0),
    )
    seed_experiment(
        repository,
        make_experiment("exp-002", trial_number=2, duration=6.0),
    )

    response = client.get(
        "/api/experiments/groups/group-001/report"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["report_type"] == "benchmark_group"
    assert data["run_group_id"] == "group-001"
    assert data["summary"]["total_trials"] == 2
    assert data["summary"]["successful_trials"] == 2
    assert data["summary"]["success_rate"] == 100
    assert data["summary"]["average_duration_seconds"] == 5.0
    assert len(data["trials"]) == 2


def test_benchmark_group_report_returns_404(client):
    response = client.get(
        "/api/experiments/groups/unknown-group/report"
    )

    assert response.status_code == 404


def test_benchmark_group_report_returns_503(
    client,
    monkeypatch
):
    monkeypatch.setattr(main, "experiment_runner", None)

    response = client.get(
        "/api/experiments/groups/group-001/report"
    )

    assert response.status_code == 503
