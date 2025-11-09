"""
Hyperdimensional visualization tool for semantic space analysis.

Enables agents to generate t-SNE visualizations of ontology terms or custom
text, revealing semantic clusters and relationships in 2D/3D projections.

Usage (as agent tool):
    from agent_kit.tools import generate_hyperdim_viz
    from agents import Agent

    agent = Agent(
        name="Analyst",
        tools=[generate_hyperdim_viz]
    )
    result = await Runner.run(agent, "Visualize business.ttl semantics")

Usage (direct call):
    path = generate_hyperdim_viz(
        ontology_path='assets/ontologies/business.ttl',
        output_file='business_viz.png'
    )
"""

import os
from pathlib import Path
from typing import Annotated

import matplotlib.pyplot as plt
import numpy as np
from rdflib import Graph
from sklearn.manifold import TSNE

from agent_kit.vectorspace.embedder import Embedder


def generate_hyperdim_viz(
    ontology_path: Annotated[str | None, "Path to RDF/OWL ontology file (*.ttl, *.owl)"] = None,
    terms: Annotated[list[str] | None, "Custom list of terms to visualize (overrides ontology)"] = None,
    model_name: Annotated[str, "SentenceTransformer model name"] = 'all-MiniLM-L6-v2',
    n_components: Annotated[int, "Output dimensions (2 or 3 for visualization)"] = 2,
    perplexity: Annotated[int | None, "t-SNE perplexity (auto-computed if None)"] = None,
    max_terms: Annotated[int, "Maximum terms to extract from ontology"] = 50,
    output_file: Annotated[str, "Path to save PNG visualization"] = 'hyperdim_viz.png',
) -> str:
    """
    Generate 2D/3D t-SNE visualization of hyperdimensional semantic space.

    Embeds terms semantically (384D via SentenceTransformers), reduces to
    2D/3D via t-SNE (preserving local structure), and plots with annotations.
    Useful for exploring ontology clusters or custom term relationships.

    Args:
        ontology_path: Path to ontology file. If provided, extracts entity/property names.
        terms: List of strings to visualize. If both ontology_path and terms given, uses terms.
        model_name: Embedding model (default: all-MiniLM-L6-v2, 384D).
        n_components: 2 for 2D plot, 3 for 3D plot.
        perplexity: t-SNE perplexity parameter. Auto-set to min(30, n_terms-1) if None.
        max_terms: Maximum terms to extract from ontology (prevents overwhelming plots).
        output_file: Path to save visualization PNG.

    Returns:
        Absolute path to saved PNG file.

    Raises:
        ValueError: If no valid input (missing both ontology_path and terms),
                    insufficient terms (<2), invalid n_components, or file I/O errors.
        FileNotFoundError: If ontology_path doesn't exist.

    Examples:
        >>> # From ontology
        >>> path = generate_hyperdim_viz(
        ...     ontology_path='assets/ontologies/business.ttl',
        ...     output_file='business_space.png'
        ... )

        >>> # From custom terms
        >>> path = generate_hyperdim_viz(
        ...     terms=['Business', 'Client', 'Revenue', 'Forecast'],
        ...     n_components=3,
        ...     output_file='custom_3d.png'
        ... )
    """
    # Validation
    if n_components not in (2, 3):
        raise ValueError(f"n_components must be 2 or 3, got {n_components}")

    # Step 1: Extract terms
    final_terms = _extract_terms(ontology_path, terms, max_terms)

    if len(final_terms) < 2:
        raise ValueError(
            f"Need at least 2 terms for visualization, got {len(final_terms)}. "
            f"Provide valid ontology_path or terms list."
        )

    # Step 2: Embed semantically (reuse existing Embedder)
    embedder = Embedder(model_name=model_name)
    embeddings = embedder.embed_batch(final_terms)

    # Step 3: Reduce dimensions with t-SNE
    perplexity_val = perplexity if perplexity is not None else min(30, len(final_terms) - 1)
    if perplexity_val >= len(final_terms):
        perplexity_val = max(1, len(final_terms) - 1)

    tsne = TSNE(n_components=n_components, random_state=42, perplexity=perplexity_val, init='random')
    embed_low_d = tsne.fit_transform(embeddings)

    # Step 4: Plot and save
    output_path = _plot_embeddings(embed_low_d, final_terms, n_components, output_file)

    # Step 5: Compute sample distances (for validation/logging)
    _log_sample_distances(embed_low_d, final_terms)

    return output_path


