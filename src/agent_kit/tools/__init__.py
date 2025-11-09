"""
Agent-callable tools for ontology-kit.

Tools are functions decorated with @function_tool that agents can invoke
during execution. They bridge agents with core capabilities like:
- Hyperdimensional visualization
- Leverage analysis
- Ontology manipulation
- Vector space operations
"""

from .hyperdim_leverage_viz import generate_hyperdim_leverage_viz
from .hyperdim_viz import generate_hyperdim_viz
from .business import predict, optimize
from .vector_space import embed, embed_batch, query_vector_index
from .ontology import query_ontology, add_ontology_statement

__all__ = [
    'generate_hyperdim_viz',
    'generate_hyperdim_leverage_viz',
    'predict',
    'optimize',
    'embed',
    'embed_batch',
    'query_vector_index',
    'query_ontology',
    'add_ontology_statement',
]
