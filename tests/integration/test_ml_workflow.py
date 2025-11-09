"""Integration test for ontology-driven ML workflow."""
import pytest

from agent_kit.ontology.loader import OntologyLoader
from agent_kit.orchestrator.ontology_orchestrator import OntologyOrchestrator
from agent_kit.tools.ml_training import ML_TOOL_REGISTRY, advance_mock_jobs

ML_TRAIN = 'http://agent-kit.com/ontology/ml#ModelTrainerTool'
ML_CV = 'http://agent-kit.com/ontology/ml#CrossValidatorTool'
ML_JOB = 'http://agent-kit.com/ontology/ml#JobStatusTool'


@pytest.fixture
def orchestrator():
    """Create orchestrator with loaded ML tools ontology."""
    loader = OntologyLoader('assets/ontologies/ml_tools.ttl')
    loader.load()
    return OntologyOrchestrator(loader, ML_TOOL_REGISTRY)


def test_ontology_tool_discovery(orchestrator):
    """Test that tools can be discovered via ontology queries."""
    # Should discover trainer tool
    trainer = orchestrator.discover_tool(ML_TRAIN)
    assert trainer is not None
    assert trainer['function'].__name__ == 'train_model'
    assert 'schema' in trainer
    assert 'tool_spec' in trainer

    # Should discover validator tool
    validator = orchestrator.discover_tool(ML_CV)
    assert validator is not None
    assert validator['function'].__name__ == 'run_cross_validation'

    # Should discover job checker
    job_checker = orchestrator.discover_tool(ML_JOB)
    assert job_checker is not None
    assert job_checker['function'].__name__ == 'check_job_status'


def test_discover_by_algorithm(orchestrator):
    """Test discovering tools by implemented algorithm."""
    tools = orchestrator.discover_tools_by_algorithm('GradientDescent')
    assert len(tools) >= 1
    assert any(t['function'].__name__ == 'train_model' for t in tools)


def test_openai_tool_specs(orchestrator):
    """Test generating OpenAI tool specs from ontology."""
    specs = orchestrator.get_openai_tools([ML_TRAIN, ML_CV, ML_JOB])
    assert len(specs) == 3
    # Verify structure
    for spec in specs:
        assert spec['type'] == 'function'
        assert 'function' in spec
        assert 'name' in spec['function']
        assert 'description' in spec['function']
        assert 'parameters' in spec['function']


def test_end_to_end_training_then_cv(orchestrator):
    """Test complete workflow: schedule training → poll → schedule CV → poll."""
    import time
    
    # Schedule training
    train = orchestrator.call(
        ML_TRAIN, {'dataset_uri': 'demo://clients', 'hyperparameters': {'lr': 0.001}}
    )
    assert train['status'] == 'SCHEDULED'
    job_id = train['job_id']
    assert job_id.startswith('train-job-')

    # Poll until complete (simulate advancing time)
    status = None
    start_time = time.time()
    for i in range(15):
        # Advance mock time by passing a future timestamp
        advance_mock_jobs(start_time + (i + 1) * 1.0)
        status = orchestrator.call(ML_JOB, {'job_id': job_id})
        if status['status'] == 'COMPLETED':
            model_uri = status['artifact_uri']
            break

    assert status is not None
    assert status['status'] == 'COMPLETED'
    assert 'artifact_uri' in status
    model_uri = status['artifact_uri']
    assert model_uri.startswith('ml:TrainedModel_')

    # Schedule cross-validation
    cv = orchestrator.call(
        ML_CV, {'model_uri': model_uri, 'dataset_uri': 'demo://clients', 'k_folds': 5}
    )
    assert cv['status'] == 'SCHEDULED'
    job2 = cv['job_id']
    assert job2.startswith('cv-job-')

    # Poll CV job
    st2 = None
    cv_start = time.time()
    for i in range(15):
        advance_mock_jobs(cv_start + (i + 1) * 1.0)
        st2 = orchestrator.call(ML_JOB, {'job_id': job2})
        if st2['status'] == 'COMPLETED':
            assert 'metrics' in st2
            break

    assert st2 is not None
    assert st2['status'] == 'COMPLETED'
    assert 'metrics' in st2
    assert 'accuracy' in st2['metrics']
    assert 'f1' in st2['metrics']


def test_call_by_python_id(orchestrator):
    """Test calling tools directly by Python identifier."""
    result = orchestrator.call_by_python_id(
        'train_model', {'dataset_uri': 'demo://test', 'hyperparameters': {}}
    )
    assert result['status'] == 'SCHEDULED'
    assert 'job_id' in result


def test_invalid_class_iri(orchestrator):
    """Test error handling for non-existent class."""
    with pytest.raises(RuntimeError, match='No tool bound for class'):
        orchestrator.discover_tool('http://agent-kit.com/ontology/ml#NonExistentTool')


def test_invalid_python_id(orchestrator):
    """Test error handling for non-existent Python identifier."""
    with pytest.raises(RuntimeError, match='not found in registry'):
        orchestrator.call_by_python_id('non_existent_function', {})

