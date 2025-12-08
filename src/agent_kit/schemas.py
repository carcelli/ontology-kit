"""
Pydantic schemas for structured agent outputs across domains.

From first principles: Schemas enforce interface contracts between agents
and downstream consumers (APIs, DBs, dashboards). Pydantic provides:
- Runtime validation (fail fast on bad data)
- Type hints for IDE support
- JSON serialization for APIs
- OpenAPI spec generation

Design choices:
- Field validators for business logic (e.g., probabilities in [0,1])
- Descriptive field names for explainability (stakeholders read these)
- Optional fields with None defaults for partial results
- ge/le constraints for numeric bounds (prevent negative prices, etc.)

References:
- Pydantic docs: https://docs.pydantic.dev/latest/
- JSON Schema: https://json-schema.org/
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ============================================================================
# Base Schema with Strict Validation
# ============================================================================


class StrictBaseModel(BaseModel):
    """
    Base model that forbids extra fields (critical for LLM structured outputs).

    Prevents model drift from silently leaking junk fields into agent outputs.
    """

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# Enums for Type Safety
# ============================================================================


class Domain(str, Enum):
    """Domain identifiers for agent orchestration."""

    BUSINESS = "business"
    BETTING = "betting"
    TRADING = "trading"


class SignalType(str, Enum):
    """Trading signal types."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class RiskLevel(str, Enum):
    """Risk level classifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ============================================================================
# Schema Name Literal for Type Safety
# ============================================================================

SchemaName = Literal[
    "BusinessOptimizationResult",
    "BettingRecommendation",
    "TradingRecommendation",
    "ForecastResult",
    "InterventionRecommendation",
    "BettingEdge",
    "TradingSignal",
    "PortfolioMetrics",
]


# ============================================================================
# Business Domain Schemas
# ============================================================================


class ForecastResult(StrictBaseModel):
    """Revenue or metric forecast with confidence intervals."""

    forecast: list[float] = Field(
        ..., description="Predicted values for each time step", min_length=1
    )
    horizon_days: int = Field(..., description="Forecast horizon in days", ge=1, le=365)
    timestamps: list[str] = Field(
        ..., description="ISO 8601 timestamps for each forecast point"
    )
    model_name: str = Field(..., description="Model used (ARIMA, Prophet, Ensemble)")
    confidence_intervals: dict[str, list[float]] | None = Field(
        None, description="Upper/lower bounds at 95% confidence"
    )
    cv_metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Cross-validation metrics (MAE, RMSE, R2)",
    )
    feature_importance: dict[str, float] = Field(
        default_factory=dict, description="Feature contribution scores"
    )

    @field_validator("forecast")
    @classmethod
    def forecast_non_negative(cls, v: list[float]) -> list[float]:
        """Ensure forecast values are non-negative (revenue can't be negative)."""
        if any(x < 0 for x in v):
            raise ValueError("Forecast values must be non-negative")
        return v


class InterventionRecommendation(StrictBaseModel):
    """Actionable intervention to improve a business metric."""

    action: str = Field(
        ..., description="What to do (e.g., 'Increase email frequency')"
    )
    target_node: str = Field(..., description="What metric/concept this affects")
    expected_impact: float = Field(
        ..., description="Expected change in target KPI (%)", ge=-100, le=100
    )
    confidence: float = Field(
        ..., description="Agent confidence in this recommendation", ge=0.0, le=1.0
    )
    estimated_cost: float | None = Field(
        None, description="Implementation cost ($)", ge=0
    )
    estimated_duration: str | None = Field(
        None, description="Time to see results (e.g., '2-4 weeks')"
    )
    risk_level: RiskLevel = Field(default=RiskLevel.MEDIUM, description="Risk level")
    guardrails: list[str] = Field(
        default_factory=list, description="Metrics to monitor for adverse effects"
    )


class BusinessOptimizationResult(StrictBaseModel):
    """
    Comprehensive result for business domain workflows.

    Combines forecasting, leverage analysis, and interventions.
    """

    domain: Domain = Field(default=Domain.BUSINESS, description="Domain identifier")
    goal: str = Field(..., description="Original goal/query from user")
    forecast: ForecastResult | None = Field(
        None, description="Forecast results if requested"
    )
    interventions: list[InterventionRecommendation] = Field(
        default_factory=list,
        description="Ranked interventions to improve metrics",
    )
    leverage_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Leverage scores for key business concepts",
    )
    summary: str = Field(..., description="Plain-English summary for stakeholders")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional context (model versions, etc.)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When result was generated"
    )

    @field_validator("interventions")
    @classmethod
    def limit_interventions(
        cls, v: list[InterventionRecommendation]
    ) -> list[InterventionRecommendation]:
        """Limit to top 10 interventions (avoid overwhelming users)."""
        if len(v) > 10:
            return v[:10]
        return v


