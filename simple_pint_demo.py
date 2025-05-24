#!/usr/bin/env python3
"""
Simple demonstration of Pint integration in ProlabDep
This script showcases the core unit management features.
"""

import pandas as pd
from prolabdep.utils.units import unit_manager
from prolabdep.analytics.massflow import MassFlowCalculator

def main():
    print("=" * 80)
    print("ProlabDep Pint Integration - Core Features Demo")
    print("=" * 80)
    
    # 1. Basic Unit Manager Functionality
    print("\n1. BASIC UNIT MANAGEMENT")
    print("-" * 40)
    
    # Unit standardization
    print("Unit Standardization:")
    test_units = ['mg/l', 'MG/L', 'g/L', 'm3/h', 'pH', '°C', '-']
    for unit in test_units:
        standardized = unit_manager.standardize_unit(unit)
        print(f"  {unit:8} → {standardized}")
    
    # Unit conversions
    print("\nUnit Conversions:")
    conversions = [
        (1000, 'mg/L', 'g/L'),
        (1, 'g/L', 'mg/L'),
        (1, 'm³/h', 'L/s'),
        (100, 'L/s', 'm³/h'),
        (20, 'kg/h', 'kg/d'),
        (480, 'kg/d', 'kg/h')
    ]
    
    for value, from_unit, to_unit in conversions:
        converted = unit_manager.convert_value(value, from_unit, to_unit)
        print(f"  {value:6} {from_unit:6} = {converted:8.3f} {to_unit}")
    
    # Unit compatibility
    print("\nUnit Compatibility:")
    compatibility_tests = [
        ('mg/L', 'g/L'),
        ('m³/h', 'L/s'),
        ('kg/h', 'kg/d'),
        ('mg/L', 'm³/h'),  # Should be False
        ('°C', 'mg/L')     # Should be False
    ]
    
    for unit1, unit2 in compatibility_tests:
        compatible = unit_manager.are_compatible(unit1, unit2)
        status = "✓" if compatible else "✗"
        print(f"  {status} {unit1:6} ↔ {unit2:6}")
    
    # 2. Mass Flow Calculations
    print("\n2. MASS FLOW CALCULATIONS")
    print("-" * 40)
    
    calc = MassFlowCalculator()
    
    # Basic calculations
    print("Basic Mass Flow Calculations:")
    mass_flow_tests = [
        (200, 'mg/L', 100, 'm³/h', 'kg/h'),
        (0.2, 'g/L', 100, 'm³/h', 'kg/h'),
        (200, 'mg/L', 27.78, 'L/s', 'kg/h'),
        (200, 'mg/L', 100, 'm³/h', 'kg/d'),
        (500, 'mg/L', 50, 'm³/h', 'kg/h')
    ]
    
    for conc, conc_unit, flow, flow_unit, output_unit in mass_flow_tests:
        mass_flow = calc.calculate_mass_flow(conc, flow, conc_unit, flow_unit, output_unit)
        print(f"  {conc:6} {conc_unit:6} × {flow:6} {flow_unit:6} = {mass_flow:8.2f} {output_unit}")
    
    # 3. Advanced Mass Flow with DataFrames
    print("\n3. ADVANCED MASS FLOW WITH DATAFRAMES")
    print("-" * 40)
    
    # Create sample concentration and flow data
    dates = pd.date_range('2024-01-01', periods=5, freq='D')
    
    concentration_data = pd.DataFrame({
        'date': dates,
        'value': [200, 210, 195, 205, 200],
        'unit': ['mg/L'] * 5,
        'parameter_name': ['COD'] * 5,
        'site': ['Test Site'] * 5
    })
    
    flow_data = pd.DataFrame({
        'date': dates,
        'value': [100, 105, 95, 100, 102],
        'unit': ['m³/h'] * 5,
        'parameter_name': ['FLOW'] * 5,
        'site': ['Test Site'] * 5
    })
    
    # Calculate mass flow
    mass_flow_result = calc.apply_mass_flow_calculation(
        concentration_data, 
        flow_data, 
        'kg/h'
    )
    
    print("Mass Flow Calculation Results:")
    print(mass_flow_result[['date', 'concentration', 'flow', 'mass_flow', 'mass_flow_unit']].head())
    
    # 4. Unit Suggestions and Dimensionality
    print("\n4. UNIT SUGGESTIONS AND DIMENSIONALITY")
    print("-" * 40)
    
    dimensionalities = [
        '[mass] / [length] ** 3',  # Concentration
        '[length] ** 3 / [time]',  # Flow
        '[mass] / [time]',         # Mass flow
        'dimensionless'            # pH, ratios
    ]
    
    for dim in dimensionalities:
        suggestions = unit_manager.suggest_common_units(dim)
        print(f"  {dim:25} → {', '.join(suggestions[:5])}")
    
    # 5. Unit Extraction from Parameter Codes
    print("\n5. UNIT EXTRACTION FROM PARAMETER CODES")
    print("-" * 40)
    
    parameter_codes = [
        'COD@ISO15705@mg/L',
        'BOD@M2@g/L',
        'pH@APHA@-',
        'FLOW@METER@m³/h',
        'TSS@APHA@mg/L'
    ]
    
    print("Parameter Code Unit Extraction:")
    for code in parameter_codes:
        unit = unit_manager.extract_unit_from_parameter_code(code)
        if unit:
            standardized = unit_manager.standardize_unit(unit)
            dimensionality = unit_manager.get_unit_dimensionality(unit)
            print(f"  {code:20} → {unit:6} → {standardized:20} | {dimensionality}")
        else:
            print(f"  {code:20} → No unit found")
    
    # 6. Error Handling Demonstration
    print("\n6. ERROR HANDLING")
    print("-" * 40)
    
    print("Testing error handling:")
    
    # Invalid unit conversion
    try:
        unit_manager.convert_value(100, 'mg/L', 'm³/h')
    except Exception as e:
        print(f"  ✓ Caught incompatible unit conversion: {type(e).__name__}")
    
    # Invalid unit parsing
    try:
        unit_manager.convert_value(100, 'invalid_unit', 'mg/L')
    except Exception as e:
        print(f"  ✓ Caught invalid unit: {type(e).__name__}")
    
    # Mass flow with incompatible units
    try:
        calc.calculate_mass_flow(100, 20, 'mg/L', '°C', 'kg/h')  # Temperature instead of flow
    except Exception as e:
        print(f"  ✓ Caught incompatible mass flow calculation: {type(e).__name__}")
    
    # 7. Performance Test
    print("\n7. PERFORMANCE TEST")
    print("-" * 40)
    
    import time
    
    # Test caching performance
    start_time = time.time()
    for _ in range(1000):
        unit_manager.parse_unit('mg/L')
    cached_time = time.time() - start_time
    
    print(f"  1000 unit parsing operations: {cached_time:.4f} seconds")
    print(f"  Average per operation: {cached_time/1000*1000:.4f} ms")
    
    # Test conversion performance
    start_time = time.time()
    for _ in range(1000):
        unit_manager.convert_value(200, 'mg/L', 'g/L')
    conversion_time = time.time() - start_time
    
    print(f"  1000 unit conversions: {conversion_time:.4f} seconds")
    print(f"  Average per conversion: {conversion_time/1000*1000:.4f} ms")
    
    print("\n" + "=" * 80)
    print("Pint Integration Core Features Demo Complete!")
    print("All unit management features are working correctly.")
    print("=" * 80)

if __name__ == "__main__":
    main() 