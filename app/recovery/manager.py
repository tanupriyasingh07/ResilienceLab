
import time

from app.recovery.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
)
from app.recovery.state import RecoveryState
from app.recovery.strategies import (
    FixedRetryStrategy,
    ExponentialBackoffStrategy,
    RecoveryContext,
)


class RecoveryManager:
    """
    Owns authoritative recovery state, retry scheduling,
    strategy selection and circuit-breaker coordination.

    RecoveryExecutor is responsible only for executing
    an individual recovery attempt.
    """

    def __init__(self, clock=time.time):
        self.states = {}
        self.breakers = {}
        self.clock = clock

        self.max_retries = 5
        self.base_delay = 2.0
        self.max_delay = 60.0

        self.strategies = {
            "fixed_retry": FixedRetryStrategy(),
            "exponential_backoff": ExponentialBackoffStrategy(),
        }

    def register(self, state: RecoveryState):
        self.states[state.item_id] = state

        breaker = CircuitBreaker(clock=self.clock)
        breaker.failure_count = state.consecutive_failures

        if state.circuit_state == "open":
            breaker.state = CircuitState.OPEN
            breaker.opened_at = state.circuit_opened_at

        elif state.circuit_state == "half_open":
            breaker.state = CircuitState.HALF_OPEN

        self.breakers[state.item_id] = breaker

    def get_state(self, item_id: str):
        return self.states.get(item_id)

    def get_breaker(self, item_id: str):
        return self.breakers.get(item_id)

    def get_strategy(self, item_id: str):
        state = self.get_state(item_id)

        if state is None:
            raise KeyError(f"Unknown recovery item: {item_id}")

        if state.strategy not in self.strategies:
            raise ValueError(
                f"Unsupported recovery strategy: {state.strategy}"
            )

        return self.strategies[state.strategy]

    def configure_strategy(self, item_id: str, strategy_name: str):
        if item_id not in self.states:
            raise KeyError(f"Unknown recovery item: {item_id}")

        if strategy_name not in self.strategies:
            raise ValueError(
                f"Unsupported recovery strategy: {strategy_name}"
            )

        state = self.states[item_id]

        if state.strategy != strategy_name:
            state.strategy = strategy_name

            # Reset the old strategy's pending retry schedule.
            state.retry_count = 0
            state.next_retry_at = None

            # Preserve last_attempt_at as historical information.


    def schedule_retry(self, item_id: str):
        state = self.get_state(item_id)

        if state is None:
            raise KeyError(f"Unknown recovery item: {item_id}")

    # Never create duplicate schedules.
        if state.next_retry_at is not None:
            return state.next_retry_at

        breaker = self.get_breaker(item_id)
        now = self.clock()

    # An OPEN circuit must wait for its cooldown,
    # regardless of the remaining retry budget.
        if (
            breaker is not None
            and breaker.state == CircuitState.OPEN
            and breaker.opened_at is not None
        ):

            state.next_retry_at = max(
                now,
                breaker.opened_at + breaker.reset_timeout
            )
            return state.next_retry_at

        strategy = self.get_strategy(item_id)

        context = RecoveryContext(
            retry_count=state.retry_count,
            max_retries=self.max_retries,
            base_delay=self.base_delay,
            max_delay=self.max_delay,
        )

        if not strategy.should_retry(context):
            state.next_retry_at = None
            return None

        delay = strategy.get_delay(context)
        state.next_retry_at = now + delay

    # Counts scheduled retry slots consumed.
        state.retry_count += 1

    # last_attempt_at changes only when an attempt is authorized.
        return state.next_retry_at


    def is_retry_due(self, item_id: str) -> bool:
        state = self.get_state(item_id)

        if state is None:
            raise KeyError(f"Unknown recovery item: {item_id}")

        if state.next_retry_at is None:
            return False

        return self.clock() >= state.next_retry_at

    def can_attempt_recovery(self, item_id: str) -> bool:
        state = self.get_state(item_id)
        breaker = self.get_breaker(item_id)

        if state is None or breaker is None:
            raise KeyError(f"Unknown recovery item: {item_id}")

        if not self.is_retry_due(item_id):
            return False

        allowed = breaker.allow_request()

        # Synchronize persisted circuit-breaker state.
        state.circuit_state = breaker.state.value
        state.circuit_opened_at = breaker.opened_at

        if not allowed:
            return False

        # A HALF_OPEN authorization starts a fresh retry cycle.
        if breaker.state == CircuitState.HALF_OPEN:
            state.retry_count = 0

        # Record actual authorization time.
        state.last_attempt_at = self.clock()

        return True

    def record_success(self, item_id: str):
        state = self.get_state(item_id)
        breaker = self.get_breaker(item_id)

        if state is None or breaker is None:
            raise KeyError(f"Unknown recovery item: {item_id}")

        breaker.record_success()

        state.retry_count = 0
        state.consecutive_failures = 0
        state.next_retry_at = None
        state.circuit_state = breaker.state.value
        state.circuit_opened_at = None

    def record_failure(self, item_id: str):
        state = self.get_state(item_id)
        breaker = self.get_breaker(item_id)

        if state is None or breaker is None:
            raise KeyError(f"Unknown recovery item: {item_id}")

        breaker.record_failure()

        # Clear the consumed retry schedule.
        state.next_retry_at = None

        state.consecutive_failures = breaker.failure_count
        state.circuit_state = breaker.state.value
        state.circuit_opened_at = breaker.opened_at

    def get_all_states(self):
        return list(self.states.values())
