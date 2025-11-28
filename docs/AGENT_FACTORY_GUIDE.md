# Agent Factory Guide

**Purpose**: Centralized, dependency-injected agent creation for domain-specific workflows.

---

## 🎯 What is the Agent Factory?

The `AgentFactory` is a **Factory Pattern** implementation that creates domain-specific agents (orchestrators and specialists) with all their dependencies automatically injected.

**From first principles**: Instead of manually instantiating agents with complex dependencies, the factory:
1. Reads domain configuration (YAML)
2. Loads required tools dynamically
3. Injects dependencies (ontology, API keys, configs)
4. Assembles orchestrators with specialists

**Key Benefit**: You don't need to know how agents are constructed—just ask for a domain, get a ready-to-use orchestrator.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│   Domain Config (YAML)                  │
│   • Agents: [ForecastAgent, ...]        │
│   • Tools: [tools.business.predict, ...]│
│   • Risk Policies: {...}                │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│   AgentFactory                          │
│   1. Reads domain config                │
│   2. Loads tools dynamically            │
│   3. Creates specialists                │
│   4. Assembles orchestrator             │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│   OntologyOrchestratorAgent             │
│   • Specialists: [ForecastAgent, ...]   │
│   • Tools: [predict, optimize, ...]     │
│   • Risk Policies: {...}                 │
│   • Ready to run!                       │
└─────────────────────────────────────────┘
```

---

## 🔑 Key Components

### 1. Agent Registry

**What**: Maps agent names to Python classes.

```python
AGENT_REGISTRY: dict[str, Type[BaseAgent]] = {
    "ForecastAgent": ForecastAgent,
    "OptimizerAgent": OptimizerAgent,
    "AlgoTradingAgent": AlgoTradingAgent,
    "PropBettingAgent": PropBettingAgent,
    "OntologyAgent": OntologyAgent,
}
```

**Why**: Allows dynamic agent creation by name (from YAML config) without hardcoding.

### 2. Domain Registry Integration

**What**: Reads domain YAML files to discover:
- Which agents belong to a domain
- Which tools are allowed
- What risk policies apply
- What output schema to use

**Example** (`business.yaml`):
```yaml
default_agents:
  - ForecastAgent
  - OptimizerAgent

allowed_tools:
  - tools.business.predict
  - tools.business.optimize
  - tools.ontology.query_ontology

risk_policies:
  max_forecast_horizon_days: 90
  min_confidence_threshold: 0.7
```

### 3. Dynamic Tool Loading

**What**: Loads tool functions from string paths using `importlib`.

**How**:
```python
tool_path = "tools.business.predict"
# Splits into: module="tools.business", func="predict"
# Dynamically imports: from agent_kit.tools.business import predict
```

**Why**: Tools are defined in YAML, not hardcoded. Easy to add/remove tools per domain.

### 4. Dependency Injection

**What**: Automatically provides agents with:
- Ontology loaders (for SPARQL queries)
- Grok configs (API keys, temperature, etc.)
- Domain-specific defaults

**Why**: Agents don't need to know where dependencies come from. Factory handles it.

---

## 📋 Core Methods

### `create_orchestrator(domain: str) -> BaseAgent`

**Purpose**: Create a complete orchestrator for a domain.

**What it does**:
1. Loads domain config from registry
2. Creates specialist agents
3. Loads allowed tools
4. Loads ontology
5. Assembles orchestrator with all dependencies

**Example**:
```python
factory = AgentFactory()
orchestrator = factory.create_orchestrator("business")
result = orchestrator.run(AgentTask(prompt="Forecast revenue"))
```

**Returns**: `OntologyOrchestratorAgent` ready to execute tasks.

### `create_agent(agent_name: str, domain: str) -> BaseAgent`

**Purpose**: Create a single specialist agent.

**What it does**:
1. Looks up agent class in registry
2. Loads domain config (if provided)
3. Injects dependencies based on agent type
4. Returns instantiated agent

**Example**:
```python
factory = AgentFactory()
forecast_agent = factory.create_agent("ForecastAgent", domain="business")
```

**Agent Types**:
- **Grok-based** (AlgoTradingAgent, PropBettingAgent): Need ontology + Grok config
- **Simple** (ForecastAgent, OptimizerAgent): Just instantiate

### `_load_tools(tool_paths: list[str]) -> list[Callable]`

**Purpose**: Dynamically import tool functions.

**How it works**:
```python
# Input: ["tools.business.predict"]
# 1. Split: module="tools.business", func="predict"
# 2. Import: from agent_kit.tools.business import predict
# 3. Return: [predict]
```

**Error handling**: Warns on missing tools, continues with available ones.

### `_load_ontology(ontology_iri: str) -> OntologyLoader`

**Purpose**: Load ontology file from IRI.

**Mapping**:
- IRI: `http://agent_kit.io/business#`
- File: `assets/ontologies/business.ttl`

