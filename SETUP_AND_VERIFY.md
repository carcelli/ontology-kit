# Complete Setup and Verification Guide

**Status**: ✅ Implementation Complete  
**Version**: 0.2.0  
**Last Updated**: 2025-11-26

---

## Overview

This guide walks you through setting up and verifying the unified ADK + OpenAI Agents SDK integration.

---

## Step 1: Install Dependencies

### Option A: Using pip

```bash
cd /home/orson-dev/projects/ontology-kit

# Install all dependencies
pip install -r requirements.txt

# Verify OpenAI SDK
python3 -c "import agents; print('✅ OpenAI Agents SDK:', agents.__version__)"

# Verify ADK (optional - may fail if not publicly available yet)
python3 -c "import google.adk; print('✅ Google ADK installed')" || echo "⚠️  ADK not installed (optional)"
```

###Option B: Using uv (faster)

```bash
cd /home/orson-dev/projects/ontology-kit

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv venv --python python3.11 .venv
source .venv/bin/activate
uv sync

```

---

## Step 2: Set Environment Variables

```bash
# Required for OpenAI SDK
export OPENAI_API_KEY='your-openai-api-key-here'

# Optional for Grok/xAI
export XAI_API_KEY='your-xai-key'

# Verify
echo "OpenAI Key: ${OPENAI_API_KEY:0:10}..."
```

---

## Step 3: Verify Installation

Run the verification script:

```bash
python3 scripts/verify_installation.py
```

Expected output:
```
✅ Core imports successful
✅ Adapters available
✅ Events system ready
✅ Sessions configured
✅ Memory service ready
✅ Runners initialized
✅ Orchestration available
✅ OpenAI SDK detected
⚠️  ADK not installed (optional)
```

---

## Step 4: Run Examples

### Quick Test

```bash
python3 examples/test_unified_sdk.py
```

### Multi-Agent Handoffs

```bash
python3 examples/multi_agent_handoff.py
```

### Full Integration Demo

```bash
python3 examples/adk_openai_integration.py
```

---

## Step 5: Run Tests

```bash
# Unit tests
pytest tests/integration/test_unified_sdk.py -v

# All integration tests
pytest tests/integration/ -v

# With coverage
pytest tests/integration/test_unified_sdk.py --cov=agent_kit --cov-report=html
```

---

## Troubleshooting

### Issue: "Module not found: agents"

**Solution:**
```bash
pip install openai-agents
```

### Issue: "Module not found: google.adk"

**Solution:**
ADK is optional. The code works without it using fallback implementations.

```bash
# If you have access to ADK:
pip install google-adk
```

### Issue: "Module not found: rdflib"

**Solution:**
```bash
pip install rdflib>=7.0.0
```

### Issue: "OPENAI_API_KEY not set"

**Solution:**
```bash
export OPENAI_API_KEY='your-key'
# Or add to ~/.bashrc or ~/.zshrc
```

### Issue: Linter warnings about imports

**Expected behavior:** Warnings about `google.adk` imports are normal if ADK isn't installed. The code handles this with try/except blocks.

---

## Architecture Verification

### Check Module Structure

```bash
tree -L 3 src/agent_kit/
```

Expected structure:
```
src/agent_kit/
├── __init__.py                    # Main exports
├── adapters/                      # SDK adapters
│   ├── ontology_agent_adapter.py
│   ├── ontology_guardrail.py
│   ├── ontology_tool_filter.py
│   ├── handoff_manager.py
│   └── openai_sdk.py
├── events/                        # Event system
│   ├── ontology_event.py
│   └── ontology_event_logger.py
├── sessions/                      # Session management
│   ├── backends.py
│   └── ontology_session_service.py
├── memory/                        # Memory service
│   └── ontology_memory_service.py
├── runners/                       # Runner implementations
│   ├── ontology_runner.py
│   └── streaming_runner.py
└── orchestrator/                  # Orchestration
    ├── unified_orchestrator.py
    └── ontology_orchestrator.py
```

### Verify Imports

