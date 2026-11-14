
from typing import Awaitable, Callable


RecoveryCallback = Callable[[], Awaitable[bool]]


class RecoveryExecutor:
    """
    Executes exactly one recovery attempt.

    Retry scheduling, retry limits and circuit-breaker
    authorization belong to RecoveryManager.
    """

    async def execute(
        self,
        recovery_callback: RecoveryCallback,
    ) -> bool:
        """
        Execute one recovery callback.

        Exceptions intentionally propagate to the caller,
        which owns failure recording and retry scheduling.
        """
        return await recovery_callback()
