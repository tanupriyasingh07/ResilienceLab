
import app.main as main
from app.experiments.repository import ExperimentRepository


def setup_repository(tmp_path):
    main.DB = str(tmp_path / "repository_test.db")
    main.init_db()
    return ExperimentRepository(main.DB)


def sample_experiment():
    return {
        "id": "exp-001",
        "run_group_id": "group-001",
        "trial_number": 1,
        "name": "Node Recovery Test",
        "target_node": "node-1",
        "strategy": "fixed_retry",
        "status": "running",
        "started_at": 1000.0,
        "config": {"failure_type": "container_stop"},
        "result": {}
    }


def test_create_and_get_experiment(tmp_path):
    repo = setup_repository(tmp_path)
    experiment = sample_experiment()

    repo.create(experiment)
    result = repo.get("exp-001")

    assert result is not None
    assert result["id"] == "exp-001"
    assert result["target_node"] == "node-1"
    assert result["config"]["failure_type"] == "container_stop"


def test_update_experiment(tmp_path):
    repo = setup_repository(tmp_path)
    repo.create(sample_experiment())

    updated = repo.update("exp-001", {
        "status": "completed",
        "completed_at": 1010.0,
        "duration_seconds": 10.0,
        "outcome": "success",
        "result": {"recovery_attempts": 1}
    })

    result = repo.get("exp-001")

    assert updated is True
    assert result["status"] == "completed"
    assert result["duration_seconds"] == 10.0
    assert result["outcome"] == "success"
    assert result["result"]["recovery_attempts"] == 1


def test_update_missing_experiment_returns_false(tmp_path):
    repo = setup_repository(tmp_path)

    assert repo.update("missing-id", {
        "status": "failed"
    }) is False


def test_list_experiments(tmp_path):
    repo = setup_repository(tmp_path)

    first = sample_experiment()
    second = sample_experiment()
    second["id"] = "exp-002"
    second["started_at"] = 2000.0

    repo.create(first)
    repo.create(second)

    results = repo.list_all()

    assert len(results) == 2
    assert results[0]["id"] == "exp-002"
    assert results[1]["id"] == "exp-001"


def test_list_experiments_pagination(tmp_path):
    repo = setup_repository(tmp_path)

    for number in range(3):
        experiment = sample_experiment()
        experiment["id"] = f"exp-{number}"
        experiment["started_at"] = 1000.0 + number
        repo.create(experiment)

    results = repo.list_all(limit=1, offset=1)

    assert len(results) == 1
    assert results[0]["id"] == "exp-1"


def test_get_missing_experiment_returns_none(tmp_path):
    repo = setup_repository(tmp_path)

    assert repo.get("missing-id") is None

def test_list_by_group_returns_only_matching_experiments(tmp_path):
    repo = setup_repository(tmp_path)

    first = sample_experiment()
    second = sample_experiment()
    second["id"] = "exp-002"
    second["trial_number"] = 2

    third = sample_experiment()
    third["id"] = "exp-003"
    third["run_group_id"] = "group-002"

    repo.create(first)
    repo.create(second)
    repo.create(third)

    results = repo.list_by_group("group-001")

    assert len(results) == 2
    assert [item["id"] for item in results] == ["exp-001", "exp-002"]


def test_list_by_group_returns_empty_for_unknown_group(tmp_path):
    repo = setup_repository(tmp_path)

    results = repo.list_by_group("unknown-group")

    assert results == []
