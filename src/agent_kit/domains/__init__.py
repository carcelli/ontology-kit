"""
Domain configuration system for ontology-kit.

Domains define specialized agent ecosystems with:
- Agent rosters (ForecastAgent, AlgoTradingAgent, etc.)
- Tool allowlists (only relevant tools per domain)
- Risk policies (bankroll limits, position sizing, etc.)
- Output schemas (structured Pydantic results)

From first principles: Domains are boundary contexts (DDD) that partition
the agent graph into cohesive subgraphs, enabling specialization and isolation.
"""

from agent_kit.domains.registry import DomainConfig, DomainRegistry, get_global_registry

__all__ = [
    "DomainConfig",
    "DomainRegistry",
    "get_global_registry",
]
