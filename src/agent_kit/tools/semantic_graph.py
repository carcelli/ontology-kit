# src/agent_kit/tools/semantic_graph.py
"""
Semantic graph tools for targeted leverage analysis.

Implements the semantic relation framework for business entity prioritization:
1. build_semantic_graph: Constructs weighted graph from embeddings + relations
2. compute_target_leverage: Calculates targeted betweenness and path strength to KPI
3. recommend_interventions: Generates experiment plans for high-leverage nodes

These tools extend basic t-SNE visualization with graph-theoretic analysis
and causal reasoning about intervention points.
"""
from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any

import networkx as nx
from pydantic import BaseModel, Field
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


# ---------------- Pydantic Schemas ----------------
class SemanticGraphInput(BaseModel):
    """Input schema for building semantic graph."""

    terms: list[str] = Field(..., description='Domain concepts/entities to analyze')
    similarity_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description='Minimum cosine similarity for edges'
    )
    corpus_path: str | None = Field(
        None, description='Optional text corpus to extract relations (drives, depends_on, etc.)'
    )
    output_path: str = Field(
        default='outputs/semantic_graph.json', description='Path to save graph JSON'
    )


class TargetLeverageInput(BaseModel):
    """Input schema for targeted leverage computation."""

    graph_path: str = Field(..., description='Path to semantic graph JSON')
    target: str = Field(..., description='Target node/KPI (e.g., Revenue)')
    model_shap_path: str | None = Field(
        None, description='Optional path to SHAP values JSON for model effects'
    )
    top_k: int = Field(default=5, ge=1, le=50, description='Number of top levers to return')


class InterventionRecommendationInput(BaseModel):
    """Input schema for intervention recommendations."""

    graph_path: str = Field(..., description='Path to semantic graph JSON')
    node: str = Field(..., description='Lever node to intervene on')
    target: str = Field(..., description='Target node/KPI')
    historical_data_path: str | None = Field(
        None, description='Optional historical experiment data for effect size estimates'
    )
    top_paths: int = Field(default=3, ge=1, le=10, description='Number of paths to analyze')


