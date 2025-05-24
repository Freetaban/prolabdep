"""
Tests for flexible search functionality in the database module
"""
import os
import pytest
import pandas as pd
import tempfile
from datetime import datetime

from prolabdep.core.database import Database
from prolabdep.core.models import Sample, Parameter, Measurement
from prolabdep.utils.standardization import default_mappings


@pytest.fixture
def temp_db_path(request):
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    def finalizer():
        # Import gc to clean up any lingering connections before deleting
        import gc
        gc.collect()  # Force garbage collection
        
        try:
            # Try to remove the file
            if os.path.exists(db_path):
                os.remove(db_path)
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not delete temp database {db_path}: {e}")
    
    request.addfinalizer(finalizer)
    return db_path


@pytest.fixture
def db_with_test_data(temp_db_path):
    """Create a database with test data for flexible search testing."""
    db = Database(temp_db_path)
    
    # Create test data
    samples_data = pd.DataFrame({
        'id': ['S0001', 'S0002', 'S0003', 'S0004'],
        'date': [
            datetime(2024, 1, 1),
            datetime(2024, 1, 2),
            datetime(2024, 1, 3),
            datetime(2024, 1, 4)
        ],
        'municipality': ['AA', 'BB', 'AA', 'CC'],
        'site': ['Dep. S. Giusto', 'Dep. Centrale', 'Dep. S. Colombano', 'Impianto Test'],
        'site_std': ['San Giusto', 'Centrale', 'San Colombano', 'Impianto Test'],
        'sampling_point': ['ingresso', 'uscita', 'ingresso', 'vasca'],
        'sampling_point_std': ['inlet', 'outlet', 'inlet', 'vasca'],
        'reason': ['Routine', 'Routine', 'Special', 'Routine'],
        'sampling_method': ['Manual', 'Manual', 'Automatic', 'Manual'],
        'status': ['Completed', 'Completed', 'Completed', 'Completed']
    })
    
    parameters_data = pd.DataFrame({
        'code': ['COD@M1@mg/l', 'BOD@M2@mg/l', 'TSS@M3@mg/l', 'pH@M4@-'],
        'name': ['COD', 'BOD5', 'Solidi Sospesi', 'pH'],
        'name_std': ['COD', 'BOD', 'TSS', 'pH'],
        'method': ['M1', 'M2', 'M3', 'M4'],
        'unit': ['mg/l', 'mg/l', 'mg/l', '-'],
        'description': ['Chemical Oxygen Demand', 'Biochemical Oxygen Demand', 'Total Suspended Solids', 'pH']
    })
    
    # Create measurements data
    measurements_data = []
    for sample_id in samples_data['id']:
        for param_code in parameters_data['code']:
            # Generate some test values
            if sample_id == 'S0001':
                value = 150.0 if 'COD' in param_code else 25.0 if 'BOD' in param_code else 30.0 if 'TSS' in param_code else 7.0
            elif sample_id == 'S0002':
                value = 50.0 if 'COD' in param_code else 10.0 if 'BOD' in param_code else 15.0 if 'TSS' in param_code else 7.5
            elif sample_id == 'S0003':
                value = 200.0 if 'COD' in param_code else 40.0 if 'BOD' in param_code else 50.0 if 'TSS' in param_code else 6.5
            else:
                value = 100.0 if 'COD' in param_code else 20.0 if 'BOD' in param_code else 25.0 if 'TSS' in param_code else 7.2
            
            measurements_data.append({
                'sample_id': sample_id,
                'parameter_code': param_code,
                'value': value
            })
    
    measurements_df = pd.DataFrame(measurements_data)
    
    # Store data in database
    db.store_data({
        'samples': samples_data,
        'parameters': parameters_data,
        'data': measurements_df
    })
    
    return db


def test_exact_search(db_with_test_data):
    """Test exact search mode for parameter data."""
    # Test exact match with standard name
    results = db_with_test_data.get_parameter_data('COD', search_mode='exact')
    assert len(results) == 4
    assert all(results['parameter_name'] == 'COD')
    
    # Test exact match with non-standard name that has a standard equivalent
    results = db_with_test_data.get_parameter_data('Solidi Sospesi', search_mode='exact')
    assert len(results) == 4
    assert all(results['parameter_name'] == 'Solidi Sospesi')
    
    # Test exact match with standardized name
    results = db_with_test_data.get_parameter_data('TSS', search_mode='exact')
    assert len(results) == 4
    assert all(results['parameter_name_std'] == 'TSS')
    
    # Test non-existent parameter
    results = db_with_test_data.get_parameter_data('NonExistent', search_mode='exact')
    assert len(results) == 0


