"""
Tests for the DataValidator class in the processors module
"""
import pytest
import pandas as pd
from datetime import datetime

from prolabdep.processors.validator import DataValidator
from prolabdep.core.config import Config


@pytest.fixture
def data_validator():
    """DataValidator instance for testing."""
    return DataValidator(Config())


@pytest.fixture
def valid_data_dict():
    """Create valid test data for validation."""
    # Create sample data
    data = pd.DataFrame({
        'codice_prelievo': ['S0001', 'S0001', 'S0002'],
        'data_prelievo': [datetime(2024, 1, 1), datetime(2024, 1, 1), datetime(2024, 1, 2)],
        'codice_param': ['COD@M1@mg/l', 'BOD@M2@mg/l', 'COD@M1@mg/l'],
        'valore': [150.0, 25.0, 300.0],
        'municipality': ['SN', 'SN', 'AA'],
        'site': ['Dep. S. Giusto', 'Dep. S. Giusto', 'Dep. Centrale'],
        'sampling_point': ['uscita', 'uscita', 'ingresso']
    })
    
    # Create parameters data
    parameters = pd.DataFrame({
        'codice_param': ['COD@M1@mg/l', 'BOD@M2@mg/l'],
        'nome_param': ['COD', 'BOD'],
        'metodo': ['M1', 'M2'],
        'udm': ['mg/l', 'mg/l'],
        'descrizione': ['Chemical Oxygen Demand', 'Biochemical Oxygen Demand']
    })
    
    # Create samples data
    samples = pd.DataFrame({
        'codice_prelievo': ['S0001', 'S0002'],
        'data_prelievo': [datetime(2024, 1, 1), datetime(2024, 1, 2)],
        'municipality': ['SN', 'AA'],
        'site': ['Dep. S. Giusto', 'Dep. Centrale'],
        'sampling_point': ['uscita', 'ingresso'],
        'motivo_prelievo': ['Routine', 'Routine'],
        'modo_prelievo': ['Manual', 'Manual'],
        'stato': ['Completed', 'Completed']
    })
    
    return {
        'data': data,
        'parameters': parameters,
        'samples': samples
    }


@pytest.fixture
def invalid_data_dict():
    """Create invalid test data for validation."""
    # Create sample data with issues
    data = pd.DataFrame({
        'codice_prelievo': ['S0001', 'S0001', 'S0003'],  # S0003 not in samples
        'data_prelievo': [datetime(2024, 1, 1), datetime(2024, 1, 1), None],  # Missing date
        'codice_param': ['COD@M1@mg/l', 'UNKNOWN@M3@mg/l', 'COD@M1@mg/l'],  # Unknown parameter
        'valore': [150.0, 25.0, None],  # Missing value
        'municipality': ['SN', 'SN', 'XX'],
        'site': ['Dep. S. Giusto', 'Dep. S. Giusto', ''],  # Empty site
        'sampling_point': ['uscita', 'uscita', None]  # Missing sampling point
    })
    
    # Create parameters data
    parameters = pd.DataFrame({
        'codice_param': ['COD@M1@mg/l'],  # Missing BOD parameter
        'nome_param': ['COD'],
        'metodo': ['M1'],
        'udm': ['mg/l'],
        'descrizione': ['Chemical Oxygen Demand']
    })
    
    # Create samples data with missing sample
    samples = pd.DataFrame({
        'codice_prelievo': ['S0001', 'S0002'],  # Missing S0003
        'data_prelievo': [datetime(2024, 1, 1), datetime(2024, 1, 2)],
        'municipality': ['SN', 'AA'],
        'site': ['Dep. S. Giusto', 'Dep. Centrale'],
        'sampling_point': ['uscita', 'ingresso'],
        'motivo_prelievo': ['Routine', 'Routine'],
        'modo_prelievo': ['Manual', 'Manual'],
        'stato': ['Completed', 'Completed']
    })
    
    return {
        'data': data,
        'parameters': parameters,
        'samples': samples
    }


def test_valid_data(data_validator, valid_data_dict):
    """Test validation of valid data."""
    # Validate data
    result = data_validator.validate(valid_data_dict)
    
    # Check result
    assert result['valid'] == True
    assert len(result['errors']) == 0
    assert result['summary']['total_samples'] == 2
    assert result['summary']['total_measurements'] == 3
    assert result['summary']['total_parameters'] == 2


def test_missing_required_dataframes(data_validator):
    """Test validation when required dataframes are missing."""
    # Test with missing data dataframe
    incomplete_dict1 = {
        'parameters': pd.DataFrame(),
        'samples': pd.DataFrame()
    }
    result1 = data_validator.validate(incomplete_dict1)
    assert result1['valid'] == False
    assert any('missing required dataframe' in e.lower() for e in result1['errors'])
    
    # Test with missing parameters dataframe
    incomplete_dict2 = {
        'data': pd.DataFrame(),
        'samples': pd.DataFrame()
    }
    result2 = data_validator.validate(incomplete_dict2)
    assert result2['valid'] == False
    assert any('missing required dataframe' in e.lower() for e in result2['errors'])
    
    # Test with missing samples dataframe
    incomplete_dict3 = {
        'data': pd.DataFrame(),
        'parameters': pd.DataFrame()
    }
    result3 = data_validator.validate(incomplete_dict3)
    assert result3['valid'] == False
    assert any('missing required dataframe' in e.lower() for e in result3['errors'])


def test_invalid_data(data_validator, invalid_data_dict):
    """Test validation of invalid data."""
    # Validate data
    result = data_validator.validate(invalid_data_dict)
    
    # Check result
    assert result['valid'] == False
    assert len(result['errors']) > 0
    
    # Check specific errors
    error_messages = ' '.join(result['errors']).lower()
    assert 'unknown parameter' in error_messages or 'unknown@m3@mg/l' in error_messages  # Unknown parameter


def test_empty_dataframes(data_validator):
    """Test validation with empty dataframes."""
    empty_dict = {
        'data': pd.DataFrame(),
        'parameters': pd.DataFrame(),
        'samples': pd.DataFrame()
    }
    
    result = data_validator.validate(empty_dict)
    
    assert result['valid'] == False
    assert any('empty dataframe' in e.lower() for e in result['errors'])


def test_duplicate_detection(data_validator, valid_data_dict):
    """Test detection of duplicate measurements."""
    # Create data with duplicates
    data_with_duplicates = valid_data_dict.copy()
    
    # Add a duplicate measurement (same sample_id and parameter_code)
    duplicate_row = data_with_duplicates['data'].iloc[0].copy()
    data_with_duplicates['data'] = pd.concat([
        data_with_duplicates['data'], 
        pd.DataFrame([duplicate_row])
    ]).reset_index(drop=True)
    
    # Validate data
    result = data_validator.validate(data_with_duplicates)
    
    # Check result
    assert result['valid'] == False
    assert any('duplicate' in e.lower() for e in result['errors'])
    assert 's0001' in ' '.join(result['errors']).lower()  # Sample ID in error message
    assert 'cod@m1@mg/l' in ' '.join(result['errors']).lower()  # Parameter in error message 