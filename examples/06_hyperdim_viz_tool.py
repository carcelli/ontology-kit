"""
Example 6: Hyperdimensional Visualization Tool

Demonstrates how agents can dynamically call the hyperdim_viz tool to
generate semantic space visualizations from ontology files or custom terms.

Shows:
1. Direct tool invocation
2. Agent-driven visualization (if OpenAI SDK available)
3. Ontology-based visualization
4. Custom term visualization
"""

import asyncio
import os

from agent_kit.tools.hyperdim_viz import generate_hyperdim_viz

# Try to import OpenAI SDK for agent-driven example
try:
    from agents import Agent, Runner, function_tool

    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False


def main_direct():
    """Direct tool invocation examples."""
    print('=' * 70)
    print('Agent Kit - Example 6: Hyperdimensional Visualization Tool')
    print('=' * 70)

    # Example 1: Visualize business ontology
    print('\n📊 Example 1: Business Ontology Visualization (2D)')
    print('-' * 70)
    ontology_path = 'assets/ontologies/business.ttl'
    if os.path.exists(ontology_path):
        output_path = generate_hyperdim_viz(
            ontology_path=ontology_path, n_components=2, output_file='outputs/business_2d.png'
        )
        print(f'✅ Visualization saved: {output_path}')
        print('   Open this file to see semantic clusters of business entities')
    else:
        print(f'⚠️  Ontology not found: {ontology_path}')

    # Example 2: Visualize custom terms (3D)
    print('\n🎯 Example 2: Custom Terms Visualization (3D)')
    print('-' * 70)
    custom_terms = [
        'Revenue',
        'Forecast',
        'Client',
        'Business',
        'Agent',
        'Optimization',
        'Strategy',
        'LeveragePoint',
        'TimeSeriesData',
        'MachineLearning',
    ]
    output_path_3d = generate_hyperdim_viz(terms=custom_terms, n_components=3, output_file='outputs/custom_3d.png')
    print(f'✅ 3D visualization saved: {output_path_3d}')
    print('   Rotate the plot to explore semantic relationships')

    # Example 3: Core ontology visualization
    print('\n🔧 Example 3: Core Ontology Visualization')
    print('-' * 70)
    core_path = 'assets/ontologies/core.ttl'
    if os.path.exists(core_path):
        output_core = generate_hyperdim_viz(
            ontology_path=core_path, max_terms=30, output_file='outputs/core_ontology.png'
        )
        print(f'✅ Core ontology visualization: {output_core}')
    else:
        print(f'⚠️  Core ontology not found: {core_path}')

    print('\n' + '=' * 70)
    print('✅ Direct Invocation Examples Complete!')
    print('=' * 70)


async def main_agent_driven():
    """Agent-driven visualization example (requires OpenAI SDK)."""
    if not OPENAI_SDK_AVAILABLE:
        print('\n⚠️  OpenAI SDK not available — skipping agent-driven example')
        print('Install via: pip install openai-agents>=0.5.0')
        return

    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print('\n⚠️  OPENAI_API_KEY not set — skipping agent-driven example')
        print('Set via: export OPENAI_API_KEY=sk-...')
        return

    print('\n\n' + '=' * 70)
    print('🤖 Agent-Driven Visualization (OpenAI SDK)')
    print('=' * 70)

    try:
        # Wrap tool with @function_tool decorator for agent use
        @function_tool
        def visualize_ontology(
            ontology_path: str,
            output_file: str = 'outputs/agent_viz.png',
            n_components: int = 2,
        ) -> str:
            """Generate hyperdimensional visualization of ontology semantic space."""
            return generate_hyperdim_viz(
                ontology_path=ontology_path, n_components=n_components, output_file=output_file
            )

        # Create agent with visualization tool
        analyst_agent = Agent(
            name='SemanticAnalyst',
            instructions=(
                'You are a semantic analysis expert. When asked to visualize ontologies, '
                'use the visualize_ontology tool to generate hyperdimensional space plots. '
                'Explain what the visualization reveals about term relationships.'
            ),
            tools=[visualize_ontology],
            model='gpt-4.1',
        )

        # Run agent
        print('\n📋 Task: "Visualize the business ontology to reveal semantic clusters"')
        print('-' * 70)
        result = await Runner.run(
            analyst_agent, 'Visualize assets/ontologies/business.ttl and explain the semantic relationships'
        )

        print(f'\n🤖 Agent Response:')
        print(result.final_output)

        print('\n' + '=' * 70)
        print('✅ Agent-Driven Example Complete!')
        print('=' * 70)
    except Exception as e:
        print(f'\n⚠️  Agent execution failed: {e}')
        print('This is expected without a valid API key or if the model is unavailable')


def print_summary():
    """Print usage summary."""
    print('\n\n' + '=' * 70)
    print('📚 Summary: Hyperdimensional Visualization Tool')
    print('=' * 70)
    print('\n✨ Key Capabilities:')
    print('  1. Extract terms from RDF/OWL ontologies automatically')
    print('  2. Visualize custom term lists')
    print('  3. Generate 2D or 3D semantic space plots')
    print('  4. Agent-callable via @function_tool')
    print('  5. Reveals semantic clusters and relationships')

    print('\n🔍 What the Visualizations Show:')
    print('  • Terms close together: Semantically related')
    print('  • Terms far apart: Semantically distinct')
    print('  • Clusters: Groups of related concepts')
    print('  • Example: "Revenue" near "Forecast", "Client" near "Business"')

    print('\n🛠️  Usage Patterns:')
    print('  • Direct: generate_hyperdim_viz(ontology_path="...", output_file="...")')
    print('  • Agent-driven: Agent with tools=[visualize_ontology]')
    print('  • Custom terms: generate_hyperdim_viz(terms=[...], n_components=3)')

    print('\n🎯 Business Value:')
    print('  • Ontology exploration: Discover hidden relationships')
    print('  • Quality assurance: Verify ontology structure')
    print('  • Knowledge communication: Visual explanations for stakeholders')
    print('  • Leverage point identification: Find semantic bridges')

    print('\n📁 Output Files:')
    if os.path.exists('outputs/business_2d.png'):
        print('  ✅ outputs/business_2d.png')
    if os.path.exists('outputs/custom_3d.png'):
        print('  ✅ outputs/custom_3d.png')
    if os.path.exists('outputs/core_ontology.png'):
        print('  ✅ outputs/core_ontology.png')

    print('\n💡 Next Steps:')
    print('  1. Open generated PNGs to explore semantic spaces')
    print('  2. Try different ontologies: core.ttl, business.ttl')
    print('  3. Experiment with 3D visualizations (n_components=3)')
    print('  4. Integrate with agent workflows for automated analysis')

    print('\n' + '=' * 70)
    print('Ship it! 🚀 Hyperdimensional navigation made visible.')
    print('=' * 70)


async def main():
    """Run all examples."""
    # Direct invocation
    main_direct()

    # Agent-driven (if SDK available)
    await main_agent_driven()

    # Summary
    print_summary()


if __name__ == '__main__':
    asyncio.run(main())