def test_contains_search(db_with_test_data):
    """Test contains search mode for parameter data."""
    # Test partial match
    results = db_with_test_data.get_parameter_data('BOD', search_mode='contains')
    assert len(results) == 4
    assert all(results['parameter_name_std'] == 'BOD')
    
    # Test partial match with non-standard name
    results = db_with_test_data.get_parameter_data('Sospesi', search_mode='contains')
    assert len(results) == 4
    assert all(results['parameter_name'] == 'Solidi Sospesi')
    
    # Test non-existent parameter
    results = db_with_test_data.get_parameter_data('NonExistent', search_mode='contains')
    assert len(results) == 0


def test_fuzzy_search(db_with_test_data):
    """Test fuzzy search mode for parameter data."""
    # Test fuzzy match
    results = db_with_test_data.get_parameter_data('CD', search_mode='fuzzy')
    assert len(results) > 0  # Should find COD
    
    # Test fuzzy match with non-standard name
    results = db_with_test_data.get_parameter_data('Soldi Sospsi', search_mode='fuzzy')
    assert len(results) > 0  # Should find Solidi Sospesi
    
    # Test non-existent parameter
    results = db_with_test_data.get_parameter_data('xyzabc', search_mode='fuzzy')
    assert len(results) == 0


def test_site_filtering(db_with_test_data):
    """Test filtering by site with standardization."""
    # Test exact site match
    filter_criteria = {'site': 'Dep. S. Giusto'}
    results = db_with_test_data.get_parameter_data('COD', filter_criteria, search_mode='exact')
    assert len(results) == 1
    assert results['site'].iloc[0] == 'Dep. S. Giusto'
    
    # Test standardized site match
    filter_criteria = {'site': 'San Giusto'}
    results = db_with_test_data.get_parameter_data('COD', filter_criteria, search_mode='exact')
    assert len(results) == 1
    assert results['site_std'].iloc[0] == 'San Giusto'
    
    # Test partial site match
    filter_criteria = {'site': 'Giusto'}
    results = db_with_test_data.get_parameter_data('COD', filter_criteria, search_mode='exact')
    assert len(results) == 1
    assert 'Giusto' in results['site'].iloc[0]


def test_sampling_point_filtering(db_with_test_data):
    """Test filtering by sampling point with standardization."""
    # Test exact sampling point match
    filter_criteria = {'sampling_point': 'ingresso'}
    results = db_with_test_data.get_parameter_data('COD', filter_criteria, search_mode='exact')
    assert len(results) == 2
    assert all(results['sampling_point'] == 'ingresso')
    
    # Test standardized sampling point match
    filter_criteria = {'sampling_point': 'inlet'}
    results = db_with_test_data.get_parameter_data('COD', filter_criteria, search_mode='exact')
    assert len(results) == 2
    assert all(results['sampling_point_std'] == 'inlet')


def test_combined_filters(db_with_test_data):
    """Test combined filters with standardization."""
    # Test site and sampling point
    filter_criteria = {
        'site': 'San Colombano',
        'sampling_point': 'inlet'
    }
    results = db_with_test_data.get_parameter_data('COD', filter_criteria, search_mode='exact')
    assert len(results) == 1
    assert results['site_std'].iloc[0] == 'San Colombano'
    assert results['sampling_point_std'].iloc[0] == 'inlet'
    
    # Test site, sampling point, and date range
    filter_criteria = {
        'site': 'San Colombano',
        'sampling_point': 'inlet',
        'date_from': datetime(2024, 1, 1),
        'date_to': datetime(2024, 1, 3)
    }
    results = db_with_test_data.get_parameter_data('COD', filter_criteria, search_mode='exact')
    assert len(results) == 1
    assert results['site_std'].iloc[0] == 'San Colombano'
    assert results['sampling_point_std'].iloc[0] == 'inlet'
    assert results['date'].iloc[0] <= datetime(2024, 1, 3)
    assert results['date'].iloc[0] >= datetime(2024, 1, 1) 