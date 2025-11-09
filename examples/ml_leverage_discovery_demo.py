#!/usr/bin/env python3
"""
Demo: Ontology-Driven Business Leverage Analysis

Shows how agents:
1. Query ontology to discover dimensionality reduction tools
2. Find tools by algorithm (t-SNE)
3. Execute leverage analysis to prioritize business entities
4. Get actionable intervention points

This integrates your existing hyperdim_leverage_viz.py tool with the
new ontology-driven ML tool discovery pattern.

Run from repo root:
    python examples/ml_leverage_discovery_demo.py
"""
import sys
from pathlib import Path

# Add src to path for demo purposes
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / 'src'))

from agent_kit.ontology.loader import OntologyLoader
from agent_kit.orchestrator.ontology_orchestrator import OntologyOrchestrator
from agent_kit.tools.ml_training import ML_TOOL_REGISTRY

# Tool class IRIs from ontology
ML_LEVERAGE = 'http://agent-kit.com/ontology/ml#LeverageAnalysisTool'


def print_section(title: str) -> None:
    """Print formatted section header."""
    print(f'\n{"=" * 70}')
    print(f'  {title}')
    print('=' * 70)


def main() -> None:
    """Run the business leverage discovery demo."""
    print_section('Ontology-Driven Business Leverage Analysis Demo')
    print('\nDemonstrates: Agent discovers dimensionality reduction tool → analyzes')
    print('business entities → identifies high-leverage intervention points')

    # Step 1: Load ontology
    print_section('Step 1: Load ML Tools Ontology')
    ontology_path = repo_root / 'assets' / 'ontologies' / 'ml_tools.ttl'
    print(f'Loading: {ontology_path}')
    loader = OntologyLoader(str(ontology_path))
    loader.load()
    print(f'✓ Loaded {len(loader.graph)} triples')

    # Step 2: Create orchestrator
    print_section('Step 2: Initialize Orchestrator')
    orch = OntologyOrchestrator(loader, ML_TOOL_REGISTRY)
    print('✓ Orchestrator ready')

    # Step 3: Discover dimensionality reduction tools by algorithm
    print_section('Step 3: Discover Tools by Algorithm')
    print('Query: Find tools implementing t-SNE')
    tsne_tools = orch.discover_tools_by_algorithm('t-SNE')
    print(f'✓ Found {len(tsne_tools)} t-SNE tool(s):')
    for t in tsne_tools:
        print(f'  - {t["function"].__name__}')

    # Step 4: Discover leverage analysis tool specifically
    print_section('Step 4: Discover Leverage Analysis Tool')
    print(f'Query: Find tool for class {ML_LEVERAGE.split("#")[1]}')
    leverage_tool = orch.discover_tool(ML_LEVERAGE)
    print(f'✓ Discovered: {leverage_tool["function"].__name__}')
    print(f'  Schema: {leverage_tool["schema"].__name__}')

    # Step 5: Execute leverage analysis on business entities
    print_section('Step 5: Execute Leverage Analysis')

    business_entities = [
        'Revenue',
        'Forecast',
        'Client',
        'Customer',
        'OutreachCampaign',
        'EmailTiming',
        'Budget',
        'Marketing',
        'Sales',
        'Product',
        'Service',
        'Website',
        'SocialMedia',
        'Advertising',
        'CustomerSatisfaction',
    ]

    actionable_entities = [
        'OutreachCampaign',
        'EmailTiming',
        'Budget',
        'Marketing',
        'Website',
        'SocialMedia',
        'Advertising',
    ]

    print(f'Analyzing {len(business_entities)} entities for KPI: Revenue')
    print(f'Actionable entities: {len(actionable_entities)}')

    result = orch.call(
        ML_LEVERAGE,
        {
            'terms': business_entities,
            'kpi_term': 'Revenue',
            'actionable_terms': actionable_entities,
        },
    )

    # Step 6: Display results
    print_section('Step 6: High-Leverage Intervention Points')
    print(f'Status: {result["status"]}')
    print(f'Job ID: {result["job_id"]}')
    print(f'Visualization: {result.get("viz_path", "N/A")}')

    if result['status'] == 'COMPLETED':
        print(f'\n🎯 Top {len(result["top_levers"])} Leverage Points:')
        for i, lever in enumerate(result['top_levers'], 1):
            term = lever['term']
            score = lever['leverage']
            is_actionable = term in actionable_entities
            action_flag = '✓ Actionable' if is_actionable else '✗ Fixed (observe only)'
            print(f'\n  {i}. {term}: {score:.3f}')
            print(f'     {action_flag}')

        # Business recommendations
        print_section('Step 7: Business Recommendations')
        print('Based on leverage scores, prioritize interventions:')
        for i, lever in enumerate(result['top_levers'][:3], 1):
            if lever['term'] in actionable_entities:
                print(f'\n  {i}. {lever["term"]} (Leverage: {lever["leverage"]:.3f})')
                if lever['term'] == 'Budget':
                    print('     → Reallocate budget to high-ROI channels')
                elif lever['term'] == 'Marketing':
                    print('     → Optimize marketing spend via A/B tests')
                elif lever['term'] == 'Advertising':
                    print('     → Target ads to high-conversion segments')
                elif lever['term'] == 'OutreachCampaign':
                    print('     → Adjust campaign timing and messaging')
                elif lever['term'] == 'EmailTiming':
                    print('     → Optimize send times for max open rates')
                else:
                    print(f'     → Experiment with {lever["term"]} adjustments')

    else:
        print(f'\n✗ Analysis failed: {result.get("message", "Unknown error")}')

    # Summary
    print_section('Summary')
    print('✓ Ontology → t-SNE Tool Discovery → Leverage Analysis → Prioritization')
    print('\n📊 Leverage Formula:')
    print('  L = Actionability × (Sensitivity + Uncertainty + Centrality)')
    print('  • Actionability: Can we change it? (0 or 1)')
    print('  • Sensitivity: Distance to KPI in semantic space (closer = higher impact)')
    print('  • Uncertainty: Cluster variance (high = info gain opportunity)')
    print('  • Centrality: Graph betweenness (bridges amplify interventions)')

    print('\n💡 Business Value:')
    print('  • Focus resources on high-leverage, actionable entities')
    print('  • Prioritize interventions by ROI potential')
    print('  • Identify data collection opportunities (high uncertainty)')
    print('  • Discover hidden relationships via t-SNE clustering')

    print('\n🚀 Next Steps:')
    print('  1. Wire this into OpenAI SDK Agent for auto-discovery')
    print('  2. Track leverage scores over time (monitor drift)')
    print('  3. A/B test interventions on top leverage points')
    print('  4. Extend ontology with domain-specific KPIs')
    print()


if __name__ == '__main__':
    main()

