"""
Orchestrators for multi-agent coordination.

From first principles: Orchestrators coordinate multiple agents to achieve
complex goals. They handle:
- Task decomposition (breaking down complex requests)
- Agent selection (routing to appropriate specialists)
- Execution management (handoffs, retries, fallbacks)
- Result aggregation (combining outputs)

This module provides:
- OntologyOrchestrator: Legacy ontology-driven orchestrator
- UnifiedOrchestrator: Combined ADK + OpenAI SDK orchestrator
"""

from .ontology_orchestrator import OntologyOrchestrator
from .unified_orchestrator import (
    OrchestratorConfig,
    OrchestratorResult,
    UnifiedOrchestrator,
    create_business_orchestrator,
)

__all__ = [
    # Legacy
    "OntologyOrchestrator",
    # Unified
    "UnifiedOrchestrator",
    "OrchestratorConfig",
    "OrchestratorResult",
    "create_business_orchestrator",
]
