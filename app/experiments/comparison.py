
def compare_experiments(experiments: list) -> dict:
    if len(experiments) < 2 or len(experiments) > 10:
        raise ValueError(
            "Comparison requires between 2 and 10 experiments"
        )

    successful = sum(
        1 for item in experiments
        if item.get("outcome") == "success"
    )

    durations = [
        item["duration_seconds"]
        for item in experiments
        if item.get("duration_seconds") is not None
    ]

    comparisons = []

    for item in experiments:
        comparisons.append({
            "id": item["id"],
            "name": item["name"],
            "run_group_id": item.get("run_group_id"),
            "trial_number": item.get("trial_number"),
            "target_node": item["target_node"],
            "strategy": item["strategy"],
            "status": item["status"],
            "outcome": item.get("outcome"),
            "duration_seconds": item.get("duration_seconds"),
            "error": item.get("error"),
        })

    return {
        "total_experiments": len(experiments),
        "successful_experiments": successful,
        "failed_experiments": sum(
            1 for item in experiments
            if item.get("status") == "failed"
        ),
        "timed_out_experiments": sum(
            1 for item in experiments
            if item.get("status") == "timed_out"
        ),
        "success_rate": round(
            successful / len(experiments) * 100, 2
        ),
        "average_duration_seconds": (
            round(sum(durations) / len(durations), 4)
            if durations else None
        ),
        "experiments": comparisons,
    }
