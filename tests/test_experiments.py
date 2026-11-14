import sqlite3


def test_experiment_table_created(client, monkeypatch, tmp_path):
    import app.main as main

    monkeypatch.setattr(
        main, "DB", str(tmp_path / "experiments.db")
    )

    main.init_db()

    with sqlite3.connect(main.DB) as conn:
        columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(experiments)"
            ).fetchall()
        }

    expected = {
        "id", "run_group_id", "trial_number", "name",
        "target_node", "strategy", "status", "started_at",
        "completed_at", "duration_seconds", "outcome",
        "error", "config_json", "result_json",
    }

    assert expected.issubset(columns)


def test_experiment_schema_initialization_is_idempotent(
    client, monkeypatch, tmp_path
):
    import app.main as main

    monkeypatch.setattr(
        main, "DB", str(tmp_path / "idempotent.db")
    )

    main.init_db()
    main.init_db()

    with sqlite3.connect(main.DB) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

    assert "experiments" in tables
    assert "recovery_state" in tables
    assert "system_state" in tables