import pytest

from app.recovery.manager import RecoveryManager
from app.recovery.state import RecoveryState
from app.recovery.circuit_breaker import CircuitState


def test_register_recovery_state():
    manager = RecoveryManager()

    state = RecoveryState(
        item_id="node-1",
        item_type="node"
    )

    manager.register(state)

    assert manager.get_state("node-1") == state
    assert manager.get_breaker("node-1") is not None


def test_default_strategy_is_fixed_retry():
    manager = RecoveryManager()

    manager.register(
        RecoveryState("node-1", "node")
    )

    strategy = manager.get_strategy("node-1")

    assert strategy is manager.strategies["fixed_retry"]


def test_configure_exponential_backoff():
    manager = RecoveryManager()

    manager.register(
        RecoveryState("node-1", "node")
    )

    manager.configure_strategy(
        "node-1",
        "exponential_backoff"
    )

    assert manager.get_state("node-1").strategy == "exponential_backoff"
    assert manager.get_strategy("node-1") is manager.strategies[
        "exponential_backoff"
    ]


def test_reject_unknown_strategy():
    manager = RecoveryManager()

    manager.register(
        RecoveryState("node-1", "node")
    )

    with pytest.raises(ValueError):
        manager.configure_strategy("node-1", "unknown")


def test_reject_unknown_recovery_item():
    manager = RecoveryManager()

    with pytest.raises(KeyError):
        manager.get_strategy("unknown-node")


def test_register_restores_open_circuit():
    manager = RecoveryManager()

    state = RecoveryState(
        item_id="node-1",
        item_type="node",
        circuit_state="open",
        consecutive_failures=3,
        circuit_opened_at=1000.0
    )

    manager.register(state)

    breaker = manager.get_breaker("node-1")

    assert breaker.state == CircuitState.OPEN
    assert breaker.failure_count == 3
    assert breaker.opened_at == 1000.0


def test_fixed_retry_scheduling():
    current_time = [1000.0]
    manager = RecoveryManager(clock=lambda: current_time[0])

    state = RecoveryState("node-1", "node")
    manager.register(state)

    next_retry = manager.schedule_retry("node-1")

    assert next_retry == 1002.0
    assert state.retry_count == 1
    assert state.consecutive_failures == 0

    # Scheduling is not an actual recovery attempt.
    assert state.last_attempt_at is None

    current_time[0] = 1002.0

    assert manager.can_attempt_recovery("node-1") is True
    assert state.last_attempt_at == 1002.0


def test_schedule_retry_is_idempotent():
    current_time = [1000.0]
    manager = RecoveryManager(clock=lambda: current_time[0])

    state = RecoveryState("node-1", "node")
    manager.register(state)

    first_schedule = manager.schedule_retry("node-1")
    second_schedule = manager.schedule_retry("node-1")

    assert first_schedule == second_schedule == 1002.0
    assert state.retry_count == 1



def test_exponential_backoff_scheduling():
    current_time = [1000.0]
    manager = RecoveryManager(clock=lambda: current_time[0])

    state = RecoveryState(
        "node-1", "node",
        strategy="exponential_backoff",
        retry_count=2,
    )
    manager.register(state)

    next_retry = manager.schedule_retry("node-1")

    assert next_retry == 1008.0
    assert state.retry_count == 3


def test_retry_due_check():
    current_time = [1000.0]
    manager = RecoveryManager(clock=lambda: current_time[0])

    manager.register(RecoveryState("node-1", "node"))
    manager.schedule_retry("node-1")

    assert manager.is_retry_due("node-1") is False

    current_time[0] = 1002.0

    assert manager.is_retry_due("node-1") is True


def test_retry_stops_at_maximum_attempts():
    manager = RecoveryManager(clock=lambda: 1000.0)

    state = RecoveryState(
        "node-1", "node",
        retry_count=5,
    )
    manager.register(state)

    assert manager.schedule_retry("node-1") is None
    assert state.next_retry_at is None


