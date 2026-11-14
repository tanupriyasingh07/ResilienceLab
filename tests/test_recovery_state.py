from app.recovery.state import RecoveryState


def test_recovery_state_default_values():
    state = RecoveryState(
        item_id="node-1",
        item_type="node"
    )

    assert state.strategy == "fixed_retry"
    assert state.retry_count == 0
    assert state.consecutive_failures == 0
    assert state.circuit_state == "closed"
    assert state.last_attempt_at is None
    assert state.next_retry_at is None
    assert state.circuit_opened_at is None


def test_recovery_state_custom_values():
    state = RecoveryState(
        item_id="node-2",
        item_type="node",
        strategy="exponential_backoff",
        retry_count=3,
        consecutive_failures=3,
        circuit_state="open",
        last_attempt_at=1000.0,
        next_retry_at=1060.0,
        circuit_opened_at=1000.0
    )

    assert state.retry_count == 3
    assert state.strategy == "exponential_backoff"
    assert state.circuit_state == "open"
    assert state.next_retry_at == 1060.0


def test_recovery_state_is_independent():
    first = RecoveryState("node-1", "node")
    second = RecoveryState("node-2", "node")

    first.retry_count = 3

    assert second.retry_count == 0

def test_recovery_state_to_record():
    state = RecoveryState(
        item_id="node-1",
        item_type="node",
        strategy="exponential_backoff",
        retry_count=3,
        consecutive_failures=3,
        circuit_state="open",
        last_attempt_at=1000.0,
        next_retry_at=1060.0,
        circuit_opened_at=1000.0,
    )

    record = state.to_record()

    assert record["item_id"] == "node-1"
    assert record["strategy"] == "exponential_backoff"
    assert record["retry_count"] == 3
    assert record["circuit_state"] == "open"


def test_recovery_state_from_record():
    record = {
        "item_id": "node-2",
        "item_type": "node",
        "strategy": "fixed_retry",
        "retry_count": 2,
        "last_attempt_at": 100.0,
        "next_retry_at": 105.0,
        "consecutive_failures": 2,
        "circuit_state": "closed",
        "circuit_opened_at": None,
    }

    state = RecoveryState.from_record(record)

    assert state.item_id == "node-2"
    assert state.retry_count == 2
    assert state.next_retry_at == 105.0


def test_recovery_state_serialization_round_trip():
    original = RecoveryState(
        item_id="node-3",
        item_type="node",
        strategy="exponential_backoff",
        retry_count=4,
        consecutive_failures=4,
        circuit_state="open",
        last_attempt_at=200.0,
        next_retry_at=230.0,
        circuit_opened_at=200.0,
    )

    restored = RecoveryState.from_record(original.to_record())

    assert restored == original