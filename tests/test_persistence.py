from app.recovery.state import RecoveryState
from app.recovery.manager import RecoveryManager

def test_state_persists_after_reload(client, monkeypatch, tmp_path):
    import app.main as main

    # Use an isolated temporary database
    monkeypatch.setattr(
        main,
        "DB",
        str(tmp_path / "persistence_test.db")
    )

    main.init_db()

    # Set a known state
    main.nodes["node-1"]["status"] = "failed"
    main.nodes["node-1"]["restarts"] = 4
    main.nodes["node-1"]["requests"] = 25
    main.nodes["node-1"]["failed_at"] = 12345.0

    # Persist state
    main.save_states()

    # Simulate application state being reset
    main.nodes["node-1"]["status"] = "healthy"
    main.nodes["node-1"]["restarts"] = 0
    main.nodes["node-1"]["requests"] = 0
    main.nodes["node-1"]["failed_at"] = None

    # Reload persisted state
    main.load_states()

    # Verify restoration
    assert main.nodes["node-1"]["status"] == "failed"
    assert main.nodes["node-1"]["restarts"] == 4
    assert main.nodes["node-1"]["requests"] == 25
    assert main.nodes["node-1"]["failed_at"] == 12345.0



def test_load_states_ignores_unknown_item_type(client, monkeypatch, tmp_path):
    import sqlite3
    import app.main as main

    monkeypatch.setattr(
        main,
        "DB",
        str(tmp_path / "invalid_state_test.db")
    )

    main.init_db()

    with sqlite3.connect(main.DB) as conn:
        conn.execute("""
            INSERT INTO system_state
            (item_id, item_type, status, restarts, requests, failed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "unknown-item",
            "invalid_type",
            "failed",
            10,
            50,
            12345.0
        ))

    main.load_states()

    assert "unknown-item" not in main.services
    assert "unknown-item" not in main.nodes

def test_recovery_state_persists_after_reload(
    client, monkeypatch, tmp_path
):
    import app.main as main

    monkeypatch.setattr(
        main,
        "DB",
        str(tmp_path / "recovery_state_test.db")
    )

    main.init_db()

    state = {
        "strategy": "exponential_backoff",
        "retry_count": 3,
        "last_attempt_at": 1000.0,
        "next_retry_at": 1060.0,
        "consecutive_failures": 3,
        "circuit_state": "open",
        "circuit_opened_at": 1000.0
    }

    main.save_recovery_state(
        "node-1",
        "node",
        state
    )

    restored = main.load_recovery_state("node-1")

    assert restored is not None
    assert restored["item_id"] == "node-1"
    assert restored["item_type"] == "node"
    assert restored["strategy"] == "exponential_backoff"
    assert restored["retry_count"] == 3
    assert restored["last_attempt_at"] == 1000.0
    assert restored["next_retry_at"] == 1060.0
    assert restored["consecutive_failures"] == 3
    assert restored["circuit_state"] == "open"
    assert restored["circuit_opened_at"] == 1000.0
    assert restored["updated_at"] is not None


def test_load_recovery_state_returns_none_when_missing(
    client, monkeypatch, tmp_path
):
    import app.main as main

    monkeypatch.setattr(
        main,
        "DB",
        str(tmp_path / "empty_recovery_state_test.db")
    )

    main.init_db()

    result = main.load_recovery_state("unknown-node")

    assert result is None

def test_reset_recovery_state(client, monkeypatch, tmp_path):
    import app.main as main

    monkeypatch.setattr(
        main,
        "DB",
        str(tmp_path / "reset_recovery_test.db")
    )

    main.init_db()

    state = {
        "strategy": "exponential_backoff",
        "retry_count": 3,
        "last_attempt_at": 1000.0,
        "next_retry_at": 1060.0,
        "consecutive_failures": 3,
        "circuit_state": "open",
        "circuit_opened_at": 1000.0
    }

    main.save_recovery_state("node-1", "node", state)

    main.reset_recovery_state("node-1")

    assert main.load_recovery_state("node-1") is None

def test_get_recovery_state_returns_typed_object(client, monkeypatch, tmp_path):
    import app.main as main

    monkeypatch.setattr(
        main, "DB", str(tmp_path / "typed_state.db")
    )
    main.init_db()

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

    main.save_recovery_state(
        state.item_id, state.item_type, state.to_record()
    )

    restored = main.get_recovery_state("node-1")

    assert isinstance(restored, RecoveryState)
    assert restored == state


def test_get_recovery_state_returns_none_when_missing(
    client, monkeypatch, tmp_path
):
    import app.main as main

    monkeypatch.setattr(
        main, "DB", str(tmp_path / "missing_state.db")
    )
    main.init_db()

    assert main.get_recovery_state("unknown-node") is None

def test_recovery_manager_persists_state_to_database(
    client, monkeypatch, tmp_path
):
    import app.main as main

    monkeypatch.setattr(
        main, "DB", str(tmp_path / "manager_state.db")
    )
    main.init_db()

    manager = RecoveryManager(clock=lambda: 1000.0)

    state = RecoveryState(
        item_id="node-1",
        item_type="node",
        strategy="exponential_backoff",
        retry_count=2,
        consecutive_failures=2,
    )

    manager.register(state)
    manager.schedule_retry("node-1")

    main.persist_recovery_manager(manager)

    restored = main.get_recovery_state("node-1")

    assert restored == state
    assert restored.retry_count == 3
    assert restored.next_retry_at == 1008.0

def test_load_recovery_manager_restores_saved_states(
    client, monkeypatch, tmp_path
):
    import app.main as main

    monkeypatch.setattr(
        main, "DB", str(tmp_path / "restore_manager.db")
    )
    main.init_db()

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

    main.save_recovery_state(
        state.item_id,
        state.item_type,
        state.to_record()
    )

    manager = main.load_recovery_manager()

    restored = manager.get_state("node-1")
    breaker = manager.get_breaker("node-1")

    assert restored == state
    assert restored.strategy == "exponential_backoff"
    assert restored.retry_count == 3
    assert breaker.state.value == "open"
    assert breaker.failure_count == 3
    assert breaker.opened_at == 1000.0
