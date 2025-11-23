"""
Industry-Agnostic Agent Factory

Pattern for spawning domain-specific agents from ontologies.
Use this to create agents for ANY industry (betting, trading, healthcare, logistics, etc.)

Architecture:
1. Define domain ontology with agent specs, tools, risk rules
2. Factory queries ontology and instantiates agent
3. Agent inherits instructions, tools, and constraints from ontology
"""
from __future__ import annotations

from typing import Any, Type

from agent_kit.agents.algo_trading_agent import AlgoTradingAgent
from agent_kit.agents.base import GrokAgent, GrokConfig
from agent_kit.agents.ontology_agent import OntologyAgent
from agent_kit.agents.prop_betting_agent import PropBettingAgent
from agent_kit.ontology.loader import OntologyLoader


class AgentFactory:
    """
    Factory for creating domain-specific agents from ontologies.
    
    Example:
        >>> loader = OntologyLoader('assets/ontologies/betting.ttl')
        >>> loader.load()
        >>> factory = AgentFactory(loader)
        >>> agent = factory.create_agent("bet:PropBettingAgent", bankroll=10000)
    """
    
    # Registry of agent classes by IRI
    AGENT_REGISTRY: dict[str, Type[GrokAgent | OntologyAgent]] = {
        "bet:PropBettingAgent": PropBettingAgent,
        "trade:AlgoTradingAgent": AlgoTradingAgent,
        # Add more as you build them
    }
    
    def __init__(self, ontology: OntologyLoader):
        """
        Initialize factory with ontology.
        
        Args:
            ontology: Loaded ontology with agent definitions
        """
        self.ontology = ontology
    
    def create_agent(
        self,
        agent_iri: str,
        grok_config: GrokConfig | None = None,
        **agent_kwargs
    ) -> GrokAgent | OntologyAgent:
        """
        Create agent from ontology definition.
        
        Args:
            agent_iri: Agent IRI (e.g., "bet:PropBettingAgent")
            grok_config: Optional Grok configuration
            **agent_kwargs: Additional agent-specific parameters
        
        Returns:
            Instantiated agent
        
        Raises:
            ValueError: If agent IRI not found in registry or ontology
        """
        # Check if agent is in registry
        if agent_iri not in self.AGENT_REGISTRY:
            raise ValueError(
                f"Agent {agent_iri} not found in registry. "
                f"Available: {list(self.AGENT_REGISTRY.keys())}"
            )
        
        # Query ontology for agent configuration
        agent_config = self._query_agent_config(agent_iri)
        
        # Get agent class
        agent_class = self.AGENT_REGISTRY[agent_iri]
        
        # Merge ontology config with provided kwargs
        merged_kwargs = {**agent_config, **agent_kwargs}
        
        # Instantiate agent
        return agent_class(
            ontology=self.ontology,
            grok_config=grok_config,
            **merged_kwargs
        )
    
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
            raise ValueError(f"Agent IRI must have namespace prefix (e.g., 'bet:PropBettingAgent')")
        
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
        base_class: Type[GrokAgent | OntologyAgent] = OntologyAgent,
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