**Fallback**: Uses `core.ttl` if domain-specific ontology not found.

---

## 🎨 Design Patterns Used

### 1. Factory Pattern
**What**: Centralizes object creation logic.
**Why**: Avoids scattered `new Agent(...)` calls with complex dependencies.

### 2. Dependency Injection
**What**: Factory provides dependencies, agents don't create them.
**Why**: Testable (can inject mocks), flexible (swap implementations).

### 3. Registry Pattern
**What**: Domain configs stored in registry, looked up by name.
**Why**: Configuration-driven, no hardcoded mappings.

### 4. Builder Pattern (`IndustryAgentBuilder`)
**What**: Fluent API for building custom agents.
**Why**: Easy to create agents for new industries not yet in registry.

---

## 💡 Usage Examples

### Example 1: Create Business Orchestrator

```python
from agent_kit.factories import AgentFactory

# Create factory (uses global domain registry)
factory = AgentFactory()

# Create orchestrator for business domain
orchestrator = factory.create_orchestrator("business")

# Use it
from agent_kit.agents.base import AgentTask
result = orchestrator.run(AgentTask(prompt="Forecast revenue for next 30 days"))
```

**What happens**:
1. Factory reads `business.yaml`
2. Creates `ForecastAgent` and `OptimizerAgent`
3. Loads tools: `predict`, `optimize`, `query_ontology`
4. Loads ontology: `assets/ontologies/business.ttl`
5. Assembles orchestrator with risk policies

### Example 2: Create Single Agent

```python
factory = AgentFactory()

# Create just the forecast agent
forecast_agent = factory.create_agent("ForecastAgent", domain="business")

# Use it directly
result = forecast_agent.run(AgentTask(prompt="Forecast Q1 revenue"))
```

### Example 3: Custom Configuration

```python
from agent_kit.agents.grok_agent import GrokConfig

# Override defaults
grok_config = GrokConfig(
    api_key="custom-key",
    temperature=0.5,
    max_tokens=2048
)

orchestrator = factory.create_orchestrator(
    "business",
    grok_config=grok_config
)
```

### Example 4: New Industry (Builder Pattern)

```python
from agent_kit.factories import IndustryAgentBuilder
from agent_kit.ontology.loader import OntologyLoader
from agent_kit.agents.grok_agent import GrokAgent

# Load custom ontology
loader = OntologyLoader("assets/ontologies/healthcare.ttl")
loader.load()

# Build agent
builder = IndustryAgentBuilder(loader)
agent = builder.build_agent(
    name="DiagnosticAgent",
    agent_iri="health:DiagnosticAgent",
    tools=[diagnose_patient, query_medical_db],
    base_class=GrokAgent
)
```

---

## 🔗 Integration with Unified SDK

The factory can be extended to create **OpenAI SDK agents** via adapters:

