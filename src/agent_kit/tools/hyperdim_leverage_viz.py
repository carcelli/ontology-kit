"""
Hyperdimensional leverage visualization tool for identifying intervention points.

Extends semantic space visualization with multi-factor leverage scoring:
- Leverage(v) = A(v) × (S(v) + U(v) + C(v))

Where:
- A(v): Actionability (binary: can we intervene?)
- S(v): Sensitivity (distance to KPI - closer = higher impact)
- U(v): Uncertainty (embedding variance - higher = more info value)
- C(v): Centrality (graph betweenness - bridges = leverage)

Enables agents to identify high-leverage intervention points in ontologies,
revealing which terms/concepts offer the most impactful change opportunities.

Usage:
    from agent_kit.tools import generate_hyperdim_leverage_viz

    result = generate_hyperdim_leverage_viz(
        ontology_path='assets/ontologies/business.ttl',
        kpi_term='Revenue',
        actionable_terms=['OutreachCampaign', 'EmailTiming'],
        output_file='leverage_analysis.png'
    )

    print(f"Visualization: {result['viz_path']}")
    print(f"Top levers: {result['top_levers']}")
"""

import logging
from pathlib import Path
from typing import Annotated, Any

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from agents import function_tool
from rdflib import Graph
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE

from agent_kit.vectorspace.embedder import Embedder

logger = logging.getLogger(__name__)


@function_tool
def generate_hyperdim_leverage_viz(
    ontology_path: Annotated[str | None, "Path to RDF/OWL ontology file"] = None,
    terms: Annotated[
        list[str] | None, "Custom terms to analyze (overrides ontology)"
    ] = None,
    kpi_term: Annotated[
        str, "Key Performance Indicator term for sensitivity calculation"
    ] = "Revenue",
    actionable_terms: Annotated[
        list[str] | None,
        "Terms that can be intervened upon (default: all terms actionable)",
    ] = None,
    model_name: Annotated[str, "SentenceTransformer model name"] = "all-MiniLM-L6-v2",
    n_components: Annotated[int, "Output dimensions (2 or 3)"] = 2,
    perplexity: Annotated[int | None, "t-SNE perplexity (auto if None)"] = None,
    max_terms: Annotated[int, "Maximum terms to extract from ontology"] = 50,
    output_file: Annotated[
        str, "Path to save leverage visualization PNG"
    ] = "hyperdim_leverage_viz.png",
) -> dict[str, Any]:
    """
    Generate hyperdimensional semantic visualization with multi-factor leverage scoring.

    Computes leverage as L(v) = A(v) × (S(v) + U(v) + C(v)) where:
    - A: Actionability (binary: 1 if intervene-able, 0 if fixed)
    - S: Sensitivity (1 - normalized_distance_to_KPI)
    - U: Uncertainty (cluster variance, proxy for information value)
    - C: Centrality (betweenness in ontology graph)

    Colors nodes by leverage score (red=high, blue=low) to highlight
    intervention points for maximum impact.

    Args:
        ontology_path: Path to ontology file. Extracts terms and builds graph if provided.
        terms: Custom terms to analyze. Takes precedence over ontology.
        kpi_term: KPI for sensitivity calculation (e.g., 'Revenue', 'ClientSatisfaction').
        actionable_terms: Terms flagged as actionable. If None, all terms default to A=1.
        model_name: Embedding model for semantic analysis.
        n_components: 2 for 2D plot, 3 for 3D plot.
        perplexity: t-SNE perplexity. Auto-tuned if None.
        max_terms: Maximum terms to extract from ontology.
        output_file: Path to save visualization PNG.

    Returns:
        {
            'viz_path': str,  # Absolute path to PNG
            'top_levers': List[Dict],  # Top 10 leverage points with scores
            'scores': Dict[str, Dict],  # Full breakdown: {term: {L, A, S, U, C}}
        }

    Raises:
        ValueError: If insufficient terms, missing KPI, or invalid input.
        FileNotFoundError: If ontology_path doesn't exist.

    Examples:
        >>> # Identify leverage points in business ontology
        >>> result = generate_hyperdim_leverage_viz(
        ...     ontology_path='assets/ontologies/business.ttl',
        ...     kpi_term='Revenue',
        ...     actionable_terms=['OutreachCampaign', 'EmailTiming']
        ... )
        >>> print(f"Top lever: {result['top_levers'][0]}")
    """
    # Validation
    if n_components not in (2, 3):
        raise ValueError(f"n_components must be 2 or 3, got {n_components}")

    # Step 1: Extract terms and build graph
    final_terms, nx_graph = _extract_terms_and_graph(ontology_path, terms, max_terms)

    if len(final_terms) < 2:
        raise ValueError(f"Need at least 2 terms, got {len(final_terms)}")

    if kpi_term not in final_terms:
        raise ValueError(
            f"KPI term '{kpi_term}' not in term list. Available terms: {final_terms[:10]}..."
        )

    # Step 2: Embed semantically
    embedder = Embedder(model_name=model_name)
    embeddings = embedder.embed_batch(final_terms)

    # Step 3: Compute leverage components
    print(f"\n🔬 Computing leverage scores for {len(final_terms)} terms...")

    # A: Actionability (binary)
    actionability = _compute_actionability(final_terms, actionable_terms)

    # C: Centrality (betweenness in graph)
    centrality = _compute_centrality(nx_graph, final_terms)

    # U: Uncertainty (cluster variance)
    uncertainty = _compute_uncertainty(embeddings, final_terms)

    # S: Sensitivity (inverse distance to KPI)
    sensitivity = _compute_sensitivity(embeddings, final_terms, kpi_term)

    # Aggregate: L = A × (S + U + C)
    leverage_scores = {}
    for term in final_terms:
        leverage_scores[term] = actionability[term] * (
            sensitivity[term] + uncertainty[term] + centrality[term]
        )

    # Top levers
    top_levers = sorted(
        [{"term": t, "leverage": leverage_scores[t]} for t in final_terms],
        key=lambda x: x["leverage"],
        reverse=True,
    )[:10]

    print("\n🎯 Top 3 Leverage Points:")
    for i, lever in enumerate(top_levers[:3], 1):
        print(f"  {i}. {lever['term']}: {lever['leverage']:.3f}")

    # Step 4: Reduce dimensions with t-SNE
    perplexity_val = (
        perplexity if perplexity is not None else min(30, len(final_terms) - 1)
    )
    if perplexity_val >= len(final_terms):
        perplexity_val = max(1, len(final_terms) - 1)

    tsne = TSNE(
        n_components=n_components,
        random_state=42,
        perplexity=perplexity_val,
        init="random",
    )
    embed_low_d = tsne.fit_transform(embeddings)

    # Step 5: Visualize with leverage coloring
    output_path = _plot_leverage(
        embed_low_d,
        final_terms,
        leverage_scores,
        actionability,
        n_components,
        output_file,
    )

    # Step 6: Return structured results
    scores_breakdown = {
        term: {
            "leverage": leverage_scores[term],
            "actionability": actionability[term],
            "sensitivity": sensitivity[term],
            "uncertainty": uncertainty[term],
            "centrality": centrality[term],
        }
        for term in final_terms
    }

    return {
        "viz_path": output_path,
        "top_levers": top_levers,
        "scores": scores_breakdown,
    }


