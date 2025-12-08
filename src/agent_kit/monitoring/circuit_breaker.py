"""
Circuit Breaker Pattern for Agent Risk Management

Automatically halts trading when:
- Drawdown exceeds threshold
- Error rate too high
- Sharpe ratio drops below minimum
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any

from pydantic import BaseModel  # pyright: ignore[reportMissingImports]


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Trading halted
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreakerConfig(BaseModel):
    """Configuration for circuit breaker."""

    max_drawdown: float = 0.15  # 15% max drawdown
    min_sharpe_ratio: float = 0.5  # Minimum Sharpe
    error_rate_threshold: float = 0.05  # 5% error rate
    check_window_minutes: int = 5  # Error rate window
    recovery_timeout_minutes: int = 30  # Time before trying HALF_OPEN


class CircuitBreakerEvent(BaseModel):
    """Event logged when circuit breaker triggers."""

    timestamp: datetime
    event_type: str  # "OPENED", "CLOSED", "HALF_OPENED"
    reason: str
    metrics: dict[str, Any]


class CircuitBreaker:
    """
    Circuit breaker to halt trading on excessive losses or errors.

    Example:
        >>> breaker = CircuitBreaker(max_drawdown=0.15)
        >>>
        >>> # Update metrics after each trade
        >>> breaker.update_portfolio_value(95000)  # $95k from $100k
        >>>
        >>> # Execute trades with protection
        >>> try:
        ...     breaker.call(execute_trade_function, trade_params)
        >>> except Exception as e:
        ...     print(f"Circuit breaker prevented trade: {e}")
    """

    def __init__(self, config: CircuitBreakerConfig | None = None):
        """
        Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration
        """
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED

        # State tracking
        self.errors: list[datetime] = []
        self.successes: list[datetime] = (
            []
        )  # Track successes for error rate calculation
        self.peak_portfolio_value = 0.0
        self.current_portfolio_value = 0.0
        self.current_sharpe_ratio = 0.0

        # Events log
        self.events: list[CircuitBreakerEvent] = []
        self.last_state_change: datetime | None = None

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit breaker is OPEN or function fails
        """
        if self.state == CircuitState.OPEN:
            self._check_recovery()
            if self.state == CircuitState.OPEN:
                raise Exception(
                    f"Circuit breaker OPEN - trading halted. Last event: {self.events[-1].reason}"
                )

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_error()
            raise e

    def update_portfolio_value(self, value: float):
        """
        Update portfolio value and check drawdown.

        Args:
            value: Current portfolio value
        """
        self.current_portfolio_value = value

        if value > self.peak_portfolio_value:
            self.peak_portfolio_value = value

        if self.peak_portfolio_value > 0:
            drawdown = 1 - (self.current_portfolio_value / self.peak_portfolio_value)

            if drawdown >= self.config.max_drawdown:
                self._open_circuit(
                    reason=f"Drawdown {drawdown:.2%} >= max {self.config.max_drawdown:.2%}",
                    metrics={"drawdown": drawdown, "portfolio_value": value},
                )

    def update_sharpe_ratio(self, sharpe: float):
        """
        Update Sharpe ratio and check minimum threshold.

        Args:
            sharpe: Current Sharpe ratio
        """
        self.current_sharpe_ratio = sharpe

        if sharpe < self.config.min_sharpe_ratio:
            self._open_circuit(
                reason=f"Sharpe ratio {sharpe:.2f} < min {self.config.min_sharpe_ratio:.2f}",
                metrics={"sharpe_ratio": sharpe},
            )

    def _record_error(self):
        """Record error and check error rate threshold."""
        self.errors.append(datetime.now())

        # Remove old errors outside check window
        cutoff = datetime.now() - timedelta(minutes=self.config.check_window_minutes)
        self.errors = [e for e in self.errors if e > cutoff]
        self.successes = [e for e in self.successes if e > cutoff]

        # Calculate error rate based on actual call count
        total_calls = len(self.errors) + len(self.successes)
        if total_calls > 0:
            error_rate = len(self.errors) / total_calls

            if error_rate >= self.config.error_rate_threshold:
                self._open_circuit(
                    reason=f"Error rate {error_rate:.2%} >= threshold {self.config.error_rate_threshold:.2%}",
                    metrics={
                        "error_count": len(self.errors),
                        "total_calls": total_calls,
                        "error_rate": error_rate,
                    },
                )

    def _record_success(self):
        """Record successful execution."""
        self.successes.append(datetime.now())

        # Remove old successes outside check window
        cutoff = datetime.now() - timedelta(minutes=self.config.check_window_minutes)
        self.successes = [e for e in self.successes if e > cutoff]

        if self.state == CircuitState.HALF_OPEN:
            # Success in HALF_OPEN state -> close circuit
            self._close_circuit()

    def _open_circuit(self, reason: str, metrics: dict[str, Any]):
        """Open circuit breaker."""
        if self.state != CircuitState.OPEN:
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()

            event = CircuitBreakerEvent(
                timestamp=datetime.now(),
                event_type="OPENED",
                reason=reason,
                metrics=metrics,
            )
            self.events.append(event)

            self._send_alert(event)

    def _close_circuit(self):
        """Close circuit breaker."""
        self.state = CircuitState.CLOSED
        self.last_state_change = datetime.now()

        event = CircuitBreakerEvent(
            timestamp=datetime.now(),
            event_type="CLOSED",
            reason="Recovered - successful execution",
            metrics={},
        )
        self.events.append(event)

        self._send_alert(event)

    def _check_recovery(self):
        """Check if circuit can transition to HALF_OPEN."""
        if self.state == CircuitState.OPEN and self.last_state_change:
            time_since_open = datetime.now() - self.last_state_change
            recovery_timeout = timedelta(minutes=self.config.recovery_timeout_minutes)

            if time_since_open >= recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = datetime.now()

                event = CircuitBreakerEvent(
                    timestamp=datetime.now(),
                    event_type="HALF_OPENED",
                    reason="Recovery timeout reached - attempting test execution",
                    metrics={},
                )
                self.events.append(event)

    def _send_alert(self, event: CircuitBreakerEvent):
        """
        Send alert to monitoring system.

        In production, integrate with:
        - Email (SendGrid, AWS SES)
        - Slack (webhook)
        - PagerDuty (API)
        - SMS (Twilio)
        """
        print(f"🚨 CIRCUIT BREAKER ALERT: {event.event_type}")
        print(f"   Time: {event.timestamp}")
        print(f"   Reason: {event.reason}")
        print(f"   Metrics: {event.metrics}")

        # TODO: Integrate with real alerting
        # import requests
        # slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        # requests.post(slack_webhook, json={"text": f"Circuit Breaker {event.event_type}: {event.reason}"})

    def get_status(self) -> dict[str, Any]:
        """Get current circuit breaker status."""
        return {
            "state": self.state.value,
            "portfolio_value": self.current_portfolio_value,
            "peak_value": self.peak_portfolio_value,
            "current_drawdown": (
                1 - (self.current_portfolio_value / self.peak_portfolio_value)
                if self.peak_portfolio_value > 0
                else 0.0
            ),
            "sharpe_ratio": self.current_sharpe_ratio,
            "recent_errors": len(self.errors),
            "recent_successes": len(self.successes),
            "last_state_change": (
                self.last_state_change.isoformat() if self.last_state_change else None
            ),
            "recent_events": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "type": e.event_type,
                    "reason": e.reason,
                }
                for e in self.events[-5:]  # Last 5 events
            ],
        }

    def manual_reset(self):
        """Manually reset circuit breaker (use with caution)."""
        self.state = CircuitState.CLOSED
        self.errors = []
        self.last_state_change = datetime.now()

        event = CircuitBreakerEvent(
            timestamp=datetime.now(),
            event_type="CLOSED",
            reason="Manual reset by operator",
            metrics={},
        )
        self.events.append(event)
        print("⚠️  Circuit breaker manually reset")