```python
from agent_kit.adapters import OntologyAgentAdapter
from agents import Agent

# Create OpenAI SDK agent
openai_agent = Agent(
    name="ForecastAgent",
    instructions="Forecast business metrics.",
    tools=[predict, optimize],
)

# Wrap with ontology adapter
adapter = OntologyAgentAdapter(openai_agent, ontology, "business")

# Use with OpenAI SDK Runner
from agents import Runner
result = await Runner.run(adapter.agent, input="Forecast revenue")
```

**Future Enhancement**: Factory could create OpenAI SDK agents directly:

```python
# Hypothetical future API
factory = AgentFactory(sdk="openai")  # or "grok", "adk"
orchestrator = factory.create_orchestrator("business")
# Returns OpenAI SDK Agent wrapped with OntologyAgentAdapter
```

---

## 🎯 Key Benefits

### 1. **Configuration-Driven**
- Add new domains by creating YAML files
- No code changes needed for new domains

### 2. **Dependency Management**
- Factory handles all dependencies
- Agents don't need to know where configs come from

### 3. **Testability**
- Easy to inject mocks for testing
- Can create agents without real API keys

### 4. **Extensibility**
- Add new agents by registering them
- Add new tools by updating YAML
- Use `IndustryAgentBuilder` for custom industries

### 5. **Consistency**
- All agents created the same way
- Enforces domain policies automatically

---

## 🔧 Advanced Usage

### Custom Domain Registry

```python
from agent_kit.domains.registry import DomainRegistry

# Create custom registry
custom_registry = DomainRegistry()
custom_registry.load_domain("custom_domain.yaml")

# Use with factory
factory = AgentFactory(domain_registry=custom_registry)
```

### Pre-loaded Ontology

```python
from agent_kit.ontology.loader import OntologyLoader

# Load once, reuse
ontology = OntologyLoader("assets/ontologies/business.ttl")
ontology.load()

# Share across factory
factory = AgentFactory(ontology_loader=ontology)
```

### Agent-Specific Overrides

```python
# Override config for specific agent
orchestrator = factory.create_orchestrator(
    "business",
    ForecastAgent={"custom_param": "value"}
)
```

---

## 📊 Factory vs Manual Creation

### Manual (Without Factory)
```python
# ❌ Complex, error-prone
ontology = OntologyLoader("assets/ontologies/business.ttl")
ontology.load()

grok_config = GrokConfig(api_key=os.getenv("XAI_API_KEY"))

forecast_agent = ForecastAgent()
optimizer_agent = OptimizerAgent()

tools = [predict, optimize, query_ontology]
# ... load tools manually ...

orchestrator = OntologyOrchestratorAgent(
    domain="business",
    specialists=[forecast_agent, optimizer_agent],
    tools=tools,
    ontology=ontology,
    risk_policies={...},  # Where do these come from?
    output_schema="BusinessOptimizationResult",
    grok_config=grok_config,
)
```

### With Factory
```python
# ✅ Simple, declarative
factory = AgentFactory()
orchestrator = factory.create_orchestrator("business")
```

**Difference**: Factory handles all the complexity. You just specify the domain.

---

## 🚀 Next Steps

1. **Use Factory in CLI**: `ontology-kit run --domain business`
2. **Extend for OpenAI SDK**: Add adapter support to factory
3. **Add More Domains**: Create YAML files for new industries
4. **Custom Agents**: Use `IndustryAgentBuilder` for specialized needs

---

## 📚 References

- **Factory Pattern**: [Gang of Four Design Patterns](https://en.wikipedia.org/wiki/Factory_method_pattern)
- **Dependency Injection**: [Martin Fowler - Inversion of Control](https://martinfowler.com/articles/injection.html)
- **Registry Pattern**: [Patterns of Enterprise Application Architecture](https://martinfowler.com/eaaCatalog/registry.html)

---

**Status**: ✅ Production-ready  
**Location**: `src/agent_kit/factories/agent_factory.py`






