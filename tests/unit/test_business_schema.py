"""Unit tests for ontology.business_schema module."""

from datetime import date

import pytest

from agent_kit.ontology.business_schema import (
    Business,
    Client,
    ForecastModel,
    Insight,
    LeveragePoint,
    OutreachCampaign,
    RevenueStream,
    TimeSeries,
)


def test_business_creation() -> None:
    """Test creating valid Business instance."""
    biz = Business(
        id="biz_001",
        name="Test Bakery",
        industry="Bakery",
        location="Milwaukee, WI",
        annual_revenue=500000.0,
        employee_count=10,
    )

    assert biz.id == "biz_001"
    assert biz.name == "Test Bakery"
    assert biz.annual_revenue == 500000.0


def test_business_location_validation() -> None:
    """Test location must be 'City, State' format."""
    with pytest.raises(ValueError, match="Location must be"):
        Business(
            id="biz_001",
            name="Test",
            industry="Bakery",
            location="InvalidLocation",  # Missing comma
            annual_revenue=500000.0,
            employee_count=10,
        )


def test_business_revenue_validation() -> None:
    """Test revenue must be positive."""
    with pytest.raises(ValueError):
        Business(
            id="biz_001",
            name="Test",
            industry="Bakery",
            location="Milwaukee, WI",
            annual_revenue=-1000.0,  # Negative
            employee_count=10,
        )


def test_client_creation() -> None:
    """Test creating valid Client instance."""
    client = Client(
        id="client_001",
        name="Restaurant Partner",
        lifetime_value=125000.0,
        acquisition_date=date(2024, 3, 15),
        segment="wholesale",
    )

    assert client.lifetime_value == 125000.0
    assert client.acquisition_date.year == 2024


def test_revenue_stream_creation() -> None:
    """Test creating RevenueStream."""
    revenue = RevenueStream(
        id="rev_001",
        amount=32000.0,
        period="Q1 2025",
        forecast_confidence=0.87,
        client_id="client_001",
    )

    assert revenue.amount == 32000.0
    assert 0 <= revenue.forecast_confidence <= 1


def test_timeseries_validation() -> None:
    """Test time series must have at least 2 points."""
    with pytest.raises(ValueError, match="at least 2 data points"):
        TimeSeries(
            id="ts_001",
            data_points=[10.0],  # Only 1 point
            frequency="monthly",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )


def test_timeseries_valid() -> None:
    """Test valid time series creation."""
    ts = TimeSeries(
        id="ts_001",
        data_points=[10.0, 12.0, 15.0, 14.0],
        frequency="monthly",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 4, 30),
    )

    assert len(ts.data_points) == 4


def test_forecast_model_accuracy() -> None:
    """Test forecast model accuracy in [0, 1]."""
    model = ForecastModel(
        id="model_001",
        model_type="ARIMA",
        accuracy_score=0.89,
        last_trained=date(2025, 1, 1),
    )

    assert 0 <= model.accuracy_score <= 1


def test_outreach_campaign_conversion_rate() -> None:
    """Test campaign conversion rate validation."""
    campaign = OutreachCampaign(
        id="campaign_001",
        name="Spring Email",
        channel="email",
        budget=5000.0,
        start_date=date(2025, 3, 1),
        conversion_rate=0.12,
    )

    assert 0 <= campaign.conversion_rate <= 1


def test_leverage_point_roi() -> None:
    """Test leverage point ROI calculation."""
    lever = LeveragePoint(
        id="lever_001",
        name="Email Optimization",
        expected_impact=1.25,
        cost=500.0,
        priority=1,
        affects_business_id="biz_001",
    )

    # ROI includes small epsilon (1e-6) to avoid division by zero
    expected_roi = 1.25 / (500.0 + 1e-6)
    assert abs(lever.roi - expected_roi) < 1e-6
    assert lever.priority >= 1


def test_leverage_point_zero_cost() -> None:
    """Test ROI with near-zero cost doesn't crash."""
    lever = LeveragePoint(
        id="lever_001",
        name="Free Optimization",
        expected_impact=2.0,
        cost=0.0,
        priority=1,
        affects_business_id="biz_001",
    )

    # Should not divide by zero (adds 1e-6 in property)
    assert lever.roi > 1000.0


def test_insight_to_natural_language() -> None:
    """Test insight formatting."""
    insight = Insight(
        id="insight_001",
        text="High-value clients respond better to morning emails",
        confidence=0.91,
        generated_at=date(2025, 11, 9),
    )

    output = insight.to_natural_language()
    assert "91% confidence" in output
    assert "morning emails" in output


def test_insight_confidence_bounds() -> None:
    """Test insight confidence in [0, 1]."""
    insight = Insight(
        id="insight_001",
        text="Test insight",
        confidence=0.5,
        generated_at=date(2025, 1, 1),
    )

    assert 0 <= insight.confidence <= 1
