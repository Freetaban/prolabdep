"""
Tests for the client API's standardization and flexible search features
"""
import os
import pytest
import pandas as pd
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock

from prolabdep.api.client import Client
from prolabdep.utils.standardization import default_mappings


@pytest.fixture
def mock_db():
    """Create a mock database for testing."""
    mock = MagicMock()
    
    # Mock get_parameter_data with different search modes
    def mock_get_parameter_data(parameter, filter_criteria=None, search_mode='exact'):
        if filter_criteria is None:
            filter_criteria = {}
            
        # Create sample data based on search mode
        if search_mode == 'exact':
            if parameter == 'COD':
                return pd.DataFrame({
                    'parameter_name': ['COD'] * 3,
                    'parameter_name_std': ['COD'] * 3,
                    'value': [100, 150, 200],
                    'date': [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)]
                })
            elif parameter == 'BOD':
                return pd.DataFrame({
                    'parameter_name': ['BOD5'] * 2,
                    'parameter_name_std': ['BOD'] * 2,
                    'value': [50, 75],
                    'date': [datetime(2024, 1, 1), datetime(2024, 1, 2)]
                })
            else:
                return pd.DataFrame()
                
        elif search_mode == 'contains':
            if parameter == 'CO' or 'CO' in parameter:
                return pd.DataFrame({
                    'parameter_name': ['COD'] * 3,
                    'parameter_name_std': ['COD'] * 3,
                    'value': [100, 150, 200],
                    'date': [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)]
                })
            elif parameter == 'BOD' or 'BOD' in parameter:
                return pd.DataFrame({
                    'parameter_name': ['BOD5'] * 2,
                    'parameter_name_std': ['BOD'] * 2,
                    'value': [50, 75],
                    'date': [datetime(2024, 1, 1), datetime(2024, 1, 2)]
                })
            else:
                return pd.DataFrame()
                
        elif search_mode == 'fuzzy':
            if parameter.lower() in ['cod', 'co', 'cd']:
                return pd.DataFrame({
                    'parameter_name': ['COD'] * 3,
                    'parameter_name_std': ['COD'] * 3,
                    'value': [100, 150, 200],
                    'date': [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)]
                })
            elif parameter.lower() in ['bod', 'bo', 'bd']:
                return pd.DataFrame({
                    'parameter_name': ['BOD5'] * 2,
                    'parameter_name_std': ['BOD'] * 2,
                    'value': [50, 75],
                    'date': [datetime(2024, 1, 1), datetime(2024, 1, 2)]
                })
            else:
                return pd.DataFrame()
        
        return pd.DataFrame()
    
    mock.get_parameter_data.side_effect = mock_get_parameter_data
    
    # Mock get_parameters
    mock.get_parameters.return_value = pd.DataFrame({
        'code': ['COD@M1@mg/l', 'BOD@M2@mg/l', 'TSS@M3@mg/l'],
        'name': ['COD', 'BOD5', 'Solidi Sospesi'],
        'name_std': ['COD', 'BOD', 'TSS'],
        'method': ['M1', 'M2', 'M3'],
        'unit': ['mg/l', 'mg/l', 'mg/l'],
        'description': ['Chemical Oxygen Demand', 'Biochemical Oxygen Demand', 'Total Suspended Solids']
    })
    
    # Mock get_samples
    mock.get_samples.return_value = pd.DataFrame({
        'id': ['S0001', 'S0002', 'S0003'],
        'date': [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)],
        'municipality': ['AA', 'BB', 'AA'],
        'site': ['Dep. S. Giusto', 'Dep. Centrale', 'Dep. S. Colombano'],
        'site_std': ['San Giusto', 'Centrale', 'San Colombano'],
        'sampling_point': ['ingresso', 'uscita', 'ingresso'],
        'sampling_point_std': ['inlet', 'outlet', 'inlet'],
        'reason': ['Routine', 'Routine', 'Special'],
        'sampling_method': ['Manual', 'Manual', 'Automatic'],
        'status': ['Completed', 'Completed', 'Completed']
    })
    
    return mock


