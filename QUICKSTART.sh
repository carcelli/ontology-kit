#!/bin/bash
#
# Ontology-Kit Quickstart Script
# 
# Validates setup and runs smoke tests across all domains
#

set -e  # Exit on error

echo "🚀 Ontology-Kit v0.1 Quickstart"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check Python version
echo "1️⃣  Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python: $python_version"

# Step 2: Validate domain configs
echo ""
echo "2️⃣  Validating domain configurations..."
for domain in business betting trading; do
    config_file="src/agent_kit/domains/${domain}.yaml"
    if [ -f "$config_file" ]; then
        echo -e "   ${GREEN}✓${NC} Found: $domain.yaml"
    else
        echo -e "   ${RED}✗${NC} Missing: $domain.yaml"
        exit 1
    fi
done

# Step 3: Check key files exist
echo ""
echo "3️⃣  Checking core components..."
core_files=(
    "src/agent_kit/domains/registry.py"
    "src/agent_kit/schemas.py"
    "src/agent_kit/cli.py"
    "src/agent_kit/factories/agent_factory.py"
    "src/agent_kit/agents/orchestrator.py"
    "src/agent_kit/monitoring/circuit_breaker.py"
    "tests/integration/test_business_flow.py"
)

for file in "${core_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   ${GREEN}✓${NC} $(basename $file)"
    else
        echo -e "   ${RED}✗${NC} Missing: $file"
        exit 1
    fi
done

# Step 4: Test imports (no exceptions)
echo ""
echo "4️⃣  Testing Python imports..."
python3 << EOF
try:
    from agent_kit.domains.registry import DomainRegistry
    from agent_kit.factories.agent_factory import AgentFactory
    from agent_kit.schemas import BusinessOptimizationResult
    from agent_kit.monitoring.circuit_breaker import with_circuit_breaker
    print("   ✓ All imports successful")
except Exception as e:
    print(f"   ✗ Import failed: {e}")
    exit(1)
EOF

# Step 5: List domains
echo ""
echo "5️⃣  Listing available domains..."
python3 << EOF
from agent_kit.domains import get_global_registry
registry = get_global_registry()
domains = registry.list_domains()
for domain in domains:
    cfg = registry.get(domain)
    print(f"   • {domain}: {len(cfg.default_agents)} agents, {len(cfg.allowed_tools)} tools")
EOF

# Step 6: Smoke test - Create orchestrator
echo ""
echo "6️⃣  Smoke test: Creating business orchestrator..."
python3 << EOF
from agent_kit.factories.agent_factory import AgentFactory
import os
os.environ['XAI_API_KEY'] = 'test-key'  # Mock for smoke test
try:
    factory = AgentFactory()
    orch = factory.create_orchestrator("business")
    print(f"   ✓ Orchestrator created: {orch.domain}")
    print(f"   ✓ Specialists: {len(orch.specialists)}")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    exit(1)
EOF

# Step 7: Run quick tests (if pytest available)
echo ""
echo "7️⃣  Running quick tests..."
if command -v pytest &> /dev/null; then
    pytest tests/integration/test_business_flow.py::TestDomainRegistry::test_registry_lists_domains -v --tb=short 2>&1 | tail -5
else
    echo "   ⚠  pytest not found, skipping tests"
fi

# Step 8: Show next steps
echo ""
echo "✅ Setup validated successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Set API keys (optional for testing):"
echo "   export XAI_API_KEY='your-xai-key'"
echo ""
echo "2. Run CLI commands:"
echo "   ontology-kit list-domains"
echo "   ontology-kit validate-config"
echo "   ontology-kit run --domain business --goal 'Forecast next 30 days'"
echo ""
echo "3. Run tests:"
echo "   pytest tests/integration/test_business_flow.py -v"
echo "   pytest -m integration"
echo ""
echo "4. Check circuit breaker status:"
echo "   ontology-kit status"
echo ""
echo "5. Read docs:"
echo "   cat IMPLEMENTATION_SUMMARY.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