# ============================================================================
# Betting Domain Schemas
# ============================================================================


class BettingEdge(StrictBaseModel):
    """Detected edge with Kelly-optimal bet sizing."""

    event_id: str = Field(..., description="Unique event identifier")
    description: str = Field(..., description="Human-readable bet description")
    bookmaker: str = Field(..., description="Bookmaker offering the odds")
    odds: float = Field(..., description="Decimal odds", ge=1.01)
    implied_probability: float = Field(
        ..., description="Bookmaker's implied probability", ge=0.0, le=1.0
    )
    true_probability: float = Field(
        ..., description="Agent's estimated true probability", ge=0.0, le=1.0
    )
    edge: float = Field(..., description="true_prob - implied_prob", ge=-1.0, le=1.0)
    kelly_fraction: float = Field(
        ..., description="Optimal bet size (fraction of bankroll)", ge=0.0, le=1.0
    )
    recommended_stake: float = Field(
        ..., description="Recommended bet amount ($)", ge=0.0
    )
    expected_value: float = Field(..., description="Expected value of this bet ($)")
    confidence: float = Field(
        ..., description="Agent confidence in estimate", ge=0.0, le=1.0
    )
    strategy: str = Field(default="ValueBetting", description="Strategy used")

    @model_validator(mode="after")
    def validate_edge_consistency(self) -> BettingEdge:
        """Validate that edge approximately equals true_prob - implied_prob."""
        expected_edge = self.true_probability - self.implied_probability
        if (
            abs(self.edge - expected_edge) > 0.01
        ):  # Allow small floating point differences
            raise ValueError(
                f"Edge ({self.edge}) should equal true_prob ({self.true_probability}) "
                f"- implied_prob ({self.implied_probability}) = {expected_edge}"
            )
        if abs(self.edge) > 0.5:  # 50% edge is suspicious
            import warnings

            warnings.warn(
                f"Extreme edge detected: {self.edge:.2%}. Verify probabilities.",
                stacklevel=2,
            )
        return self


class BettingRecommendation(StrictBaseModel):
    """Final betting recommendation with risk checks."""

    domain: Domain = Field(default=Domain.BETTING, description="Domain identifier")
    goal: str = Field(..., description="Original goal/query")
    edges: list[BettingEdge] = Field(
        default_factory=list, description="Detected edges with positive EV"
    )
    total_stake: float = Field(
        ..., description="Sum of all recommended stakes ($)", ge=0.0
    )
    total_exposure: float = Field(
        ..., description="Total exposure as fraction of bankroll", ge=0.0, le=1.0
    )
    expected_roi: float = Field(..., description="Expected return on investment (%)")
    passed_risk_checks: bool = Field(
        ..., description="Whether all risk policies passed"
    )
    risk_violations: list[str] = Field(
        default_factory=list, description="Risk policies violated (if any)"
    )
    circuit_breaker_triggered: bool = Field(
        default=False, description="Whether circuit breaker halted execution"
    )
    summary: str = Field(..., description="Plain-English summary")
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Trading Domain Schemas
# ============================================================================


