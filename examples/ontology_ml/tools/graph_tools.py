import json
from pathlib import Path
from typing import Any

import polars as pl
from agents import function_tool
from pyshacl import validate
from rdflib import OWL, RDF, RDFS, XSD, Graph, Literal, Namespace, URIRef

EX = Namespace('http://example.org/retail#')


# ---------- helpers ----------
def _xsd_from_hint(h: str) -> URIRef:
    h = (h or '').lower()
    return {
        'string': XSD.string,
        'float': XSD.float,
        'double': XSD.double,
        'int': XSD.integer,
        'integer': XSD.integer,
        'date': XSD.date,
        'datetime': XSD.dateTime,
    }.get(h, XSD.string)


def _ensure_parent_dirs(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


# ---------- tools ----------
@function_tool
def create_or_update_ontology(
    proposal_json: str,
    output_path: str = 'examples/ontology_ml/ontology/current.owl.ttl',
    base_iri: str = 'http://example.org/retail#',
) -> str:
    """
    Apply a SchemaProposal (as JSON string) to an OWL/Turtle file.
    - Creates rdfs:Class for each class.
    - Creates owl:ObjectProperty / owl:DatatypeProperty for properties with domain/range.
    Returns the path to the written TTL.
    """
    proposal = json.loads(proposal_json)
    g = Graph()
    g.bind('ex', Namespace(base_iri))
    g.bind('owl', OWL)
    g.bind('rdfs', RDFS)
    g.bind('xsd', XSD)

    # Classes
    for cls in proposal.get('classes', []):
        c_iri = URIRef(f"{base_iri}{cls['name']}")
        g.add((c_iri, RDF.type, OWL.Class))
        # (Optional) Parent: if present, declare subclass
        parent = cls.get('parent')
        if parent and parent not in ('Thing', 'thing', 'owl:Thing'):
            p_iri = URIRef(f"{base_iri}{parent}")
            g.add((p_iri, RDF.type, OWL.Class))
            g.add((c_iri, RDFS.subClassOf, p_iri))

    # Properties
    for prop in proposal.get('properties', []):
        p_iri = URIRef(f"{base_iri}{prop['name']}")
        d_iri = URIRef(f"{base_iri}{prop['domain']}")
        if prop['kind'] == 'object':
            r_iri = URIRef(f"{base_iri}{prop['range']}")
            g.add((p_iri, RDF.type, OWL.ObjectProperty))
            g.add((p_iri, RDFS.domain, d_iri))
            g.add((p_iri, RDFS.range, r_iri))
            g.add((r_iri, RDF.type, OWL.Class))
        else:
            g.add((p_iri, RDF.type, OWL.DatatypeProperty))
            g.add((p_iri, RDFS.domain, d_iri))
            g.add((p_iri, RDFS.range, _xsd_from_hint(prop['range'])))
        g.add((d_iri, RDF.type, OWL.Class))

    out = Path(output_path)
    _ensure_parent_dirs(out)
    g.serialize(destination=str(out), format='turtle')
    return str(out)


@function_tool
def shacl_validate_ttl(
    data_ttl_path: str,
    shapes_ttl_path: str,
) -> dict[str, Any]:
    """
    Validate an RDF graph with SHACL.
    Returns {'conforms': bool, 'report': str}.
    """
    data_g = Graph().parse(data_ttl_path, format='turtle')
    shapes_g = Graph().parse(shapes_ttl_path, format='turtle')
    conforms, report_g, report_text = validate(data_g, shacl_graph=shapes_g, inference='rdfs', debug=False)
    return {'conforms': bool(conforms), 'report': str(report_text)}


@function_tool
def map_csv_to_rdf(
    csv_path: str,
    mapping_json: str,
    base_iri: str = 'http://example.org/retail#',
    output_path: str = 'examples/ontology_ml/graph/data.ttl',
    row_id_column: str | None = None,
) -> dict[str, Any]:
    """
    Convert a CSV into RDF using a simple column→property mapping.
    mapping_json is a JSON of {'items': [{'column': 'total', 'property_iri': 'http://...#hasTotal'}, ...]}
    Creates Invoice individuals by default (inv_<rowidx>). If `row_id_column` is provided, uses that.
    """
    mapping = {itm['column']: itm['property_iri'] for itm in json.loads(mapping_json)['items']}
    df = pl.read_csv(csv_path)
    g = Graph()
    ex = Namespace(base_iri)
    g.bind('ex', ex)
    g.bind('xsd', XSD)

    Invoice = URIRef(f'{base_iri}Invoice')
    for i, row in enumerate(df.iter_rows(named=True)):
        row_id = str(row[row_id_column]) if row_id_column and row_id_column in row else f'{i+1}'
        inv = URIRef(f'{base_iri}Invoice/inv_{row_id}')
        g.add((inv, RDF.type, Invoice))
        for col, iri in mapping.items():
            if col not in row or row[col] is None:
                continue
            val = row[col]
            p = URIRef(iri)
            # naive datatype guess
            lit = Literal(float(val), datatype=XSD.float) if isinstance(val, (int, float)) else Literal(str(val))
            g.add((inv, p, lit))

    out = Path(output_path)
    _ensure_parent_dirs(out)
    g.serialize(destination=str(out), format='turtle')
    return {'triples': len(g), 'output_path': str(out)}


@function_tool
def export_simple_features(
    graph_ttl_path: str,
    output_parquet_path: str = 'examples/ontology_ml/features/invoice_features.parquet',
) -> str:
    """
    Exports a tiny feature set from the RDF graph:
    - invoice_count (count of Invoice nodes)
    - total_sum (sum of ex:hasTotal)
    This is intentionally minimal; extend as needed.
    """
    g = Graph().parse(graph_ttl_path, format='turtle')
    ex = Namespace('http://example.org/retail#')
    Invoice = URIRef(f'{ex}Invoice')
    hasTotal = URIRef(f'{ex}hasTotal')

    invoice_nodes = set(s for s, p, o in g.triples((None, RDF.type, Invoice)))
    totals = []
    for s in invoice_nodes:
        for _, _, val in g.triples((s, hasTotal, None)):
            try:
                totals.append(float(val))
            except Exception:
                pass

    feat = pl.DataFrame({'invoice_count': [len(invoice_nodes)], 'total_sum': [sum(totals) if totals else 0.0]})
    out = Path(output_parquet_path)
    _ensure_parent_dirs(out)
    feat.write_parquet(str(out))
    return str(out)
