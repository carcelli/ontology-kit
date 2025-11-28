"""Load and query RDF/OWL ontologies."""

import hashlib
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

    def __init__(self, ontology_path: str, enable_query_cache: bool = True, cache_size: int = 128) -> None:
        """
        Initialize ontology loader.

        Args:
            ontology_path: Path to TTL/RDF/OWL file
            enable_query_cache: Whether to cache query results for performance
            cache_size: Maximum number of cached queries (LRU cache)
        """
        self.path = Path(ontology_path)
        if not self.path.exists():
            raise FileNotFoundError(f"Ontology file not found: {self.path}")

        self.graph: Graph | None = None
        self.namespaces: dict[str, Namespace] = {}
        self.enable_query_cache = enable_query_cache
        self._query_cache: dict[str, list[dict[str, Any]]] = {}
        self._cache_size = cache_size
        self._cache_hits = 0
        self._cache_misses = 0

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

    def _get_cache_key(self, sparql: str) -> str:
        """Generate cache key for SPARQL query."""
        return hashlib.md5(sparql.encode()).hexdigest()

    def query(self, sparql: str, use_cache: bool | None = None) -> list[dict[str, Any]]:
        """
        Execute SPARQL query with optional caching.

        Args:
            sparql: SPARQL query string
            use_cache: Override default caching behavior (None = use self.enable_query_cache)

        Returns:
            List of result bindings
        """
        if self.graph is None:
            raise RuntimeError("Call load() first")

        # Check cache if enabled
        should_cache = use_cache if use_cache is not None else self.enable_query_cache
        if should_cache:
            cache_key = self._get_cache_key(sparql)
            if cache_key in self._query_cache:
                self._cache_hits += 1
                return self._query_cache[cache_key]

        # Execute query
        results = self.graph.query(sparql)

        # Convert to list of dicts
        output = []
        for row in results:
            binding = {}
            for var in results.vars:
                # Handle case where variable might not be in row
                value = row.get(var) if hasattr(row, 'get') else (row[var] if var in row else None)
                binding[str(var)] = value
            output.append(binding)

        # Cache result if enabled
        if should_cache:
            cache_key = self._get_cache_key(sparql)
            # Implement LRU-style cache eviction
            if len(self._query_cache) >= self._cache_size:
                # Remove oldest entry (simple FIFO eviction)
                oldest_key = next(iter(self._query_cache))
                del self._query_cache[oldest_key]
            self._query_cache[cache_key] = output
            self._cache_misses += 1

        return output

    def clear_cache(self) -> None:
        """Clear the query cache."""
        self._query_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_queries = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_queries if total_queries > 0 else 0.0
        return {
            "cache_size": len(self._query_cache),
            "max_cache_size": self._cache_size,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate,
            "enabled": self.enable_query_cache,
        }

    def get_classes(self, use_cache: bool = True) -> list[str]:
        """
        Get all OWL/RDFS classes defined in the ontology.

        Args:
            use_cache: Whether to use query cache (default: True)

        Returns:
            List of class URIs
        """
        if self.graph is None:
            raise RuntimeError("Call load() first")

        sparql = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?class WHERE {
            { ?class a owl:Class } UNION { ?class a rdfs:Class }
        }
        """
        results = self.query(sparql, use_cache=use_cache)
        return [str(r['class']) for r in results]

    def get_properties(self, use_cache: bool = True) -> list[str]:
        """
        Get all properties (object + datatype) defined in the ontology.

        Args:
            use_cache: Whether to use query cache (default: True)

        Returns:
            List of property URIs
        """
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
        results = self.query(sparql, use_cache=use_cache)
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
