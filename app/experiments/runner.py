
import asyncio
import time
import uuid
from typing import Awaitable, Callable, Optional


class ExperimentRunner:
    def __init__(
        self,
        repository,
        recovery_manager,
        inject_failure: Callable[[str], Awaitable[dict]],
        get_node_status: Callable[[str], str],
        recovery_timeout: float = 90.0,
        poll_interval: float = 1.0,
    ):
        if recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be positive")

        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")

        self.repository = repository
        self.recovery_manager = recovery_manager
        self.inject_failure = inject_failure
        self.get_node_status = get_node_status
        self.recovery_timeout = recovery_timeout
        self.poll_interval = poll_interval

        # Prevent concurrent experiments in the same event loop.
        self._running = False

    async def run(
        self,
        name: str,
        target_node: str,
        run_group_id: Optional[str] = None,
        trial_number: int = 1,
    ) -> dict:

        if target_node not in self.recovery_manager.states:
            raise ValueError(f"Unknown recovery node: {target_node}")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Experiment name cannot be empty")

        if not isinstance(trial_number, int) or isinstance(trial_number, bool) or trial_number < 1:
            raise ValueError("trial_number must be a positive integer")

        # No await occurs between this check and assignment.
        if self._running:
            raise RuntimeError("Another experiment is already running")

        self._running = True

        try:
            return await self._execute(
                name,
                target_node,
                run_group_id,
                trial_number,
            )
        finally:
            self._running = False

    async def _execute(
        self,
        name: str,
        target_node: str,
        run_group_id: Optional[str],
        trial_number: int,
    ) -> dict:

        experiment_id = str(uuid.uuid4())
        started_at = time.time()
        started_clock = time.perf_counter()

        recovery_state = self.recovery_manager.get_state(target_node)
        strategy = recovery_state.strategy

        # Verify the node is healthy before creating an experiment.
        initial_status = await asyncio.to_thread(
            self.get_node_status,
            target_node,
        )

        if initial_status != "healthy":
            raise RuntimeError(
                f"Node must be healthy before experiment starts. "
                f"Current status: {initial_status}"
            )

        experiment = {
            "id": experiment_id,
            "run_group_id": run_group_id,
            "trial_number": trial_number,
            "name": name.strip(),
            "target_node": target_node,
            "strategy": strategy,
            "status": "running",
            "started_at": started_at,
            "config": {
                "recovery_timeout": self.recovery_timeout,
                "poll_interval": self.poll_interval,
            },
            "result": {},
        }

        await asyncio.to_thread(
            self.repository.create,
            experiment,
        )

        try:
            injection_result = await self.inject_failure(target_node)

            if (
                not isinstance(injection_result, dict)
                or injection_result.get("status") != "failed"
            ):
                raise RuntimeError(
                    "Failure injection did not confirm node failure"
                )

            deadline = time.perf_counter() + self.recovery_timeout
            failure_observed = False

            while time.perf_counter() < deadline:
                status = await asyncio.to_thread(
                    self.get_node_status,
                    target_node,
                )

                # Confirm that the node actually entered failed state.
                if status == "failed":
                    failure_observed = True

                # Success requires an observed failure followed by recovery.
                if failure_observed and status == "healthy":
                    duration = time.perf_counter() - started_clock

                    result = {
                        "recovered": True,
                        "failure_observed": True,
                        "final_node_status": status,
                        "recovery_strategy": strategy,
                    }

                    await asyncio.to_thread(
                        self.repository.update,
                        experiment_id,
                        {
                            "status": "completed",
                            "completed_at": time.time(),
                            "duration_seconds": duration,
                            "outcome": "success",
                            "result": result,
                        },
                    )

                    return await asyncio.to_thread(
                        self.repository.get,
                        experiment_id,
                    )

                remaining = deadline - time.perf_counter()

                if remaining > 0:
                    await asyncio.sleep(
                        min(self.poll_interval, remaining)
                    )

            duration = time.perf_counter() - started_clock

            await asyncio.to_thread(
                self.repository.update,
                experiment_id,
                {
                    "status": "timed_out",
                    "completed_at": time.time(),
                    "duration_seconds": duration,
                    "outcome": "timeout",
                    "error": (
                        "Node did not complete failure-to-recovery "
                        "transition within the configured timeout"
                    ),
                    "result": {
                        "recovered": False,
                        "failure_observed": failure_observed,
                        "recovery_strategy": strategy,
                    },
                },
            )
        except asyncio.CancelledError:
            duration = time.perf_counter() - started_clock

            await asyncio.to_thread(
                self.repository.update,
                experiment_id,
                {
                    "status": "failed",
                    "completed_at": time.time(),
                    "duration_seconds": duration,
                    "outcome": "cancelled",
                    "error": "Experiment was cancelled",
                    "result": {
                        "recovered": False,
                        "recovery_strategy": strategy,
                    },
                },
            )
            raise
        except Exception as error:
            duration = time.perf_counter() - started_clock

            await asyncio.to_thread(
                self.repository.update,
                experiment_id,
                {
                    "status": "failed",
                    "completed_at": time.time(),
                    "duration_seconds": duration,
                    "outcome": "failure",
                    "error": str(error),
                    "result": {
                        "recovered": False,
                        "recovery_strategy": strategy,
                    },
                },
            )

        return await asyncio.to_thread(
            self.repository.get,
            experiment_id,
        )
