#!/usr/bin/env python3
"""
Demo: Complete Semantic Graph Workflow for Business Optimization

Shows the full pipeline:
1. Build semantic graph from business entities
2. Compute targeted leverage scores for Revenue KPI
3. Generate experiment recommendations for top levers
4. (Optional) Integrate with predictive model + SHAP

This demonstrates the semantic relation framework for finding high-leverage
intervention points, as documented in docs/SEMANTIC_LEVERAGE_GUIDE.md

Run from repo root:
    python examples/semantic_graph_workflow_demo.py
"""
import json
import sys
from pathlib import Path

# Add src to path for demo purposes
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / 'src'))

from agent_kit.ontology.loader import OntologyLoader
from agent_kit.orchestrator.ontology_orchestrator import OntologyOrchestrator
from agent_kit.tools.ml_training import ML_TOOL_REGISTRY

# Tool class IRIs from ontology
ML_SEMANTIC_GRAPH = 'http://agent-kit.com/ontology/ml#SemanticGraphTool'
ML_TARGET_LEVERAGE = 'http://agent-kit.com/ontology/ml#TargetLeverageTool'
ML_INTERVENTION = 'http://agent-kit.com/ontology/ml#InterventionRecommenderTool'


def print_section(title: str) -> None:
    """Print formatted section header."""
    print(f'\n{"=" * 70}')
    print(f'  {title}')
    print('=' * 70)


