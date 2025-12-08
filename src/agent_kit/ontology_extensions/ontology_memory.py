"""
Ontology-enhanced memory session that extends the SDK memory system.

This class adds semantic search, ontology-aware context preservation,
and knowledge graph integration to the standard SDK memory capabilities.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Try to import from agents SDK, with fallbacks
try:
    from agents.memory import SQLiteSession

    AGENTS_AVAILABLE = True
except ImportError:
    # Fallback when SDK is not available
    SQLiteSession = object
    AGENTS_AVAILABLE = False

if TYPE_CHECKING:
    try:
        from agents import TResponseInputItem
    except ImportError:
        TResponseInputItem = Any


class OntologyMemorySession(SQLiteSession if AGENTS_AVAILABLE else object):
    """
    Ontology-enhanced memory session with semantic capabilities.

    Extends the SDK SQLiteSession with:
    - Ontology-aware context storage and retrieval
    - Semantic search across conversation history
    - Knowledge graph integration for memory enrichment
    - SPARQL-based memory queries
    """

    def __init__(
        self,
        session_id: str,
        ontology_path: str | None = None,
        db_path: str | None = ":memory:",
        **kwargs,
    ):
        """
        Initialize ontology-enhanced memory session.

        Args:
            session_id: Unique session identifier
            ontology_path: Path to ontology file for semantic enhancement
            db_path: SQLite database path
            **kwargs: Additional arguments for SQLiteSession
        """
        super().__init__(session_id, db_path, **kwargs)
        self.ontology_path = ontology_path

        # Load ontology if provided
        self.ontology = None
        self.ontology_loader = None
        if ontology_path:
            try:
                from ..ontology.loader import OntologyLoader

                self.ontology_loader = OntologyLoader(ontology_path)
                self.ontology = self.ontology_loader.load()
            except Exception:
                pass  # Continue without ontology if loading fails

        # Initialize embedder for semantic search (lazy loading)
        self._embedder = None
        self._embedding_cache: dict[str, np.ndarray] = {}

    def _get_embedder(self):
        """Lazy-load embedder for semantic search."""
        if self._embedder is None:
            try:
                from ..vectorspace.embedder import Embedder

                self._embedder = Embedder(model_name="all-MiniLM-L6-v2")
            except Exception:
                return None
        return self._embedder

    def _get_text_from_item(self, item: Any) -> str:
        """Extract searchable text from a conversation item."""
        if isinstance(item, dict):
            # Try common fields
            text_parts = []
            for field in ["content", "text", "message", "role", "name"]:
                if field in item:
                    value = item[field]
                    if isinstance(value, str):
                        text_parts.append(value)
            return " ".join(text_parts)
        elif isinstance(item, str):
            return item
        else:
            return str(item)

    def _get_embedding(self, text: str) -> np.ndarray | None:
        """Get embedding for text with caching."""
        # Create cache key
        cache_key = hashlib.md5(text.encode()).hexdigest()

        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        embedder = self._get_embedder()
        if embedder is None:
            return None

        try:
            embedding = embedder.embed(text)
            self._embedding_cache[cache_key] = embedding
            return embedding
        except Exception:
            return None

    def _extract_ontology_concepts(self, query: str) -> list[str]:
        """Extract relevant ontology concepts from query."""
        if not self.ontology_loader:
            return []

        try:
            # Query ontology for concepts mentioned in query
            # This is a simple implementation - can be enhanced with NLP
            query_lower = query.lower()
            concepts = []

            # Get all classes from ontology
            classes = self.ontology_loader.get_classes()
            for cls_uri in classes:
                # Extract local name
                local_name = (
                    cls_uri.split("#")[-1] if "#" in cls_uri else cls_uri.split("/")[-1]
                )
                if local_name.lower() in query_lower:
                    concepts.append(local_name)

            return concepts[:10]  # Limit to top 10
        except Exception:
            return []

    async def search_semantic(
        self,
        query: str,
        limit: int = 10,
        ontology_context: dict[str, Any] | None = None,
    ) -> list[TResponseInputItem]:
        """
        Perform semantic search across conversation history with ontology enhancement.

        Args:
            query: Semantic query to search for
            limit: Maximum number of results to return
            ontology_context: Additional ontology context for the search

        Returns:
            Semantically relevant conversation items
        """
        # Get more items than needed for better semantic filtering
        candidate_items = await self.get_items(limit=limit * 3)

        if not candidate_items:
            return []

        # If no embedder available, fall back to recent items
        query_embedding = self._get_embedding(query)
        if query_embedding is None:
            return candidate_items[:limit]

        # Extract ontology concepts from query
        ontology_concepts = self._extract_ontology_concepts(query)

        # Score items by semantic similarity
        scored_items = []
        for item in candidate_items:
            item_text = self._get_text_from_item(item)
            item_embedding = self._get_embedding(item_text)

            if item_embedding is None:
                scored_items.append((0.0, item))
                continue

            # Calculate cosine similarity
            similarity = float(
                cosine_similarity([query_embedding], [item_embedding])[0][0]
            )

            # Boost score if ontology concepts match
            ontology_boost = 0.0
            if ontology_concepts and self.ontology:
                item_text_lower = item_text.lower()
                for concept in ontology_concepts:
                    if concept.lower() in item_text_lower:
                        ontology_boost += 0.1

            final_score = similarity + ontology_boost
            scored_items.append((final_score, item))

        # Sort by score (descending) and return top items
        scored_items.sort(key=lambda x: x[0], reverse=True)
        top_items = [item for _, item in scored_items[:limit]]

        # Add ontology metadata to results
        enhanced_items = []
        for item in top_items:
            if isinstance(item, dict):
                enhanced_item = dict(item)
                enhanced_item["_ontology_context"] = {
                    "query": query,
                    "ontology_available": self.ontology is not None,
                    "semantic_search_performed": True,
                    "ontology_concepts": ontology_concepts,
                }
                enhanced_items.append(enhanced_item)
            else:
                enhanced_items.append(item)

        return enhanced_items

    async def store_with_semantic_context(
        self,
        items: list[TResponseInputItem],
        semantic_tags: list[str] | None = None,
        ontology_relations: dict[str, Any] | None = None,
    ) -> None:
        """
        Store conversation items with semantic context and ontology relationships.

        Args:
            items: Conversation items to store
            semantic_tags: Semantic tags for categorization
            ontology_relations: Ontology relationships to store with items
        """
        # Store the basic items
        await self.add_items(items)

        # TODO: Extend storage to include semantic tags and ontology relations
        # This could involve additional database tables or metadata storage

    async def get_ontology_relevant_history(
        self,
        ontology_concepts: list[str],
        limit: int = 20,
    ) -> list[TResponseInputItem]:
        """
        Retrieve conversation history relevant to specific ontology concepts.

        Args:
            ontology_concepts: Ontology concepts to search for
            limit: Maximum items to return

        Returns:
            Conversation items relevant to the ontology concepts
        """
        if not self.ontology or not ontology_concepts:
            return await self.get_items(limit=limit)

        # Get candidate items
        candidate_items = await self.get_items(limit=limit * 3)

        # Filter items by ontology concept relevance
        relevant_items = []
        concept_lower = [c.lower() for c in ontology_concepts]

        for item in candidate_items:
            item_text = self._get_text_from_item(item).lower()

            # Check if item text contains any ontology concept
            relevance_score = 0
            for concept in concept_lower:
                if concept in item_text:
                    relevance_score += 1

            # Also check for related concepts via ontology queries
            if self.ontology_loader:
                try:
                    # Query for related concepts
                    for concept in ontology_concepts:
                        sparql = f"""
                        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                        PREFIX owl: <http://www.w3.org/2002/07/owl#>
                        SELECT ?related WHERE {{
                            {{
                                ?concept rdfs:label ?label .
                                FILTER(REGEX(?label, "{concept}", "i"))
                                ?concept (rdfs:subClassOf|owl:equivalentClass|^rdfs:subClassOf)* ?related .
                                ?related rdfs:label ?relatedLabel .
                            }}
                        }}
                        LIMIT 5
                        """
                        try:
                            results = self.ontology_loader.query(sparql)
                            for result in results:
                                related = str(result.get("related", ""))
                                if related and related.lower() in item_text:
                                    relevance_score += 0.5
                        except Exception:
                            pass
                except Exception:
                    pass

            if relevance_score > 0:
                relevant_items.append((relevance_score, item))

        # Sort by relevance and return top items
        relevant_items.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in relevant_items[:limit]]

    async def enrich_with_ontology_context(
        self,
        query: str,
        context_items: list[TResponseInputItem],
    ) -> dict[str, Any]:
        """
        Enrich a query with ontology context from conversation history.

        Args:
            query: The query to enrich
            context_items: Relevant conversation items

        Returns:
            Dictionary with enriched context information
        """
        enrichment = {
            "original_query": query,
            "conversation_context": len(context_items),
            "ontology_available": self.ontology is not None,
        }

        if self.ontology and self.ontology_loader:
            # Extract ontology concepts from query
            concepts = self._extract_ontology_concepts(query)

            # Extract concepts from context items
            context_text = " ".join(
                [self._get_text_from_item(item) for item in context_items]
            )
            context_concepts = self._extract_ontology_concepts(context_text)

            # Combine and deduplicate
            all_concepts = list(set(concepts + context_concepts))

            # Find semantic relationships
            relationships = []
            if all_concepts and self.ontology_loader:
                try:
                    for concept in all_concepts[:5]:  # Limit to avoid too many queries
                        sparql = f"""
                        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                        PREFIX owl: <http://www.w3.org/2002/07/owl#>
                        SELECT ?related ?relation WHERE {{
                            {{
                                ?concept rdfs:label ?label .
                                FILTER(REGEX(?label, "{concept}", "i"))
                                ?concept ?relation ?related .
                                ?related rdfs:label ?relatedLabel .
                            }}
                        }}
                        LIMIT 3
                        """
                        try:
                            results = self.ontology_loader.query(sparql)
                            for result in results:
                                rel_type = (
                                    str(result.get("relation", ""))
                                    .split("#")[-1]
                                    .split("/")[-1]
                                )
                                related = (
                                    str(result.get("related", ""))
                                    .split("#")[-1]
                                    .split("/")[-1]
                                )
                                if rel_type and related:
                                    relationships.append(
                                        {
                                            "concept": concept,
                                            "relation": rel_type,
                                            "related": related,
                                        }
                                    )
                        except Exception:
                            pass
                except Exception:
                    pass

            enrichment["ontology_concepts"] = all_concepts
            enrichment["semantic_relationships"] = relationships
        else:
            enrichment["ontology_concepts"] = []
            enrichment["semantic_relationships"] = []

        return enrichment
