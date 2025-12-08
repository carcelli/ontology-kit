#!/usr/bin/env python
"""
Example 3: Business Ontology Navigation

Demonstrates:
- Loading business ontology (business.ttl)
- Querying business entities and relations
- Discovering leverage points
- Agent-like navigation for insights
"""

import sys
from pathlib import Path

# Add src to path (for development)
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agent_kit.ontology import OntologyLoader


def main() -> None:
    print("=" * 70)
    print("Agent Kit - Example 3: Business Ontology Navigation")
    print("=" * 70)
    print()

    # Load business ontology
    ontology_path = Path(__file__).parent.parent / 'assets' / 'ontologies' / 'business.ttl'
    print(f"📚 Loading business ontology from: {ontology_path}")

    loader = OntologyLoader(str(ontology_path))
    graph = loader.load()

    print(f"   {loader}")
    print()

    # ========================================================================
    # QUERY 1: Discover all businesses
    # ========================================================================
    print("🏢 Query 1: Discover all businesses in ontology")
    sparql = """
    PREFIX : <http://agent_kit.io/business#>
    SELECT ?business ?name ?revenue ?location WHERE {
        ?business a :Business .
        ?business rdfs:label ?name .
        OPTIONAL { ?business :hasRevenue ?revenue } .
        OPTIONAL { ?business :hasLocation ?location } .
    }
    """
    results = loader.query(sparql)

    for res in results:
        name = res.get('name', 'Unknown')
        revenue = res.get('revenue', 'N/A')
        location = res.get('location', 'N/A')
        if revenue != 'N/A':
            print(f"   - {name}: ${float(revenue):,.0f}/year in {location}")
        else:
            print(f"   - {name} in {location}")
    print()

    # ========================================================================
    # QUERY 2: Client-Revenue relationships (Causal)
    # ========================================================================
    print("💰 Query 2: Which clients generate which revenue streams?")
    sparql = """
    PREFIX : <http://agent_kit.io/business#>
    SELECT ?client ?revenue ?amount WHERE {
        ?client a :Client .
        ?client rdfs:label ?clientName .
        ?revenueStream :generatedBy ?client .
        ?revenueStream rdfs:label ?revenue .
        ?revenueStream :hasAmount ?amount .
        BIND(?clientName AS ?client)
    }
    """
    results = loader.query(sparql)

    if results:
        for res in results:
            client = res['client']
            revenue = res['revenue']
            amount = float(res['amount'])
            print(f"   - {client} → {revenue}: ${amount:,.0f}")
    else:
        print("   (No client-revenue mappings found)")
    print()

    # ========================================================================
    # QUERY 3: Forecast models and their accuracy
    # ========================================================================
    print("📈 Query 3: What forecast models exist and how accurate are they?")
    sparql = """
    PREFIX : <http://agent_kit.io/business#>
    PREFIX core: <http://agent_kit.io/ontology#>
    SELECT ?model ?modelType ?accuracy WHERE {
        ?model a :ForecastModel .
        ?model rdfs:label ?modelName .
        OPTIONAL { ?model :hasModelType ?modelType } .
        OPTIONAL { ?model :hasAccuracyScore ?accuracy } .
        BIND(?modelName AS ?model)
    }
    """
    results = loader.query(sparql)

    for res in results:
        model = res['model']
        model_type = res.get('modelType', 'Unknown')
        accuracy = res.get('accuracy', 'N/A')
        if accuracy != 'N/A':
            print(f"   - {model} ({model_type}): {float(accuracy)*100:.1f}% accuracy")
        else:
            print(f"   - {model} ({model_type})")
    print()

    # ========================================================================
    # QUERY 4: Leverage Points (Strategic Insights)
    # ========================================================================
    print("🎯 Query 4: What are the top leverage points for optimization?")
    sparql = """
    PREFIX : <http://agent_kit.io/business#>
    PREFIX core: <http://agent_kit.io/ontology#>
    SELECT ?lever ?impact ?cost ?priority ?description WHERE {
        ?leverPoint a :LeveragePoint .
        ?leverPoint rdfs:label ?lever .
        OPTIONAL { ?leverPoint :hasExpectedImpact ?impact } .
        OPTIONAL { ?leverPoint core:hasCost ?cost } .
        OPTIONAL { ?leverPoint :hasPriority ?priority } .
        OPTIONAL { ?leverPoint core:hasDescription ?description } .
    }
    ORDER BY ?priority
    """
    results = loader.query(sparql)

    for i, res in enumerate(results, 1):
        lever = res['lever']
        impact = res.get('impact', 1.0)
        cost = res.get('cost', 0)
        priority = res.get('priority', '?')
        description = res.get('description', '')

        if cost:
            roi = float(impact) / (float(cost) + 1e-6)
            print(f"   {i}. {lever} (Priority {priority})")
            print(f"      ROI: {roi:.2f}x | Impact: {float(impact):.2f} | Cost: ${float(cost):,.0f}")
        else:
            print(f"   {i}. {lever} (Priority {priority})")
            print(f"      Impact: {float(impact):.2f}")

        if description:
            print(f"      → {description}")
        print()

    # ========================================================================
    # QUERY 5: Causal Chain - Campaign → Client → Revenue
    # ========================================================================
    print("🔗 Query 5: Trace causal pathway: Campaign → Client → Revenue")
    sparql = """
    PREFIX : <http://agent_kit.io/business#>
    SELECT ?campaign ?client ?revenue WHERE {
        ?campaign a :OutreachCampaign .
        ?campaign rdfs:label ?campaignName .
        ?client :engagedBy ?campaign .
        ?client rdfs:label ?clientName .
        ?revenueStream :generatedBy ?client .
        ?revenueStream rdfs:label ?revenueName .
        BIND(?campaignName AS ?campaign) .
        BIND(?clientName AS ?client) .
        BIND(?revenueName AS ?revenue) .
    }
    """
    results = loader.query(sparql)

    if results:
        for res in results:
            print(f"   {res['campaign']} → {res['client']} → {res['revenue']}")
    else:
        print("   (No complete causal chains found - add more example data)")
    print()

    # ========================================================================
    # INSIGHT GENERATION (Agent-like behavior)
    # ========================================================================
    print("💡 AGENT NAVIGATION: Discovering optimization opportunities...")
    print()

    # Find all businesses
    biz_query = "PREFIX : <http://agent_kit.io/business#> SELECT ?b WHERE { ?b a :Business }"
    businesses = loader.query(biz_query)

    # Find all leverage points affecting those businesses
    lever_query = """
    PREFIX : <http://agent_kit.io/business#>
    PREFIX core: <http://agent_kit.io/ontology#>
    SELECT ?lever ?impact ?cost WHERE {
        ?lever a :LeveragePoint .
        ?lever :hasExpectedImpact ?impact .
        ?lever core:hasCost ?cost .
    }
    """
    levers = loader.query(lever_query)

    if levers:
        print(f"📊 Found {len(businesses)} business(es) and {len(levers)} leverage point(s)")
        print()
        print("✨ Recommended actions (sorted by ROI):")

        # Calculate ROI and sort
        lever_data = []
        for lev in levers:
            impact = float(lev['impact'])
            cost = float(lev['cost'])
            roi = impact / (cost + 1e-6)
            lever_data.append({
                'name': str(lev['lever']).split('#')[-1],
                'roi': roi,
                'impact': impact,
                'cost': cost
            })

        lever_data.sort(key=lambda x: x['roi'], reverse=True)

        for i, lev in enumerate(lever_data, 1):
            print(f"{i}. {lev['name']}")
            print(f"   → ROI: {lev['roi']:.2f}x | Impact: ${lev['impact']*1000:,.0f} | Cost: ${lev['cost']:,.0f}")
    else:
        print("No leverage points found - ontology needs more example data")

    print()
    print("=" * 70)
    print("✅ Example complete!")
    print()
    print("Next steps:")
    print("  - Add more business instances to business.ttl")
    print("  - Implement agent loop (observe/plan/act/reflect) in Phase 2C")
    print("  - Integrate with vector embeddings for hybrid search")
    print("  - Read BUSINESS_ONTOLOGY_PLAN.md for full roadmap")
    print("=" * 70)


if __name__ == '__main__':
    main()

