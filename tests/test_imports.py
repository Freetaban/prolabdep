"""
Basic tests to verify module imports
"""
import pytest

def test_import_core():
    """Test importing core modules"""
    from prolabdep.core import Database, Config, Sample, Parameter, Measurement
    assert Database is not None
    assert Config is not None
    assert Sample is not None
    assert Parameter is not None
    assert Measurement is not None

def test_import_analytics():
    """Test importing analytics modules"""
    from prolabdep.analytics import (
        TimeSeriesAnalyzer, StatisticsAnalyzer, 
        MassFlowCalculator, TrendAnalyzer
    )
    assert TimeSeriesAnalyzer is not None
    assert StatisticsAnalyzer is not None
    assert MassFlowCalculator is not None
    assert TrendAnalyzer is not None

def test_import_processors():
    """Test importing processor modules"""
    from prolabdep.processors import (
        CSVProcessor, ExcelProcessor, DataProcessor, DataValidator
    )
    assert CSVProcessor is not None
    assert ExcelProcessor is not None
    assert DataProcessor is not None
    assert DataValidator is not None

def test_import_visualization():
    """Test importing visualization modules"""
    from prolabdep.visualization import Visualizer
    assert Visualizer is not None

def test_import_api():
    """Test importing API modules"""
    from prolabdep.api import Client
    assert Client is not None

def test_import_utils():
    """Test importing utility modules"""
    from prolabdep.utils.standardization import (
        StandardizationMappings, default_mappings, standardize_location_info
    )
    assert StandardizationMappings is not None
    assert default_mappings is not None
    assert standardize_location_info is not None 