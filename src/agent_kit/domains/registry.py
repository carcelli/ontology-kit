"""
Domain registry for dynamic configuration loading.

From first principles: Registry pattern centralizes object creation/lookup,
avoiding scattered config parsing. Caching prevents redundant I/O.

Design choices:
- Pathlib for cross-platform path handling
- yaml.safe_load to prevent code injection
- DomainConfig as dict wrapper for dot-access ergonomics
- Explicit ValueError on missing domains (fail fast)

References:
- Registry Pattern: Martin Fowler, Patterns of Enterprise Application Architecture
- YAML security: https://yaml.org/spec/1.2/spec.html#id2760395
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class DomainConfig(dict):
    """
    Configuration for a domain with dot-access convenience.

    Example:
        >>> cfg = DomainConfig({"id": "business", "risk_policies": {"max_days": 90}})
        >>> cfg.id  # 'business'
        >>> cfg.risk_policies['max_days']  # 90
    """

    def __getattr__(self, name: str) -> Any:
        """Enable dot-access: cfg.id instead of cfg['id']."""
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"DomainConfig has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """Support assignment: cfg.id = 'new_value'."""
        self[name] = value


class DomainRegistry:
    """
    Loads and caches domain configurations from YAML files.

    From first principles: Singleton-like pattern (one registry per app context)
    that lazily loads configs on first access, caching for subsequent lookups.

    Thread-safety: Not thread-safe. Wrap in lock if used in multi-threaded context.

    Example:
        >>> registry = DomainRegistry()
        >>> business_cfg = registry.get("business")
        >>> business_cfg.default_agents  # ['ForecastAgent', 'OptimizerAgent']
        >>> registry.list_domains()  # ['business', 'betting', 'trading']
    """

    def __init__(self, base_path: Path | None = None) -> None:
        """
        Initialize registry with config directory.

        Args:
            base_path: Path to directory containing domain YAML files.
                      Defaults to same directory as this module.
        """
        self.base_path = base_path or Path(__file__).parent
        self._cache: dict[str, DomainConfig] = {}

    def get(self, domain: str) -> DomainConfig:
        """
        Get configuration for a domain, loading from disk if not cached.

        Args:
            domain: Domain identifier (e.g., 'business', 'betting', 'trading')

        Returns:
            DomainConfig with domain settings

        Raises:
            ValueError: If domain YAML file doesn't exist
            yaml.YAMLError: If YAML is malformed

        Example:
            >>> cfg = registry.get('business')
            >>> cfg.output_schema  # 'BusinessOptimizationResult'
        """
        # Check cache first
        if domain in self._cache:
            return self._cache[domain]

        # Load from disk
        config_path = self.base_path / f"{domain}.yaml"
        if not config_path.exists():
            available = self.list_domains()
            raise ValueError(
                f"Unknown domain: '{domain}'. "
                f"Available domains: {available}. "
                f"Create {config_path} to add new domain."
            )

        with config_path.open("r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in {config_path}: {e}") from e

        # Validate required fields
        required_fields = ["id", "description", "default_agents", "allowed_tools"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(
                f"Domain config {config_path} missing required fields: {missing}"
            )

        # Ensure ID matches filename
        if data["id"] != domain:
            raise ValueError(
                f"Domain ID mismatch: file is '{domain}.yaml' but ID is '{data['id']}'"
            )

        cfg = DomainConfig(data)
        self._cache[domain] = cfg
        return cfg

    def list_domains(self) -> list[str]:
        """
        List all available domains by scanning YAML files.

        Returns:
            List of domain identifiers (e.g., ['business', 'betting', 'trading'])

        Example:
            >>> domains = registry.list_domains()
            >>> 'business' in domains  # True
        """
        # Generator comprehension for efficiency
        return sorted(
            path.stem for path in self.base_path.glob("*.yaml")
            if not path.stem.startswith("_")  # Ignore _templates, etc.
        )

    def reload(self, domain: str) -> DomainConfig:
        """
        Force reload of a domain config from disk (bypasses cache).

        Useful during development when YAML files change.

        Args:
            domain: Domain to reload

        Returns:
            Fresh DomainConfig

        Example:
            >>> cfg = registry.reload('business')  # Re-reads business.yaml
        """
        if domain in self._cache:
            del self._cache[domain]
        return self.get(domain)

    def validate_tool(self, domain: str, tool_path: str) -> bool:
        """
        Check if a tool is allowed in a domain.

        Args:
            domain: Domain identifier
            tool_path: Tool path (e.g., 'tools.business.predict')

        Returns:
            True if tool is in allowed_tools list

        Example:
            >>> registry.validate_tool('business', 'tools.business.predict')  # True
            >>> registry.validate_tool('business', 'tools.betting_tools.fetch_odds')  # False
        """
        cfg = self.get(domain)
        return tool_path in cfg.allowed_tools

    def get_risk_policy(self, domain: str, policy_name: str) -> Any:
        """
        Get a specific risk policy value for a domain.

        Args:
            domain: Domain identifier
            policy_name: Policy key (e.g., 'max_position_size')

        Returns:
            Policy value or None if not set

        Example:
            >>> registry.get_risk_policy('trading', 'max_position_size')  # 0.02
        """
        cfg = self.get(domain)
        return cfg.get("risk_policies", {}).get(policy_name)


# Global registry instance (singleton pattern)
_global_registry: DomainRegistry | None = None


def get_global_registry() -> DomainRegistry:
    """
    Get the global domain registry (lazy singleton).

    Returns:
        Shared DomainRegistry instance

    Example:
        >>> from agent_kit.domains import get_global_registry
        >>> registry = get_global_registry()
        >>> cfg = registry.get('business')
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = DomainRegistry()
    return _global_registry