def _extract_terms_and_graph(
    ontology_path: str | None, terms: list[str] | None, max_terms: int
) -> tuple[list[str], nx.Graph]:
    """Extract terms and build NetworkX graph from ontology or custom terms."""
    if terms:
        # Custom terms: build trivial graph (no relations)
        nx_graph = nx.Graph()
        nx_graph.add_nodes_from(terms)
        return terms, nx_graph

    if not ontology_path:
        raise ValueError("Must provide either 'ontology_path' or 'terms'")

    ontology_file = Path(ontology_path)
    if not ontology_file.exists():
        raise FileNotFoundError(f"Ontology file not found: {ontology_path}")

    # Parse ontology and build graph
    graph_rdf = Graph()
    try:
        graph_rdf.parse(str(ontology_file), format="turtle")
    except Exception as e:
        raise ValueError(f"Failed to parse ontology {ontology_path}: {e}") from e

    terms_set = set()
    nx_graph = nx.Graph()

    for subj, _pred, obj in graph_rdf:
        # Extract local names
        subj_name = str(subj).split("#")[-1].split("/")[-1]
        obj_name = str(obj).split("#")[-1].split("/")[-1]

        # Filter valid SEMANTIC terms (not literals, numbers, dates)
        if subj_name and _is_semantic_term(subj_name):
            terms_set.add(subj_name)
            nx_graph.add_node(subj_name)

        if obj_name and _is_semantic_term(obj_name):
            terms_set.add(obj_name)
            nx_graph.add_node(obj_name)

        # Add edge for graph structure
        if (
            subj_name
            and obj_name
            and _is_semantic_term(subj_name)
            and _is_semantic_term(obj_name)
        ):
            nx_graph.add_edge(subj_name, obj_name)

    terms_list = sorted(terms_set)[:max_terms]

    if not terms_list:
        raise ValueError(f"No valid terms extracted from ontology: {ontology_path}")

    return terms_list, nx_graph


