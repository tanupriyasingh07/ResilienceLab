
import json
import sqlite3
from typing import Optional


class ExperimentRepository:
    def __init__(self, database_path: str):
        self.database_path = database_path

    def create(self, experiment: dict) -> None:
        with sqlite3.connect(
            self.database_path,
            timeout=10
        ) as conn:
            conn.execute("""
                INSERT INTO experiments (
                    id,
                    run_group_id,
                    trial_number,
                    name,
                    target_node,
                    strategy,
                    status,
                    started_at,
                    config_json,
                    result_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment["id"],
                experiment.get("run_group_id"),
                experiment.get("trial_number", 1),
                experiment["name"],
                experiment["target_node"],
                experiment["strategy"],
                experiment.get("status", "running"),
                experiment["started_at"],
                json.dumps(experiment.get("config", {})),
                json.dumps(experiment.get("result", {}))
            ))

    def update(
        self,
        experiment_id: str,
        updates: dict
    ) -> bool:
        allowed_fields = {
            "status",
            "completed_at",
            "duration_seconds",
            "outcome",
            "error",
            "result_json"
        }

        fields = {
            key: value
            for key, value in updates.items()
            if key in allowed_fields
        }

        if not fields:
            return False

        if "result" in updates:
            fields["result_json"] = json.dumps(
                updates["result"]
            )

        assignments = ", ".join(
            f"{field} = ?" for field in fields
        )

        values = list(fields.values())
        values.append(experiment_id)

        with sqlite3.connect(
            self.database_path,
            timeout=10
        ) as conn:
            cursor = conn.execute(
                f"""
                UPDATE experiments
                SET {assignments}
                WHERE id = ?
                """,
                values
            )

            return cursor.rowcount > 0

    def get(self, experiment_id: str) -> Optional[dict]:
        with sqlite3.connect(
            self.database_path,
            timeout=10
        ) as conn:
            conn.row_factory = sqlite3.Row

            row = conn.execute("""
                SELECT *
                FROM experiments
                WHERE id = ?
            """, (experiment_id,)).fetchone()

        return self._deserialize(row) if row else None

    def list_all(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        with sqlite3.connect(
            self.database_path,
            timeout=10
        ) as conn:
            conn.row_factory = sqlite3.Row

            rows = conn.execute("""
                SELECT *
                FROM experiments
                ORDER BY started_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset)).fetchall()

        return [
            self._deserialize(row)
            for row in rows
        ]


    def list_by_group(self, run_group_id: str) -> list:
        with sqlite3.connect(
            self.database_path,
            timeout=10
        ) as conn:
            conn.row_factory = sqlite3.Row

            rows = conn.execute("""
                SELECT *
                FROM experiments
                WHERE run_group_id = ?
                ORDER BY trial_number ASC, started_at ASC
            """, (run_group_id,)).fetchall()

        return [
            self._deserialize(row)
            for row in rows
        ]


    @staticmethod
    def _deserialize(row) -> dict:
        experiment = dict(row)

        experiment["config"] = json.loads(
            experiment.pop("config_json")
        )

        experiment["result"] = json.loads(
            experiment.pop("result_json")
        )

        return experiment