@pytest.fixture
def client_with_mock_db(mock_db):
    """Create a client with a mock database."""
    with patch('prolabdep.api.client.Database', return_value=mock_db):
        client = Client()
        return client


def test_get_parameter_timeseries_with_search_modes(client_with_mock_db):
    """Test get_parameter_timeseries with different search modes."""
    # Test exact search
    results = client_with_mock_db.get_parameter_timeseries(
        parameter='COD',
        search_mode='exact'
    )
    assert len(results) == 3
    assert all(results['parameter_name'] == 'COD')
    
    # Test contains search
    results = client_with_mock_db.get_parameter_timeseries(
        parameter='CO',
        search_mode='contains'
    )
    assert len(results) == 3
    assert all(results['parameter_name'] == 'COD')
    
    # Test fuzzy search
    results = client_with_mock_db.get_parameter_timeseries(
        parameter='CD',
        search_mode='fuzzy'
    )
    assert len(results) == 3
    assert all(results['parameter_name'] == 'COD')
    
    # Test non-existent parameter
    results = client_with_mock_db.get_parameter_timeseries(
        parameter='NonExistent',
        search_mode='exact'
    )
    assert len(results) == 0


def test_find_similar_parameters(client_with_mock_db):
    """Test find_similar_parameters method."""
    # Mock the default_mappings.find_similar_parameters method
    with patch('prolabdep.utils.standardization.default_mappings.find_similar_parameters') as mock_find:
        mock_find.return_value = ['COD', 'BOD']
        
        # Call the client method
        results = client_with_mock_db.find_similar_parameters('cod')
        
        # Check that the mock was called with the correct arguments
        mock_find.assert_called_once_with('cod', 0.6)
        
        # Check the results
        assert results == ['COD', 'BOD']


def test_find_similar_sites(client_with_mock_db):
    """Test find_similar_sites method."""
    # Mock the default_mappings.find_similar_sites method
    with patch('prolabdep.utils.standardization.default_mappings.find_similar_sites') as mock_find:
        mock_find.return_value = ['San Giusto', 'San Colombano']
        
        # Call the client method
        results = client_with_mock_db.find_similar_sites('giusto')
        
        # Check that the mock was called with the correct arguments
        mock_find.assert_called_once_with('giusto', 0.6)
        
        # Check the results
        assert results == ['San Giusto', 'San Colombano']


def test_find_similar_sampling_points(client_with_mock_db):
    """Test find_similar_sampling_points method."""
    # Mock the default_mappings.find_similar_sampling_points method
    with patch('prolabdep.utils.standardization.default_mappings.find_similar_sampling_points') as mock_find:
        mock_find.return_value = ['inlet', 'outlet']
        
        # Call the client method
        results = client_with_mock_db.find_similar_sampling_points('ingresso')
        
        # Check that the mock was called with the correct arguments
        mock_find.assert_called_once_with('ingresso', 0.6)
        
        # Check the results
        assert results == ['inlet', 'outlet']


def test_add_mappings(client_with_mock_db):
    """Test adding custom mappings."""
    # Mock the default_mappings methods
    with patch('prolabdep.utils.standardization.default_mappings.add_site_mapping') as mock_site, \
         patch('prolabdep.utils.standardization.default_mappings.add_sampling_point_mapping') as mock_sp, \
         patch('prolabdep.utils.standardization.default_mappings.add_parameter_mapping') as mock_param:
        
        # Call the client methods
        client_with_mock_db.add_site_mapping('test site', 'Test Site')
        client_with_mock_db.add_sampling_point_mapping('test point', 'Test Point')
        client_with_mock_db.add_parameter_mapping('test param', 'Test Param')
        
        # Check that the mocks were called with the correct arguments
        mock_site.assert_called_once_with('test site', 'Test Site')
        mock_sp.assert_called_once_with('test point', 'Test Point')
        mock_param.assert_called_once_with('test param', 'Test Param') 