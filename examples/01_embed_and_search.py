#!/usr/bin/env python
"""
Example 1: Embed and Search

Demonstrates basic vector space operations:
- Embedding text with SentenceTransformers
- Building FAISS index
- Querying for similar items
"""

import sys
from pathlib import Path

# Add src to path (for development)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_kit.vectorspace import Embedder, VectorIndex


def main() -> None:
    print("=" * 70)
    print("Agent Kit - Example 1: Embed and Search")
    print("=" * 70)
    print()

    # Sample task descriptions
    tasks = [
        "Sort a list of numbers in ascending order",
        "Find the maximum element in an array",
        "Reverse a string",
        "Calculate the sum of all elements",
        "Search for a specific value",
        "Filter elements that match a condition",
        "Map each element to a new value",
        "Reduce array to a single value",
        "Merge two sorted arrays",
        "Remove duplicate elements",
    ]

    print(f"📝 Embedding {len(tasks)} task descriptions...")

    # 1. Initialize embedder
    embedder = Embedder(model_name="all-MiniLM-L6-v2")
    print(f"   Model: {embedder.model_name}")
    print(f"   Dimension: {embedder.dimension}")
    print()

    # 2. Generate embeddings
    embeddings = embedder.embed_batch(tasks, show_progress=True)
    print(f"   Shape: {embeddings.shape}")
    print()

    # 3. Build vector index
    print("🔧 Building FAISS index...")
    index = VectorIndex(dim=embedder.dimension, metric="cosine")
    index.add(embeddings, ids=list(range(len(tasks))), metadata=tasks)
    print(f"   Index: {index}")
    print()

    # 4. Query
    queries = [
        "Order items by value",
        "Locate specific element",
        "Combine two lists",
    ]

    print("🔍 Searching for similar tasks...")
    print()

    for query_text in queries:
        print(f"Query: '{query_text}'")
        query_vec = embedder.embed(query_text)
        results = index.query(query_vec, k=3)

        print("Top 3 results:")
        for i, res in enumerate(results, 1):
            task_desc = res["metadata"]
            similarity = 1 - res["distance"]  # Convert distance back to similarity
            print(f"  {i}. {task_desc}")
            print(f"     (similarity: {similarity:.3f})")
        print()

    print("=" * 70)
    print("✅ Example complete!")
    print()
    print("Next steps:")
    print("  - Check out examples/02_ontology_query.py")
    print("  - Read QUICKSTART.md for Phase 1 checklist")
    print("=" * 70)


if __name__ == "__main__":
    main()