class TradingSignal(StrictBaseModel):
    """Buy/sell signal for an asset."""

    ticker: str = Field(..., description="Asset ticker symbol")
    signal_type: SignalType = Field(..., description="BUY, SELL, or HOLD")
    signal_strength: float = Field(
        ..., description="Signal strength (0.0 to 1.0)", ge=0.0, le=1.0
    )
    entry_price: float = Field(..., description="Recommended entry price", gt=0.0)
    stop_loss: float = Field(..., description="Stop loss price", gt=0.0)
    take_profit: float = Field(..., description="Take profit price", gt=0.0)
    position_size: float = Field(
        ..., description="Position size (fraction of portfolio)", ge=0.0, le=1.0
    )
    expected_return: float = Field(..., description="Expected return (%)")
    risk_reward_ratio: float = Field(..., description="Risk/reward ratio", ge=0.0)
    strategy: str = Field(..., description="Strategy name (e.g., MeanReversion)")
    indicators: dict[str, float] = Field(
        default_factory=dict, description="Technical indicators (RSI, MACD, etc.)"
    )
    confidence: float = Field(..., description="Agent confidence", ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_price_relationships(self) -> TradingSignal:
        """Validate stop loss and take profit relative to entry price."""
        if self.signal_type == SignalType.BUY:
            if self.stop_loss >= self.entry_price:
                raise ValueError(
                    f"For BUY signals, stop_loss ({self.stop_loss}) must be below entry_price ({self.entry_price})"
                )
            if self.take_profit <= self.entry_price:
                raise ValueError(
                    f"For BUY signals, take_profit ({self.take_profit}) must be above entry_price ({self.entry_price})"
                )
        elif self.signal_type == SignalType.SELL:
            if self.stop_loss <= self.entry_price:
                raise ValueError(
                    f"For SELL signals, stop_loss ({self.stop_loss}) must be above entry_price ({self.entry_price})"
                )
            if self.take_profit >= self.entry_price:
                raise ValueError(
                    f"For SELL signals, take_profit ({self.take_profit}) must be below entry_price ({self.entry_price})"
                )
        return self


class PortfolioMetrics(StrictBaseModel):
    """Portfolio-level risk metrics."""

    sharpe_ratio: float = Field(..., description="Sharpe ratio (risk-adjusted return)")
    max_drawdown: float = Field(
        ..., description="Maximum drawdown (%)", ge=0.0, le=100.0
    )
    current_drawdown: float = Field(
        ..., description="Current drawdown (%)", ge=0.0, le=100.0
    )
    var_95: float = Field(..., description="95% Value at Risk (%)", ge=0.0, le=100.0)
    total_exposure: float = Field(
        ..., description="Sum of position sizes (fraction)", ge=0.0
    )
    correlation_matrix: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="Pairwise asset correlations"
    )
    annualized_volatility: float = Field(
        ..., description="Portfolio volatility (%)", ge=0.0
    )


class TradingRecommendation(StrictBaseModel):
    """Final trading recommendation with risk checks."""

    domain: Domain = Field(default=Domain.TRADING, description="Domain identifier")

    @model_validator(mode="after")
    def validate_portfolio_metrics(self) -> TradingRecommendation:
        """Validate portfolio metrics consistency."""
        if (
            self.portfolio_metrics.current_drawdown
            > self.portfolio_metrics.max_drawdown
        ):
            raise ValueError(
                f"Current drawdown ({self.portfolio_metrics.current_drawdown:.2%}) "
                f"cannot exceed max drawdown ({self.portfolio_metrics.max_drawdown:.2%})"
            )
        return self

    goal: str = Field(..., description="Original goal/query")
    signals: list[TradingSignal] = Field(
        default_factory=list, description="Trading signals for assets"
    )
    portfolio_metrics: PortfolioMetrics = Field(
        ..., description="Portfolio-level risk metrics"
    )
    passed_risk_checks: bool = Field(
        ..., description="Whether all risk policies passed"
    )
    risk_violations: list[str] = Field(
        default_factory=list, description="Risk policies violated (if any)"
    )
    circuit_breaker_triggered: bool = Field(
        default=False, description="Whether circuit breaker halted execution"
    )
    rebalance_required: bool = Field(
        default=False, description="Whether portfolio needs rebalancing"
    )
    summary: str = Field(..., description="Plain-English summary")
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Schema Registry (for dynamic lookup by name)
# ============================================================================

SCHEMA_REGISTRY: dict[str, type[StrictBaseModel]] = {}


def register_schema(cls: type[StrictBaseModel]) -> type[StrictBaseModel]:
    """
    Decorator to auto-register schemas in the registry.

    Keeps schema ontology in one place as the system grows.
    """
    SCHEMA_REGISTRY[cls.__name__] = cls
    return cls


# Manually register all schemas (auto-registration would require decorators on class definitions)
SCHEMA_REGISTRY.update(
    {
        "BusinessOptimizationResult": BusinessOptimizationResult,
        "BettingRecommendation": BettingRecommendation,
        "TradingRecommendation": TradingRecommendation,
        "ForecastResult": ForecastResult,
        "InterventionRecommendation": InterventionRecommendation,
        "BettingEdge": BettingEdge,
        "TradingSignal": TradingSignal,
        "PortfolioMetrics": PortfolioMetrics,
    }
)


def get_schema(name: SchemaName | str) -> type[StrictBaseModel]:
    """
    Get a schema class by name.

    Args:
        name: Schema name (e.g., 'BusinessOptimizationResult')

    Returns:
        Pydantic model class

    Raises:
        ValueError: If schema not found

    Example:
        >>> schema = get_schema('BusinessOptimizationResult')
        >>> result = schema(goal="Forecast", forecast=None, summary="Done")
    """
    if name not in SCHEMA_REGISTRY:
        available = list(SCHEMA_REGISTRY.keys())
        raise ValueError(f"Unknown schema: '{name}'. Available schemas: {available}")
    return SCHEMA_REGISTRY[name]
