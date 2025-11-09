import asyncio
import json
from pathlib import Path

import polars as pl

from agents import Runner

from .agents.mapper_agent import MappingPlan, mapper_agent
from .agents.schema_agent import SchemaProposal, schema_agent
from .tools.graph_tools import (
    create_or_update_ontology,
    export_simple_features,
    map_csv_to_rdf,
    shacl_validate_ttl,
)

SHAPES = 'examples/ontology_ml/ontology/shapes.ttl'
DEFAULT_ONTOLOGY = 'examples/ontology_ml/ontology/current.owl.ttl'


async def main(
    csv_path: str,
    csv_preview_rows: int = 5,
) -> None:
    print('=' * 70)
    print('Ontology-Driven ML Pipeline (OpenAI Agents SDK)')
    print('=' * 70)

    # 1) Get CSV header + preview to ground the agents
    df = pl.read_csv(csv_path)
    preview = df.head(csv_preview_rows).to_pandas().to_markdown(index=False)

    # 2) Ask SchemaAgent for a minimal ontology extension
    print('\n📋 Step 1: Schema Design (SchemaAgent)')
    print('-' * 70)
    schema_input = (
        'Dataset preview:\n'
        f'{preview}\n\n'
        'Seed concepts: Customer, Invoice with hasDate (date), hasTotal (float). '
        'Propose any additional classes/properties needed.'
    )
    schema_result = await Runner.run(schema_agent, schema_input)
    proposal: SchemaProposal = schema_result.output
    print(f"Proposed classes: {[c.name for c in proposal.classes]}")
    print(f"Proposed properties: {[p.name for p in proposal.properties]}")

    # 3) Apply ontology changes
    print('\n🔧 Step 2: Apply Schema Changes')
    print('-' * 70)
    onto_path = create_or_update_ontology(json.dumps(proposal.model_dump()), output_path=DEFAULT_ONTOLOGY)
    print(f'✅ Ontology written: {onto_path}')

    # 4) Validate (no instances yet — should still conform)
    print('\n✓ Step 3: SHACL Validation')
    print('-' * 70)
    val = shacl_validate_ttl(onto_path, SHAPES)
    print(f"Conforms: {val['conforms']}")

    # 5) Run mapping agent
    print('\n🗺️  Step 4: Column Mapping (MapperAgent)')
    print('-' * 70)
    terms = ', '.join(sorted({p.name for p in proposal.properties} | {'hasDate', 'hasTotal'}))
    mapper_prompt = (
        f"CSV columns: {', '.join(df.columns)}\n"
        f'Known properties: {terms}\n'
        f'Base IRI: http://example.org/retail# . '
        f'Map columns to IRIs. If you see date/total-like columns, map to ex:hasDate / ex:hasTotal.'
    )
    mapping_result = await Runner.run(mapper_agent, mapper_prompt)
    mapping: MappingPlan = mapping_result.output
    for item in mapping.items:
        print(f'  {item.column} → {item.property_iri}')

    # 6) Materialize instances from CSV using the mapping
    print('\n🔄 Step 5: CSV → RDF Conversion')
    print('-' * 70)
    mapping_json = mapping.model_dump_json()
    rdf = map_csv_to_rdf(csv_path, mapping_json, output_path='examples/ontology_ml/graph/data.ttl')
    print(f"✅ RDF triples: {rdf['triples']}")

    # 7) Validate SHACL with instances
    print('\n✓ Step 6: SHACL Validation (With Data)')
    print('-' * 70)
    val2 = shacl_validate_ttl(rdf['output_path'], SHAPES)
    print(f"Conforms: {val2['conforms']}")
    if not val2['conforms']:
        print(val2['report'])

    # 8) Export a minimal features table
    print('\n📊 Step 7: Feature Extraction')
    print('-' * 70)
    feat_path = export_simple_features(rdf['output_path'])
    print(f'✅ Features exported: {feat_path}')

    # Show extracted features
    features_df = pl.read_parquet(feat_path)
    print('\nExtracted Features:')
    print(features_df.to_pandas().to_markdown(index=False))

    print('\n' + '=' * 70)
    print('✅ Pipeline Complete!')
    print('=' * 70)


if __name__ == '__main__':
    import argparse

    ap = argparse.ArgumentParser(description='Ontology-driven ML (agents demo)')
    ap.add_argument('--csv', required=True, help='Path to a CSV with at least date/total columns')
    args = ap.parse_args()
    asyncio.run(main(args.csv))
