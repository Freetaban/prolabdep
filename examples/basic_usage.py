"""
Basic example demonstrating the use of the ProlabDep package
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
from prolabdep.api import Client

# Set up logging
import logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File path - update this to point to your data file
DATA_FILE = "../TUTTO_2024_25.csv"  # Path relative to the example file
DB_FILE = "prolabdep_data.db"


def main():
    """Run the example"""
    print("ProlabDep Example")
    print("================")
    
    # Check if data file exists
    if not os.path.exists(DATA_FILE):
        print(f"Error: Data file not found at {DATA_FILE}")
        print("Please update the DATA_FILE variable to point to your data file.")
        return
    
    # Initialize client
    print("\n1. Initializing client...")
    client = Client(db_path=DB_FILE)
    
    # Load data
    print("\n2. Loading and processing data...")
    try:
        data_id = client.import_data(DATA_FILE)
        print(f"Data imported with ID: {data_id}")
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return
    
    # Get parameters
    print("\n3. Getting parameters...")
    try:
        parameters = client.get_parameters()
        print(f"Found {len(parameters)} parameters")
        
        # Display first 5 parameters
        if not parameters.empty:
            print("\nParameter examples:")
            for _, row in parameters.head(5).iterrows():
                print(f"  - {row['name']}: {row.get('description', 'No description')} ({row.get('unit', 'No unit')})")
    except Exception as e:
        print(f"Error getting parameters: {str(e)}")
    
    # Get samples
    print("\n4. Getting samples...")
    try:
        # Get all samples
        samples = client.get_samples()
        print(f"Found {len(samples)} samples")
        
        # Get municipalities
        municipalities = samples['municipality'].dropna().unique() if 'municipality' in samples.columns else []
        print(f"Found {len(municipalities)} municipalities: {', '.join(municipalities[:5])}{'...' if len(municipalities) > 5 else ''}")
        
        # Get sites
        sites = samples['site'].dropna().unique() if 'site' in samples.columns else []
        print(f"Found {len(sites)} sites: {', '.join(str(s) for s in sites[:5])}{'...' if len(sites) > 5 else ''}")
    except Exception as e:
        print(f"Error getting samples: {str(e)}")
    
    # Get parameter time series data
    print("\n5. Getting parameter time series data...")
    try:
        # Choose a common parameter (e.g., COD)
        parameter = "COD"
        
        # If we have sites, choose one
        site = sites[0] if len(sites) > 0 else None
        
        cod_data = client.get_parameter_timeseries(
            parameter=parameter,
            site=site
        )
        
        if cod_data.empty:
            print(f"No {parameter} data found")
        else:
            print(f"Retrieved {len(cod_data)} {parameter} measurements")
            
            # Analyze the data
            print("\n6. Analyzing data...")
            stats = client.analyze_statistics(cod_data)
            print(f"\n{parameter} Statistics:")
            for stat, value in stats.items():
                print(f"  {stat}: {value}")
                
            # Create a plot
            print("\n7. Creating visualization...")
            fig = client.plot_timeseries(
                cod_data,
                parameter_name=parameter,
                title=f"{parameter} Time Series{'for ' + site if site else ''}",
                include_trend=True
            )
            
            # Save the plot
            plot_file = f"{parameter.lower()}_timeseries.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            print(f"Plot saved to {plot_file}")
            
            # Export data to Excel
            excel_file = f"{parameter.lower()}_data.xlsx"
            client.export_to_excel(cod_data, excel_file)
            print(f"Data exported to {excel_file}")
    except Exception as e:
        print(f"Error processing parameter data: {str(e)}")
    
    print("\nExample completed!")


if __name__ == "__main__":
    main() 