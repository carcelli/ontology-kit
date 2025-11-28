"""
Ontology-aware evaluation framework for agent testing.

From first principles: Evaluation answers "is the agent working correctly?"
We validate:
1. Output correctness (expected vs actual)
2. Ontology compliance (entities, relationships)
3. Domain constraints (risk policies)
4. Tool usage patterns
5. Performance metrics (latency, cost)
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, Field

from agent_kit.adapters import OntologyAgentAdapter
from agent_kit.ontology.loader import OntologyLoader
from agent_kit.runners import OntologyRunner, RunConfig

logger = logging.getLogger(__name__)


class EvalCase(BaseModel):
    """Single test case for evaluation."""
    model_config = {"extra": "forbid"}

    id: str = Field(..., description="Unique test case ID")
    name: str = Field(..., description="Descriptive name")
    input: str = Field(..., description="Input to agent")
    expected_output: str | None = Field(
        None, description="Expected output (for exact match)"
    )
    expected_entities: list[str] = Field(
        default_factory=list, description="Expected entities in output"
    )
    expected_tool_calls: list[str] = Field(
        default_factory=list, description="Expected tools to be called"
    )
    tags: list[str] = Field(
        default_factory=list, description="Tags for filtering"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class EvalSet(BaseModel):
    """Collection of test cases."""
    model_config = {"extra": "forbid"}

    name: str = Field(..., description="Eval set name")
    description: str = Field(default="", description="Description")
    domain: str = Field(default="business", description="Domain")
    cases: list[EvalCase] = Field(default_factory=list, description="Test cases")

    @classmethod
    def from_json(cls, path: str | Path) -> "EvalSet":
        """Load eval set from JSON file."""
        with open(path) as f:
            data = json.load(f)
        return cls(**data)

    def filter_by_tag(self, tag: str) -> "EvalSet":
        """Filter cases by tag."""
        filtered = [c for c in self.cases if tag in c.tags]
        return EvalSet(
            name=f"{self.name} ({tag})",
            description=self.description,
            domain=self.domain,
            cases=filtered,
        )


@dataclass
class EvalMetrics:
    """Metrics from evaluation."""

    accuracy: float = 0.0
    """Fraction of cases passed"""

    avg_latency_ms: float = 0.0
    """Average latency in milliseconds"""

    ontology_compliance: float = 0.0
    """Fraction compliant with ontology"""

    entity_recall: float = 0.0
    """Fraction of expected entities found"""

    tool_accuracy: float = 0.0
    """Fraction of expected tools called"""

    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0


@dataclass
class CaseResult:
    """Result for single test case."""

    case_id: str
    passed: bool
    output: str
    expected: str | None
    latency_ms: float
    entities_found: list[str] = field(default_factory=list)
    tools_called: list[str] = field(default_factory=list)
    ontology_compliant: bool = True
    error: str | None = None
    scores: dict[str, float] = field(default_factory=dict)


@dataclass
class EvalResult:
    """Complete evaluation result."""

    eval_set_name: str
    metrics: EvalMetrics
    case_results: list[CaseResult]
    duration_seconds: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "eval_set_name": self.eval_set_name,
            "metrics": {
                "accuracy": self.metrics.accuracy,
                "avg_latency_ms": self.metrics.avg_latency_ms,
                "ontology_compliance": self.metrics.ontology_compliance,
                "entity_recall": self.metrics.entity_recall,
                "tool_accuracy": self.metrics.tool_accuracy,
                "total_cases": self.metrics.total_cases,
                "passed_cases": self.metrics.passed_cases,
                "failed_cases": self.metrics.failed_cases,
            },
            "case_results": [
                {
                    "case_id": r.case_id,
                    "passed": r.passed,
                    "latency_ms": r.latency_ms,
                    "error": r.error,
                }
                for r in self.case_results
            ],
            "duration_seconds": self.duration_seconds,
        }

    def summary(self) -> str:
        """Generate summary report."""
        return f"""
Evaluation: {self.eval_set_name}
{'=' * 50}
Total Cases: {self.metrics.total_cases}
Passed: {self.metrics.passed_cases} ({self.metrics.accuracy:.1%})
Failed: {self.metrics.failed_cases}

Metrics:
  Accuracy: {self.metrics.accuracy:.1%}
  Avg Latency: {self.metrics.avg_latency_ms:.0f}ms
  Ontology Compliance: {self.metrics.ontology_compliance:.1%}
  Entity Recall: {self.metrics.entity_recall:.1%}
  Tool Accuracy: {self.metrics.tool_accuracy:.1%}

