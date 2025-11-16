# src/agent_kit/tools/ml_training.py
"""
ML training tools with async job pattern for long-running operations.

Tools are discovered via ontology queries and executed through the orchestrator.
Training and validation return job_id immediately; poll with check_job_status.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from pydantic import BaseModel, Field
from agents import function_tool

logger = logging.getLogger(__name__)

# --- mock job store (swap with Redis/Celery/K8s) ---
MOCK_JOB_DB: dict[str, dict[str, Any]] = {}


# ---------------- Pydantic Schemas ----------------
class ModelTrainingInput(BaseModel):
    """Input schema for model training."""

    dataset_uri: str = Field(..., description='URI of ml:Dataset for training')
    hyperparameters: dict[str, Any] = Field(default_factory=dict)


class JobStatusInput(BaseModel):
    """Input schema for job status checking."""

    job_id: str = Field(..., description='Job identifier to check')


class CrossValidationInput(BaseModel):
    """Input schema for cross-validation."""

    model_uri: str = Field(..., description='URI of ml:TrainedModel to evaluate')
    dataset_uri: str = Field(..., description='URI of ml:Dataset to use for validation')
    k_folds: int = Field(default=5, ge=2, le=20)


# -------------- Tool Implementations --------------
@function_tool
def train_model(input_data: ModelTrainingInput) -> dict[str, Any]:
    """
    ASYNC: schedule training, return job_id immediately.

    Args:
        input_data: Training configuration

    Returns:
        Job scheduling confirmation with job_id
    """
    job_id = f'train-job-{uuid.uuid4()}'
    logger.info('Scheduling training: %s on %s', job_id, input_data.dataset_uri)
    MOCK_JOB_DB[job_id] = {
        'status': 'SCHEDULED',
        'type': 'TRAIN',
        'start_time': time.time(),
        'params': input_data.model_dump(),
        'artifact_uri': f'ml:TrainedModel_{job_id}',
        'progress': 0.0,
    }
    return {'status': 'SCHEDULED', 'job_id': job_id, 'message': 'Use check_job_status to monitor.'}


@function_tool
def run_cross_validation(input_data: CrossValidationInput) -> dict[str, Any]:
    """
    ASYNC: schedule cross-validation, return job_id immediately.

    Args:
        input_data: Cross-validation configuration

    Returns:
        Job scheduling confirmation with job_id
    """
    job_id = f'cv-job-{uuid.uuid4()}'
    logger.info('Scheduling CV: %s on %s', job_id, input_data.model_uri)
    MOCK_JOB_DB[job_id] = {
        'status': 'SCHEDULED',
        'type': 'VALIDATE',
        'start_time': time.time(),
        'params': input_data.model_dump(),
        'artifact_uri': f'ml:PerformanceMetric_{job_id}',
        'progress': 0.0,
    }
    return {'status': 'SCHEDULED', 'job_id': job_id, 'message': 'Use check_job_status to monitor.'}


def _finalize_job(job: dict[str, Any]) -> dict[str, Any]:
    """Helper to finalize job and return completion payload."""
    job['status'] = 'COMPLETED'
    if job['type'] == 'TRAIN':
        return {
            'status': 'COMPLETED',
            'job_id': job['artifact_uri'].split('_')[-1].replace('TrainedModel-', 'train-job-'),
            'artifact_uri': job['artifact_uri'],
            'message': 'Model training complete.',
        }
    # VALIDATE
    return {
        'status': 'COMPLETED',
        'job_id': job['artifact_uri'].split('_')[-1].replace('PerformanceMetric-', 'cv-job-'),
        'artifact_uri': job['artifact_uri'],
        'metrics': {'accuracy': 0.88, 'f1': 0.85},  # stub
    }


def advance_mock_jobs(now: float | None = None) -> None:
    """
    Dev helper: advance job states deterministically. Call from tests or a cron.

    Args:
        now: Optional current timestamp for deterministic testing
    """
    t = now or time.time()
    for job in MOCK_JOB_DB.values():
        elapsed = t - job['start_time']
        if job['status'] == 'SCHEDULED':
            job['status'] = 'RUNNING'
        elif job['status'] == 'RUNNING':
            # finish after ~10s for demo
            job['progress'] = min(1.0, elapsed / 10.0)
            if elapsed >= 10.0:
                job.update(_finalize_job(job))


@function_tool
def check_job_status(input_data: JobStatusInput) -> dict[str, Any]:
    """
    Poll job state. In prod, your worker updates real status/metrics.

    Args:
        input_data: Job identifier to check

    Returns:
        Current job status, progress, and artifacts when complete
    """
    job = MOCK_JOB_DB.get(input_data.job_id)
    if not job:
        return {'status': 'NOT_FOUND', 'job_id': input_data.job_id}
    # In dev, auto-advance to simulate work
    advance_mock_jobs()
    job = MOCK_JOB_DB[input_data.job_id]
    resp = {'status': job['status'], 'job_id': input_data.job_id}
    if job['status'] == 'RUNNING':
        resp['progress'] = round(job.get('progress', 0.0), 3)
    if job['status'] == 'COMPLETED':
        if job['type'] == 'TRAIN':
            resp.update({'artifact_uri': job['artifact_uri'], 'message': 'Model training complete.'})
        else:
            resp.update(
                {'artifact_uri': job['artifact_uri'], 'metrics': {'accuracy': 0.88, 'f1': 0.85}}
            )
    return resp


# -------------- Dimensionality Reduction / Leverage Analysis --------------
class LeverageAnalysisInput(BaseModel):
    """Input schema for leverage analysis."""

    terms: list[str] = Field(..., description='Business entities/terms to analyze')
    kpi_term: str = Field(..., description='Key Performance Indicator for sensitivity analysis')
    actionable_terms: list[str] = Field(
        default_factory=list, description='Terms that can be intervened upon'
    )
    ontology_path: str | None = Field(
        None, description='Optional ontology path for graph structure analysis'
    )


@function_tool
def analyze_leverage(input_data: LeverageAnalysisInput) -> dict[str, Any]:
    """
    Analyze high-leverage intervention points using t-SNE dimensionality reduction.

    Computes multi-factor leverage scores:
    Leverage = Actionability × (Sensitivity + Uncertainty + Centrality)

    Args:
        input_data: Analysis configuration

    Returns:
        Top leverage points ranked by score with visualization path
    """
    try:
        from agent_kit.tools.hyperdim_leverage_viz import generate_hyperdim_leverage_viz
    except ImportError:
        return {
            'status': 'ERROR',
            'message': 'hyperdim_leverage_viz not available. Install dependencies.',
        }

    job_id = f'leverage-job-{uuid.uuid4()}'
    logger.info('Running leverage analysis: %s for KPI: %s', job_id, input_data.kpi_term)

    try:
        result = generate_hyperdim_leverage_viz(
            terms=input_data.terms,
            kpi_term=input_data.kpi_term,
            actionable_terms=input_data.actionable_terms if input_data.actionable_terms else None,
            ontology_path=input_data.ontology_path,
            output_file=f'outputs/leverage_{job_id}.png',
            n_components=2,
        )

        return {
            'status': 'COMPLETED',
            'job_id': job_id,
            'top_levers': result['top_levers'][:5],
            'viz_path': result['viz_path'],
            'message': f"Identified {len(result['top_levers'])} leverage points",
        }
    except Exception as e:
        logger.error('Leverage analysis failed: %s', e)
        return {'status': 'ERROR', 'job_id': job_id, 'message': str(e)}


# ------------ OpenAI tool spec (Pydantic → JSON) ------------
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


ML_TOOL_REGISTRY = {
    'train_model': {
        'function': train_model,
        'schema': ModelTrainingInput,
        'tool_spec': pydantic_to_openai_tool(
            'train_model', 'Schedule model training and return a job_id.', ModelTrainingInput
        ),
    },
    'run_cross_validation': {
        'function': run_cross_validation,
        'schema': CrossValidationInput,
        'tool_spec': pydantic_to_openai_tool(
            'run_cross_validation',
            'Schedule k-fold validation and return a job_id.',
            CrossValidationInput,
        ),
    },
    'check_job_status': {
        'function': check_job_status,
        'schema': JobStatusInput,
        'tool_spec': pydantic_to_openai_tool(
            'check_job_status',
            'Check status of a previously scheduled ML job.',
            JobStatusInput,
        ),
    },
    'analyze_leverage': {
        'function': analyze_leverage,
        'schema': LeverageAnalysisInput,
        'tool_spec': pydantic_to_openai_tool(
            'analyze_leverage',
            'Identify high-leverage intervention points via t-SNE dimensionality reduction and multi-factor scoring.',
            LeverageAnalysisInput,
        ),
    },
}


# -------------- Clustering Tool --------------
class ClusteringInput(BaseModel):
    """Input schema for clustering analysis."""

    data: list[list[float]] = Field(..., description='2D array of data points to cluster')
    eps: float = Field(default=0.5, gt=0.0, description='Maximum distance between points in cluster (DBSCAN)')
    min_samples: int = Field(default=5, ge=1, description='Minimum points to form dense region (DBSCAN)')
    algorithm: str = Field(default='DBSCAN', description='Clustering algorithm: DBSCAN, KMeans, or Hierarchical')
    n_clusters: int | None = Field(None, description='Number of clusters (for KMeans/Hierarchical)')


@function_tool
def cluster_data(input_data: ClusteringInput) -> dict[str, Any]:
    """
    Cluster data points using DBSCAN, KMeans, or Hierarchical clustering.

    Implements density-based, centroid-based, and hierarchical clustering
    for discovering patterns in high-dimensional data after dimensionality reduction.

    Args:
        input_data: Clustering parameters

    Returns:
        Cluster labels, number of clusters, and noise points (if applicable)

    References:
        - DBSCAN: Ester et al. (1996), KDD
        - KMeans: Lloyd (1982), IEEE Trans
        - Hierarchical: Ward (1963), JASA
    """
    job_id = f'cluster-job-{uuid.uuid4()}'
    logger.info('Running clustering: %s with %s', job_id, input_data.algorithm)

    try:
        import numpy as np
        from sklearn.cluster import DBSCAN, AgglomerativeClustering, KMeans

        X = np.array(input_data.data)

        if input_data.algorithm == 'DBSCAN':
            clusterer = DBSCAN(eps=input_data.eps, min_samples=input_data.min_samples)
            labels = clusterer.fit_predict(X)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise = list(labels).count(-1)

            return {
                'status': 'COMPLETED',
                'job_id': job_id,
                'algorithm': 'DBSCAN',
                'labels': labels.tolist(),
                'n_clusters': n_clusters,
                'n_noise': n_noise,
                'message': f'Found {n_clusters} clusters and {n_noise} noise points',
            }

        elif input_data.algorithm == 'KMeans':
            if input_data.n_clusters is None:
                raise ValueError('n_clusters required for KMeans')
            clusterer = KMeans(n_clusters=input_data.n_clusters, random_state=42)
            labels = clusterer.fit_predict(X)

            return {
                'status': 'COMPLETED',
                'job_id': job_id,
                'algorithm': 'KMeans',
                'labels': labels.tolist(),
                'n_clusters': input_data.n_clusters,
                'centroids': clusterer.cluster_centers_.tolist(),
                'inertia': float(clusterer.inertia_),
                'message': f'Clustered into {input_data.n_clusters} groups',
            }

        elif input_data.algorithm == 'Hierarchical':
            if input_data.n_clusters is None:
                raise ValueError('n_clusters required for Hierarchical clustering')
            clusterer = AgglomerativeClustering(n_clusters=input_data.n_clusters)
            labels = clusterer.fit_predict(X)

            return {
                'status': 'COMPLETED',
                'job_id': job_id,
                'algorithm': 'Hierarchical',
                'labels': labels.tolist(),
                'n_clusters': input_data.n_clusters,
                'message': f'Hierarchically clustered into {input_data.n_clusters} groups',
            }

        else:
            return {
                'status': 'ERROR',
                'job_id': job_id,
                'message': f"Unknown algorithm: {input_data.algorithm}. Use DBSCAN, KMeans, or Hierarchical",
            }

    except Exception as e:
        logger.error('Clustering failed: %s', e)
        return {'status': 'ERROR', 'job_id': job_id, 'message': str(e)}


# Update ML_TOOL_REGISTRY with clustering
ML_TOOL_REGISTRY['cluster_data'] = {
    'function': cluster_data,
    'schema': ClusteringInput,
    'tool_spec': pydantic_to_openai_tool(
        'cluster_data',
        'Cluster data points using DBSCAN, KMeans, or Hierarchical clustering.',
        ClusteringInput,
    ),
}


# Import and merge semantic graph tools
try:
    from agent_kit.tools.semantic_graph import SEMANTIC_GRAPH_TOOL_REGISTRY

    ML_TOOL_REGISTRY.update(SEMANTIC_GRAPH_TOOL_REGISTRY)
except ImportError:
    logger.warning('Semantic graph tools not available')

# Import and merge interactive visualization tools
try:
    from agent_kit.tools.interactive_viz import (
        INTERACTIVE_VIZ_TOOL_SPEC,
        generate_interactive_leverage_viz,
    )

    ML_TOOL_REGISTRY['generate_interactive_leverage_viz'] = {
        'function': generate_interactive_leverage_viz,
        'schema': None,  # Uses type hints directly
        'tool_spec': INTERACTIVE_VIZ_TOOL_SPEC,
    }
except ImportError:
    logger.warning('Interactive visualization tools not available (install plotly, kaleido)')


