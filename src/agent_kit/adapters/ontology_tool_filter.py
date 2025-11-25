"""
Tool filter that restricts agent tools based on domain allowlist.

From first principles: Domain isolation prevents agents from accessing
tools outside their domain. This enforces security and prevents
cross-domain contamination.
"""

from __future__ import annotations

from typing import Any

from agents import Tool, RunContextWrapper

from agent_kit.domains.registry import DomainRegistry, get_global_registry


class OntologyToolFilter:
    """
    Filters tools based on domain allowlist configuration.

    Ensures agents only have access to tools allowed in their domain
    configuration (defined in domain YAML files).

    Example:
        >>> from agents import Agent
        >>> from agent_kit.adapters import OntologyToolFilter
        >>>
        >>> filter = OntologyToolFilter("business")
        >>> filtered_tools = filter.filter_tools(agent.tools)
    """

    def __init__(self, domain: str):
        """
        Initialize filter with domain configuration.

        Args:
            domain: Domain identifier
        """
        self.domain = domain
        registry = get_global_registry()
        self.domain_config = registry.get(domain)

    def filter_tools(self, tools: list[Tool]) -> list[Tool]:
        """
        Filter tools by domain allowlist.

        Args:
            tools: List of tools to filter

        Returns:
            Filtered list of tools allowed in domain
        """
        if not self.domain_config or not self.domain_config.allowed_tools:
            # No restrictions - return all tools
            return tools

        allowed_tools = set(self.domain_config.allowed_tools)
        filtered = []

        for tool in tools:
            tool_name = self._get_tool_name(tool)
            if self._is_tool_allowed(tool_name, allowed_tools):
                filtered.append(tool)

        return filtered

    def _get_tool_name(self, tool: Tool) -> str:
        """Extract tool name from tool object."""
        # Try various attributes
        if hasattr(tool, "name"):
            return tool.name
        if hasattr(tool, "__name__"):
            return tool.__name__
        if hasattr(tool, "function"):
            return getattr(tool.function, "__name__", "")
        return str(tool)

    def _is_tool_allowed(self, tool_name: str, allowed_tools: set[str]) -> bool:
        """
        Check if tool is in domain allowlist.

        Supports multiple naming patterns:
        - "predict" (simple name)
        - "tools.business.predict" (full path)
        - "agent_kit.tools.business.predict" (module path)
        """
        # Check exact match
        if tool_name in allowed_tools:
            return True

        # Check domain-prefixed match
        domain_path = f"tools.{self.domain}.{tool_name}"
        if domain_path in allowed_tools:
            return True

        # Check full module path
        full_path = f"agent_kit.tools.{self.domain}.{tool_name}"
        if full_path in allowed_tools:
            return True

        return False

