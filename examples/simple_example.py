"""
Simple example demonstrating the use of the ProlabDep package
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
from prolabdep import DataProcessor, Database, TimeSeriesAnalyzer, Visualizer

# Set up logging
import logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File path - update this to point to your data file
DATA_FILE = "path/to/your/LIMS_export.csv"  # e.g., "TUTTO_2024_25.csv"
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
    
    # Initialize data processor
    print("\n1. Loading and processing data...")
    processor = DataProcessor()
    
    # Load data
    try:
        data_dict = processor.load_from_file(DATA_FILE)
        print(f"Loaded {len(data_dict['data'])} measurements")
        print(f"Found {len(data_dict['parameters'])} unique parameters")
        print(f"Found {len(data_dict['samples'])} samples")
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return
    
    # Initialize database
    print("\n2. Storing data in database...")
    try:
        db = Database(DB_FILE)
        measurements_count = db.store_data(data_dict)
        print(f"Stored {measurements_count} measurements in database")
    except Exception as e:
        print(f"Error storing data: {str(e)}")
        return
    
    # Query database for a specific parameter (e.g., COD)
    print("\n3. Querying database for COD parameter...")
    try:
        # Retrieve COD data for a specific site
        parameter_data = db.get_parameter_data(
            parameter_name="COD",
            filter_criteria={
                'site': "S. Giusto",
                'sampling_point': "uscita"
            }
        )
        
        if parameter_data.empty:
            print("No COD data found for the specified criteria.")
            # Try with another site
            print("Trying to find any COD data...")
            parameter_data = db.get_parameter_data(parameter_name="COD")
            
            if parameter_data.empty:
                print("No COD data found in the database.")
                return
        
        print(f"Retrieved {len(parameter_data)} COD measurements")
    except Exception as e:
        print(f"Error querying database: {str(e)}")
        return
    
    # Analyze time series
    print("\n4. Analyzing time series data...")
    try:
        analyzer = TimeSeriesAnalyzer()
        
        # Calculate statistics
        stats = analyzer.calculate_statistics(parameter_data)
        print("Statistics:")
        for stat, value in stats.items():
            print(f"  {stat}: {value}")
        
        # Resample to monthly data
        monthly_data = analyzer.resample(
            parameter_data, 
            frequency='M',
            method='mean'
        )
        print(f"Resampled to {len(monthly_data)} monthly data points")
    except Exception as e:
        print(f"Error analyzing data: {str(e)}")
        return
    
    # Visualize data
    print("\n5. Creating visualizations...")
    try:
        visualizer = Visualizer()
        
        # Create time series plot
        fig1 = visualizer.plot_time_series(
            parameter_data,
            y_column='value',
            x_column='date',
            parameter_name="COD",
            include_trend=True
        )
        
        # Create histogram
        fig2 = visualizer.plot_histogram(
            parameter_data,
            column='value',
            bins=15,
            title="COD Histogram"
        )
        
        # Save figures
        visualizer.save_figure(fig1, "cod_time_series.png")
        visualizer.save_figure(fig2, "cod_histogram.png")
        
        print("Visualizations created and saved")
        print("  - cod_time_series.png")
        print("  - cod_histogram.png")
    except Exception as e:
        print(f"Error creating visualizations: {str(e)}")
        return
    
    print("\nExample completed successfully!")

if __name__ == "__main__":
    main() 