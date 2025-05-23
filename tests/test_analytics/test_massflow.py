"""
Tests for the MassFlowCalculator class in the analytics module
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from prolabdep.analytics.massflow import MassFlowCalculator


@pytest.fixture
def massflow_calculator():
    """MassFlowCalculator instance for testing."""
    return MassFlowCalculator()


@pytest.fixture
def concentration_data():
    """Sample concentration data for testing."""
    # Create sample dates
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(10)]
    
    # Create sample concentration values (mg/L)
    values = [200, 210, 205, 195, 200, 205, 210, 200, 195, 200]
    
    # Create a dataframe
    df = pd.DataFrame({
        'date': dates,
        'value': values,
        'parameter_name': 'COD',
        'unit': 'mg/l',
        'site': 'Test Site',
        'sampling_point': 'Outlet'
    })
    
    return df


@pytest.fixture
def flow_data():
    """Sample flow data for testing."""
    # Use same dates as concentration data
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(10)]
    
    # Create sample flow values (m3/h)
    values = [100, 105, 102, 98, 100, 103, 101, 99, 102, 100]
    
    # Create a dataframe
    df = pd.DataFrame({
        'date': dates,
        'value': values,
        'parameter_name': 'FLOW',
        'unit': 'm3/h',
        'site': 'Test Site',
        'sampling_point': 'Outlet'
    })
    
    return df


def test_calculate_mass_flow_basic(massflow_calculator):
    """Test basic mass flow calculation with known inputs."""
    # Test case: 200 mg/L and 100 m3/h should give 20 kg/h
    # 200 mg/L * 100 m3/h / 1,000,000 = 0.02 kg/h
    mass_flow = massflow_calculator.calculate_mass_flow(
        concentration=200,
        flow=100,
        concentration_unit='mg/l',
        flow_unit='m3/h',
        output_unit='kg/h'
    )
    
    assert mass_flow == pytest.approx(0.02, abs=0.0001)


def test_unit_conversions(massflow_calculator):
    """Test mass flow calculations with different units."""
    # Base case: 200 mg/L and 100 m3/h = 0.02 kg/h
    base_mass_flow = massflow_calculator.calculate_mass_flow(
        concentration=200,
        flow=100,
        concentration_unit='mg/l',
        flow_unit='m3/h',
        output_unit='kg/h'
    )
    
    # Test concentration unit conversion (g/L)
    # 0.2 g/L and 100 m3/h = 20 kg/h
    mass_flow_g_l = massflow_calculator.calculate_mass_flow(
        concentration=0.2,
        flow=100,
        concentration_unit='g/l',
        flow_unit='m3/h',
        output_unit='kg/h'
    )
    assert mass_flow_g_l == pytest.approx(0.02, abs=0.0001)
    
    # Test flow unit conversion (L/s)
    # 200 mg/L and 27.78 L/s (= 100 m3/h) = 0.02 kg/h
    mass_flow_l_s = massflow_calculator.calculate_mass_flow(
        concentration=200,
        flow=27.78,
        concentration_unit='mg/l',
        flow_unit='l/s',
        output_unit='kg/h'
    )
    assert mass_flow_l_s == pytest.approx(0.02, abs=0.0001)
    
    # Test output unit conversion (kg/d)
    # 200 mg/L and 100 m3/h = 0.48 kg/d
    mass_flow_kg_d = massflow_calculator.calculate_mass_flow(
        concentration=200,
        flow=100,
        concentration_unit='mg/l',
        flow_unit='m3/h',
        output_unit='kg/d'
    )
    assert mass_flow_kg_d == pytest.approx(0.48, abs=0.001)  # 0.02 kg/h * 24 h/d = 0.48 kg/d


def test_extract_unit(massflow_calculator):
    """Test extraction of quantity and time units from unit strings."""
    # Test valid units
    quantity, time_unit = massflow_calculator.extract_unit('mg/l')
    assert quantity == 'mg'
    assert time_unit == 'l'
    
    quantity, time_unit = massflow_calculator.extract_unit('m3/h')
    assert quantity == 'm3'
    assert time_unit == 'h'
    
    # Test case sensitivity
    quantity, time_unit = massflow_calculator.extract_unit('MG/L')
    assert quantity == 'mg'
    assert time_unit == 'l'
    
    # Test invalid unit format
    quantity, time_unit = massflow_calculator.extract_unit('invalid')
    assert quantity == 'invalid'
    assert time_unit is None
    
    # Test empty unit
    quantity, time_unit = massflow_calculator.extract_unit('')
    assert quantity is None
    assert time_unit is None
    
    # Test None input
    quantity, time_unit = massflow_calculator.extract_unit(None)
    assert quantity is None
    assert time_unit is None


def test_apply_mass_flow_calculation(concentration_data, flow_data, massflow_calculator):
    """Test applying mass flow calculation to datasets."""
    # Apply mass flow calculation
    mass_flow_data = massflow_calculator.apply_mass_flow_calculation(
        concentration_data=concentration_data,
        flow_data=flow_data,
        output_unit='kg/h'
    )
    
    # Check result structure
    assert 'date' in mass_flow_data.columns
    assert 'concentration' in mass_flow_data.columns
    assert 'flow' in mass_flow_data.columns
    assert 'mass_flow' in mass_flow_data.columns
    assert 'unit' in mass_flow_data.columns
    
    # Check number of rows
    assert len(mass_flow_data) == len(concentration_data)
    
    # Check specific mass flow calculations
    # First row: 200 mg/L * 100 m3/h / 1,000,000 = 0.02 kg/h
    assert mass_flow_data['mass_flow'].iloc[0] == pytest.approx(0.02, abs=0.0001)
    
    # Check unit
    assert mass_flow_data['unit'].iloc[0] == 'kg/h'
    
    # Test with a different output unit
    mass_flow_data_kg_d = massflow_calculator.apply_mass_flow_calculation(
        concentration_data=concentration_data,
        flow_data=flow_data,
        output_unit='kg/d'
    )
    
    # Check conversion: 0.02 kg/h * 24 h/d = 0.48 kg/d
    assert mass_flow_data_kg_d['mass_flow'].iloc[0] == pytest.approx(0.48, abs=0.001)
    assert mass_flow_data_kg_d['unit'].iloc[0] == 'kg/d'


def test_invalid_inputs(massflow_calculator):
    """Test error handling for invalid inputs."""
    # Test invalid concentration unit
    with pytest.raises(ValueError):
        massflow_calculator.calculate_mass_flow(
            concentration=200,
            flow=100,
            concentration_unit='invalid',
            flow_unit='m3/h',
            output_unit='kg/h'
        )
    
    # Test invalid flow unit
    with pytest.raises(ValueError):
        massflow_calculator.calculate_mass_flow(
            concentration=200,
            flow=100,
            concentration_unit='mg/l',
            flow_unit='invalid',
            output_unit='kg/h'
        )
    
    # Test invalid output unit
    with pytest.raises(ValueError):
        massflow_calculator.calculate_mass_flow(
            concentration=200,
            flow=100,
            concentration_unit='mg/l',
            flow_unit='m3/h',
            output_unit='invalid'
        ) 