def _is_semantic_term(term: str) -> bool:
    """
    Check if term is a semantic entity (not a literal, number, date, etc.).

    Args:
        term: Term to check

    Returns:
        True if semantic, False if literal/number/date
    """
    # Filter out empty, too short, too long
    if not term or len(term) < 2 or len(term) > 50:
        return False

    # Filter out blank nodes
    if term.startswith("_:"):
        return False

    # Filter out pure numbers
    try:
        float(term)
        return False  # It's a number
    except ValueError:
        pass

    # Filter out date-like patterns (YYYY-MM-DD, etc.)
    if any(char.isdigit() for char in term) and any(
        sep in term for sep in ["-", "/", ":"]
    ):
        # Looks like a date or timestamp
        digit_ratio = sum(c.isdigit() for c in term) / len(term)
        if digit_ratio > 0.3:  # >30% digits = likely literal
            return False

    # Filter out URIs
    if term.startswith("http") or "://" in term:
        return False

    # Keep terms with mostly alphabetic characters
    alpha_ratio = sum(c.isalpha() for c in term) / len(term)
    if alpha_ratio < 0.5:  # <50% alphabetic = likely not semantic
        return False

    return True


def _compute_actionability(
    terms: list[str], actionable_terms: list[str] | None
) -> dict[str, float]:
    """
    Compute actionability (A): Binary flag for whether term can be intervened upon.

    Args:
        terms: All terms
        actionable_terms: User-flagged actionable terms. If None, default all to 1.0.

    Returns:
        {term: 1.0 or 0.0}
    """
    if actionable_terms is None:
        # Default: all terms actionable (MVP assumption)
        return dict.fromkeys(terms, 1.0)

    return {t: 1.0 if t in actionable_terms else 0.0 for t in terms}


def _compute_centrality(nx_graph: nx.Graph, terms: list[str]) -> dict[str, float]:
    """
    Compute centrality (C): Betweenness centrality in ontology graph.

    Betweenness measures how many shortest paths go through a node.
    High betweenness = bridge between clusters = high leverage.

    Args:
        nx_graph: NetworkX graph built from ontology relations
        terms: All terms

    Returns:
        {term: normalized_betweenness [0, 1]}
    """
    try:
        betweenness = nx.betweenness_centrality(nx_graph)
    except Exception as e:
        # Fallback for disconnected graphs or errors
        logger.warning(f"Failed to calculate betweenness centrality: {e}")
        betweenness = dict.fromkeys(terms, 0.0)

    # Normalize to [0, 1]
    max_betweenness = max(betweenness.values()) if betweenness else 1.0
    if max_betweenness == 0:
        max_betweenness = 1.0

    return {t: betweenness.get(t, 0.0) / max_betweenness for t in terms}


def _compute_uncertainty(embeddings: np.ndarray, terms: list[str]) -> dict[str, float]:
    """
    Compute uncertainty (U): Cluster variance as proxy for information value.

    High variance = semantically diverse cluster = high uncertainty
    = high value of information (worth investigating).

    Args:
        embeddings: Term embeddings (n_terms, embedding_dim)
        terms: All terms

    Returns:
        {term: normalized_cluster_variance [0, 1]}
    """
    n_terms = len(terms)
    k = max(2, int(np.sqrt(n_terms)))  # Number of clusters (heuristic)

    try:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(embeddings)
    except Exception as e:
        # Fallback: single cluster
        logger.warning(f"Failed to perform clustering: {e}")
        return dict.fromkeys(terms, 0.0)

    # Compute variance per cluster
    uncertainty_scores = {}
    for cluster_id in range(k):
        cluster_mask = kmeans.labels_ == cluster_id
        cluster_embeddings = embeddings[cluster_mask]

        if len(cluster_embeddings) > 1:
            # Variance: mean of standard deviations across dimensions
            variance = np.mean(np.std(cluster_embeddings, axis=0))
        else:
            variance = 0.0

        # Assign to all terms in cluster
        for idx in np.where(cluster_mask)[0]:
            uncertainty_scores[terms[idx]] = variance

    # Normalize to [0, 1]
    max_uncertainty = max(uncertainty_scores.values()) if uncertainty_scores else 1.0
    if max_uncertainty == 0:
        max_uncertainty = 1.0

    return {t: uncertainty_scores.get(t, 0.0) / max_uncertainty for t in terms}


