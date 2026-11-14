
import uuid

from typing import Optional


class BenchmarkRunner:
    def __init__(self, experiment_runner):
        self.experiment_runner = experiment_runner

    async def run(
        self,
        name: str,
        target_node: str,
        trials: int = 5,
        run_group_id: Optional[str] = None,
    ) -> dict:

        if not isinstance(trials, int) or isinstance(trials, bool):
            raise ValueError("trials must be an integer")

        if trials < 1 or trials > 20:
            raise ValueError("trials must be between 1 and 20")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Benchmark name cannot be empty")

        group_id = run_group_id or str(uuid.uuid4())
        results = []

        for trial_number in range(1, trials + 1):
            experiment = await self.experiment_runner.run(
                name=name.strip(),
                target_node=target_node,
                run_group_id=group_id,
                trial_number=trial_number,
            )

            results.append(experiment)

            # Stop if a trial fails or times out.
            if experiment["status"] != "completed":
                break

        successful = sum(
            1 for item in results
            if item["outcome"] == "success"
        )

        failed = sum(
            1 for item in results
            if item["status"] == "failed"
        )

        timed_out = sum(
            1 for item in results
            if item["status"] == "timed_out"
        )

        durations = [
            item["duration_seconds"]
            for item in results
            if item.get("duration_seconds") is not None
        ]

        total = len(results)

        return {
            "run_group_id": group_id,
            "name": name.strip(),
            "target_node": target_node,
            "requested_trials": trials,
            "executed_trials": total,
            "successful_trials": successful,
            "failed_trials": failed,
            "timed_out_trials": timed_out,
            "success_rate": (
                round((successful / total) * 100, 2)
                if total else 0
            ),
            "average_duration_seconds": (
                round(sum(durations) / len(durations), 4)
                if durations else None
            ),
            "stopped_early": total < trials,
            "trials": results,
        }
