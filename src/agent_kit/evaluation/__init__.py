"""
Evaluation framework for systematic agent testing.

From first principles: Evaluation enables:
- Regression testing (catch breaking changes)
- Performance measurement (latency, accuracy)
- Quality metrics (LLM-as-judge, rubric scoring)
- Domain validation (ontology compliance)

Inspired by ADK's evaluation framework, enhanced with ontology validation.

This module provides:
- OntologyEvaluator: Main evaluator with ontology validation
- EvalCase: Test case definition
- EvalResult: Evaluation results
- Evaluators: LLM-as-judge, rubric-based, trajectory
"""

from .evaluators import (
    BaseEvaluator,
    ExactMatchEvaluator,
    LLMJudgeEvaluator,
    OntologyComplianceEvaluator,
    RubricEvaluator,
)
from .ontology_evaluator import (
    EvalCase,
    EvalMetrics,
    EvalResult,
    EvalSet,
    OntologyEvaluator,
)

__all__ = [
    # Core
    "OntologyEvaluator",
    "EvalCase",
    "EvalSet",
    "EvalResult",
    "EvalMetrics",
    # Evaluators
    "BaseEvaluator",
    "ExactMatchEvaluator",
    "LLMJudgeEvaluator",
    "RubricEvaluator",
    "OntologyComplianceEvaluator",
]
