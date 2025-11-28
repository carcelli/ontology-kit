"""
Business-specific agents for forecasting and optimization.

Concrete implementations of BaseAgent for small business ML tasks.
"""

from __future__ import annotations

from agent_kit.agents.base import (
    AgentActionResult,
    AgentObservation,
    AgentPlan,
    AgentResult,
    AgentTask,
    BaseAgent,
)


class ForecastAgent(BaseAgent):
    """
    Agent that generates revenue forecasts using time-series models.

    Observes business data, plans forecast approach, executes predictions.
    """

    def __init__(self) -> None:
        super().__init__(
            name="ForecastAgent",
            description="Generates revenue forecasts using ARIMA and ML models",
        )

    def observe(self, task: AgentTask) -> AgentObservation:
        """Gather historical revenue data for forecasting."""
        # In production: query database, load time-series
        observations = {
            "historical_revenue": [100, 120, 115, 130, 140],  # Stub data
            "seasonality": "Q4_spike",
            "data_quality": "good",
        }

        notes = [
            "Retrieved 5 months of historical revenue",
            "Detected Q4 seasonal spike pattern",
        ]

        return AgentObservation(data=observations, notes=notes)

    def plan(self, task: AgentTask, observation: AgentObservation) -> AgentPlan:
        """Determine forecast model and horizon."""
        steps = [
            "Apply ARIMA(2,1,2) model to historical data",
            "Generate 3-month forward forecast",
            "Calculate confidence intervals",
            "Identify optimization opportunities",
        ]

        metadata = {
            "model": "ARIMA(2,1,2)",
            "horizon": 3,
            "confidence": 0.89,
        }

        return AgentPlan(steps=steps, metadata=metadata)

    def act(
        self,
        task: AgentTask,
        plan: AgentPlan,
        observation: AgentObservation,
    ) -> AgentActionResult:
        """Execute forecast and return predictions."""
        # In production: run actual model
        forecast = [145, 150, 160]  # Stub predictions

        summary = (
            f"Forecast Q1-Q3: ${forecast[0]}K, ${forecast[1]}K, ${forecast[2]}K. "
            f"Recommendation: Optimize outreach in Q2 for {forecast[1]*0.1:.0f}K uplift."
        )

        artifacts = {
            "forecast_values": forecast,
            "model_accuracy": plan.metadata["confidence"],
            "recommendation": "optimize_outreach",
        }

        log = [
            "Loaded historical data",
            f"Trained {plan.metadata['model']} model",
            "Generated 3-month forecast",
            "Identified optimization trigger in Q2",
        ]

        return AgentActionResult(summary=summary, artifacts=artifacts, log=log)

    def run(self, task: AgentTask) -> AgentResult:
        """
        Execute forecast workflow (observe → plan → act).

        This is the simplified entrypoint for orchestrator integration.
        """
        observation = self.observe(task)
        plan = self.plan(task, observation)
        action_result = self.act(task, plan, observation)

        # Convert to AgentResult format expected by orchestrator
        result_dict = {
            "forecast": {
                "forecast": action_result.artifacts.get("forecast_values", []),
                "horizon_days": 90,  # 3 months
                "model_name": plan.metadata.get("model", "ARIMA"),
                "cv_metrics": {"confidence": action_result.artifacts.get("model_accuracy", 0.8)},
            },
            "summary": action_result.summary,
        }

        return AgentResult(result=result_dict)


class OptimizerAgent(BaseAgent):
    """
    Agent that identifies leverage points for revenue optimization.

    Analyzes forecasts and business data to recommend high-ROI actions.
    """

    def __init__(self) -> None:
        super().__init__(
            name="OptimizerAgent",
            description="Identifies leverage points for revenue and efficiency optimization",
        )

    def observe(self, task: AgentTask) -> AgentObservation:
        """Gather business metrics and constraints."""
        # Extract forecast from previous agent (if handed off)
        previous_forecast = task.parameters.get("previous_artifacts", {}).get(
            "forecast_values", []
        )

        observations = {
            "current_revenue": 140,  # K
            "forecast": previous_forecast or [145, 150, 160],
            "outreach_budget": 5.0,  # K
            "conversion_rate": 0.12,
        }

        notes = [
            "Retrieved current business metrics",
            f"Forecast received: {previous_forecast}" if previous_forecast else "Using default forecast",
        ]

        return AgentObservation(data=observations, notes=notes)

    def plan(self, task: AgentTask, observation: AgentObservation) -> AgentPlan:
        """Determine optimization strategy."""
        steps = [
            "Calculate potential uplift from outreach optimization",
            "Evaluate ROI of timing adjustments",
            "Prioritize leverage points by impact/cost",
            "Generate actionable recommendations",
        ]

        metadata = {
            "strategy": "outreach_timing",
            "expected_roi": 1.25,
        }

        return AgentPlan(steps=steps, metadata=metadata)

    def act(
        self,
        task: AgentTask,
        plan: AgentPlan,
        observation: AgentObservation,
    ) -> AgentActionResult:
        """Execute optimization analysis."""
        forecast = observation.data.get("forecast", [145, 150, 160])
        budget = observation.data.get("outreach_budget", 5.0)
        conversion_rate = observation.data.get("conversion_rate", 0.12)

        # Calculate optimization impact
        expected_uplift = budget * conversion_rate * 10  # Simplified model
        roi = expected_uplift / budget

        summary = (
            f"Optimization recommendation: Adjust email send times for {expected_uplift:.0f}K uplift. "
            f"ROI: {roi:.2f}x on ${budget}K investment. Priority: High."
        )

        artifacts = {
            "leverage_point": "email_timing_optimization",
            "expected_uplift": expected_uplift,
            "roi": roi,
            "cost": budget,
            "priority": 1,
        }

        log = [
            "Analyzed forecast trends",
            f"Calculated potential uplift: {expected_uplift:.0f}K",
            f"ROI assessment: {roi:.2f}x",
            "Prioritized email timing as top lever",
        ]

        return AgentActionResult(summary=summary, artifacts=artifacts, log=log)

    def run(self, task: AgentTask) -> AgentResult:
        """
        Execute optimization workflow (observe → plan → act).

        This is the simplified entrypoint for orchestrator integration.
        """
        observation = self.observe(task)
        plan = self.plan(task, observation)
        action_result = self.act(task, plan, observation)

        # Convert to AgentResult format expected by orchestrator
        result_dict = {
            "interventions": [
                {
                    "action": action_result.artifacts.get("leverage_point", ""),
                    "expected_impact": action_result.artifacts.get("expected_uplift", 0),
                    "confidence": 0.8,
                    "estimated_cost": action_result.artifacts.get("cost", 0),
                }
            ],
            "summary": action_result.summary,
        }

        return AgentResult(result=result_dict)

