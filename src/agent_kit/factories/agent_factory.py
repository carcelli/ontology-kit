"""
Industry-Agnostic Agent Factory with Dependency Injection

Pattern for spawning domain-specific agents from ontologies.
Use this to create agents for ANY industry (betting, trading, healthcare, logistics, etc.)

From first principles: Dependency Injection decouples object creation from usage,
allowing runtime configuration and testability. Factory pattern centralizes
instantiation logic, ensuring consistent agent creation.

Architecture:
1. Domain configs (YAML) define relations (agents/tools/policies)
2. Factory queries registry and assembles dependencies
3. Agents receive injected deps (clients, ontologies, tools)
4. Orchestrator coordinates specialists via handoffs

Design choices:
- Registry-driven to avoid hardcoded class mappings
- Dynamic tool loading via importlib for extensibility
- Client injection for centralized API management
- Comprehensive error messages for debugging

References:
- Dependency Injection: Martin Fowler, Inversion of Control Containers
- Factory Pattern: Gang of Four Design Patterns
"""
from __future__ import annotations

import os
from importlib import import_module
from typing import Any, Callable, Type

from agent_kit.agents.algo_trading_agent import AlgoTradingAgent
from agent_kit.agents.base import BaseAgent
from agent_kit.agents.business_agents import ForecastAgent, OptimizerAgent
from agent_kit.agents.grok_agent import GrokConfig
from agent_kit.agents.ontology_agent import OntologyAgent
from agent_kit.agents.prop_betting_agent import PropBettingAgent
from agent_kit.domains.registry import DomainRegistry, get_global_registry
from agent_kit.ontology.loader import OntologyLoader


