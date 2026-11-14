from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RecoveryContext:
    retry_count: int = 0
    max_retries: int = 5
    base_delay: float = 2.0
    max_delay: float = 60.0


class RecoveryStrategy(ABC):

    @abstractmethod
    def get_delay(self, context: RecoveryContext) -> float:
        pass

    @abstractmethod
    def should_retry(self, context: RecoveryContext) -> bool:
        pass


class FixedRetryStrategy(RecoveryStrategy):

    def get_delay(self, context: RecoveryContext) -> float:
        return context.base_delay

    def should_retry(self, context: RecoveryContext) -> bool:
        return context.retry_count < context.max_retries


class ExponentialBackoffStrategy(RecoveryStrategy):

    def get_delay(self, context: RecoveryContext) -> float:
        delay = context.base_delay * (2 ** context.retry_count)
        return min(delay, context.max_delay)

    def should_retry(self, context: RecoveryContext) -> bool:
        return context.retry_count < context.max_retries