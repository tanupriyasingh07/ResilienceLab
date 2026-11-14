import pytest

from app.recovery.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
)


def test_circuit_starts_closed():
    breaker = CircuitBreaker()

    assert breaker.state == CircuitState.CLOSED
    assert breaker.allow_request() is True


def test_circuit_opens_after_failure_threshold():
    breaker = CircuitBreaker(failure_threshold=3)

    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state == CircuitState.CLOSED

    breaker.record_failure()

    assert breaker.state == CircuitState.OPEN
    assert breaker.allow_request() is False


def test_open_circuit_transitions_to_half_open():
    current_time = [100.0]

    breaker = CircuitBreaker(
        failure_threshold=2,
        reset_timeout=10,
        clock=lambda: current_time[0],
    )

    breaker.record_failure()
    breaker.record_failure()

    current_time[0] = 111.0

    assert breaker.allow_request() is True
    assert breaker.state == CircuitState.HALF_OPEN


def test_half_open_allows_only_one_probe():
    current_time = [100.0]

    breaker = CircuitBreaker(
        failure_threshold=1,
        reset_timeout=5,
        clock=lambda: current_time[0],
    )

    breaker.record_failure()
    current_time[0] = 106.0

    assert breaker.allow_request() is True
    assert breaker.allow_request() is False


def test_half_open_success_closes_circuit():
    current_time = [100.0]

    breaker = CircuitBreaker(
        failure_threshold=1,
        reset_timeout=5,
        clock=lambda: current_time[0],
    )

    breaker.record_failure()
    current_time[0] = 106.0
    breaker.allow_request()

    breaker.record_success()

    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0
    assert breaker.allow_request() is True


def test_half_open_failure_reopens_circuit():
    current_time = [100.0]

    breaker = CircuitBreaker(
        failure_threshold=1,
        reset_timeout=5,
        clock=lambda: current_time[0],
    )

    breaker.record_failure()
    current_time[0] = 106.0
    breaker.allow_request()

    breaker.record_failure()

    assert breaker.state == CircuitState.OPEN
    assert breaker.allow_request() is False


def test_invalid_configuration():
    with pytest.raises(ValueError):
        CircuitBreaker(failure_threshold=0)

    with pytest.raises(ValueError):
        CircuitBreaker(reset_timeout=0)

from concurrent.futures import ThreadPoolExecutor


def test_half_open_allows_only_one_concurrent_probe():
    current_time = [100.0]

    breaker = CircuitBreaker(
        failure_threshold=1,
        reset_timeout=5,
        clock=lambda: current_time[0],
    )

    breaker.record_failure()
    current_time[0] = 106.0

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(
            executor.map(
                lambda _: breaker.allow_request(),
                range(20),
            )
        )

    assert sum(results) == 1
    assert breaker.state == CircuitState.HALF_OPEN