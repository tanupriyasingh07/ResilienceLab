import pytest

from app.recovery.strategies import (
    RecoveryContext,
    FixedRetryStrategy,
    ExponentialBackoffStrategy,
)


def test_fixed_retry_delay():
    strategy = FixedRetryStrategy()
    context = RecoveryContext(retry_count=2, base_delay=3)

    assert strategy.get_delay(context) == 3


def test_exponential_backoff_delay():
    strategy = ExponentialBackoffStrategy()
    context = RecoveryContext(retry_count=3, base_delay=2)

    assert strategy.get_delay(context) == 16


def test_exponential_backoff_respects_max_delay():
    strategy = ExponentialBackoffStrategy()
    context = RecoveryContext(
        retry_count=5,
        base_delay=2,
        max_delay=20,
    )

    assert strategy.get_delay(context) == 20


@pytest.mark.parametrize("strategy", [
    FixedRetryStrategy(),
    ExponentialBackoffStrategy(),
])
def test_retry_stops_at_max_retries(strategy):
    context = RecoveryContext(retry_count=5, max_retries=5)

    assert strategy.should_retry(context) is False


@pytest.mark.parametrize("strategy", [
    FixedRetryStrategy(),
    ExponentialBackoffStrategy(),
])
def test_retry_allowed_before_max_retries(strategy):
    context = RecoveryContext(retry_count=2, max_retries=5)

    assert strategy.should_retry(context) is True