```python
# Test all main imports
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

# Core
from agent_kit import OntologyLoader, Embedder, VectorIndex
print("✅ Core")

# Adapters
from agent_kit import OntologyAgentAdapter, OntologyOutputGuardrail
print("✅ Adapters")

# Events
from agent_kit import OntologyEvent, OntologyEventLogger
print("✅ Events")

# Sessions
from agent_kit import OntologySessionService, create_session_backend
print("✅ Sessions")

# Memory
from agent_kit import OntologyMemoryService, InMemoryBackend
print("✅ Memory")

# Runners
from agent_kit import OntologyRunner, RunConfig, RunResult
print("✅ Runners")

# Orchestration
from agent_kit import UnifiedOrchestrator, create_business_orchestrator
print("✅ Orchestration")

print("\n🎉 All imports successful!")
EOF
```

---

## Quick API Test

```python
import asyncio
from agent_kit import (
    OntologyLoader,
    OntologyAgentAdapter,
    OntologyRunner,
    create_session_backend,
    OntologySessionService,
)

async def main():
    # Setup
    ontology = OntologyLoader("assets/ontologies/business.ttl")
    ontology.load()
    print("✅ Ontology loaded")
    
    # Session
    backend = create_session_backend("memory")
    session_service = OntologySessionService(backend, ontology)
    session = await session_service.get_session("test_001")
    print("✅ Session created")
    
    # Runner
    runner = OntologyRunner(ontology, domain="business")
    print("✅ Runner ready")
    
    print("\n🎉 Setup successful!")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Performance Verification

```bash
# Time imports
time python3 -c "import agent_kit"

# Should be < 2 seconds

# Memory usage
python3 -c "
import tracemalloc
tracemalloc.start()

import agent_kit

current, peak = tracemalloc.get_traced_memory()
print(f'Memory: Current={current/1024/1024:.2f}MB, Peak={peak/1024/1024:.2f}MB')
"
```

---

## Common Integration Patterns

### Pattern 1: Simple Agent Execution

```python
from agents import Agent, Runner
from agent_kit import OntologyAgentAdapter, OntologyLoader

ontology = OntologyLoader("business.ttl")
agent = Agent(name="Assistant", instructions="...")
adapter = OntologyAgentAdapter(agent, ontology, "business")

result = await Runner.run(adapter.agent, input="Hello")
```

### Pattern 2: With Session Management

```python
from agent_kit import (
    OntologyRunner,
    RunConfig,
    create_session_backend,
    OntologySessionService,
)

backend = create_session_backend("sqlite", db_path="sessions.db")
session_service = OntologySessionService(backend, ontology)
runner = OntologyRunner(ontology, session_service=session_service)

config = RunConfig(session_id="user_001", domain="business")
result = await runner.run(adapter, "Query", config)
```

### Pattern 3: Full Orchestration

```python
from agent_kit import UnifiedOrchestrator, OrchestratorConfig

config = OrchestratorConfig(
    domain="business",
    session_backend="sqlite",
    enable_memory=True,
    enable_guardrails=True,
)

orchestrator = UnifiedOrchestrator(ontology, config)
orchestrator.register_agent("ForecastAgent", forecast_agent)
orchestrator.register_agent("OptimizerAgent", optimizer_agent)
orchestrator.create_orchestrator_agent()

result = await orchestrator.run("Forecast and optimize revenue")
```

---

## Next Steps

1. ✅ Verify installation
2. ✅ Run examples
3. ✅ Run tests
4. 📖 Read [UNIFIED_SDK_CHANGELOG.md](docs/UNIFIED_SDK_CHANGELOG.md)
5. 🔧 Build your agents
6. 🚀 Deploy to production

---

## Support

- **Documentation**: `docs/UNIFIED_SDK_INTEGRATION_STRATEGY.md`
- **Examples**: `examples/`
- **Tests**: `tests/integration/test_unified_sdk.py`
- **Issues**: Create GitHub issue with full stack trace

---

**Status**: ✅ Ready for production  
**Architecture**: Validated  
**Tests**: Passing  
**Dependencies**: Documented

