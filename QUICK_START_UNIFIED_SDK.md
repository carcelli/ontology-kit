# Quick Start: Unified SDK Integration

**Status**: ✅ Ready to test with your OpenAI API key!

---

## 🚀 Quick Test (30 seconds)

```bash
# Make sure you're in the project root
cd /home/orson-dev/projects/ontology-kit

# Run the quick test
python examples/test_unified_sdk.py
```

This validates:
- ✅ OpenAI API key is set
- ✅ Dependencies are installed
- ✅ Adapter integration works
- ✅ Basic agent execution

---

## 📋 What's Ready

### ✅ Adapter Layer (`src/agent_kit/adapters/`)
- `OntologyAgentAdapter` - Wraps OpenAI SDK agents with ontology context
- `OntologyOutputGuardrail` - Validates outputs against Pydantic schemas
- `OntologyInputGuardrail` - Validates inputs against domain constraints
- `OntologyToolFilter` - Filters tools by domain allowlist

### ✅ Example Scripts (`examples/`)
- `test_unified_sdk.py` - Quick validation test
- `unified_sdk_integration.py` - Full integration demo

### ✅ Documentation (`docs/`)
- `UNIFIED_SDK_INTEGRATION_STRATEGY.md` - Complete architecture guide
- `SDK_INTEGRATION_QUICK_REFERENCE.md` - Quick reference
- `ADK_INTEGRATION_RECOMMENDATIONS.md` - ADK-specific details

---

## 🎯 Next Steps

### 1. Test Basic Integration
```bash
python examples/test_unified_sdk.py
```

Expected output:
```
🧪 Testing Basic Integration...
✅ Adapter created: domain=business
✅ Agent executed: Hello! ...
✅ All tests passed!
```

### 2. Run Full Example
```bash
python examples/unified_sdk_integration.py
```

This demonstrates:
- Creating OpenAI SDK agents
- Wrapping with ontology adapters
- Adding guardrails
- Executing with business tools

### 3. Build Your Own Agent

```python
from agents import Agent, Runner
from agent_kit.adapters import OntologyAgentAdapter, OntologyOutputGuardrail
from agent_kit.ontology.loader import OntologyLoader

# Setup
ontology = OntologyLoader("assets/ontologies/business.ttl")
ontology.load()

# Create agent
agent = Agent(
    name="MyAgent",
    instructions="Your instructions here",
    tools=[...],  # Your tools
)

# Wrap with adapter
adapter = OntologyAgentAdapter(agent, ontology, "business")

# Add guardrails
adapter.agent.output_guardrails = [
    OntologyOutputGuardrail("business")
]

# Execute
result = await Runner.run(adapter.agent, input="Your query")
print(result.final_output)
```

---

## 🔧 Troubleshooting

### Issue: "Module 'agents' not found"
**Solution:**
```bash
pip install openai-agents
```

### Issue: "OPENAI_API_KEY not set"
**Solution:**
```bash
export OPENAI_API_KEY='your-key-here'
# Verify:
echo $OPENAI_API_KEY
```

### Issue: "Domain 'business' not found"
**Solution:**
- Ensure `src/agent_kit/domains/business.yaml` exists
- Check domain registry is initialized

### Issue: Import errors
**Solution:**
- Make sure you're running from project root
- Check Python path includes `src/` directory

---

## 📚 Architecture Overview

```
┌─────────────────────────────────────┐
│   Your Code                         │
│   (Agent definitions)               │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   OntologyAgentAdapter             │
│   • Adds ontology context          │
│   • Filters tools by domain        │
│   • Tracks SPARQL queries          │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   OpenAI SDK Agent                 │
│   • Handoffs                       │
│   • Guardrails                     │
│   • Tool calling                   │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   OpenAI API                       │
│   (LLM calls)                      │
└─────────────────────────────────────┘
```

---

## 🎓 Key Concepts

1. **Ontology Layer** - Domain knowledge (SPARQL, entities, schemas)
2. **Adapter Layer** - Bridges SDKs to ontology (what we built)
3. **SDK Layer** - Execution engines (OpenAI SDK, ADK)

**Principle**: Ontology is the source of truth. SDKs are execution engines.

---

## 📖 Learn More

- **Architecture**: `docs/UNIFIED_SDK_INTEGRATION_STRATEGY.md`
- **Quick Reference**: `docs/SDK_INTEGRATION_QUICK_REFERENCE.md`
- **Examples**: `examples/unified_sdk_integration.py`

---

**Ready to ship!** 🚀 Your OpenAI API key is set, adapters are implemented, and examples are ready to run.

