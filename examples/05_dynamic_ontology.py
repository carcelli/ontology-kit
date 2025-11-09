# examples/05_dynamic_ontology.py
import asyncio
import os
from pathlib import Path
from agent_kit.agents.ontology_agent import OntologyAgent
from agent_kit.tools.ontology import query_ontology, add_ontology_statement

# WARNING: This is a placeholder API key. Do not use this in production.
os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"

async def main():
    ontology_path = Path(__file__).parent.parent / 'assets' / 'ontologies' / 'business.ttl'

    # 1. Query the ontology for existing information
    print("\n--- Querying existing ontology ---")
    query_results = query_ontology("""
        PREFIX : <http://agent_kit.io/business#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?businessName WHERE {
            ?business a :Business ;
                      rdfs:label ?businessName .
        }
    """)
    print("Existing businesses:", [str(r['businessName']) for r in query_results])

    # 2. Simulate an agent generating a new insight and adding it to the ontology
    print("\n--- Agent adding new insight ---")
    new_insight_id = "insight_002"
    new_insight_text = "Customers in cold climates prefer warm beverages in Q4."
    affected_business_id = "biz_001" # Assuming Sunshine Bakery from business.ttl

    # Add the insight as a new entity
    add_ontology_statement(new_insight_id, "type", "Insight", object_type="uri")
    add_ontology_statement(new_insight_id, "hasText", new_insight_text, object_type="literal")
    add_ontology_statement(new_insight_id, "informsBusiness", affected_business_id, object_type="uri")

    print(f"Added new insight '{new_insight_id}': '{new_insight_text}' informing '{affected_business_id}'")

    # 3. Verify the new insight is in the ontology
    print("\n--- Verifying new insight ---")
    verify_query_results = query_ontology(f"""
        PREFIX : <http://agent_kit.io/business#>
        SELECT ?text WHERE {{
            :{new_insight_id} :hasText ?text .
        }}
    """ )
    print("Retrieved new insight text:", [str(r['text']) for r in verify_query_results])

if __name__ == '__main__':
    asyncio.run(main())