class AgentFactory:
    """
    Factory for creating domain-specific agents with dependency injection.

    From first principles: Centralizes instantiation logic, injecting dependencies
    (clients, ontologies, tools) to avoid hardcoded coupling.

    Example:
        >>> factory = AgentFactory()
        >>> orchestrator = factory.create_orchestrator("business")
        >>> result = orchestrator.run("Forecast next 30 days")
    """

    # Registry of agent classes by name
    AGENT_REGISTRY: dict[str, Type[BaseAgent]] = {
        "ForecastAgent": ForecastAgent,
        "OptimizerAgent": OptimizerAgent,
        "AlgoTradingAgent": AlgoTradingAgent,
        "PropBettingAgent": PropBettingAgent,
        "OntologyAgent": OntologyAgent,
    }

    def __init__(
        self,
        domain_registry: DomainRegistry | None = None,
        ontology_loader: OntologyLoader | None = None,
        grok_api_key: str | None = None,
    ):
        """
        Initialize factory with injected dependencies.

        Args:
            domain_registry: Registry for domain configs (defaults to global)
            ontology_loader: Ontology loader (defaults to None, loaded per domain)
            grok_api_key: xAI API key (defaults to XAI_API_KEY env var)

        Raises:
            ValueError: If Grok API key not provided and not in environment
        """
        self.registry = domain_registry or get_global_registry()
        self.ontology_loader = ontology_loader
        self.grok_api_key = grok_api_key or os.getenv("XAI_API_KEY")

        # Warn if no API key (allow for testing with mock agents)
        if not self.grok_api_key:
            import warnings
            warnings.warn(
                "No XAI_API_KEY found. Grok-based agents will fail. "
                "Set XAI_API_KEY env var or pass grok_api_key to factory."
            )

    def create_orchestrator(self, domain: str, **kwargs) -> BaseAgent:
        """
        Create domain-specific orchestrator with specialists and tools.

        From first principles: Orchestrator is a coordinator (not executor) that
        delegates to specialists via handoffs, enforcing domain policies.

        Args:
            domain: Domain identifier (e.g., 'business', 'betting', 'trading')
            **kwargs: Override defaults (e.g., grok_config, custom tools)

        Returns:
            Orchestrator agent ready to run

        Raises:
            ValueError: If domain unknown or agents missing

        Example:
            >>> factory = AgentFactory()
            >>> orch = factory.create_orchestrator("business")
            >>> result = orch.run("Forecast revenue for next 30 days")
        """
        cfg = self.registry.get(domain)

        # Load specialists from config
        specialists = self._create_specialists(domain, cfg, **kwargs)

        # Load tools dynamically
        tools = self._load_tools(cfg.allowed_tools)

        # Load ontology if needed
        ontology = self._load_ontology(cfg.ontology_iri)

        # Create orchestrator (simplified; enhance with handoffs in orchestrator.py)
        from agent_kit.agents.orchestrator import OntologyOrchestratorAgent

        grok_config = kwargs.get("grok_config") or GrokConfig(
            api_key=self.grok_api_key,
            temperature=0.7,
            max_tokens=4096,
        )

        orchestrator = OntologyOrchestratorAgent(
            domain=domain,
            specialists=specialists,
            tools=tools,
            ontology=ontology,
            risk_policies=cfg.get("risk_policies", {}),
            output_schema=cfg.get("output_schema"),
            grok_config=grok_config,
        )

        return orchestrator

    def _create_specialists(
        self, domain: str, cfg, **kwargs
    ) -> list[BaseAgent]:
        """
        Instantiate specialist agents from domain config.

        Args:
            domain: Domain identifier
            cfg: Domain config
            **kwargs: Agent-specific overrides

        Returns:
            List of specialist agents

        Raises:
            ValueError: If agent class not in registry
        """
        specialists = []
        grok_config = kwargs.get("grok_config") or GrokConfig(
            api_key=self.grok_api_key
        )

        for agent_name in cfg.default_agents:
            if agent_name not in self.AGENT_REGISTRY:
                available = list(self.AGENT_REGISTRY.keys())
                raise ValueError(
                    f"Agent '{agent_name}' not found in registry for domain '{domain}'. "
                    f"Available agents: {available}"
                )

            agent_class = self.AGENT_REGISTRY[agent_name]

            # Inject dependencies based on agent type
            agent_kwargs = kwargs.get(agent_name, {})

            # For Grok-based agents (betting/trading), inject ontology + config
            if agent_class in [AlgoTradingAgent, PropBettingAgent]:
                ontology = self._load_ontology(cfg.ontology_iri)
                specialist = agent_class(
                    ontology=ontology,
                    grok_config=grok_config,
                    **agent_kwargs
                )
            # For simple BaseAgent subclasses (business agents)
            elif agent_class in [ForecastAgent, OptimizerAgent]:
                specialist = agent_class(**agent_kwargs)
            else:
                # Fallback: attempt instantiation
                specialist = agent_class(**agent_kwargs)

            specialists.append(specialist)

        return specialists

    def _load_tools(self, tool_paths: list[str]) -> list[Callable]:
        """
        Dynamically load tool functions from module paths.

        Args:
            tool_paths: List of dot-separated paths (e.g., 'tools.business.predict')

        Returns:
            List of callable tool functions

        Example:
            >>> tools = factory._load_tools(['tools.business.predict'])
            >>> tools[0].__name__  # 'predict'
        """
        tools = []
        for tool_path in tool_paths:
            try:
                # Parse path: 'tools.business.predict' -> module='tools.business', func='predict'
                parts = tool_path.split(".")
                module_path = ".".join(parts[:-1])
                func_name = parts[-1]

                # Dynamic import
                module = import_module(f"agent_kit.{module_path}")
                func = getattr(module, func_name)
                tools.append(func)
            except (ImportError, AttributeError) as e:
                import warnings
                warnings.warn(f"Failed to load tool '{tool_path}': {e}")

        return tools

    def _load_ontology(self, ontology_iri: str) -> OntologyLoader:
        """
        Load ontology by IRI (maps to file path).

        Args:
            ontology_iri: Ontology IRI (e.g., 'http://agent_kit.io/business#')

        Returns:
            Loaded OntologyLoader

        Note:
            In production, map IRI -> file path via registry.
            For now, use heuristic: IRI fragment -> assets/ontologies/{fragment}.ttl
        """
        if self.ontology_loader:
            return self.ontology_loader

        # Extract fragment from IRI (e.g., 'business' from 'http://...io/business#')
        fragment = ontology_iri.rstrip("#/").split("/")[-1]
        ontology_path = f"assets/ontologies/{fragment}.ttl"

        # Check if file exists; if not, warn and use core.ttl
        import pathlib
        if not pathlib.Path(ontology_path).exists():
            import warnings
            warnings.warn(
                f"Ontology file not found: {ontology_path}. Falling back to core.ttl"
            )
            ontology_path = "assets/ontologies/core.ttl"

        loader = OntologyLoader(ontology_path)
        loader.load()
        return loader

    def create_agent(
        self,
        agent_name: str,
        domain: str | None = None,
        **kwargs
    ) -> BaseAgent:
        """
        Create individual agent (specialist) by name.

        Args:
            agent_name: Agent class name (e.g., 'ForecastAgent')
            domain: Optional domain to inherit config from
            **kwargs: Agent-specific parameters

        Returns:
            Instantiated agent

        Example:
            >>> agent = factory.create_agent('ForecastAgent', domain='business')
        """
        if agent_name not in self.AGENT_REGISTRY:
            raise ValueError(
                f"Agent '{agent_name}' not found. "
                f"Available: {list(self.AGENT_REGISTRY.keys())}"
            )

        agent_class = self.AGENT_REGISTRY[agent_name]

        # Load domain config if provided
        if domain:
            cfg = self.registry.get(domain)
            # Merge domain defaults with kwargs
            defaults = cfg.get("defaults", {})
            kwargs = {**defaults, **kwargs}

        # Instantiate based on agent type
        if agent_class in [AlgoTradingAgent, PropBettingAgent]:
            # Grok-based agents need ontology
            ontology_iri = kwargs.pop("ontology_iri", "http://agent_kit.io/business#")
            ontology = self._load_ontology(ontology_iri)
            grok_config = kwargs.pop("grok_config", None) or GrokConfig(
                api_key=self.grok_api_key
            )
            return agent_class(
                ontology=ontology,
                grok_config=grok_config,
                **kwargs
            )
        else:
            # Simple agents (ForecastAgent, OptimizerAgent)
            return agent_class(**kwargs)

    def _query_agent_config(self, agent_iri: str) -> dict[str, Any]:
        """
        Query ontology for agent configuration.

        Extracts:
        - Default parameters (bankroll, portfolio_value, etc.)
        - Capabilities (strategies, tools)
        - Constraints (risk rules)
        """
        # Extract namespace prefix and local name
        if ":" not in agent_iri:
            raise ValueError("Agent IRI must have namespace prefix (e.g., 'bet:PropBettingAgent')")

        prefix, local_name = agent_iri.split(":", 1)

        # Query for agent properties
        sparql = f"""
            PREFIX {prefix}: <http://agent-kit.com/ontology/{prefix.replace('bet', 'betting').replace('trade', 'trading')}#>
            PREFIX core: <http://agent-kit.com/ontology/core#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?capability ?instructions
            WHERE {{
                {agent_iri} a core:Agent .
                OPTIONAL {{ {agent_iri} core:hasCapability ?capability . }}
                OPTIONAL {{ {agent_iri} core:hasInstructions ?instructions . }}
            }}
        """

        results = list(self.ontology.graph.query(sparql))

        config = {}

        if results:
            capabilities = [str(row.capability) for row in results if row.capability]
            if capabilities:
                config["capabilities"] = capabilities

            instructions = [str(row.instructions) for row in results if row.instructions]
            if instructions:
                config["instructions"] = instructions[0]

        return config

    def list_available_agents(self) -> dict[str, dict[str, Any]]:
        """
        List all agents available in ontology.

        Returns:
            Dict mapping agent IRI -> agent metadata
        """
        sparql = """
            PREFIX core: <http://agent-kit.com/ontology/core#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?agent ?label ?instructions
            WHERE {
                ?agent a core:Agent .
                OPTIONAL { ?agent rdfs:label ?label . }
                OPTIONAL { ?agent core:hasInstructions ?instructions . }
            }
        """

        results = list(self.ontology.graph.query(sparql))

        agents = {}
        for row in results:
            agent_iri = str(row.agent)
            agents[agent_iri] = {
                "label": str(row.label) if row.label else None,
                "instructions": str(row.instructions) if row.instructions else None
            }

        return agents