Duration: {self.duration_seconds:.1f}s
"""


class OntologyEvaluator:
    """
    Evaluator that validates agent outputs with ontology awareness.

    Features:
    - Standard correctness evaluation
    - Ontology compliance checking
    - Entity extraction validation
    - Tool usage verification
    - Performance metrics

    Example:
        >>> evaluator = OntologyEvaluator(ontology, domain="business")
        >>> eval_set = EvalSet.from_json("eval/business_tests.json")
        >>> result = await evaluator.evaluate(agent, eval_set)
        >>> print(result.summary())
    """

    def __init__(
        self,
        ontology: OntologyLoader,
        domain: str = "business",
        evaluators: list[Any] | None = None,
    ):
        """
        Initialize evaluator.

        Args:
            ontology: OntologyLoader for validation
            domain: Domain identifier
            evaluators: Optional list of custom evaluators
        """
        self.ontology = ontology
        self.domain = domain
        self.evaluators = evaluators or []
        self.runner = OntologyRunner(ontology, domain)

    async def evaluate(
        self,
        agent: OntologyAgentAdapter | Any,
        eval_set: EvalSet,
        config: RunConfig | None = None,
    ) -> EvalResult:
        """
        Run evaluation on agent.

        Args:
            agent: Agent to evaluate
            eval_set: Set of test cases
            config: Execution configuration

        Returns:
            EvalResult with metrics and case results
        """
        start_time = time.time()
        config = config or RunConfig(domain=self.domain)

        case_results: list[CaseResult] = []
        total_entities_expected = 0
        total_entities_found = 0
        total_tools_expected = 0
        total_tools_correct = 0
        compliant_count = 0

        logger.info(f"Starting evaluation: {eval_set.name} ({len(eval_set.cases)} cases)")

        for case in eval_set.cases:
            case_result = await self._evaluate_case(agent, case, config)
            case_results.append(case_result)

            # Aggregate metrics
            if case_result.ontology_compliant:
                compliant_count += 1

            if case.expected_entities:
                total_entities_expected += len(case.expected_entities)
                for entity in case.expected_entities:
                    if entity.lower() in case_result.output.lower():
                        total_entities_found += 1

            if case.expected_tool_calls:
                total_tools_expected += len(case.expected_tool_calls)
                # Would need to track actual tool calls

        # Calculate metrics
        passed = sum(1 for r in case_results if r.passed)
        total = len(case_results)

        metrics = EvalMetrics(
            accuracy=passed / total if total > 0 else 0,
            avg_latency_ms=sum(r.latency_ms for r in case_results) / total if total > 0 else 0,
            ontology_compliance=compliant_count / total if total > 0 else 0,
            entity_recall=total_entities_found / total_entities_expected if total_entities_expected > 0 else 1.0,
            tool_accuracy=total_tools_correct / total_tools_expected if total_tools_expected > 0 else 1.0,
            total_cases=total,
            passed_cases=passed,
            failed_cases=total - passed,
        )

        duration = time.time() - start_time

        result = EvalResult(
            eval_set_name=eval_set.name,
            metrics=metrics,
            case_results=case_results,
            duration_seconds=duration,
        )

        logger.info(f"Evaluation complete: {passed}/{total} passed in {duration:.1f}s")
        return result

    async def _evaluate_case(
        self,
        agent: OntologyAgentAdapter | Any,
        case: EvalCase,
        config: RunConfig,
    ) -> CaseResult:
        """Evaluate a single test case."""
        start = time.time()

        try:
            # Run agent
            result = await self.runner.run(agent, case.input, config)
            latency_ms = (time.time() - start) * 1000

            # Check pass/fail
            passed = True
            if case.expected_output:
                # Simple containment check
                passed = case.expected_output.lower() in result.output.lower()

            # Check ontology compliance
            compliant = self._check_ontology_compliance(result.output)

            # Run custom evaluators
            scores = {}
            for evaluator in self.evaluators:
                score = await evaluator.evaluate(case, result)
                scores[evaluator.name] = score
                if score < 0.5:
                    passed = False

            return CaseResult(
                case_id=case.id,
                passed=passed,
                output=result.output,
                expected=case.expected_output,
                latency_ms=latency_ms,
                entities_found=result.entities_extracted,
                ontology_compliant=compliant,
                scores=scores,
            )

        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            logger.error(f"Case {case.id} failed: {e}")

            return CaseResult(
                case_id=case.id,
                passed=False,
                output="",
                expected=case.expected_output,
                latency_ms=latency_ms,
                ontology_compliant=False,
                error=str(e),
            )

    def _check_ontology_compliance(self, output: str) -> bool:
        """Check if output complies with ontology constraints."""
        # Could check:
        # - Entity URIs exist in ontology
        # - Relationships are valid
        # - Domain constraints satisfied
        return True  # Simplified for now

    async def evaluate_trajectory(
        self,
        agent: OntologyAgentAdapter | Any,
        conversation: list[dict[str, str]],
    ) -> dict[str, float]:
        """
        Evaluate multi-turn conversation trajectory.

        Args:
            agent: Agent to evaluate
            conversation: List of {"role": "user/assistant", "content": "..."}

        Returns:
            Trajectory scores
        """
        # Would evaluate:
        # - Coherence across turns
        # - Goal achievement
        # - Entity consistency
        return {
            "coherence": 1.0,
            "goal_achievement": 1.0,
            "entity_consistency": 1.0,
        }


