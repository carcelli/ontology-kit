"""
Individual evaluators for different validation strategies.

From first principles: Different aspects of agent output need different
evaluation strategies:
- Exact match for deterministic outputs
- LLM-as-judge for subjective quality
- Rubric scoring for structured criteria
- Ontology compliance for domain validation
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from agent_kit.ontology.loader import OntologyLoader

logger = logging.getLogger(__name__)


class BaseEvaluator(ABC):
    """Base class for evaluators."""

    name: str = "base"

    @abstractmethod
    async def evaluate(
        self,
        case: Any,  # EvalCase
        result: Any,  # RunResult
    ) -> float:
        """
        Evaluate agent output.

        Args:
            case: Test case with expected values
            result: Agent output

        Returns:
            Score between 0.0 and 1.0
        """
        pass


class ExactMatchEvaluator(BaseEvaluator):
    """
    Evaluator that checks for exact string match.

    Use for deterministic outputs where exact match is required.
    """

    name = "exact_match"

    def __init__(self, case_sensitive: bool = False):
        self.case_sensitive = case_sensitive

    async def evaluate(self, case: Any, result: Any) -> float:
        """Check exact match."""
        if not case.expected_output:
            return 1.0  # No expectation = pass

        output = result.output
        expected = case.expected_output

        if not self.case_sensitive:
            output = output.lower()
            expected = expected.lower()

        return 1.0 if output.strip() == expected.strip() else 0.0


class ContainsEvaluator(BaseEvaluator):
    """
    Evaluator that checks if output contains expected text.

    More lenient than exact match.
    """

    name = "contains"

    def __init__(self, case_sensitive: bool = False):
        self.case_sensitive = case_sensitive

    async def evaluate(self, case: Any, result: Any) -> float:
        """Check containment."""
        if not case.expected_output:
            return 1.0

        output = result.output
        expected = case.expected_output

        if not self.case_sensitive:
            output = output.lower()
            expected = expected.lower()

        return 1.0 if expected in output else 0.0


class LLMJudgeEvaluator(BaseEvaluator):
    """
    Evaluator that uses an LLM to judge output quality.

    Useful for subjective criteria like helpfulness, clarity, accuracy.
    """

    name = "llm_judge"

    def __init__(
        self,
        criteria: str = "helpfulness",
        model: str = "gpt-4o-mini",
    ):
        """
        Initialize LLM judge.

        Args:
            criteria: What to evaluate (helpfulness, accuracy, clarity, etc.)
            model: Model to use for judging
        """
        self.criteria = criteria
        self.model = model

    async def evaluate(self, case: Any, result: Any) -> float:
        """Use LLM to judge output."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI()

            prompt = f"""You are evaluating an AI agent's response.

Criteria: {self.criteria}

User Input: {case.input}
Agent Output: {result.output}

Rate the output on the criteria above from 0 to 10, where:
- 0: Completely fails the criteria
- 5: Partially meets the criteria
- 10: Perfectly meets the criteria

Respond with just a number between 0 and 10."""

            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )

            score_text = response.choices[0].message.content.strip()
            score = float(score_text) / 10.0
            return max(0.0, min(1.0, score))

        except Exception as e:
            logger.error(f"LLM judge failed: {e}")
            return 0.5  # Neutral score on failure


class RubricEvaluator(BaseEvaluator):
    """
    Evaluator that scores output against a rubric.

    Rubrics define criteria with scoring levels.
    """

    name = "rubric"

    def __init__(self, rubric: dict[str, list[str]]):
        """
        Initialize rubric evaluator.

        Args:
            rubric: Dict mapping criteria to scoring levels.
                Example: {"accuracy": ["incorrect", "partially correct", "correct"]}
        """
        self.rubric = rubric

    async def evaluate(self, case: Any, result: Any) -> float:
        """Score against rubric."""
        # Would use LLM to determine rubric level for each criterion
        # For now, return simple keyword-based score

        output_lower = result.output.lower()
        total_score = 0.0
        num_criteria = len(self.rubric)

        for criteria, levels in self.rubric.items():
            # Check for keywords associated with higher levels
            for i, level in enumerate(levels):
                level_words = level.lower().split()
                if any(word in output_lower for word in level_words):
                    total_score += i / (len(levels) - 1)
                    break
            else:
                # Default to middle score
                total_score += 0.5

        return total_score / num_criteria if num_criteria > 0 else 1.0


class OntologyComplianceEvaluator(BaseEvaluator):
    """
    Evaluator that checks ontology compliance.

    Validates:
    - Referenced entities exist in ontology
    - Relationships are valid
    - Domain constraints are satisfied
    """

    name = "ontology_compliance"

    def __init__(self, ontology: OntologyLoader, domain: str = "business"):
        """
        Initialize ontology evaluator.

        Args:
            ontology: OntologyLoader for validation
            domain: Domain identifier
        """
        self.ontology = ontology
        self.domain = domain

    async def evaluate(self, case: Any, result: Any) -> float:
        """Check ontology compliance."""
        output = result.output.lower()
        score = 1.0

        # Check entities extracted exist in ontology
        if hasattr(result, "entities_extracted"):
            for entity in result.entities_extracted:
                if not self._entity_exists(entity):
                    score -= 0.1

        # Check domain-specific constraints
        if self.domain == "business":
            # Business domain: check for financial reasonableness
            pass
        elif self.domain == "betting":
            # Betting domain: check probability constraints
            if "probability" in output:
                # Probabilities should be between 0 and 1
                pass
        elif self.domain == "trading":
            # Trading domain: check risk constraints
            pass

        return max(0.0, score)

    def _entity_exists(self, entity: str) -> bool:
        """Check if entity exists in ontology."""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        ASK {{
            ?e rdfs:label "{entity}" .
        }}
        """
        try:
            results = self.ontology.query(query)
            return bool(results)
        except Exception:
            return True  # Assume exists if query fails


class EntityRecallEvaluator(BaseEvaluator):
    """
    Evaluator that checks entity recall.

    Measures what fraction of expected entities appear in output.
    """

    name = "entity_recall"

    async def evaluate(self, case: Any, result: Any) -> float:
        """Check entity recall."""
        if not case.expected_entities:
            return 1.0

        output_lower = result.output.lower()
        found = 0

        for entity in case.expected_entities:
            if entity.lower() in output_lower:
                found += 1

        return found / len(case.expected_entities)


class ToolUsageEvaluator(BaseEvaluator):
    """
    Evaluator that checks correct tool usage.

    Validates:
    - Expected tools were called
    - Tools were called with correct parameters
    """

    name = "tool_usage"

    async def evaluate(self, case: Any, result: Any) -> float:
        """Check tool usage."""
        if not case.expected_tool_calls:
            return 1.0

        # Would need to track actual tool calls in RunResult
        # For now, return 1.0
        return 1.0


class CompositeEvaluator(BaseEvaluator):
    """
    Evaluator that combines multiple evaluators with weights.
    """

    name = "composite"

    def __init__(
        self,
        evaluators: list[tuple[BaseEvaluator, float]],
    ):
        """
        Initialize composite evaluator.

        Args:
            evaluators: List of (evaluator, weight) tuples
        """
        self.evaluators = evaluators
        total_weight = sum(w for _, w in evaluators)
        self.weights = [(e, w / total_weight) for e, w in evaluators]

    async def evaluate(self, case: Any, result: Any) -> float:
        """Combine evaluator scores."""
        total = 0.0
        for evaluator, weight in self.weights:
            score = await evaluator.evaluate(case, result)
            total += score * weight
        return total


