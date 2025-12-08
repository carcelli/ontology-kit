"""
Example 7: Hyperdimensional Leverage Analysis

Demonstrates how agents identify high-leverage intervention points using
multi-factor scoring: Leverage = A × (S + U + C)

Where:
- A: Actionability (can we intervene?)
- S: Sensitivity (distance to KPI)
- U: Uncertainty (information value)
- C: Centrality (graph betweenness)

Shows:
1. Business ontology leverage analysis
2. Custom terms with specific actionability
3. Different KPIs for sensitivity
4. Structured results for agent chaining
"""

import os

from agent_kit.tools.hyperdim_leverage_viz import generate_hyperdim_leverage_viz


def main():
    print('=' * 70)
    print('Agent Kit - Example 7: Hyperdimensional Leverage Analysis')
    print('=' * 70)

    # Example 1: Business Ontology with Revenue KPI
    print('\n📊 Example 1: Business Ontology - Revenue Leverage')
    print('-' * 70)

    ontology_path = 'assets/ontologies/business.ttl'
    if os.path.exists(ontology_path):
        # First, do a quick extraction to see what terms are available
        from agent_kit.tools.hyperdim_leverage_viz import _extract_terms_and_graph

        terms_preview, _ = _extract_terms_and_graph(ontology_path, None, 50)
        print(f"\n📋 Available terms (first 10): {terms_preview[:10]}")

        # Use a term that exists in the ontology
        kpi = 'RevenueStream' if 'RevenueStream' in terms_preview else terms_preview[0]
        print(f"  Using KPI term: '{kpi}'")

        result1 = generate_hyperdim_leverage_viz(
            ontology_path=ontology_path,
            kpi_term=kpi,
            actionable_terms=[
                'Strategy',
                'Process',
                'Campaign',
            ],  # What we can change (use generic names that might exist)
            n_components=2,
            output_file='outputs/business_leverage.png',
        )

        print(f"\n✅ Visualization: {result1['viz_path']}")
        print("\n🎯 Top 5 Leverage Points (Revenue KPI):")
        for lever in result1['top_levers'][:5]:
            term = lever['term']
            score = lever['leverage']
            breakdown = result1['scores'][term]
            print(f"\n  • {term}: {score:.3f}")
            print(f"    - Actionability: {breakdown['actionability']:.2f}")
            print(f"    - Sensitivity:   {breakdown['sensitivity']:.2f} (dist to Revenue)")
            print(f"    - Uncertainty:   {breakdown['uncertainty']:.2f} (cluster variance)")
            print(f"    - Centrality:    {breakdown['centrality']:.2f} (betweenness)")
    else:
        print(f'⚠️  Ontology not found: {ontology_path}')

    # Example 2: Custom Terms - Small Business Intervention Points
    print('\n\n🎯 Example 2: Small Business Intervention Analysis')
    print('-' * 70)

    business_terms = [
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

    actionable = [
        'OutreachCampaign',
        'EmailTiming',
        'Budget',
        'Marketing',
        'Website',
        'SocialMedia',
        'Advertising',
    ]

    result2 = generate_hyperdim_leverage_viz(
        terms=business_terms,
        kpi_term='Revenue',
        actionable_terms=actionable,
        n_components=3,  # 3D for more nuanced view
        output_file='outputs/business_intervention_3d.png',
    )

    print(f"\n✅ 3D Visualization: {result2['viz_path']}")
    print("\n🎯 Top 3 Interventions:")
    for i, lever in enumerate(result2['top_levers'][:3], 1):
        print(f"\n  {i}. {lever['term']}: {lever['leverage']:.3f}")
        if result2['scores'][lever['term']]['actionability'] > 0:
            print("     ✓ Actionable - can be changed directly")
        else:
            print("     ✗ Fixed - observe/measure only")

    # Example 3: Different KPI - Customer Satisfaction
    print('\n\n😊 Example 3: Customer Satisfaction Leverage')
    print('-' * 70)

    if 'CustomerSatisfaction' in business_terms:
        result3 = generate_hyperdim_leverage_viz(
            terms=business_terms,
            kpi_term='CustomerSatisfaction',  # Different objective
            actionable_terms=actionable,
            n_components=2,
            output_file='outputs/satisfaction_leverage.png',
        )

        print(f"\n✅ Visualization: {result3['viz_path']}")
        print("\n🎯 Top 3 Levers for Customer Satisfaction:")
        for lever in result3['top_levers'][:3]:
            print(f"  • {lever['term']}: {lever['leverage']:.3f}")

        # Compare to Revenue KPI
        print("\n📊 Comparison: Revenue vs. Satisfaction Leverage")
        print(f"{'Term':<25} {'Revenue Lever':<15} {'Satisfaction Lever':<20}")
        print('-' * 60)
        for term in actionable[:5]:
            rev_score = next((l['leverage'] for l in result2['top_levers'] if l['term'] == term), 0.0)
            sat_score = next((l['leverage'] for l in result3['top_levers'] if l['term'] == term), 0.0)
            print(f"{term:<25} {rev_score:<15.3f} {sat_score:<20.3f}")

    # Summary
    print('\n\n' + '=' * 70)
    print('✅ Leverage Analysis Complete!')
    print('=' * 70)

    print('\n💡 Key Insights:')
    print('  • Red nodes = High leverage (prioritize intervention here)')
    print('  • Blue nodes = Low leverage (monitor but don\'t intervene)')
    print('  • Circles (○) = Actionable terms (can change)')
    print('  • Squares (□) = Fixed terms (observe only)')

    print('\n🎯 Business Implications:')
    print('  • Focus resources on high-leverage actionable terms')
    print('  • Bridge terms (high centrality) amplify interventions')
    print('  • Terms close to KPI (high sensitivity) have direct impact')
    print('  • High uncertainty terms = opportunities for data collection')

    print('\n🚀 Next Steps for Agents:')
    print('  1. Agent queries: "What are the top levers for Revenue?"')
    print('  2. Agent chains: Leverage viz → Optimization → Action plan')
    print('  3. Agent monitoring: Track leverage scores over time')
    print('  4. Agent experiments: A/B test interventions on high-leverage terms')

    print('\n📁 Generated Files:')
    for f in ['business_leverage.png', 'business_intervention_3d.png', 'satisfaction_leverage.png']:
        path = f'outputs/{f}'
        if os.path.exists(path):
            size_kb = os.path.getsize(path) // 1024
            print(f'  ✓ {path} ({size_kb} KB)')

    print('\n' + '=' * 70)
    print('Ship it! 🚀 Identify leverage, amplify impact.')
    print('=' * 70)


if __name__ == '__main__':
    main()

