
import pytest

from app.experiments.reports import (
    build_experiment_report,
    build_benchmark_report,
)


def sample_experiment(
    experiment_id="exp-001",
    trial_number=1,
    outcome="success",
    status="completed",
    duration=5.0,
):
    return {
        "id": experiment_id,
        "run_group_id": "group-001",
        "trial_number": trial_number,
        "name": "Node Recovery Test",
        "target_node": "node-1",
        "strategy": "fixed_retry",
        "status": status,
        "started_at": 1000.0,
        "completed_at": 1000.0 + duration if duration is not None else None,
        "duration_seconds": duration,
        "outcome": outcome,
        "error": None,
        "config": {"failure_type": "container_stop"},
        "result": {
            "failure_observed": True,
            "recovered": True,
            "final_node_status": "healthy",
            "recovery_strategy": "fixed_retry",
        },
    }


def test_build_individual_experiment_report():
    experiment = sample_experiment()

    report = build_experiment_report(experiment)

    assert report["report_type"] == "individual_experiment"
    assert report["experiment"]["id"] == "exp-001"
    assert report["execution"]["status"] == "completed"
    assert report["execution"]["outcome"] == "success"
    assert report["recovery"]["failure_observed"] is True
    assert report["recovery"]["recovered"] is True
    assert report["configuration"]["failure_type"] == "container_stop"


def test_build_benchmark_report_summary():
    experiments = [
        sample_experiment("exp-001", 1, "success", "completed", 4.0),
        sample_experiment("exp-002", 2, "success", "completed", 6.0),
        sample_experiment("exp-003", 3, "failure", "failed", 8.0),
    ]

    report = build_benchmark_report("group-001", experiments)

    assert report["report_type"] == "benchmark_group"
    assert report["summary"]["total_trials"] == 3
    assert report["summary"]["successful_trials"] == 2
    assert report["summary"]["failed_trials"] == 1
    assert report["summary"]["timed_out_trials"] == 0
    assert report["summary"]["success_rate"] == pytest.approx(66.67)
    assert report["summary"]["average_duration_seconds"] == 6.0


def test_benchmark_report_orders_trials():
    experiments = [
        sample_experiment("exp-003", 3),
        sample_experiment("exp-001", 1),
        sample_experiment("exp-002", 2),
    ]

    report = build_benchmark_report("group-001", experiments)

    trial_numbers = [
        trial["experiment"]["trial_number"]
        for trial in report["trials"]
    ]

    assert trial_numbers == [1, 2, 3]


def test_benchmark_report_empty_group_raises_error():
    with pytest.raises(ValueError, match="No experiments found"):
        build_benchmark_report("group-001", [])
