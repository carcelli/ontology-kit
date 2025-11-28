"""
Runner module for agent execution orchestration.

From first principles: The Runner is the stateless orchestration engine that
manages agent execution. It combines:
- ADK's robust event/session infrastructure
- OpenAI SDK's agent execution capabilities
- Ontology-kit's domain knowledge layer

This module provides:
- OntologyRunner: Unified runner for both SDKs
- StreamingRunner: For real-time/live interactions
- RunConfig: Configuration for execution
"""

from .ontology_runner import OntologyRunner, RunConfig, RunResult
from .streaming_runner import StreamingRunner

__all__ = [
    "OntologyRunner",
    "RunConfig",
    "RunResult",
    "StreamingRunner",
]