def _compute_sensitivity(
    embeddings: np.ndarray, terms: list[str], kpi_term: str
) -> dict[str, float]:
    """
    Compute sensitivity (S): Inverse distance to KPI term.

    Close proximity to KPI = high sensitivity = changing this term
    likely impacts KPI directly.

    Args:
        embeddings: Term embeddings
        terms: All terms
        kpi_term: KPI term (must be in terms list)

    Returns:
        {term: 1 - normalized_distance_to_KPI [0, 1]}
    """
    kpi_idx = terms.index(kpi_term)
    kpi_embedding = embeddings[kpi_idx]

    # Compute distances to KPI
    distances = np.linalg.norm(embeddings - kpi_embedding, axis=1)

    # Normalize and invert: close = high sensitivity
    max_distance = distances.max() if distances.max() > 0 else 1.0

    return {t: 1.0 - (distances[i] / max_distance) for i, t in enumerate(terms)}


def _plot_leverage(
    embed_low_d: np.ndarray,
    terms: list[str],
    leverage_scores: dict[str, float],
    actionability: dict[str, float],
    n_components: int,
    output_file: str,
) -> str:
    """Create and save leverage visualization with color coding."""
    fig = plt.figure(figsize=(16, 12))

    # Color map: red (high leverage) to blue (low leverage)
    scores_array = np.array([leverage_scores[t] for t in terms])
    min_score = scores_array.min()
    max_score = scores_array.max()
    score_range = max_score - min_score if max_score > min_score else 1.0

    colors = plt.cm.RdYlBu_r((scores_array - min_score) / score_range)

    # Marker style: circles for actionable, squares for non-actionable
    markers = ["o" if actionability[t] > 0.5 else "s" for t in terms]

    if n_components == 3:
        ax = fig.add_subplot(111, projection="3d")

        # Plot with different markers
        for i, term in enumerate(terms):
            ax.scatter(
                embed_low_d[i, 0],
                embed_low_d[i, 1],
                embed_low_d[i, 2],
                c=[colors[i]],
                marker=markers[i],
                s=200,
                alpha=0.7,
                edgecolors="black",
                linewidths=1.5,
            )
            # Annotate with term and score
            ax.text(
                embed_low_d[i, 0],
                embed_low_d[i, 1],
                embed_low_d[i, 2],
                f"{term}\n({leverage_scores[term]:.2f})",
                fontsize=8,
                alpha=0.9,
            )

        ax.set_title(
            "Hyperdimensional Leverage Analysis (3D)\nRed=High Leverage, Blue=Low | ○=Actionable, □=Fixed",
            fontsize=14,
            fontweight="bold",
        )
        ax.set_xlabel("t-SNE Dimension 1", fontsize=10)
        ax.set_ylabel("t-SNE Dimension 2", fontsize=10)
        ax.set_zlabel("t-SNE Dimension 3", fontsize=10)
        ax.grid(True, alpha=0.3)

    else:  # 2D
        for i, term in enumerate(terms):
            plt.scatter(
                embed_low_d[i, 0],
                embed_low_d[i, 1],
                c=[colors[i]],
                marker=markers[i],
                s=200,
                alpha=0.7,
                edgecolors="black",
                linewidths=1.5,
            )
            plt.annotate(
                f"{term}\n({leverage_scores[term]:.2f})",
                (embed_low_d[i, 0], embed_low_d[i, 1]),
                fontsize=8,
                alpha=0.9,
                xytext=(5, 5),
                textcoords="offset points",
            )

        plt.title(
            "Hyperdimensional Leverage Analysis (2D)\nRed=High Leverage, Blue=Low | ○=Actionable, □=Fixed",
            fontsize=14,
            fontweight="bold",
        )
        plt.xlabel("t-SNE Dimension 1", fontsize=10)
        plt.ylabel("t-SNE Dimension 2", fontsize=10)
        plt.grid(True, alpha=0.3)

    # Add colorbar legend
    sm = plt.cm.ScalarMappable(
        cmap=plt.cm.RdYlBu_r, norm=plt.Normalize(vmin=min_score, vmax=max_score)
    )
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=plt.gca() if n_components == 2 else ax, pad=0.1)
    cbar.set_label("Leverage Score", fontsize=10)

    plt.tight_layout()

    # Save
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        plt.savefig(str(output_path), dpi=150, bbox_inches="tight")
    except Exception as e:
        raise ValueError(f"Failed to save visualization to {output_file}: {e}") from e
    finally:
        plt.close(fig)

    return str(output_path.resolve())
