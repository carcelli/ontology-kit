# src/agent_kit/tools/interactive_viz.py
"""
Interactive hyperdimensional leverage visualization using Plotly.

Generates beautiful, interactive 3D visualizations with hover details, zoom,
and rotation. Replaces static matplotlib plots with production-grade Plotly charts.

References:
- Plotly 3D Scatter: https://plotly.com/python/3d-scatter-plots/
- t-SNE Paper: van der Maaten & Hinton (2008), JMLR
- Color Theory: Viridis colormap for perceptual uniformity

Key Features:
- Interactive rotation and zoom (WebGL-accelerated)
- Hover tooltips with term details and scores
- Perceptually uniform color gradients (Viridis)
- Export to HTML (interactive) or PNG (static via Kaleido)
- Handles 2D and 3D projections seamlessly
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated, Any

from agents import function_tool
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from sklearn.manifold import TSNE

from agent_kit.vectorspace.embedder import Embedder

logger = logging.getLogger(__name__)


@function_tool
def generate_interactive_leverage_viz(
    terms: Annotated[list[str], "Business terms/entities to visualize"],
    kpi_term: Annotated[str, "Key Performance Indicator for sensitivity calculation"],
    actionable_terms: Annotated[list[str], "Terms that can be directly intervened"],
    model_name: Annotated[str, "SentenceTransformer model"] = 'all-MiniLM-L6-v2',
    n_components: Annotated[int, "2 or 3 for visualization dimensions"] = 3,
    perplexity: Annotated[int | None, "t-SNE perplexity (auto if None)"] = None,
    output_file: Annotated[
        str, "Path to save (*.html for interactive, *.png for static)"
    ] = 'outputs/interactive_leverage.html',
    color_scale: Annotated[str, "Plotly colorscale name"] = 'Viridis',
    leverage_formula: Annotated[
        str, "Leverage computation method"
    ] = 'inverse_distance',  # 'inverse_distance' or 'multi_factor'
) -> dict[str, Any]:
    """
    Generate interactive 3D leverage visualization using Plotly.

    Creates beautiful, zoomable, rotatable 3D scatter plots with:
    - Color-coded leverage scores (perceptually uniform Viridis)
    - Shape-coded actionability (circles = actionable, squares = fixed)
    - Hover tooltips with term name, leverage score, actionability
    - Export to interactive HTML or static PNG

    Args:
        terms: List of business terms to embed and visualize
        kpi_term: Target KPI for leverage calculation (e.g., 'Revenue')
        actionable_terms: Terms flagged as actionable (can intervene)
        model_name: SentenceTransformer model for semantic embeddings
        n_components: Output dimensions (2 for 2D plot, 3 for 3D plot)
        perplexity: t-SNE perplexity parameter (auto-tuned if None)
        output_file: Save path (.html for interactive, .png for static)
        color_scale: Plotly colorscale (Viridis, Plasma, Inferno, Cividis)
        leverage_formula: Method for computing leverage scores

    Returns:
        Dict with viz_path, leverage_scores, and metadata

    Raises:
        ValueError: If <2 terms, invalid n_components, or KPI not in terms

    Examples:
        >>> # Interactive 3D HTML
        >>> result = generate_interactive_leverage_viz(
        ...     terms=['Revenue', 'Budget', 'Marketing', 'Sales'],
        ...     kpi_term='Revenue',
        ...     actionable_terms=['Budget', 'Marketing'],
        ...     output_file='outputs/leverage_3d.html'
        ... )
        >>> # Static 2D PNG for reports
        >>> result = generate_interactive_leverage_viz(
        ...     terms=['Revenue', 'Budget', 'Marketing', 'Sales'],
        ...     kpi_term='Revenue',
        ...     actionable_terms=['Budget', 'Marketing'],
        ...     n_components=2,
        ...     output_file='outputs/leverage_2d.png'
        ... )
    """
    # Validation
    if len(terms) < 2:
        raise ValueError(
            f"Need at least 2 terms for meaningful visualization, got {len(terms)}. "
            f"Provide more terms or use a different analysis method."
        )

    if n_components not in (2, 3):
        raise ValueError(f"n_components must be 2 or 3, got {n_components}")

    if kpi_term not in terms:
        raise ValueError(
            f"KPI term '{kpi_term}' not found in terms list. "
            f"Available: {', '.join(terms)}"
        )

    logger.info(
        'Generating interactive leverage viz: %d terms, KPI=%s, dims=%d',
        len(terms),
        kpi_term,
        n_components,
    )

    # Step 1: Semantic embedding (384D via SentenceTransformers)
    embedder = Embedder(model_name=model_name)
    embeddings = embedder.embed_batch(terms)

    # Step 2: Dimensionality reduction with t-SNE
    perplexity_val = perplexity if perplexity is not None else min(30, len(terms) - 1)
    if perplexity_val >= len(terms):
        perplexity_val = max(1, len(terms) - 1)

    tsne = TSNE(
        n_components=n_components, perplexity=perplexity_val, random_state=42, init='random'
    )
    reduced = tsne.fit_transform(embeddings)

    # Step 3: Compute leverage scores
    leverage_scores = _compute_leverage_scores(
        reduced, terms, kpi_term, actionable_terms, formula=leverage_formula
    )

    # Step 4: Prepare DataFrame for Plotly
    df = pd.DataFrame(
        {
            'x': reduced[:, 0],
            'y': reduced[:, 1],
            'term': terms,
            'leverage': leverage_scores,
            'actionable': [t in actionable_terms for t in terms],
            'actionable_label': ['✓ Actionable' if t in actionable_terms else '✗ Fixed' for t in terms],
        }
    )

    if n_components == 3:
        df['z'] = reduced[:, 2]

    # Step 5: Create interactive Plotly figure
    fig = _create_plotly_figure(df, n_components, kpi_term, color_scale)

    # Step 6: Save output
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        if output_file.endswith('.html'):
            fig.write_html(str(output_path))
            logger.info('Saved interactive HTML: %s', output_path)
        else:
            # Static export requires Kaleido
            pio.write_image(fig, str(output_path), width=1200, height=900)
            logger.info('Saved static image: %s', output_path)
    except Exception as e:
        logger.error('Failed to save visualization: %s', e)
        raise ValueError(f"Failed to save to {output_file}: {e}") from e

    return {
        'viz_path': str(output_path.resolve()),
        'n_terms': len(terms),
        'n_components': n_components,
        'leverage_scores': dict(zip(terms, leverage_scores.tolist(), strict=False)),
        'top_levers': [
            {'term': t, 'leverage': float(s)}
            for t, s in sorted(zip(terms, leverage_scores, strict=False), key=lambda x: x[1], reverse=True)[
                :5
            ]
        ],
        'actionable_count': sum(df['actionable']),
        'kpi_term': kpi_term,
    }


def _compute_leverage_scores(
    reduced: np.ndarray,
    terms: list[str],
    kpi_term: str,
    actionable_terms: list[str],
    formula: str = 'inverse_distance',
) -> np.ndarray:
    """
    Compute leverage scores for each term.

    Args:
        reduced: t-SNE reduced coordinates (N x d)
        terms: List of term names
        kpi_term: Target KPI
        actionable_terms: Actionable term list
        formula: 'inverse_distance' (simple) or 'multi_factor' (A×(S+U+C))

    Returns:
        Leverage scores (N,)
    """
    kpi_idx = terms.index(kpi_term)
    distances = np.linalg.norm(reduced - reduced[kpi_idx], axis=1)

    if formula == 'inverse_distance':
        # Simple: Leverage = 1 / (distance + epsilon)
        # Closer to KPI = higher leverage
        leverages = 1.0 / (distances + 1e-6)
        # Normalize to [0, 1]
        leverages = (leverages - leverages.min()) / (leverages.max() - leverages.min() + 1e-9)

    elif formula == 'multi_factor':
        # Advanced: A × (S + U + C)
        # S: Sensitivity (inverse normalized distance)
        sensitivity = 1.0 - (distances / (distances.max() + 1e-9))

        # U: Uncertainty (variance around each point - proxy via local density)
        uncertainty = np.ones(len(terms)) * 0.5  # Placeholder; would compute cluster variance

        # C: Centrality (betweenness - placeholder without full graph)
        centrality = np.ones(len(terms)) * 0.5

        # A: Actionability
        actionability = np.array([1.0 if t in actionable_terms else 0.0 for t in terms])

        leverages = actionability * (sensitivity + uncertainty + centrality)
        # Normalize
        if leverages.max() > 0:
            leverages = leverages / leverages.max()
    else:
        raise ValueError(f"Unknown leverage formula: {formula}")

    return leverages


def _create_plotly_figure(
    df: pd.DataFrame, n_components: int, kpi_term: str, color_scale: str
) -> go.Figure:
    """
    Create Plotly figure with interactive features.

    Args:
        df: DataFrame with x, y, (z), term, leverage, actionable
        n_components: 2 or 3
        kpi_term: KPI term for title
        color_scale: Plotly colorscale name

    Returns:
        Plotly Figure object
    """
    if n_components == 3:
        # 3D scatter plot
        fig = px.scatter_3d(
            df,
            x='x',
            y='y',
            z='z',
            color='leverage',
            symbol='actionable_label',
            hover_name='term',
            hover_data={
                'leverage': ':.3f',
                'actionable_label': True,
                'x': False,
                'y': False,
                'z': False,
            },
            color_continuous_scale=color_scale,
            title=f'Interactive 3D Hyperdimensional Leverage Map (KPI: {kpi_term})',
            labels={'leverage': 'Leverage Score', 'actionable_label': 'Status'},
        )

        # Update 3D scene
        fig.update_layout(
            scene={
                "xaxis_title": 't-SNE Dimension 1',
                "yaxis_title": 't-SNE Dimension 2',
                "zaxis_title": 't-SNE Dimension 3',
                "aspectmode": 'cube',
                "camera": {"eye": {"x": 1.5, "y": 1.5, "z": 1.3}},  # Better default angle
            },
            font={"size": 12, "family": 'Arial'},
            hovermode='closest',
            height=800,
        )

    else:
        # 2D scatter plot
        fig = px.scatter(
            df,
            x='x',
            y='y',
            color='leverage',
            symbol='actionable_label',
            hover_name='term',
            hover_data={
                'leverage': ':.3f',
                'actionable_label': True,
                'x': False,
                'y': False,
            },
            color_continuous_scale=color_scale,
            title=f'Interactive 2D Hyperdimensional Leverage Map (KPI: {kpi_term})',
            labels={'leverage': 'Leverage Score', 'actionable_label': 'Status'},
        )

        # Update 2D layout
        fig.update_layout(
            xaxis_title='t-SNE Dimension 1',
            yaxis_title='t-SNE Dimension 2',
            font={"size": 12, "family": 'Arial'},
            hovermode='closest',
            height=700,
            width=900,
        )

    # Common styling
    fig.update_traces(marker={"size": 12, "line": {"width": 1, "color": 'DarkSlateGray'}})

    return fig


# Tool specification for ontology registry
INTERACTIVE_VIZ_TOOL_SPEC = {
    'name': 'generate_interactive_leverage_viz',
    'description': (
        'Generate interactive 3D/2D leverage visualization with Plotly. '
        'Outputs zoomable, rotatable HTML or static PNG with hover details.'
    ),
    'parameters': {
        'terms': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Business terms'},
        'kpi_term': {'type': 'string', 'description': 'Target KPI'},
        'actionable_terms': {
            'type': 'array',
            'items': {'type': 'string'},
            'description': 'Actionable terms',
        },
        'n_components': {
            'type': 'integer',
            'enum': [2, 3],
            'default': 3,
            'description': 'Dimensions',
        },
        'output_file': {
            'type': 'string',
            'default': 'outputs/interactive_leverage.html',
            'description': 'Output path (.html or .png)',
        },
    },
}

