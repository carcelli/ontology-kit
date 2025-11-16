"""
Agent-callable tools for ontology-kit.

Tools are functions decorated with @function_tool that agents can invoke
during execution. They bridge agents with core capabilities like:
- Hyperdimensional visualization
- Leverage analysis
- Ontology manipulation
- Vector space operations
"""

from .business import optimize, predict
from .github_tools import write_to_github
from .hyperdim_leverage_viz import generate_hyperdim_leverage_viz
from .hyperdim_viz import generate_hyperdim_viz
from .interactive_viz import generate_interactive_leverage_viz
from .ml_training import analyze_leverage, check_job_status, cluster_data, run_cross_validation, train_model
from .ontology import add_ontology_statement, query_ontology
from .semantic_graph import build_semantic_graph, compute_target_leverage, recommend_interventions
from .vector_space import embed, embed_batch, query_vector_index

__all__ = [
    'generate_hyperdim_viz',
    'generate_hyperdim_leverage_viz',
    'generate_interactive_leverage_viz',
    'predict',
    'optimize',
    'embed',
    'embed_batch',
    'query_vector_index',
    'query_ontology',
    'add_ontology_statement',
    'write_to_github',
    'train_model',
    'run_cross_validation',
    'check_job_status',
    'analyze_leverage',
    'cluster_data',
    'build_semantic_graph',
    'compute_target_leverage',
    'recommend_interventions',
]
