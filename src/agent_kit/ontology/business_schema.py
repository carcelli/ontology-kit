"""
Pydantic schemas for Business Ontology entities.

Type-safe Python representations of ontology classes with validation.
"""

from datetime import date

from pydantic import BaseModel, Field, field_validator


class Business(BaseModel):
    """Commercial enterprise (substance): bakery, cafe, retail."""

    id: str
    name: str
    industry: str = Field(..., description="Bakery, Cafe, Retail, etc.")
    location: str = Field(..., description="City, State")
    annual_revenue: float = Field(..., gt=0, description="Annual revenue in USD")
    employee_count: int = Field(..., ge=0)
    description: str | None = None

    @field_validator('location')
    @classmethod
    def validate_location(cls, v: str) -> str:
        """Ensure location contains city and state."""
        if ', ' not in v:
            raise ValueError("Location must be 'City, State' format")
        return v


class Client(BaseModel):
    """Customer or client entity that generates revenue."""

    id: str
    name: str
    lifetime_value: float = Field(..., ge=0, description="CLV in USD")
    acquisition_date: date
    segment: str | None = None
    description: str | None = None


class RevenueStream(BaseModel):
    """Flow of revenue over time (process)."""

    id: str
    amount: float = Field(..., ge=0, description="Revenue amount in USD")
    period: str = Field(..., description="Q1 2025, Jan 2025, etc.")
    forecast_confidence: float | None = Field(None, ge=0, le=1)
    client_id: str = Field(..., description="ID of client generating revenue")
    description: str | None = None


class TimeSeries(BaseModel):
    """Sequential data points indexed by time."""

    id: str
    data_points: list[float]
    frequency: str = Field(..., description="daily, weekly, monthly")
    start_date: date
    end_date: date
    business_id: str | None = None
    description: str | None = None

    @field_validator('data_points')
    @classmethod
    def validate_data_points(cls, v: list[float]) -> list[float]:
        """Ensure at least 2 data points."""
        if len(v) < 2:
            raise ValueError("Time series must have at least 2 data points")
        return v


class ForecastModel(BaseModel):
    """ML model that predicts time-series."""

    id: str
    model_type: str = Field(..., description="ARIMA, Prophet, NeuralNet")
    accuracy_score: float = Field(..., ge=0, le=1, description="MAPE, RMSE, R²")
    last_trained: date
    timeseries_id: str | None = None
    description: str | None = None


class OutreachCampaign(BaseModel):
    """Marketing or sales campaign (process)."""

    id: str
    name: str
    channel: str = Field(..., description="email, social, direct_mail")
    budget: float = Field(..., ge=0, description="Campaign budget in USD")
    start_date: date
    conversion_rate: float | None = Field(None, ge=0, le=1)
    target_segment: str | None = None
    description: str | None = None


class LeveragePoint(BaseModel):
    """Strategic intervention with high impact/cost ratio."""

    id: str
    name: str
    expected_impact: float = Field(..., description="ROI or % change")
    cost: float = Field(..., ge=0, description="Implementation cost in USD")
    priority: int = Field(..., ge=1, description="1=highest priority")
    affects_business_id: str
    prerequisites: list[str] | None = Field(default_factory=list)
    description: str | None = None

    @property
    def roi(self) -> float:
        """Return on investment: impact / cost."""
        return self.expected_impact / (self.cost + 1e-6)


class Insight(BaseModel):
    """Derived knowledge from analysis that informs decisions."""

    id: str
    text: str
    confidence: float = Field(..., ge=0, le=1)
    generated_at: date
    derived_from_dataset: str | None = None
    informs_process: str | None = None

    def to_natural_language(self) -> str:
        """Convert to human-readable format."""
        conf_pct = int(self.confidence * 100)
        return f"[{conf_pct}% confidence] {self.text}"


# Example usage and validation
if __name__ == '__main__':
    # Create business
    bakery = Business(
        id="biz_001",
        name="Sunshine Bakery",
        industry="Bakery",
        location="Milwaukee, WI",
        annual_revenue=485000.0,
        employee_count=8,
        description="Family-owned artisan bakery"
    )
    print(f"✅ Created: {bakery.name} (Revenue: ${bakery.annual_revenue:,.0f})")

    # Create client
    client = Client(
        id="client_001",
        name="Restaurant Partner A",
        lifetime_value=125000.0,
        acquisition_date=date(2024, 3, 15),
        segment="wholesale"
    )
    print(f"✅ Created: {client.name} (CLV: ${client.lifetime_value:,.0f})")

    # Create leverage point
    lever = LeveragePoint(
        id="lever_001",
        name="Email Timing Optimization",
        expected_impact=1.25,
        cost=500.0,
        priority=1,
        affects_business_id="biz_001",
        description="Optimize send times for 25% lift"
    )
    print(f"✅ Created: {lever.name} (ROI: {lever.roi:.2f}x)")

    # Create insight
    insight = Insight(
        id="insight_001",
        text="Restaurants with >$100K annual spend respond 3x better to morning emails",
        confidence=0.91,
        generated_at=date(2025, 11, 9)
    )
    print(f"✅ Created: {insight.to_natural_language()}")

