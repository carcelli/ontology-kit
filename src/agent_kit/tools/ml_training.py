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
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- mock job store (swap with Redis/Celery/K8s) ---
MOCK_JOB_DB: Dict[str, Dict[str, Any]] = {}


# ---------------- Pydantic Schemas ----------------
class ModelTrainingInput(BaseModel):
    """Input schema for model training."""

    dataset_uri: str = Field(..., description='URI of ml:Dataset for training')
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)


class JobStatusInput(BaseModel):
    """Input schema for job status checking."""

    job_id: str = Field(..., description='Job identifier to check')


class CrossValidationInput(BaseModel):
    """Input schema for cross-validation."""

    model_uri: str = Field(..., description='URI of ml:TrainedModel to evaluate')
    dataset_uri: str = Field(..., description='URI of ml:Dataset to use for validation')
    k_folds: int = Field(default=5, ge=2, le=20)


# -------------- Tool Implementations --------------
def train_model(input_data: ModelTrainingInput) -> Dict[str, Any]:
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


def run_cross_validation(input_data: CrossValidationInput) -> Dict[str, Any]:
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


def _finalize_job(job: Dict[str, Any]) -> Dict[str, Any]:
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


def advance_mock_jobs(now: Optional[float] = None) -> None:
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


def check_job_status(input_data: JobStatusInput) -> Dict[str, Any]:
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
    ontology_path: Optional[str] = Field(
        None, description='Optional ontology path for graph structure analysis'
    )


def analyze_leverage(input_data: LeverageAnalysisInput) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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


# Import and merge semantic graph tools
try:
    from agent_kit.tools.semantic_graph import SEMANTIC_GRAPH_TOOL_REGISTRY

    ML_TOOL_REGISTRY.update(SEMANTIC_GRAPH_TOOL_REGISTRY)
except ImportError:
    logger.warning('Semantic graph tools not available')


