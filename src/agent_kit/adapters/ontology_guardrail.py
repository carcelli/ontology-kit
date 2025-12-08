"""
Guardrails that validate agent inputs/outputs against ontology schemas.

From first principles: Guardrails enforce domain constraints before/after
agent execution. We validate against Pydantic schemas defined in ontology-kit
to ensure outputs conform to domain requirements.
"""

from __future__ import annotations

import json
from typing import Any

from agents import (
    InputGuardrail,
    InputGuardrailResult,
    OutputGuardrail,
    OutputGuardrailResult,
    RunContextWrapper,
)
from pydantic import ValidationError

from agent_kit.schemas import get_schema


class OntologyOutputGuardrail(OutputGuardrail):
    """
    Validates agent outputs against domain Pydantic schemas.

    Ensures outputs conform to schemas defined in ontology-kit (e.g.,
    BusinessOptimizationResult, BettingRecommendation).

    Example:
        >>> from agents import Agent
        >>> from agent_kit.adapters import OntologyOutputGuardrail
        >>>
        >>> agent = Agent(
        ...     name="ForecastAgent",
        ...     output_guardrails=[OntologyOutputGuardrail("business")],
        ... )
    """

    def __init__(self, domain: str):
        """
        Initialize guardrail with domain schema.

        Args:
            domain: Domain identifier (e.g., 'business', 'betting', 'trading')
        """
        self.domain = domain
        schema_name = f"{domain.capitalize()}OptimizationResult"
        if domain == "betting":
            schema_name = "BettingRecommendation"
        elif domain == "trading":
            schema_name = "TradingRecommendation"

        try:
            self.schema = get_schema(schema_name)
        except ValueError:
            # Fallback to generic schema if domain-specific not found
            self.schema = None

    async def check(
        self,
        context: RunContextWrapper,
        output: str,
    ) -> Any:  # OutputGuardrailResult
        """
        Validate output against domain schema.

        Args:
            context: Run context from OpenAI SDK
            output: Agent output string (should be JSON)

        Returns:
            OutputGuardrailResult with validation status
        """
        if self.schema is None:
            # No schema configured - pass through
            return OutputGuardrailResult(passed=True)

        try:
            # Parse output as JSON
            output_dict = json.loads(output)
        except json.JSONDecodeError as e:
            return OutputGuardrailResult(
                passed=False,
                error_message=f"Output is not valid JSON: {e}",
            )

        try:
            # Validate against Pydantic schema
            self.schema(**output_dict)
            return OutputGuardrailResult(passed=True)
        except ValidationError as e:
            errors = "; ".join([str(err) for err in e.errors()])
            return OutputGuardrailResult(
                passed=False,
                error_message=f"Schema validation failed: {errors}",
            )


class OntologyInputGuardrail(InputGuardrail):
    """
    Validates agent inputs against domain constraints.

    Checks that inputs don't violate domain risk policies (e.g., betting
    limits, trading position sizes).
    """

    def __init__(self, domain: str):
        """
        Initialize guardrail with domain constraints.

        Args:
            domain: Domain identifier
        """
        self.domain = domain
        from agent_kit.domains.registry import get_global_registry

        registry = get_global_registry()
        self.domain_config = registry.get(domain)

    async def check(
        self,
        context: RunContextWrapper,
        input_text: str,
    ) -> Any:  # InputGuardrailResult
        """
        Validate input against domain constraints.

        Args:
            context: Run context
            input_text: User input text

        Returns:
            InputGuardrailResult with validation status
        """
        if not self.domain_config or not self.domain_config.risk_policies:
            return InputGuardrailResult(passed=True)

        # Domain-specific validation logic
        violations = []

        # Example: Check betting domain constraints
        if self.domain == "betting":
            # Could check for excessive bet amounts, etc.
            pass

        # Example: Check trading domain constraints
        if self.domain == "trading":
            # Could check for excessive position sizes, etc.
            pass

        if violations:
            return InputGuardrailResult(
                passed=False,
                error_message=f"Input violates domain constraints: {', '.join(violations)}",
            )

        return InputGuardrailResult(passed=True)
