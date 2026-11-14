
import asyncio
import pytest

from app.recovery.executor import RecoveryExecutor


def test_executor_executes_one_successful_attempt():
    async def run_test():
        attempts = 0

        async def recovery():
            nonlocal attempts
            attempts += 1
            return True

        executor = RecoveryExecutor()
        result = await executor.execute(recovery)

        assert result is True
        assert attempts == 1

    asyncio.run(run_test())


def test_executor_executes_only_one_failed_attempt():
    async def run_test():
        attempts = 0

        async def recovery():
            nonlocal attempts
            attempts += 1
            return False

        executor = RecoveryExecutor()
        result = await executor.execute(recovery)

        assert result is False
        assert attempts == 1

    asyncio.run(run_test())


def test_executor_propagates_recovery_exception():
    async def run_test():
        async def recovery():
            raise RuntimeError("Recovery failed")

        executor = RecoveryExecutor()

        with pytest.raises(RuntimeError, match="Recovery failed"):
            await executor.execute(recovery)

    asyncio.run(run_test())


def test_executor_does_not_retry_after_failure():
    async def run_test():
        attempts = 0

        async def recovery():
            nonlocal attempts
            attempts += 1
            return False

        executor = RecoveryExecutor()

        await executor.execute(recovery)

        assert attempts == 1

    asyncio.run(run_test())
