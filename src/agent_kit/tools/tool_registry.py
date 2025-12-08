"""
Tool Registry System - Ontology-Driven Tool Organization

Organizes all tools into categories with metadata for agent discovery.
Uses ontology to define tool relationships, capabilities, and constraints.

Architecture:
1. Tools are grouped by domain (ML, Betting, Trading, Visualization, etc.)
2. Each tool has metadata (category, cost, latency, dependencies)
3. Agents query registry/ontology to discover relevant tools
4. Registry validates tool compatibility before execution
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


# Tool categories
class ToolCategory:
    """Tool category taxonomy."""

    # Core capabilities
    ONTOLOGY = "ontology"  # Ontology queries and manipulation
    VECTOR_SPACE = "vector_space"  # Embeddings and vector search
    VISUALIZATION = "visualization"  # Charts, graphs, hyperdim viz

    # Domain-specific
    BETTING = "betting"  # Sports betting, odds, arbitrage
    TRADING = "trading"  # Market data, indicators, execution
    ML_TRAINING = "ml_training"  # Model training, validation
    BUSINESS = "business"  # Business optimization, prediction

    # Integration
    GITHUB = "github"  # GitHub operations
    SEMANTIC_GRAPH = "semantic_graph"  # Graph analysis

    # Meta
    ALL = [
        ONTOLOGY,
        VECTOR_SPACE,
        VISUALIZATION,
        BETTING,
        TRADING,
        ML_TRAINING,
        BUSINESS,
        GITHUB,
        SEMANTIC_GRAPH,
    ]


class ToolMetadata(BaseModel):
    """Metadata for a tool."""

    model_config = {"extra": "forbid"}

    name: str
    category: str
    description: str
    cost_estimate: float = 0.0  # Cost per call ($)
    latency_ms: int = 100  # Expected latency (ms)
    requires_api_key: bool = False
    api_provider: str | None = None  # "openai", "xai", "odds_api", etc.
    dependencies: list[str] = []  # Other tools this depends on
    input_schema: type[BaseModel] | None = None
    output_type: str = "dict"
    tags: list[str] = []


class ToolSpec(BaseModel):
    """Complete tool specification."""

    model_config = {"extra": "forbid"}

    metadata: ToolMetadata
    function: Callable
    tool_spec: dict[str, Any]  # OpenAI tool spec format


class ToolRegistry:
    """
    Central registry for all agent tools.

    Example:
        >>> registry = ToolRegistry()
        >>> registry.register_tool(my_tool, category=ToolCategory.BETTING)
        >>> tools = registry.get_tools_by_category(ToolCategory.BETTING)
        >>> agent = Agent(tools=tools)
    """

    def __init__(self):
        """Initialize empty registry."""
        self._tools: dict[str, ToolSpec] = {}
        self._categories: dict[str, list[str]] = {cat: [] for cat in ToolCategory.ALL}
        self._tags: dict[str, list[str]] = {}

    def register_tool(
        self,
        function: Callable,
        category: str,
        description: str | None = None,
        cost_estimate: float = 0.0,
        latency_ms: int = 100,
        requires_api_key: bool = False,
        api_provider: str | None = None,
        tags: list[str] | None = None,
        input_schema: type[BaseModel] | None = None,
    ) -> None:
        """
        Register a tool with metadata.

        Args:
            function: The tool function (decorated with @function_tool)
            category: Tool category (from ToolCategory)
            description: Tool description
            cost_estimate: Estimated cost per call
            latency_ms: Expected latency
            requires_api_key: If True, requires API key
            api_provider: API provider name
            tags: Additional tags for search
            input_schema: Pydantic schema for inputs
        """
        name = function.__name__

        # Extract description from docstring if not provided
        if description is None:
            description = inspect.getdoc(function) or "No description available"

        # Create metadata
        metadata = ToolMetadata(
            name=name,
            category=category,
            description=description,
            cost_estimate=cost_estimate,
            latency_ms=latency_ms,
            requires_api_key=requires_api_key,
            api_provider=api_provider,
            tags=tags or [],
            input_schema=input_schema,
        )

        # Generate OpenAI tool spec
        tool_spec = self._generate_tool_spec(function, metadata)

        # Store tool
        self._tools[name] = ToolSpec(
            metadata=metadata, function=function, tool_spec=tool_spec
        )

        # Add to category index
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(name)

        # Add to tag index
        for tag in tags or []:
            if tag not in self._tags:
                self._tags[tag] = []
            self._tags[tag].append(name)

    def _generate_tool_spec(
        self, function: Callable, metadata: ToolMetadata
    ) -> dict[str, Any]:
        """Generate OpenAI tool spec from function."""
        # Get function signature
        sig = inspect.signature(function)

        # Build parameters schema
        parameters = {"type": "object", "properties": {}, "required": []}

        for param_name, param in sig.parameters.items():
            # Skip self/cls
            if param_name in ["self", "cls"]:
                continue

            # Get type annotation
            param_type = param.annotation

            # Map Python types to JSON schema types
            json_type = "string"  # default
            if param_type is int:
                json_type = "integer"
            elif param_type is float:
                json_type = "number"
            elif param_type is bool:
                json_type = "boolean"
            elif param_type is list:
                json_type = "array"
            elif param_type is dict:
                json_type = "object"

            parameters["properties"][param_name] = {
                "type": json_type,
                "description": f"Parameter {param_name}",
            }

            # Mark as required if no default
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)

        return {
            "type": "function",
            "function": {
                "name": metadata.name,
                "description": metadata.description,
                "parameters": parameters,
            },
        }

    def get_tool(self, name: str) -> ToolSpec | None:
        """Get tool by name."""
        return self._tools.get(name)

    def get_tools_by_category(self, category: str) -> list[Callable]:
        """Get all tool functions in a category."""
        tool_names = self._categories.get(category, [])
        return [self._tools[name].function for name in tool_names]

    def get_tool_specs_by_category(self, category: str) -> list[dict]:
        """Get OpenAI tool specs for a category."""
        tool_names = self._categories.get(category, [])
        return [self._tools[name].tool_spec for name in tool_names]

    def get_tools_by_tags(self, tags: list[str]) -> list[Callable]:
        """Get tools matching any of the tags."""
        tool_names = set()
        for tag in tags:
            tool_names.update(self._tags.get(tag, []))
        return [self._tools[name].function for name in tool_names]

    def estimate_cost(self, tool_names: list[str]) -> float:
        """Estimate total cost for running a set of tools."""
        return sum(
            self._tools[name].metadata.cost_estimate
            for name in tool_names
            if name in self._tools
        )

    def list_all_tools(self) -> dict[str, dict[str, Any]]:
        """List all tools with metadata."""
        return {
            name: {
                "category": spec.metadata.category,
                "description": spec.metadata.description,
                "cost": spec.metadata.cost_estimate,
                "latency_ms": spec.metadata.latency_ms,
                "tags": spec.metadata.tags,
            }
            for name, spec in self._tools.items()
        }

    def filter_tools(
        self,
        categories: list[str] | None = None,
        tags: list[str] | None = None,
        max_cost: float | None = None,
        max_latency_ms: int | None = None,
    ) -> list[Callable]:
        """
        Filter tools by criteria.

        Args:
            categories: List of categories to include
            tags: List of tags to match
            max_cost: Maximum cost per call
            max_latency_ms: Maximum latency

        Returns:
            List of tool functions matching criteria
        """
        filtered_names = set(self._tools.keys())

        # Filter by category
        if categories:
            cat_names = set()
            for cat in categories:
                cat_names.update(self._categories.get(cat, []))
            filtered_names &= cat_names

        # Filter by tags
        if tags:
            tag_names = set()
            for tag in tags:
                tag_names.update(self._tags.get(tag, []))
            filtered_names &= tag_names

        # Filter by cost
        if max_cost is not None:
            filtered_names = {
                name
                for name in filtered_names
                if self._tools[name].metadata.cost_estimate <= max_cost
            }

        # Filter by latency
        if max_latency_ms is not None:
            filtered_names = {
                name
                for name in filtered_names
                if self._tools[name].metadata.latency_ms <= max_latency_ms
            }

        return [self._tools[name].function for name in filtered_names]


# Global registry instance
_global_registry = ToolRegistry()


def get_global_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _global_registry


def register_tool(
    category: str,
    description: str | None = None,
    cost_estimate: float = 0.0,
    latency_ms: int = 100,
    requires_api_key: bool = False,
    api_provider: str | None = None,
    tags: list[str] | None = None,
):
    """
    Decorator to register a tool.

    Example:
        >>> @register_tool(category=ToolCategory.BETTING, cost_estimate=0.01)
        >>> @function_tool
        >>> def fetch_odds(sport: str) -> list[dict]:
        ...     return []
    """

    def decorator(func: Callable) -> Callable:
        _global_registry.register_tool(
            function=func,
            category=category,
            description=description,
            cost_estimate=cost_estimate,
            latency_ms=latency_ms,
            requires_api_key=requires_api_key,
            api_provider=api_provider,
            tags=tags,
        )
        return func

    return decorator


# ============================================
# TOOL REGISTRATION
# ============================================


def register_all_tools():
    """Register all tools from all modules."""
    # Import all tool modules
    from agent_kit.tools import (
        betting_tools,
        business,
        github_tools,
        hyperdim_viz,
        ml_training,
        ontology,
        semantic_graph,
        trading_tools,
        vector_space,
    )

    # Betting tools
    _global_registry.register_tool(
        betting_tools.fetch_odds,
        ToolCategory.BETTING,
        cost_estimate=0.01,
        requires_api_key=True,
        api_provider="odds_api",
        tags=["sports", "odds", "data"],
    )
    _global_registry.register_tool(
        betting_tools.fetch_player_props,
        ToolCategory.BETTING,
        cost_estimate=0.01,
        requires_api_key=True,
        api_provider="odds_api",
        tags=["sports", "props", "player"],
    )
    _global_registry.register_tool(
        betting_tools.detect_arbitrage,
        ToolCategory.BETTING,
        cost_estimate=0.0,
        tags=["arbitrage", "analysis"],
    )
    _global_registry.register_tool(
        betting_tools.calculate_implied_probability,
        ToolCategory.BETTING,
        cost_estimate=0.0,
        latency_ms=10,
        tags=["math", "probability"],
    )

    # Trading tools
    _global_registry.register_tool(
        trading_tools.fetch_market_data,
        ToolCategory.TRADING,
        cost_estimate=0.005,
        requires_api_key=True,
        api_provider="alpha_vantage",
        tags=["market", "data", "price"],
    )
    _global_registry.register_tool(
        trading_tools.calculate_rsi,
        ToolCategory.TRADING,
        cost_estimate=0.0,
        latency_ms=50,
        tags=["indicators", "technical"],
    )
    _global_registry.register_tool(
        trading_tools.calculate_macd,
        ToolCategory.TRADING,
        cost_estimate=0.0,
        latency_ms=50,
        tags=["indicators", "technical"],
    )
    _global_registry.register_tool(
        trading_tools.calculate_indicators,
        ToolCategory.TRADING,
        cost_estimate=0.0,
        latency_ms=100,
        tags=["indicators", "analysis"],
    )
    _global_registry.register_tool(
        trading_tools.execute_trade,
        ToolCategory.TRADING,
        cost_estimate=1.0,
        requires_api_key=True,
        api_provider="broker",
        tags=["execution", "trading"],
    )

    # ML tools (from existing registry)
    _global_registry.register_tool(
        ml_training.train_model,
        ToolCategory.ML_TRAINING,
        cost_estimate=0.10,
        latency_ms=5000,
        tags=["ml", "training"],
    )
    _global_registry.register_tool(
        ml_training.analyze_leverage,
        ToolCategory.ML_TRAINING,
        cost_estimate=0.05,
        latency_ms=2000,
        tags=["ml", "leverage"],
    )
    _global_registry.register_tool(
        ml_training.cluster_data,
        ToolCategory.ML_TRAINING,
        cost_estimate=0.02,
        latency_ms=1000,
        tags=["ml", "clustering"],
    )

    # Business tools
    _global_registry.register_tool(
        business.predict,
        ToolCategory.BUSINESS,
        cost_estimate=0.01,
        tags=["prediction", "business"],
    )
    _global_registry.register_tool(
        business.optimize,
        ToolCategory.BUSINESS,
        cost_estimate=0.01,
        tags=["optimization", "business"],
    )

    # Ontology tools
    _global_registry.register_tool(
        ontology.query_ontology,
        ToolCategory.ONTOLOGY,
        cost_estimate=0.0,
        latency_ms=50,
        tags=["sparql", "query"],
    )
    _global_registry.register_tool(
        ontology.add_ontology_statement,
        ToolCategory.ONTOLOGY,
        cost_estimate=0.0,
        latency_ms=50,
        tags=["sparql", "write"],
    )

    # Vector space tools
    _global_registry.register_tool(
        vector_space.embed,
        ToolCategory.VECTOR_SPACE,
        cost_estimate=0.0001,
        latency_ms=100,
        tags=["embeddings", "vector"],
    )
    _global_registry.register_tool(
        vector_space.query_vector_index,
        ToolCategory.VECTOR_SPACE,
        cost_estimate=0.0,
        latency_ms=50,
        tags=["search", "vector"],
    )

    # Semantic graph tools
    _global_registry.register_tool(
        semantic_graph.build_semantic_graph,
        ToolCategory.SEMANTIC_GRAPH,
        cost_estimate=0.05,
        latency_ms=2000,
        tags=["graph", "semantic"],
    )

    # Visualization tools
    try:
        _global_registry.register_tool(
            hyperdim_viz.generate_hyperdim_viz,
            ToolCategory.VISUALIZATION,
            cost_estimate=0.01,
            latency_ms=1000,
            tags=["viz", "hyperdim"],
        )
    except Exception as exc:
        logger.debug("Skipping hyperdimensional viz tool registration: %s", exc)

    # GitHub tools
    _global_registry.register_tool(
        github_tools.write_to_github,
        ToolCategory.GITHUB,
        cost_estimate=0.0,
        requires_api_key=True,
        api_provider="github",
        tags=["github", "write"],
    )


# Auto-register on import
register_all_tools()
