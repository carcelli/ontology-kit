"""
Circuit Breaker Pattern for Agent Risk Management

Automatically halts trading when:
- Drawdown exceeds threshold
- Error rate too high
- Sharpe ratio drops below minimum
"""
from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel


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
                raise Exception(f"Circuit breaker OPEN - trading halted. Last event: {self.events[-1].reason}")
        
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
                    metrics={"drawdown": drawdown, "portfolio_value": value}
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
                metrics={"sharpe_ratio": sharpe}
            )
    
    def _record_error(self):
        """Record error and check error rate threshold."""
        self.errors.append(datetime.now())
        
        # Remove old errors outside check window
        cutoff = datetime.now() - timedelta(minutes=self.config.check_window_minutes)
        self.errors = [e for e in self.errors if e > cutoff]
        
        # Check error rate (assume 100 calls per window for rate calculation)
        if len(self.errors) > 0:
            error_rate = len(self.errors) / 100  # Simplified rate
            
            if error_rate >= self.config.error_rate_threshold:
                self._open_circuit(
                    reason=f"Error rate {error_rate:.2%} >= threshold {self.config.error_rate_threshold:.2%}",
                    metrics={"error_count": len(self.errors), "error_rate": error_rate}
                )
    
    def _record_success(self):
        """Record successful execution."""
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
                metrics=metrics
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
            metrics={}
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
                    metrics={}
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
            "current_drawdown": 1 - (self.current_portfolio_value / self.peak_portfolio_value) if self.peak_portfolio_value > 0 else 0.0,
            "sharpe_ratio": self.current_sharpe_ratio,
            "recent_errors": len(self.errors),
            "last_state_change": self.last_state_change.isoformat() if self.last_state_change else None,
            "recent_events": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "type": e.event_type,
                    "reason": e.reason
                }
                for e in self.events[-5:]  # Last 5 events
            ]
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
            metrics={}
        )
        self.events.append(event)
        print("⚠️  Circuit breaker manually reset")


# Global circuit breaker instances (one per agent)
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(agent_name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
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