def main() -> None:
    """Run the complete semantic graph workflow demo."""
    print_section('Semantic Graph Workflow Demo')
    print('\nDemonstrates: Build semantic graph → Compute targeted leverage →')
    print('Generate experiment recommendations for business optimization')

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
    print('✓ Orchestrator ready with unified ML_TOOL_REGISTRY')

    # Step 3: Discover semantic graph tools
    print_section('Step 3: Discover Semantic Graph Tools')
    tools = [
        ('SemanticGraphTool', ML_SEMANTIC_GRAPH),
        ('TargetLeverageTool', ML_TARGET_LEVERAGE),
        ('InterventionRecommenderTool', ML_INTERVENTION),
    ]

    for name, iri in tools:
        tool = orch.discover_tool(iri)
        print(f'✓ {name}: {tool["function"].__name__}')

    # Step 4: Define business domain
    print_section('Step 4: Define Business Entities')

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

    print(f'Analyzing {len(business_entities)} business entities:')
    print(f'  {", ".join(business_entities[:5])}...')

    # Step 5: Build semantic graph
    print_section('Step 5: Build Semantic Graph')
    print('Constructing weighted graph from embeddings...')

    graph_result = orch.call(
        ML_SEMANTIC_GRAPH,
        {
            'terms': business_entities,
            'similarity_threshold': 0.7,
            'output_path': 'outputs/business_semantic_graph.json',
        },
    )

    if graph_result['status'] == 'COMPLETED':
        print(f'✓ Status: {graph_result["status"]}')
        print(f'✓ Graph saved: {graph_result["graph_path"]}')
        print(f'  • Nodes: {graph_result["n_nodes"]}')
        print(f'  • Edges: {graph_result["n_edges"]}')
        print(f'  • Avg degree: {graph_result["avg_degree"]}')
        print(f'  • Clusters: {graph_result["n_clusters"]}')
    else:
        print(f'✗ Failed: {graph_result.get("message", "Unknown error")}')
        return

    # Step 6: Compute targeted leverage
    print_section('Step 6: Compute Targeted Leverage for Revenue')
    print('Analyzing paths to Revenue KPI with graph-theoretic scoring...')

    leverage_result = orch.call(
        ML_TARGET_LEVERAGE,
        {
            'graph_path': graph_result['graph_path'],
            'target': 'Revenue',
            'top_k': 5,
        },
    )

    if leverage_result['status'] == 'COMPLETED':
        print(f'✓ Status: {leverage_result["status"]}')
        print(f'\n🎯 Top 5 Leverage Points for Revenue:')

        for i, lever in enumerate(leverage_result['levers'], 1):
            print(f'\n  {i}. {lever["term"]}: {lever["total_leverage"]:.4f}')
            print(f'     • Targeted betweenness: {lever["betweenness"]:.3f}')
            print(f'     • Path strength: {lever["path_strength"]:.3f}')
            print(f'     • Actionability: {lever["actionability"]:.3f}')
            print(f'     • Model effect (SHAP): {lever["shap_score"]:.3f}')
            if lever['strongest_path']:
                path_str = ' → '.join(lever['strongest_path'])
                print(f'     • Strongest path: {path_str}')

        # Store top lever for intervention recommendations
        top_lever = leverage_result['levers'][0]['term']

    else:
        print(f'✗ Failed: {leverage_result.get("message", "Unknown error")}')
        return

    # Step 7: Generate intervention recommendations
    print_section(f'Step 7: Generate Experiment Recommendations for {top_lever}')
    print(f'Analyzing paths from {top_lever} → Revenue...')

    intervention_result = orch.call(
        ML_INTERVENTION,
        {
            'graph_path': graph_result['graph_path'],
            'node': top_lever,
            'target': 'Revenue',
            'top_paths': 3,
        },
    )

    if intervention_result['status'] == 'COMPLETED':
        print(f'✓ Status: {intervention_result["status"]}')
        print(f'\n📊 Experiment Recommendations:')

        for exp in intervention_result['recommendations']:
            print(f'\n  {exp["name"]}')
            print(f'  {"─" * 66}')
            print(f'  Lever: {exp["lever"]}')
            print(f'  Target: {exp["target"]}')
            print(f'  Path: {exp["path"]}')
            print(f'    (weight: {exp["path_weight"]}, length: {exp["path_length"]} hops)')
            print(f'\n  💡 Action:')
            print(f'    {exp["action"]}')
            print(f'\n  📈 Expected Impact:')
            print(f'    • Estimated lift: {exp["expected_lift"]:.1%}')
            print(f'    • Sample size: {exp["sample_size"]:,} per group')
            print(f'    • Duration: {exp["duration"]}')
            print(f'\n  📊 KPIs to Track:')
            print(f'    • Primary: {exp["primary_kpi"]}')
            if exp['intermediate_kpis']:
                print(f'    • Intermediates: {", ".join(exp["intermediate_kpis"])}')
            print(f'\n  ⚠️  Guardrails:')
            for guardrail in exp['guardrails']:
                print(f'    • {guardrail}')

    else:
        print(f'✗ Failed: {intervention_result.get("message", "Unknown error")}')

    # Summary
    print_section('Summary: Semantic Leverage Workflow')
    print('\n✓ Complete pipeline executed:')
    print('  1. Built semantic graph (embeddings + similarity)')
    print('  2. Computed targeted leverage (betweenness + path strength)')
    print('  3. Generated experiment specifications (actions + KPIs)')

    print('\n📊 Key Insights:')
    print(f'  • Highest leverage point: {top_lever}')
    print('  • Graph structure: Entities cluster by semantic similarity')
    print('  • Paths to Revenue: Multiple indirect routes identified')
    print('  • Actionable: Experiment specs ready for A/B testing')

    print('\n💡 What Makes This Different:')
    print('  • Not just t-SNE visualization (though that is included)')
    print('  • Graph-theoretic path analysis (betweenness, strength)')
    print('  • Targeted scoring for specific KPIs (Revenue, Satisfaction, etc.)')
    print('  • Experiment design automation (sample size, duration, guardrails)')

    print('\n🚀 Next Steps:')
    print('  1. Validate with predictive model (add SHAP values)')
    print('  2. Run pilot experiment on top lever')
    print('  3. Measure lift and update graph edge weights')
    print('  4. Recompute leverage scores to detect shifts')
    print('  5. Iterate: Focus on next lever in the queue')

    print('\n📁 Generated Files:')
    files = ['business_semantic_graph.json']
    for f in files:
        path = repo_root / 'outputs' / f
        if path.exists():
            size_kb = path.stat().st_size // 1024
            print(f'  ✓ {path} ({size_kb} KB)')

    print('\n' + '=' * 70)
    print('Ship it! 🚀 Semantic leverage → Actionable experiments')
    print('=' * 70)


if __name__ == '__main__':
    main()