def test_unknown_item_cannot_be_scheduled():
    manager = RecoveryManager()

    with pytest.raises(KeyError):
        manager.schedule_retry("unknown-node")

def test_record_success_resets_recovery_state():
    manager = RecoveryManager(clock=lambda: 2000.0)

    state = RecoveryState(
        "node-1",
        "node",
        retry_count=3,
        consecutive_failures=3,
        circuit_state="open",
        circuit_opened_at=1000.0,
    )

    manager.register(state)
    manager.record_success("node-1")

    assert state.retry_count == 0
    assert state.consecutive_failures == 0
    assert state.next_retry_at is None
    assert state.circuit_state == "closed"
    assert manager.get_breaker("node-1").state == CircuitState.CLOSED


def test_record_failure_updates_circuit_state():
    manager = RecoveryManager(clock=lambda: 2000.0)

    state = RecoveryState(
        "node-1",
        "node",
        consecutive_failures=2,
    )

    manager.register(state)
    manager.record_failure("node-1")

    assert state.consecutive_failures == 3
    assert state.circuit_state == "open"
    assert state.circuit_opened_at == 2000.0


def test_get_all_states_returns_registered_states():
    manager = RecoveryManager()

    first = RecoveryState("node-1", "node")
    second = RecoveryState("node-2", "node")

    manager.register(first)
    manager.register(second)

    states = manager.get_all_states()

    assert len(states) == 2
    assert first in states
    assert second in states


def test_record_success_rejects_unknown_item():
    manager = RecoveryManager()

    with pytest.raises(KeyError):
        manager.record_success("unknown-node")


def test_record_failure_rejects_unknown_item():
    manager = RecoveryManager()

    with pytest.raises(KeyError):
        manager.record_failure("unknown-node")


def test_exhausted_retries_schedule_circuit_probe_after_cooldown():
    current_time = [1000.0]
    manager = RecoveryManager(clock=lambda: current_time[0])

    state = RecoveryState(
        "node-1",
        "node",
        retry_count=5,
        consecutive_failures=3,
        circuit_state="open",
        circuit_opened_at=1000.0,
    )
    manager.register(state)

    next_retry = manager.schedule_retry("node-1")

    assert next_retry == 1030.0
    assert state.retry_count == 5

    current_time[0] = 1029.0
    assert manager.can_attempt_recovery("node-1") is False

    current_time[0] = 1030.0
    assert manager.can_attempt_recovery("node-1") is True
    assert state.circuit_state == "half_open"
    assert state.retry_count == 0


def test_failed_half_open_probe_starts_new_retry_cycle():
    current_time = [1000.0]
    manager = RecoveryManager(clock=lambda: current_time[0])

    state = RecoveryState(
        "node-1",
        "node",
        retry_count=5,
        consecutive_failures=3,
        circuit_state="open",
        circuit_opened_at=1000.0,
    )
    manager.register(state)

    manager.schedule_retry("node-1")

    current_time[0] = 1030.0
    assert manager.can_attempt_recovery("node-1") is True

    manager.record_failure("node-1")

    assert state.circuit_state == "open"
    assert state.retry_count == 0

    next_retry = manager.schedule_retry("node-1")

    assert next_retry == 1060.0
    assert state.next_retry_at == 1060.0
    assert state.retry_count == 0
    assert state.consecutive_failures == 4
    assert state.circuit_state == "open"
    assert state.next_retry_at == 1060.0


def test_successful_half_open_probe_resets_recovery_cycle():
    current_time = [1000.0]
    manager = RecoveryManager(clock=lambda: current_time[0])

    state = RecoveryState(
        "node-1",
        "node",
        retry_count=5,
        consecutive_failures=3,
        circuit_state="open",
        circuit_opened_at=1000.0,
    )
    manager.register(state)

    manager.schedule_retry("node-1")

    current_time[0] = 1030.0
    assert manager.can_attempt_recovery("node-1") is True

    manager.record_success("node-1")

    assert state.retry_count == 0
    assert state.consecutive_failures == 0
    assert state.circuit_state == "closed"
    assert state.next_retry_at is None