class IndustryAgentBuilder:
    """
    Builder for creating custom agents for new industries.

    Use this when you want to spawn an agent for a domain NOT yet in the registry.

    Example:
        >>> # Create healthcare diagnosis agent
        >>> loader = OntologyLoader('assets/ontologies/healthcare.ttl')
        >>> loader.load()
        >>> builder = IndustryAgentBuilder(loader)
        >>> agent = builder.build_agent(
        ...     name="DiagnosticAgent",
        ...     agent_iri="health:DiagnosticAgent",
        ...     tools=["diagnose_patient", "query_medical_ontology"],
        ...     base_class=GrokAgent
        ... )
    """

    def __init__(self, ontology: OntologyLoader):
        """Initialize builder with ontology."""
        self.ontology = ontology

    def build_agent(
        self,
        name: str,
        agent_iri: str,
        tools: list[Any],
        base_class: type[GrokAgent | OntologyAgent] = OntologyAgent,
        grok_config: GrokConfig | None = None,
        **kwargs
    ) -> GrokAgent | OntologyAgent:
        """
        Build custom agent for new industry.

        Args:
            name: Agent name
            agent_iri: IRI in ontology (e.g., "health:DiagnosticAgent")
            tools: List of tools (functions decorated with @function_tool)
            base_class: Base agent class (GrokAgent or OntologyAgent)
            grok_config: Optional Grok configuration
            **kwargs: Additional agent parameters

        Returns:
            Instantiated agent
        """
        # Query ontology for instructions
        instructions = self._query_instructions(agent_iri)

        # Instantiate agent
        if base_class == OntologyAgent:
            return OntologyAgent(
                name=name,
                ontology_path=self.ontology.ontology_path,
                **kwargs
            )
        elif issubclass(base_class, GrokAgent):
            return base_class(
                name=name,
                ontology=self.ontology,
                system_prompt=instructions,
                grok_config=grok_config or GrokConfig(),
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported base class: {base_class}")

    def _query_instructions(self, agent_iri: str) -> str:
        """Query ontology for agent instructions."""
        sparql = f"""
            PREFIX core: <http://agent-kit.com/ontology/core#>

            SELECT ?instructions
            WHERE {{
                <{agent_iri}> core:hasInstructions ?instructions .
            }}
        """

        results = list(self.ontology.graph.query(sparql))
        if results:
            return str(results[0].instructions)

        return f"You are the {agent_iri} agent with ontology-driven capabilities."


# ============================================
# USAGE EXAMPLES
# ============================================

def example_betting_agent():
    """Example: Create prop betting agent."""
    loader = OntologyLoader('assets/ontologies/betting.ttl')
    loader.load()

    factory = AgentFactory(loader)

    # Create betting agent with custom bankroll
    agent = factory.create_agent(
        "bet:PropBettingAgent",
        bankroll=10000.0,
        strategy="ValueBetting"
    )

    print(f"Created agent: {agent}")
    return agent


def example_trading_agent():
    """Example: Create algo trading agent."""
    loader = OntologyLoader('assets/ontologies/trading.ttl')
    loader.load()

    factory = AgentFactory(loader)

    # Create trading agent with custom portfolio
    agent = factory.create_agent(
        "trade:AlgoTradingAgent",
        portfolio_value=100000.0,
        strategy="MeanReversion"
    )

    print(f"Created agent: {agent}")
    return agent


def example_custom_industry():
    """Example: Create agent for new industry (e.g., supply chain)."""
    # 1. First, create ontology: assets/ontologies/supply_chain.ttl
    # 2. Define agent, tools, risk rules in ontology
    # 3. Build agent with factory

    loader = OntologyLoader('assets/ontologies/supply_chain.ttl')
    loader.load()

    builder = IndustryAgentBuilder(loader)

    # Define custom tools
    from agents import function_tool

    @function_tool
    def optimize_route(origin: str, destination: str) -> dict:
        """Optimize delivery route."""
        return {"route": f"{origin} -> {destination}", "cost": 100}

    @function_tool
    def predict_demand(product_id: str) -> float:
        """Predict product demand."""
        return 1500.0

    # Build agent
    agent = builder.build_agent(
        name="SupplyChainAgent",
        agent_iri="supply:OptimizationAgent",
        tools=[optimize_route, predict_demand],
        base_class=GrokAgent
    )

    print(f"Created custom agent: {agent}")
    return agent


if __name__ == "__main__":
    # Run examples
    print("=== Betting Agent ===")
    example_betting_agent()

    print("\n=== Trading Agent ===")
    example_trading_agent()

    print("\n=== Custom Industry Agent ===")
    # example_custom_industry()  # Uncomment when supply_chain.ttl exists