# -------------- Tool Implementations --------------
def build_semantic_graph(input_data: SemanticGraphInput) -> dict[str, Any]:
    """
    Build weighted semantic graph from term embeddings and optional text relations.

    Constructs a graph where:
    - Nodes = domain terms/concepts
    - Edges = semantic similarity (cosine > threshold) + extracted relations
    - Weights = combination of embedding similarity and relation strength

    Args:
        input_data: Graph construction parameters

    Returns:
        Graph metadata including node/edge counts, clusters, and file path
    """
    job_id = f'graph-job-{uuid.uuid4()}'
    logger.info('Building semantic graph: %s with %d terms', job_id, len(input_data.terms))

    try:
        from agent_kit.vectorspace.embedder import Embedder

        # Step 1: Generate embeddings
        embedder = Embedder()
        embeddings = embedder.embed_batch(input_data.terms)

        # Step 2: Create graph
        G = nx.Graph()
        for i, term in enumerate(input_data.terms):
            G.add_node(
                term,
                embedding=embeddings[i].tolist(),
                index=i,
                actionable=0.5,  # Default; can be overridden
            )

        # Step 3: Add edges based on similarity
        n_edges = 0
        for i, term_i in enumerate(input_data.terms):
            for j, term_j in enumerate(input_data.terms):
                if i >= j:
                    continue

                # Cosine similarity
                sim = float(cosine_similarity([embeddings[i]], [embeddings[j]])[0][0])

                if sim >= input_data.similarity_threshold:
                    G.add_edge(term_i, term_j, weight=sim, relation_type='semantic')
                    n_edges += 1

        # Step 4: Extract relations from corpus (optional)
        if input_data.corpus_path and Path(input_data.corpus_path).exists():
            extracted_relations = _extract_text_relations(
                input_data.corpus_path, input_data.terms
            )
            for term_i, term_j, rel_type in extracted_relations:
                if G.has_edge(term_i, term_j):
                    # Boost existing edge
                    G[term_i][term_j]['weight'] *= 1.5
                    G[term_i][term_j]['relation_type'] = f"semantic+{rel_type}"
                else:
                    # Add new edge
                    G.add_edge(term_i, term_j, weight=0.8, relation_type=rel_type)
                    n_edges += 1

        # Step 5: Compute graph metrics
        n_nodes = G.number_of_nodes()
        n_edges = G.number_of_edges()
        avg_degree = sum(dict(G.degree()).values()) / n_nodes if n_nodes > 0 else 0
        n_clusters = nx.number_connected_components(G)

        # Step 6: Compute centrality measures
        betweenness = nx.betweenness_centrality(G, weight='weight')
        closeness = nx.closeness_centrality(G, distance='weight')

        for node in G.nodes():
            G.nodes[node]['betweenness'] = betweenness.get(node, 0.0)
            G.nodes[node]['closeness'] = closeness.get(node, 0.0)

        # Step 7: Save graph
        output_path = Path(input_data.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        graph_data = {
            'nodes': [
                {
                    'id': node,
                    'betweenness': G.nodes[node].get('betweenness', 0.0),
                    'closeness': G.nodes[node].get('closeness', 0.0),
                    'actionable': G.nodes[node].get('actionable', 0.5),
                }
                for node in G.nodes()
            ],
            'edges': [
                {
                    'source': u,
                    'target': v,
                    'weight': G[u][v]['weight'],
                    'relation_type': G[u][v].get('relation_type', 'semantic'),
                }
                for u, v in G.edges()
            ],
            'metadata': {
                'n_nodes': n_nodes,
                'n_edges': n_edges,
                'avg_degree': avg_degree,
                'n_clusters': n_clusters,
            },
        }

        with open(output_path, 'w') as f:
            json.dump(graph_data, f, indent=2)

        return {
            'status': 'COMPLETED',
            'job_id': job_id,
            'graph_path': str(output_path.resolve()),
            'n_nodes': n_nodes,
            'n_edges': n_edges,
            'avg_degree': round(avg_degree, 2),
            'n_clusters': n_clusters,
            'message': f'Built semantic graph with {n_nodes} nodes, {n_edges} edges',
        }

    except Exception as e:
        logger.error('Graph construction failed: %s', e)
        return {'status': 'ERROR', 'job_id': job_id, 'message': str(e)}


def compute_target_leverage(input_data: TargetLeverageInput) -> dict[str, Any]:
    """
    Compute targeted leverage scores for nodes with respect to a specific KPI.

    Formula:
    Leverage(i → T) = Betweenness_T(i) × PathStrength(i → T) × Actionability(i) × ModelEffect_T(i)

    Args:
        input_data: Leverage computation parameters

    Returns:
        Ranked list of levers with detailed score breakdowns and paths
    """
    job_id = f'leverage-job-{uuid.uuid4()}'
    logger.info('Computing targeted leverage for: %s', input_data.target)

    try:
        # Load graph
        with open(input_data.graph_path) as f:
            graph_data = json.load(f)

        G = nx.Graph()
        for node_data in graph_data['nodes']:
            G.add_node(
                node_data['id'],
                betweenness=node_data.get('betweenness', 0.0),
                closeness=node_data.get('closeness', 0.0),
                actionable=node_data.get('actionable', 0.5),
            )

        for edge_data in graph_data['edges']:
            G.add_edge(
                edge_data['source'],
                edge_data['target'],
                weight=edge_data['weight'],
                relation_type=edge_data.get('relation_type', 'semantic'),
            )

        # Load SHAP values if provided
        shap_values = {}
        if input_data.model_shap_path and Path(input_data.model_shap_path).exists():
            with open(input_data.model_shap_path) as f:
                shap_data = json.load(f)
                shap_values = shap_data.get(input_data.target, {})

        # Compute leverage for each node
        leverage_scores = []
        target = input_data.target

        for node in G.nodes():
            if node == target:
                continue  # Skip target itself

            # 1. Targeted betweenness (how often node is on paths to target)
            betweenness_T = _compute_targeted_betweenness(G, node, target)

            # 2. Path strength (sum of weighted paths to target)
            path_strength, strongest_path = _compute_path_strength(G, node, target)

            # 3. Actionability (from node metadata)
            actionability = G.nodes[node].get('actionable', 0.5)

            # 4. Model effect (SHAP value if available)
            shap_score = abs(shap_values.get(node, 1.0))  # Default to 1.0 if no model

            # Total leverage
            total_leverage = betweenness_T * path_strength * actionability * shap_score

            leverage_scores.append(
                {
                    'term': node,
                    'total_leverage': round(total_leverage, 4),
                    'betweenness': round(betweenness_T, 3),
                    'path_strength': round(path_strength, 3),
                    'actionability': round(actionability, 3),
                    'shap_score': round(shap_score, 3),
                    'strongest_path': strongest_path,
                }
            )

        # Sort by total leverage
        leverage_scores.sort(key=lambda x: x['total_leverage'], reverse=True)

        return {
            'status': 'COMPLETED',
            'job_id': job_id,
            'target': target,
            'levers': leverage_scores[: input_data.top_k],
            'message': f'Computed leverage for {len(leverage_scores)} nodes targeting {target}',
        }

    except Exception as e:
        logger.error('Leverage computation failed: %s', e)
        return {'status': 'ERROR', 'job_id': job_id, 'message': str(e)}


def recommend_interventions(input_data: InterventionRecommendationInput) -> dict[str, Any]:
    """
    Generate experiment recommendations for a high-leverage node.

    Analyzes paths from lever to target and generates:
    - Recommended actions (domain-specific heuristics)
    - Expected effect sizes
    - Experiment specifications (sample size, duration, KPIs)
    - Guardrail metrics

    Args:
        input_data: Intervention recommendation parameters

    Returns:
        List of experiment plans with actions, KPIs, and specifications
    """
    job_id = f'intervention-job-{uuid.uuid4()}'
    logger.info('Generating interventions for: %s → %s', input_data.node, input_data.target)

    try:
        # Load graph
        with open(input_data.graph_path) as f:
            graph_data = json.load(f)

        G = nx.Graph()
        for node_data in graph_data['nodes']:
            G.add_node(node_data['id'])
        for edge_data in graph_data['edges']:
            G.add_edge(
                edge_data['source'], edge_data['target'], weight=edge_data['weight']
            )

        # Find paths from node to target
        try:
            all_paths = list(
                nx.all_simple_paths(G, input_data.node, input_data.target, cutoff=5)
            )
        except nx.NodeNotFound:
            return {
                'status': 'ERROR',
                'job_id': job_id,
                'message': f"Node '{input_data.node}' or '{input_data.target}' not found in graph",
            }

        if not all_paths:
            return {
                'status': 'COMPLETED',
                'job_id': job_id,
                'recommendations': [],
                'message': f'No paths found from {input_data.node} to {input_data.target}',
            }

        # Sort paths by length and total edge weight
        scored_paths = []
        for path in all_paths:
            path_weight = sum(
                G[path[i]][path[i + 1]]['weight'] for i in range(len(path) - 1)
            )
            scored_paths.append((path, path_weight, len(path)))

        scored_paths.sort(key=lambda x: (-x[1], x[2]))  # High weight, short length

        # Generate recommendations for top paths
        recommendations = []
        for i, (path, path_weight, path_len) in enumerate(
            scored_paths[: input_data.top_paths]
        ):
            intermediates = path[1:-1]

            # Generate action (domain-specific heuristics)
            action = _generate_action_for_node(input_data.node)

            # Estimate effect size (simple heuristic based on path strength)
            expected_lift = min(0.5, path_weight * 0.3)  # Cap at 50%

            # Compute sample size for 80% power, α=0.05
            sample_size = _compute_sample_size(expected_lift, power=0.8, alpha=0.05)

            experiment = {
                'name': f'Experiment {i+1}: {input_data.node} Intervention',
                'lever': input_data.node,
                'target': input_data.target,
                'path': ' → '.join(path),
                'path_weight': round(path_weight, 3),
                'path_length': path_len,
                'action': action,
                'expected_lift': round(expected_lift, 3),
                'sample_size': sample_size,
                'duration': _estimate_duration(sample_size),
                'primary_kpi': input_data.target,
                'intermediate_kpis': intermediates,
                'guardrails': _identify_guardrails(input_data.node, intermediates),
            }
            recommendations.append(experiment)

        return {
            'status': 'COMPLETED',
            'job_id': job_id,
            'recommendations': recommendations,
            'message': f'Generated {len(recommendations)} experiment recommendations',
        }

    except Exception as e:
        logger.error('Intervention recommendation failed: %s', e)
        return {'status': 'ERROR', 'job_id': job_id, 'message': str(e)}


# -------------- Helper Functions --------------
def _extract_text_relations(
    corpus_path: str, terms: list[str]
) -> list[tuple[str, str, str]]:
    """
    Extract explicit relations (drives, depends_on, precedes) from text corpus.

    Simple keyword-based extraction. Can be replaced with NLP models.
    """
    relations = []
    try:
        with open(corpus_path) as f:
            text = f.read().lower()

        relation_patterns = {
            'drives': ['drives', 'causes', 'leads to', 'results in'],
            'depends_on': ['depends on', 'requires', 'needs', 'relies on'],
            'precedes': ['before', 'precedes', 'prior to', 'first'],
        }

        for term_i in terms:
            for term_j in terms:
                if term_i == term_j:
                    continue

                term_i_lower = term_i.lower()
                term_j_lower = term_j.lower()

                for rel_type, keywords in relation_patterns.items():
                    for keyword in keywords:
                        # Simple pattern: "term_i KEYWORD term_j"
                        if f'{term_i_lower} {keyword} {term_j_lower}' in text:
                            relations.append((term_i, term_j, rel_type))
                            break

    except Exception as e:
        logger.warning('Failed to extract relations from corpus: %s', e)

    return relations


def _compute_targeted_betweenness(G: nx.Graph, node: str, target: str) -> float:
    """
    Compute betweenness centrality for node with respect to target.

    Measures how often node appears on shortest paths that end at target.
    """
    try:
        # Find all shortest paths ending at target
        paths_to_target = []
        for source in G.nodes():
            if source == target or source == node:
                continue
            try:
                paths = list(nx.all_shortest_paths(G, source, target, weight='weight'))
                paths_to_target.extend(paths)
            except nx.NetworkXNoPath:
                continue

        # Count how many paths include this node
        paths_through_node = sum(1 for path in paths_to_target if node in path)

        # Normalize
        max_paths = len(paths_to_target) if paths_to_target else 1
        return paths_through_node / max_paths

    except Exception:
        return 0.0


def _compute_path_strength(
    G: nx.Graph, node: str, target: str
) -> tuple[float, list[str]]:
    """
    Compute path strength as sum of weighted paths from node to target.

    Returns (total_strength, strongest_path).
    """
    try:
        all_paths = list(nx.all_simple_paths(G, node, target, cutoff=5))
        if not all_paths:
            return 0.0, []

        path_strengths = []
        for path in all_paths:
            path_weight = 1.0
            for i in range(len(path) - 1):
                path_weight *= G[path[i]][path[i + 1]]['weight']
            path_strengths.append((path, path_weight))

        # Total strength (sum)
        total_strength = sum(w for _, w in path_strengths)

        # Strongest path
        strongest = max(path_strengths, key=lambda x: x[1])

        return total_strength, strongest[0]

    except Exception:
        return 0.0, []


def _generate_action_for_node(node: str) -> str:
    """Generate domain-specific action for a node (heuristic)."""
    node_lower = node.lower()

    action_map = {
        'budget': 'Reallocate 10-20% of budget to high-ROI channels identified via analysis',
        'advertising': 'Target ads to customer segments with highest conversion rates',
        'marketing': 'Optimize marketing spend via A/B testing across channels',
        'website': 'Redesign conversion funnel to reduce friction (checkout, pricing page)',
        'emailtiming': 'Optimize send times for maximum open and reply rates',
        'outreachcampaign': 'Refine campaign messaging and targeting based on segment analysis',
        'product': 'Prioritize feature development based on customer feedback and retention data',
        'service': 'Improve response times and quality metrics for customer support',
        'socialmedia': 'Increase engagement through targeted content and community building',
    }

    for key, action in action_map.items():
        if key in node_lower:
            return action

    return f'Optimize {node} through data-driven experimentation and measurement'


def _compute_sample_size(effect_size: float, power: float = 0.8, alpha: float = 0.05) -> int:
    """
    Compute sample size per group for A/B test.

    Uses simplified formula for binary outcomes.
    """
    # Simplified: n ≈ 16 / (effect_size)^2 for 80% power, α=0.05
    if effect_size <= 0.01:
        return 10000  # Cap for very small effects
    n = int(16 / (effect_size**2))
    return min(max(n, 100), 10000)  # Clamp between 100 and 10k


def _estimate_duration(sample_size: int) -> str:
    """Estimate experiment duration based on sample size."""
    if sample_size < 1000:
        return '1-2 weeks'
    elif sample_size < 3000:
        return '2-4 weeks'
    elif sample_size < 7000:
        return '4-6 weeks'
    else:
        return '6-8 weeks'


def _identify_guardrails(node: str, intermediates: list[str]) -> list[str]:
    """Identify guardrail metrics to monitor during experiment."""
    guardrails = [
        'Customer satisfaction score',
        'Churn rate',
        'Support ticket volume',
    ]

    # Add node-specific guardrails
    node_lower = node.lower()
    if 'budget' in node_lower or 'cost' in node_lower:
        guardrails.append('Cost per acquisition (CPA)')
    if 'email' in node_lower or 'outreach' in node_lower:
        guardrails.append('Unsubscribe rate')
    if 'website' in node_lower:
        guardrails.append('Bounce rate')
    if 'advertising' in node_lower:
        guardrails.append('Ad spend efficiency (ROAS)')

    return guardrails


# ------------ OpenAI tool spec generation ------------
def pydantic_to_openai_tool(
    name: str, description: str, schema_model: type[BaseModel]
) -> dict[str, Any]:
    """Convert Pydantic schema to OpenAI function tool spec."""
    return {
        'type': 'function',
        'function': {
            'name': name,
            'description': description,
            'parameters': schema_model.model_json_schema(),
        },
    }


SEMANTIC_GRAPH_TOOL_REGISTRY = {
    'build_semantic_graph': {
        'function': build_semantic_graph,
        'schema': SemanticGraphInput,
        'tool_spec': pydantic_to_openai_tool(
            'build_semantic_graph',
            'Build weighted semantic graph from term embeddings and optional text relations.',
            SemanticGraphInput,
        ),
    },
    'compute_target_leverage': {
        'function': compute_target_leverage,
        'schema': TargetLeverageInput,
        'tool_spec': pydantic_to_openai_tool(
            'compute_target_leverage',
            'Compute targeted leverage scores for nodes with paths to a specific KPI/target.',
            TargetLeverageInput,
        ),
    },
    'recommend_interventions': {
        'function': recommend_interventions,
        'schema': InterventionRecommendationInput,
        'tool_spec': pydantic_to_openai_tool(
            'recommend_interventions',
            'Generate experiment recommendations for high-leverage intervention points.',
            InterventionRecommendationInput,
        ),
    },
}

