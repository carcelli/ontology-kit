"""Load and query RDF/OWL ontologies."""

from pathlib import Path
from typing import Any

from rdflib import Graph, Namespace


class OntologyLoader:
    """
    Load and query ontologies from TTL/RDF/OWL files.
    
    Example:
        >>> loader = OntologyLoader('assets/ontologies/core.ttl')
        >>> graph = loader.load()
        >>> results = loader.query("SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10")
        >>> len(results)
        10
    """

    def __init__(self, ontology_path: str) -> None:
        """
        Initialize ontology loader.
        
        Args:
            ontology_path: Path to TTL/RDF/OWL file
        """
        self.path = Path(ontology_path)
        if not self.path.exists():
            raise FileNotFoundError(f"Ontology file not found: {self.path}")

        self.graph: Graph | None = None
        self.namespaces: dict[str, Namespace] = {}

    def load(self, format: str = 'turtle') -> Graph:
        """
        Load ontology into RDFLib graph.
        
        Args:
            format: 'turtle', 'xml', 'n3', etc.
            
        Returns:
            RDFLib Graph object
        """
        self.graph = Graph()
        self.graph.parse(self.path, format=format)

        # Extract namespaces
        for prefix, namespace in self.graph.namespaces():
            self.namespaces[prefix] = namespace

        return self.graph

    def query(self, sparql: str) -> list[dict[str, Any]]:
        """
        Execute SPARQL query.
        
        Args:
            sparql: SPARQL query string
            
        Returns:
            List of result bindings
        """
        if self.graph is None:
            raise RuntimeError("Call load() first")

        results = self.graph.query(sparql)

        # Convert to list of dicts
        output = []
        for row in results:
            binding = {}
            for var in results.vars:
                binding[str(var)] = row[var]
            output.append(binding)

        return output

    def get_classes(self) -> list[str]:
        """Get all OWL/RDFS classes defined in the ontology."""
        if self.graph is None:
            raise RuntimeError("Call load() first")

        sparql = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?class WHERE {
            { ?class a owl:Class } UNION { ?class a rdfs:Class }
        }
        """
        results = self.query(sparql)
        return [str(r['class']) for r in results]

    def get_properties(self) -> list[str]:
        """Get all properties (object + datatype) defined in the ontology."""
        if self.graph is None:
            raise RuntimeError("Call load() first")

        sparql = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT DISTINCT ?prop WHERE {
            { ?prop a owl:ObjectProperty } UNION 
            { ?prop a owl:DatatypeProperty } UNION
            { ?prop a rdf:Property }
        }
        """
        results = self.query(sparql)
        return [str(r['prop']) for r in results]

    def __repr__(self) -> str:
        status = 'loaded' if self.graph is not None else 'not loaded'
        triples = len(self.graph) if self.graph is not None else 0
        return f"OntologyLoader(path='{self.path}', status={status}, triples={triples})"

    def add_triple(self, subject: Any, predicate: Any, object_: Any) -> None:
        """Adds a triple to the graph (idempotent if exists)."""
        if self.graph is None:
            raise RuntimeError("Call load() first")
        self.graph.add((subject, predicate, object_))

    def save(self, file_path: str | None = None, format: str = 'turtle') -> None:
        """Serializes and saves the graph back to file."""
        if self.graph is None:
            raise RuntimeError("Call load() first")
        path = file_path or self.path
        self.graph.serialize(destination=path, format=format)
