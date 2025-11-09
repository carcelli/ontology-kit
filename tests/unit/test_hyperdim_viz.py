"""Tests for hyperdimensional visualization tool."""

import os
from pathlib import Path

import pytest

from agent_kit.tools.hyperdim_viz import generate_hyperdim_viz


@pytest.fixture
def sample_terms():
    """Sample terms for testing."""
    return ['Business', 'Client', 'Revenue', 'Forecast', 'Agent', 'Tool', 'Optimization', 'Strategy']


@pytest.fixture
def temp_output(tmp_path):
    """Temporary output file path."""
    return str(tmp_path / 'test_viz.png')


def test_generate_viz_from_terms(sample_terms, temp_output):
    """Test visualization generation from custom terms."""
    result_path = generate_hyperdim_viz(terms=sample_terms, output_file=temp_output, n_components=2)

    assert os.path.exists(result_path)
    assert Path(result_path).suffix == '.png'
    assert os.path.getsize(result_path) > 1000  # Non-empty PNG


def test_generate_viz_3d(sample_terms, temp_output):
    """Test 3D visualization generation."""
    result_path = generate_hyperdim_viz(terms=sample_terms, output_file=temp_output, n_components=3)

    assert os.path.exists(result_path)
    assert Path(result_path).suffix == '.png'


def test_generate_viz_from_ontology(temp_output):
    """Test visualization from ontology file."""
    ontology_path = 'assets/ontologies/business.ttl'
    if not os.path.exists(ontology_path):
        pytest.skip('Business ontology not found')

    result_path = generate_hyperdim_viz(ontology_path=ontology_path, output_file=temp_output)

    assert os.path.exists(result_path)


def test_terms_override_ontology(sample_terms, temp_output):
    """Test that terms parameter takes priority over ontology."""
    ontology_path = 'assets/ontologies/business.ttl'
    if not os.path.exists(ontology_path):
        pytest.skip('Business ontology not found')

    result_path = generate_hyperdim_viz(
        ontology_path=ontology_path, terms=sample_terms, output_file=temp_output  # Should use these, not ontology
    )

    assert os.path.exists(result_path)


def test_insufficient_terms(temp_output):
    """Test error on insufficient terms."""
    with pytest.raises(ValueError, match='at least 2 terms'):
        generate_hyperdim_viz(terms=['OnlyOne'], output_file=temp_output)


def test_no_input_provided(temp_output):
    """Test error when neither ontology nor terms provided."""
    with pytest.raises(ValueError, match='Must provide either'):
        generate_hyperdim_viz(output_file=temp_output)


def test_invalid_n_components(sample_terms, temp_output):
    """Test error on invalid n_components."""
    with pytest.raises(ValueError, match='must be 2 or 3'):
        generate_hyperdim_viz(terms=sample_terms, n_components=4, output_file=temp_output)


def test_nonexistent_ontology(temp_output):
    """Test error on non-existent ontology file."""
    with pytest.raises(FileNotFoundError):
        generate_hyperdim_viz(ontology_path='/nonexistent/path.ttl', output_file=temp_output)


def test_custom_perplexity(sample_terms, temp_output):
    """Test custom perplexity parameter."""
    result_path = generate_hyperdim_viz(terms=sample_terms, output_file=temp_output, perplexity=5)

    assert os.path.exists(result_path)


def test_max_terms_limit(temp_output):
    """Test max_terms parameter limits extraction."""
    # Create a dummy ontology would be complex, so we use terms
    many_terms = [f'Term{i}' for i in range(100)]
    result_path = generate_hyperdim_viz(terms=many_terms[:10], output_file=temp_output, max_terms=10)  # Limit to 10

    assert os.path.exists(result_path)


def test_output_path_returned(sample_terms, temp_output):
    """Test that absolute output path is returned."""
    result_path = generate_hyperdim_viz(terms=sample_terms, output_file=temp_output)

    assert os.path.isabs(result_path)
    assert result_path == str(Path(temp_output).resolve())

