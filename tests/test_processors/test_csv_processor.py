"""
Tests for the CSVProcessor class in the processors module
"""
import os
import pytest
import pandas as pd
import tempfile
from datetime import datetime

from prolabdep.processors.csv_processor import CSVProcessor
from prolabdep.core.config import Config
from prolabdep.core.exceptions import ProcessingError


@pytest.fixture
def csv_processor():
    """CSVProcessor instance for testing."""
    return CSVProcessor(Config())


@pytest.fixture
def sample_csv_file():
    """Create a sample CSV file for testing."""
    csv_content = """Codice;Attività;Data prelievo;Motivo del prelievo;Modalità di campionamento;Stato;COD@M1@mg/l;BOD@M2@mg/l;
;Chemical Oxygen Demand;Biochemical Oxygen Demand;;;;
S0001;SN Dep. S. Giusto uscita - Scandicci - 10624;01/01/2024;Routine;Manual;Completed;150;25;
S0002;AA Dep. Centrale ingresso - Milano - 20100;02/01/2024;Routine;Manual;Completed;300;60;
S0003;SN Dep. S. Giusto ingresso - Scandicci - 10624;03/01/2024;Special;Automatic;Completed;400;80;
"""
    
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w', encoding='latin-1') as tmp:
        tmp.write(csv_content)
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Clean up after test
    if os.path.exists(tmp_path):
        os.remove(tmp_path)


def test_csv_load_and_parse(csv_processor, sample_csv_file):
    """Test loading and parsing a CSV file."""
    # Process the CSV file
    result = csv_processor.process(sample_csv_file)
    
    # Check that result has the expected structure
    assert 'data' in result
    assert 'parameters' in result
    assert 'samples' in result
    
    # Check parameters were extracted correctly
    params = result['parameters']
    assert len(params) == 2
    assert 'COD' in params['nome_param'].values
    assert 'BOD' in params['nome_param'].values
    assert 'mg/l' in params['udm'].values
    
    # Check samples were extracted correctly
    samples = result['samples']
    assert len(samples) == 3
    assert 'Dep. S. Giusto' in samples['site'].values
    assert 'Dep. Centrale' in samples['site'].values
    assert 'ingresso' in samples['sampling_point'].values
    assert 'uscita' in samples['sampling_point'].values
    
    # Check dates were parsed correctly
    assert isinstance(samples['data_prelievo'].iloc[0], datetime)
    
    # Check data was extracted correctly
    data = result['data']
    assert len(data) == 6  # 3 samples x 2 parameters
    assert 150.0 in data['valore'].values
    assert 300.0 in data['valore'].values
    assert 400.0 in data['valore'].values
    assert 25.0 in data['valore'].values
    assert 60.0 in data['valore'].values
    assert 80.0 in data['valore'].values


def test_extract_location_info(csv_processor):
    """Test extraction of location information from activity string."""
    # Test typical format: "SN Dep. S. Giusto uscita - Scandicci - 10624"
    result1 = csv_processor._extract_location_info("SN Dep. S. Giusto uscita - Scandicci - 10624")
    assert result1['municipality'] == 'SN'
    assert result1['site'] == 'Dep. S. Giusto'
    assert result1['sampling_point'] == 'uscita'
    
    # Test format with 'ingresso'
    result2 = csv_processor._extract_location_info("AA Dep. Centrale ingresso - Milano - 20100")
    assert result2['municipality'] == 'AA'
    assert result2['site'] == 'Dep. Centrale'
    assert result2['sampling_point'] == 'ingresso'
    
    # Test format without municipality prefix
    result3 = csv_processor._extract_location_info("Impianto 1 uscita - Roma - 00100")
    assert result3['municipality'] is None  # No prefix recognized
    assert result3['site'] == 'Impianto 1'
    assert result3['sampling_point'] == 'uscita'
    
    # Test format without recognizable sampling point
    result4 = csv_processor._extract_location_info("AA Stazione di monitoraggio - Torino")
    assert result4['municipality'] == 'AA'
    assert result4['site'] == 'Stazione di monitoraggio'
    assert result4['sampling_point'] is None  # No sampling point recognized


def test_parse_date(csv_processor):
    """Test date parsing with different formats."""
    # Test dd/mm/yyyy format
    date1 = csv_processor._parse_date("01/01/2024")
    assert date1 == datetime(2024, 1, 1)
    
    # Test yyyy-mm-dd format
    date2 = csv_processor._parse_date("2024-01-01")
    assert date2 == datetime(2024, 1, 1)
    
    # Test dd.mm.yyyy format
    date3 = csv_processor._parse_date("01.01.2024")
    assert date3 == datetime(2024, 1, 1)
    
    # Test dd-mm-yyyy format
    date4 = csv_processor._parse_date("01-01-2024")
    assert date4 == datetime(2024, 1, 1)
    
    # Test invalid format
    with pytest.raises(ValueError):
        csv_processor._parse_date("2024/01/01-invalid")


def test_convert_value(csv_processor):
    """Test value conversion with special handling."""
    # Test normal number
    assert csv_processor._convert_value("150.5") == 150.5
    
    # Test decimal separator
    assert csv_processor._convert_value("150,5") == 150.5
    
    # Test detection limit
    detection_limit_value = csv_processor._convert_value("<10")
    assert detection_limit_value == 5.0  # Default fraction is 2
    
    # Test greater than value
    assert csv_processor._convert_value(">100") == 100.0
    
    # Test conversion map
    assert csv_processor._convert_value("Assente", {'Assente': '0', 'Presente': '1'}) == 0.0
    assert csv_processor._convert_value("Presente", {'Assente': '0', 'Presente': '1'}) == 1.0
    
    # Test non-string input
    assert csv_processor._convert_value(150) == 150
    
    # Test invalid input
    assert pd.isna(csv_processor._convert_value("not-a-number"))


def test_file_not_found(csv_processor):
    """Test error handling when file is not found."""
    with pytest.raises(ProcessingError) as excinfo:
        csv_processor.process("nonexistent_file.csv")
    assert "File not found" in str(excinfo.value)


def test_invalid_file_extension(csv_processor):
    """Test error handling for invalid file extension."""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        with pytest.raises(Exception):
            csv_processor.process(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path) 