def _extract_terms(ontology_path: str | None, terms: list[str] | None, max_terms: int) -> list[str]:
    """
    Extract terms from ontology or use provided list.

    Priority: terms (if provided) > ontology extraction
    """
    if terms:
        return terms

    if not ontology_path:
        raise ValueError("Must provide either 'ontology_path' or 'terms'")

    ontology_file = Path(ontology_path)
    if not ontology_file.exists():
        raise FileNotFoundError(f"Ontology file not found: {ontology_path}")

    # Parse ontology and extract local names
    graph = Graph()
    try:
        graph.parse(str(ontology_file), format='turtle')
    except Exception as e:
        raise ValueError(f"Failed to parse ontology {ontology_path}: {e}")

    extracted = set()
    for subj, pred, obj in graph:
        # Extract local names (after # or /)
        for node in (subj, pred, obj):
            node_str = str(node)
            if '#' in node_str:
                local_name = node_str.split('#')[-1]
            elif '/' in node_str:
                local_name = node_str.split('/')[-1]
            else:
                local_name = node_str

            # Filter out URIs, blanks, literals that are too long
            if local_name and len(local_name) < 50 and not local_name.startswith('_:'):
                extracted.add(local_name)

    # Sort for determinism, limit to max_terms
    terms_list = sorted(extracted)[:max_terms]

    if not terms_list:
        raise ValueError(f"No valid terms extracted from ontology: {ontology_path}")

    return terms_list


def _plot_embeddings(embed_low_d: np.ndarray, terms: list[str], n_components: int, output_file: str) -> str:
    """Create and save visualization plot."""
    fig = plt.figure(figsize=(14, 10))

    if n_components == 3:
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(embed_low_d[:, 0], embed_low_d[:, 1], embed_low_d[:, 2], c='steelblue', alpha=0.6, s=100, edgecolors='navy')

        for i, term in enumerate(terms):
            ax.text(
                embed_low_d[i, 0],
                embed_low_d[i, 1],
                embed_low_d[i, 2],
                term,
                fontsize=8,
                alpha=0.8,
            )

        ax.set_title('3D Hyperdimensional Semantic Space (t-SNE)', fontsize=14, fontweight='bold')
        ax.set_xlabel('t-SNE Dimension 1', fontsize=10)
        ax.set_ylabel('t-SNE Dimension 2', fontsize=10)
        ax.set_zlabel('t-SNE Dimension 3', fontsize=10)
        ax.grid(True, alpha=0.3)

    else:  # 2D
        plt.scatter(embed_low_d[:, 0], embed_low_d[:, 1], c='steelblue', alpha=0.6, s=100, edgecolors='navy')

        for i, term in enumerate(terms):
            plt.annotate(
                term,
                (embed_low_d[i, 0], embed_low_d[i, 1]),
                fontsize=8,
                alpha=0.8,
                xytext=(5, 5),
                textcoords='offset points',
            )

        plt.title('2D Hyperdimensional Semantic Space (t-SNE)', fontsize=14, fontweight='bold')
        plt.xlabel('t-SNE Dimension 1', fontsize=10)
        plt.ylabel('t-SNE Dimension 2', fontsize=10)
        plt.grid(True, alpha=0.3)

    plt.tight_layout()

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
    except Exception as e:
        raise ValueError(f"Failed to save visualization to {output_file}: {e}")
    finally:
        plt.close(fig)  # Free memory

    return str(output_path.resolve())


def _log_sample_distances(embed_low_d: np.ndarray, terms: list[str]) -> None:
    """Log sample semantic distances for validation."""
    # Check common ontology term pairs
    pairs = [
        ('Business', 'Client'),
        ('Revenue', 'Forecast'),
        ('Agent', 'Tool'),
        ('optimizes', 'improves'),
    ]

    for term1, term2 in pairs:
        if term1 in terms and term2 in terms:
            idx1 = terms.index(term1)
            idx2 = terms.index(term2)
            dist = np.linalg.norm(embed_low_d[idx1] - embed_low_d[idx2])
            print(f"  Semantic distance '{term1}' ↔ '{term2}': {dist:.3f}")

