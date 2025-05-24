#!/usr/bin/env python
"""
Example demonstrating standardization and flexible search features

This example shows how to use the standardization utilities and flexible search
capabilities of the ProlabDep package.
"""
import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to path to import prolabdep
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from prolabdep.api.client import Client
from prolabdep.utils.standardization import StandardizationMappings, default_mappings


def main():
    """Run the standardization and flexible search example"""
    print("ProlabDep Standardization and Flexible Search Example")
    print("====================================================\n")
    
    # Create a client
    client = Client()
    
    # 1. Demonstrate standardization mappings
    print("1. Standardization Mappings")
    print("--------------------------")
    
    # Show default mappings
    print("Default site mappings:")
    for original, standardized in default_mappings.site_mappings.items():
        print(f"  '{original}' -> '{standardized}'")
    
    print("\nDefault sampling point mappings:")
    for original, standardized in default_mappings.sampling_point_mappings.items():
        print(f"  '{original}' -> '{standardized}'")
    
    print("\nDefault parameter mappings:")
    for original, standardized in default_mappings.parameter_mappings.items():
        print(f"  '{original}' -> '{standardized}'")
    
    # 2. Demonstrate standardization of values
    print("\n2. Standardizing Values")
    print("----------------------")
    
    # Standardize site names
    sites = ["dep. s. giusto", "DEP. CENTRALE", "Impianto dep. s. colombano", "Unknown Site"]
    print("\nStandardizing site names:")
    for site in sites:
        std_site = default_mappings.standardize_site(site)
        print(f"  '{site}' -> '{std_site}'")
    
    # Standardize sampling points
    points = ["ingresso", "USCITA", "punto entrata", "Unknown Point"]
    print("\nStandardizing sampling points:")
    for point in points:
        std_point = default_mappings.standardize_sampling_point(point)
        print(f"  '{point}' -> '{std_point}'")
    
    # Standardize parameters
    params = ["cod", "BOD5", "parameter solidi sospesi", "Unknown Parameter"]
    print("\nStandardizing parameters:")
    for param in params:
        std_param = default_mappings.standardize_parameter(param)
        print(f"  '{param}' -> '{std_param}'")
    
    # 3. Demonstrate fuzzy matching
    print("\n3. Fuzzy Matching")
    print("----------------")
    
    # Find similar sites
    search_terms = ["giusto", "central", "colomban"]
    print("\nFinding similar sites:")
    for term in search_terms:
        similar = client.find_similar_sites(term)
        print(f"  '{term}' -> {similar}")
    
    # Find similar sampling points
    search_terms = ["ingres", "out", "entr"]
    print("\nFinding similar sampling points:")
    for term in search_terms:
        similar = client.find_similar_sampling_points(term)
        print(f"  '{term}' -> {similar}")
    
    # Find similar parameters
    search_terms = ["co", "bod", "sospesi"]
    print("\nFinding similar parameters:")
    for term in search_terms:
        similar = client.find_similar_parameters(term)
        print(f"  '{term}' -> {similar}")
    
    # 4. Demonstrate flexible search modes
    print("\n4. Flexible Search Modes")
    print("----------------------")
    
    # Try different search modes for parameters
    search_modes = ["exact", "contains", "fuzzy"]
    parameter = "COD"
    
    print(f"\nSearching for parameter '{parameter}' with different modes:")
    for mode in search_modes:
        results = client.get_parameter_timeseries(parameter=parameter, search_mode=mode)
        print(f"  {mode} search: found {len(results)} results")
    
    # Try partial parameter name with different search modes
    partial_param = "CO"
    print(f"\nSearching for partial parameter '{partial_param}' with different modes:")
    for mode in search_modes:
        results = client.get_parameter_timeseries(parameter=partial_param, search_mode=mode)
        print(f"  {mode} search: found {len(results)} results")
    
    # 5. Adding custom mappings
    print("\n5. Adding Custom Mappings")
    print("-----------------------")
    
    # Add custom mappings
    client.add_site_mapping("my site", "My Custom Site")
    client.add_sampling_point_mapping("my point", "My Custom Point")
    client.add_parameter_mapping("my param", "My Custom Parameter")
    
    print("Custom mappings added:")
    print(f"  'my site' -> '{default_mappings.standardize_site('my site')}'")
    print(f"  'my point' -> '{default_mappings.standardize_sampling_point('my point')}'")
    print(f"  'my param' -> '{default_mappings.standardize_parameter('my param')}'")
    
    print("\nExample completed!")


if __name__ == "__main__":
    main() 