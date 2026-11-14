
def build_experiment_report(experiment: dict) -> dict:
    result = experiment.get("result") or {}

    return {
        "report_type": "individual_experiment",
        "experiment": {
            "id": experiment["id"],
            "name": experiment["name"],
            "target_node": experiment["target_node"],
            "strategy": experiment["strategy"],
            "run_group_id": experiment.get("run_group_id"),
            "trial_number": experiment.get("trial_number"),
        },
        "execution": {
            "status": experiment["status"],
            "outcome": experiment.get("outcome"),
            "started_at": experiment["started_at"],
            "completed_at": experiment.get("completed_at"),
            "duration_seconds": experiment.get("duration_seconds"),
            "error": experiment.get("error"),
        },
        "recovery": {
            "failure_observed": result.get("failure_observed"),
            "recovered": result.get("recovered"),
            "final_node_status": result.get("final_node_status"),
            "recovery_strategy": result.get("recovery_strategy"),
        },
        "configuration": experiment.get("config") or {},
        "result": result,
    }


def build_benchmark_report(
    run_group_id: str,
    experiments: list,
) -> dict:

    if not experiments:
        raise ValueError("No experiments found for this benchmark group")

    successful = sum(
        1 for item in experiments
        if item.get("outcome") == "success"
    )

    failed = sum(
        1 for item in experiments
        if item.get("status") == "failed"
    )

    timed_out = sum(
        1 for item in experiments
        if item.get("status") == "timed_out"
    )

    durations = [
        item["duration_seconds"]
        for item in experiments
        if item.get("duration_seconds") is not None
    ]

    total = len(experiments)

    ordered_trials = sorted(
        experiments,
        key=lambda item: item.get("trial_number", 1)
    )

    return {
        "report_type": "benchmark_group",
        "run_group_id": run_group_id,
        "name": experiments[0]["name"],
        "target_node": experiments[0]["target_node"],
        "strategy": experiments[0]["strategy"],
        "summary": {
            "total_trials": total,
            "successful_trials": successful,
            "failed_trials": failed,
            "timed_out_trials": timed_out,
            "success_rate": round(
                successful / total * 100, 2
            ),
            "average_duration_seconds": (
                round(sum(durations) / len(durations), 4)
                if durations else None
            ),
        },
        "trials": [
            build_experiment_report(item)
            for item in ordered_trials
        ],
    }
