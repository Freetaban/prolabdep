"""
Tests for the BaseProcessor class in the processors module
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from prolabdep.processors.base_processor import BaseProcessor
from prolabdep.core.config import Config


@pytest.fixture
def base_processor():
    """BaseProcessor instance for testing."""
    return BaseProcessor(Config())


@pytest.fixture
def sample_df_with_parameters():
    """Create a sample dataframe with parameter information."""
    # Create a dataframe with parameter information in headers
    df = pd.DataFrame(
        columns=['Codice', 'COD@M1@mg/l', 'BOD@M2@mg/l', 'pH@APHA@-'],
        data=[
            ['', 'Chemical Oxygen Demand', 'Biochemical Oxygen Demand', 'pH'],
            ['S0001', '150', '25', '7.2'],
            ['S0002', '300', '60', '7.5']
        ]
    )
    return df


def test_base_processor_initialization():
    """Test initialization of BaseProcessor."""
    config = Config()
    processor = BaseProcessor(config)
    assert processor.config == config


def test_process_not_implemented(base_processor):
    """Test that the process method raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        base_processor.process("file_path.csv")


def test_get_parameters(base_processor, sample_df_with_parameters):
    """Test extraction of parameter information from dataframe headers."""
    # Extract parameters
    params_df = base_processor._get_parameters(sample_df_with_parameters)
    
    # Check result structure
    assert 'codice_param' in params_df.columns
    assert 'testo_param' in params_df.columns
    assert 'nome_param' in params_df.columns
    assert 'metodo' in params_df.columns
    assert 'udm' in params_df.columns
    
    # Check extracted parameters
    assert len(params_df) == 3  # Should have 3 parameters
    
    # Check specific parameters
    param_codes = params_df['codice_param'].tolist()
    assert 'COD@M1@mg/l' in param_codes
    assert 'BOD@M2@mg/l' in param_codes
    assert 'pH@APHA@-' in param_codes
    
    # Check parameter names were cleaned
    param_names = params_df['nome_param'].tolist()
    assert 'COD' in param_names
    assert 'BOD' in param_names
    assert 'pH' in param_names
    
    # Check parameter methods
    methods = params_df['metodo'].tolist()
    assert 'M1' in methods
    assert 'M2' in methods
    assert 'APHA' in methods
    
    # Check parameter units
    units = params_df['udm'].tolist()
    assert 'mg/l' in units
    assert '-' in units


def test_parse_date(base_processor):
    """Test date parsing with different formats."""
    # Default config has multiple date formats
    
    # Test dd/mm/yyyy format
    date1 = base_processor._parse_date("01/01/2024")
    assert date1 == datetime(2024, 1, 1)
    
    # Test yyyy-mm-dd format
    date2 = base_processor._parse_date("2024-01-01")
    assert date2 == datetime(2024, 1, 1)
    
    # Test dd.mm.yyyy format
    date3 = base_processor._parse_date("01.01.2024")
    assert date3 == datetime(2024, 1, 1)
    
    # Test dd-mm-yyyy format
    date4 = base_processor._parse_date("01-01-2024")
    assert date4 == datetime(2024, 1, 1)
    
    # Test passing an existing datetime object
    date5 = datetime(2024, 1, 1)
    assert base_processor._parse_date(date5) is date5
    
    # Test invalid format
    with pytest.raises(ValueError):
        base_processor._parse_date("not-a-date")


def test_extract_location_info(base_processor):
    """Test extraction of location information from activity string."""
    # Test typical format: "SN Dep. S. Giusto uscita - Scandicci - 10624"
    result1 = base_processor._extract_location_info("SN Dep. S. Giusto uscita - Scandicci - 10624")
    assert result1['municipality'] == 'SN'
    assert result1['site'] == 'Dep. S. Giusto'
    assert result1['sampling_point'] == 'uscita'
    
    # Test format with 'ingresso'
    result2 = base_processor._extract_location_info("AA Dep. Centrale ingresso - Milano - 20100")
    assert result2['municipality'] == 'AA'
    assert result2['site'] == 'Dep. Centrale'
    assert result2['sampling_point'] == 'ingresso'
    
    # Test format without municipality prefix
    result3 = base_processor._extract_location_info("Impianto 1 vasca 3 - Roma - 00100")
    assert result3['municipality'] is None  # No prefix recognized
    assert result3['site'] == 'Impianto 1'
    assert result3['sampling_point'] == 'vasca 3'
    
    # Test missing or None input
    result4 = base_processor._extract_location_info(None)
    assert result4['municipality'] is None
    assert result4['site'] is None
    assert result4['sampling_point'] is None


def test_convert_value(base_processor):
    """Test value conversion with special handling."""
    # Test normal number
    assert base_processor._convert_value("150.5") == 150.5
    
    # Test detection limit
    # Default config has detection_limit_fraction = 2
    detection_limit_value = base_processor._convert_value("<10")
    assert detection_limit_value == 5.0  # 10/2 = 5
    
    # Test greater than value
    assert base_processor._convert_value(">100") == 100.0
    
    # Test conversion map
    assert base_processor._convert_value("Assente", {'Assente': '0', 'Presente': '1'}) == 0.0
    assert base_processor._convert_value("Presente", {'Assente': '0', 'Presente': '1'}) == 1.0
    
    # Test non-string input
    assert base_processor._convert_value(150) == 150
    
    # Test invalid input
    assert pd.isna(base_processor._convert_value("not-a-number")) 