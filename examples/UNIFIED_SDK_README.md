# Unified SDK Integration Examples

Quick start guide for testing ADK + OpenAI Agents SDK integration.

## Prerequisites

1. **Set OpenAI API Key:**
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```

2. **Install Dependencies:**
   ```bash
   pip install openai-agents
   # Or if using requirements.txt:
   pip install -r requirements.txt
   ```

## Quick Test

Run the basic test to validate integration:

```bash
python examples/test_unified_sdk.py
```

This will:
- ✅ Check API key is set
- ✅ Create an OpenAI SDK agent
- ✅ Wrap it with ontology adapter
- ✅ Execute a simple query

## Full Example

Run the complete integration example:

```bash
python examples/unified_sdk_integration.py
```

This demonstrates:
- 🤖 Creating OpenAI SDK agents
- 🔗 Wrapping with ontology adapters
- 🛡️ Adding guardrails
- 🚀 Executing with business tools
- 🔍 Tracking SPARQL queries

## What's Happening

1. **OpenAI SDK Agent** - Creates the agent with instructions and tools
2. **Ontology Adapter** - Wraps the agent, adding:
   - Domain context from ontology
   - Tool filtering by domain allowlist
   - SPARQL query tracking
3. **Guardrails** - Validates outputs against Pydantic schemas
4. **Execution** - Runs agent with OpenAI SDK Runner

## Troubleshooting

### "OPENAI_API_KEY not set"
```bash
export OPENAI_API_KEY='your-key'
```

### "Module not found: agents"
```bash
pip install openai-agents
```

### "Module not found: agent_kit"
Make sure you're running from the project root:
```bash
cd /path/to/ontology-kit
python examples/test_unified_sdk.py
```

### "Ontology file not found"
The example will work without ontology, but for full functionality:
- Ensure `assets/ontologies/business.ttl` exists
- Or update the path in the example

## Next Steps

1. ✅ Run `test_unified_sdk.py` to validate setup
2. ✅ Run `unified_sdk_integration.py` for full demo
3. 📖 Read `docs/UNIFIED_SDK_INTEGRATION_STRATEGY.md` for architecture
4. 🔧 Customize agents for your domain

## Architecture

```
Your Code
    ↓
OntologyAgentAdapter (wraps OpenAI SDK Agent)
    ↓
OpenAI SDK Agent (execution)
    ↓
OpenAI API (LLM calls)
```

The adapter enriches the agent with:
- Ontology context (entities, relationships)
- Domain-specific tool filtering
- SPARQL query tracking
- Guardrail validation

