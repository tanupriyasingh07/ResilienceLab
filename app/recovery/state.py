from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class RecoveryState:
    item_id: str
    item_type: str
    strategy: str = "fixed_retry"
    retry_count: int = 0
    last_attempt_at: Optional[float] = None
    next_retry_at: Optional[float] = None
    consecutive_failures: int = 0
    circuit_state: str = "closed"
    circuit_opened_at: Optional[float] = None

    def to_record(self) -> dict:
        return asdict(self)

    @classmethod
    def from_record(cls, record: dict):
        return cls(
            item_id=record["item_id"],
            item_type=record["item_type"],
            strategy=record["strategy"],
            retry_count=record["retry_count"],
            last_attempt_at=record["last_attempt_at"],
            next_retry_at=record["next_retry_at"],
            consecutive_failures=record["consecutive_failures"],
            circuit_state=record["circuit_state"],
            circuit_opened_at=record["circuit_opened_at"],
        )