# Global circuit breaker instances (one per agent/tool)
# Note: Not thread-safe. Wrap in lock if used in multi-threaded context.
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    agent_name: str, config: CircuitBreakerConfig | None = None
) -> CircuitBreaker:
    """
    Get or create circuit breaker for agent.

    Args:
        agent_name: Unique agent identifier
        config: Optional configuration (used on first creation)

    Returns:
        CircuitBreaker instance
    """
    if agent_name not in _circuit_breakers:
        _circuit_breakers[agent_name] = CircuitBreaker(config)
    return _circuit_breakers[agent_name]


# ============================================================================
# Decorator for Functional Composition (Apply circuit breaker to any function)
# ============================================================================


def with_circuit_breaker(
    max_failures: int = 3, reset_timeout: int = 60, failure_threshold: float = 0.5
):
    """
    Decorator to apply circuit breaker pattern to any function.

    From first principles: Functional composition—wrap function with resilience logic.
    Uses nonlocal state (failure count) to track errors across invocations.

    Args:
        max_failures: Max consecutive failures before opening circuit
        reset_timeout: Seconds before attempting recovery
        failure_threshold: Error rate threshold (0.0 to 1.0)

    Returns:
        Decorated function with circuit breaker protection

    Example:
        >>> @with_circuit_breaker(max_failures=3, reset_timeout=60)
        ... def fetch_api_data(url: str) -> dict:
        ...     response = requests.get(url)
        ...     return response.json()

    References:
        - Release It! by Michael Nygard (Circuit Breaker pattern)
        - Python decorators: PEP 318
    """

    def decorator(func: Callable) -> Callable:
        # Nonlocal state for circuit breaker (closure pattern)
        state: dict[str, Any] = {
            "failures": 0,
            "successes": 0,
            "last_failure_time": None,
            "is_open": False,
        }

        @wraps(func)  # Preserve function metadata
        def wrapper(*args, **kwargs):
            # Check if circuit is open
            if state["is_open"]:
                # Check if timeout elapsed
                if state["last_failure_time"]:
                    elapsed = (
                        datetime.now() - state["last_failure_time"]
                    ).total_seconds()
                    if elapsed >= reset_timeout:
                        # Try half-open state
                        state["is_open"] = False
                        state["failures"] = 0  # Reset
                        print(
                            f"🔄 Circuit breaker HALF-OPEN for {func.__name__} - testing recovery"
                        )
                    else:
                        raise Exception(
                            f"Circuit breaker OPEN for {func.__name__}. "
                            f"Wait {reset_timeout - elapsed:.0f}s before retry."
                        )
                else:
                    raise Exception(f"Circuit breaker OPEN for {func.__name__}")

            # Execute function
            try:
                result = func(*args, **kwargs)
                state["successes"] += 1
                state["failures"] = 0  # Reset on success
                return result
            except Exception as e:
                state["failures"] += 1
                state["last_failure_time"] = datetime.now()

                # Check if should open circuit
                total_calls = state["successes"] + state["failures"]
                error_rate = state["failures"] / total_calls if total_calls > 0 else 0

                if state["failures"] >= max_failures or error_rate >= failure_threshold:
                    state["is_open"] = True
                    print(
                        f"🚨 Circuit breaker OPENED for {func.__name__} - "
                        f"{state['failures']} failures, {error_rate:.2%} error rate"
                    )

                raise e

        # Expose state for testing/monitoring
        wrapper.circuit_state = state  # type: ignore

        return wrapper

    return decorator
