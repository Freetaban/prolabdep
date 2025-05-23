"""
Tests for the Database class in the core module
"""
import os
import pytest
import pandas as pd
from datetime import datetime
import tempfile

from prolabdep.core.database import Database
from prolabdep.core.models import Sample, Parameter, Measurement


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
def sample_data():
    """Create sample data for testing."""
    # Sample data
    data = pd.DataFrame({
        'codice_prelievo': ['S0001', 'S0002', 'S0003'],
        'data_prelievo': [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)],
        'municipality': ['AA', 'BB', 'AA'],
        'site': ['Site 1', 'Site 2', 'Site 1'],
        'sampling_point': ['Inlet', 'Outlet', 'Outlet'],
        'codice_param': ['COD@M1@mg/l', 'COD@M1@mg/l', 'BOD@M2@mg/l'],
        'valore': [150.0, 30.0, 25.0]
    })
    
    # Parameters data
    parameters = pd.DataFrame({
        'codice_param': ['COD@M1@mg/l', 'BOD@M2@mg/l'],
        'nome_param': ['COD', 'BOD'],
        'metodo': ['M1', 'M2'],
        'udm': ['mg/l', 'mg/l'],
        'descrizione': ['Chemical Oxygen Demand', 'Biochemical Oxygen Demand']
    })
    
    # Samples data
    samples = pd.DataFrame({
        'id': ['S0001', 'S0002', 'S0003'],
        'date': [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)],
        'municipality': ['AA', 'BB', 'AA'],
        'site': ['Site 1', 'Site 2', 'Site 1'],
        'sampling_point': ['Inlet', 'Outlet', 'Outlet'],
        'reason': ['Routine', 'Routine', 'Special'],
        'sampling_method': ['Manual', 'Manual', 'Automatic'],
        'status': ['Completed', 'Completed', 'Completed']
    }).set_index('id')
    
    return {
        'data': data,
        'parameters': parameters,
        'samples': samples.reset_index()
    }


def test_database_initialization(temp_db_path):
    """Test that the database is initialized correctly."""
    db = Database(temp_db_path)
    assert os.path.exists(temp_db_path)
    assert db.engine is not None
    assert db.Session is not None


def test_store_and_retrieve_data(temp_db_path, sample_data):
    """Test storing and retrieving data from the database."""
    db = Database(temp_db_path)
    
    # Store data
    measurement_count = db.store_data(sample_data)
    assert measurement_count == 3
    
    # Retrieve parameters
    parameters = db.get_parameters()
    assert len(parameters) == 2
    assert 'COD' in parameters['name'].values
    assert 'BOD' in parameters['name'].values
    
    # Retrieve samples
    samples = db.get_samples()
    assert len(samples) == 3
    assert 'Site 1' in samples['site'].values
    assert 'Site 2' in samples['site'].values
    
    # Retrieve parameter data (COD)
    cod_data = db.get_parameter_data('COD')
    assert len(cod_data) == 2
    assert 150.0 in cod_data['value'].values
    assert 30.0 in cod_data['value'].values
    
    # Retrieve parameter data with filter
    filtered_data = db.get_parameter_data('COD', {'site': 'Site 1'})
    assert len(filtered_data) == 1
    assert filtered_data['value'].iloc[0] == 150.0


def test_get_samples_with_filters(temp_db_path, sample_data):
    """Test retrieving samples with filters."""
    db = Database(temp_db_path)
    db.store_data(sample_data)
    
    # Filter by municipality
    samples_aa = db.get_samples(municipality='AA')
    assert len(samples_aa) == 2
    assert all(s == 'AA' for s in samples_aa['municipality'])
    
    # Filter by site
    samples_site1 = db.get_samples(site='Site 1')
    assert len(samples_site1) == 2
    assert all(s == 'Site 1' for s in samples_site1['site'])
    
    # Filter by sampling point
    samples_outlet = db.get_samples(sampling_point='Outlet')
    assert len(samples_outlet) == 2
    assert all(s == 'Outlet' for s in samples_outlet['sampling_point'])
    
    # Filter by date range
    samples_date_range = db.get_samples(
        date_from=datetime(2024, 1, 2),
        date_to=datetime(2024, 1, 3)
    )
    assert len(samples_date_range) == 2
    assert all(d >= datetime(2024, 1, 2) for d in samples_date_range['date'])
    assert all(d <= datetime(2024, 1, 3) for d in samples_date_range['date'])


def test_get_parameter_data_with_filters(temp_db_path, sample_data):
    """Test retrieving parameter data with filters."""
    db = Database(temp_db_path)
    db.store_data(sample_data)
    
    # Filter by municipality
    cod_aa = db.get_parameter_data('COD', {'municipality': 'AA'})
    assert len(cod_aa) == 1
    assert cod_aa['value'].iloc[0] == 150.0
    
    # Filter by date range
    cod_date_range = db.get_parameter_data(
        'COD',
        {
            'date_from': datetime(2024, 1, 2),
            'date_to': datetime(2024, 1, 3)
        }
    )
    assert len(cod_date_range) == 1
    assert cod_date_range['value'].iloc[0] == 30.0 