"""
# ProlabDep Tutorial

This notebook demonstrates how to use the ProlabDep package to process and analyze wastewater treatment plant data.
"""

# %% [markdown]
# ## 1. Installation and Setup
# 
# First, let's install the package if you haven't already:
# 
# ```bash
# pip install prolabdep
# ```
# 
# Now, let's import the necessary modules:

# %%
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Import ProlabDep modules
from prolabdep.api import Client
from prolabdep.visualization import Visualizer

# Configure matplotlib for better display in notebook
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['figure.dpi'] = 100

# Enable inline plotting
# %matplotlib inline

# %% [markdown]
# ## 2. Initialize Client
# 
# The `Client` class is the main entry point for interacting with the ProlabDep package:

# %%
# Initialize client with a local database
client = Client(db_path="tutorial_data.db")

print(f"Client initialized with database at {client._data_cache}")

# %% [markdown]
# ## 3. Load Sample Data
# 
# For this tutorial, we'll either use your own data file or create some synthetic data:

# %%
# Define file path to your data
data_file = "../TUTTO_2024_25.csv"  # Replace with your data file path

# Check if the file exists
if os.path.exists(data_file):
    print(f"Found data file at {data_file}")
    # Import data from file
    data_id = client.import_data(data_file)
    print(f"Data imported with ID: {data_id}")
else:
    print(f"Data file not found at {data_file}, using synthetic data instead")
    
    # Create synthetic data for demonstration purposes
    # First, let's create sample metadata
    sample_ids = [f"S{i:04d}" for i in range(1, 101)]
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(100)]
    sites = ["North WWTP", "South WWTP"] * 50
    sampling_points = ["Inlet", "Outlet"] * 50
    
    # Create synthetic parameters
    parameters = {
        "COD": {"unit": "mg/L", "values": np.random.normal(250, 50, 100)},
        "BOD": {"unit": "mg/L", "values": np.random.normal(120, 30, 100)},
        "TSS": {"unit": "mg/L", "values": np.random.normal(180, 40, 100)},
        "pH": {"unit": "pH", "values": np.random.normal(7.2, 0.5, 100)},
        "FLOW": {"unit": "m3/h", "values": np.random.normal(500, 100, 100)}
    }
    
    # Create sample dataframes for each parameter
    dfs = []
    for param, info in parameters.items():
        df = pd.DataFrame({
            "sample_id": sample_ids,
            "date": dates,
            "site": sites,
            "sampling_point": sampling_points,
            "parameter_name": param,
            "unit": info["unit"],
            "value": info["values"]
        })
        dfs.append(df)
    
    # Combine all parameter dataframes
    synthetic_data = pd.concat(dfs, ignore_index=True)
    print(f"Created synthetic data with {len(synthetic_data)} measurements")

# %% [markdown]
# ## 4. Explore Parameters
# 
# Let's look at what parameters are available in our dataset:

# %%
# Get parameters from database
parameters = client.get_parameters()

if not parameters.empty:
    print(f"Found {len(parameters)} parameters:")
    display(parameters.head())
else:
    # If using synthetic data, show parameters
    print("Parameters in synthetic data:")
    print(list(parameters.keys()))

# %% [markdown]
# ## 5. Retrieve Time Series Data
# 
# Now, let's retrieve time series data for a specific parameter (e.g., COD):

# %%
# Get time series data for COD parameter
parameter = "COD"
site = "North WWTP"  # Update this to match your data
sampling_point = "Outlet"  # Update this to match your data

timeseries = client.get_parameter_timeseries(
    parameter=parameter,
    site=site,
    sampling_point=sampling_point
)

if not timeseries.empty:
    print(f"Retrieved {len(timeseries)} {parameter} measurements")
    display(timeseries.head())
else:
    print(f"No {parameter} data found for {site} {sampling_point}")
    
    # If using synthetic data, filter it
    if 'synthetic_data' in locals():
        timeseries = synthetic_data[
            (synthetic_data['parameter_name'] == parameter) & 
            (synthetic_data['site'] == site) & 
            (synthetic_data['sampling_point'] == sampling_point)
        ]
        print(f"Using synthetic data: {len(timeseries)} {parameter} measurements")
        display(timeseries.head())

# %% [markdown]
# ## 6. Basic Statistics and Analysis
# 
# Let's calculate some basic statistics for the time series data:

# %%
# Calculate statistics
stats = client.analyze_statistics(timeseries)

print(f"{parameter} Statistics:")
for stat, value in stats.items():
    print(f"  {stat}: {value}")

# %% [markdown]
# ## 7. Time Series Visualization
# 
# Now, let's create a time series plot:

# %%
# Create time series plot
fig = client.plot_time_series(
    timeseries,
    parameter_name=parameter,
    title=f"{parameter} Time Series for {site} {sampling_point}",
    include_trend=True
)

plt.tight_layout()
plt.show()

# %% [markdown]
# ## 8. Data Resampling
# 
# Let's resample the data to a different frequency (e.g., weekly averages):

# %%
# Resample to weekly data
weekly_data = client.resample_timeseries(
    timeseries,
    frequency='W',  # Weekly
    method='mean'   # Average
)

print(f"Resampled to {len(weekly_data)} weekly data points")
display(weekly_data.head())

# Create time series plot of resampled data
fig = client.plot_time_series(
    weekly_data,
    parameter_name=f"Weekly {parameter}",
    title=f"Weekly Average {parameter} for {site} {sampling_point}",
    include_trend=True
)

plt.tight_layout()
plt.show()

# %% [markdown]
# ## 9. Compare Different Sites or Sampling Points
# 
# Let's compare data from different sites or sampling points:

# %%
# Get data for another site or sampling point
alt_sampling_point = "Inlet"  # Change this based on your data

alt_timeseries = client.get_parameter_timeseries(
    parameter=parameter,
    site=site,
    sampling_point=alt_sampling_point
)

if alt_timeseries.empty and 'synthetic_data' in locals():
    # Use synthetic data if needed
    alt_timeseries = synthetic_data[
        (synthetic_data['parameter_name'] == parameter) & 
        (synthetic_data['site'] == site) & 
        (synthetic_data['sampling_point'] == alt_sampling_point)
    ]

# Create comparison plot using the Visualizer class directly
visualizer = Visualizer()

if not timeseries.empty and not alt_timeseries.empty:
    fig = visualizer.plot_comparison(
        [timeseries, alt_timeseries],
        labels=[f"{sampling_point}", f"{alt_sampling_point}"],
        title=f"{parameter} Comparison at {site}"
    )
    
    plt.tight_layout()
    plt.show()

# %% [markdown]
# ## 10. Calculate Mass Flow
# 
# If we have concentration and flow data, we can calculate mass flow:

# %%
# Get flow data
flow_parameter = "FLOW"
flow_data = client.get_parameter_timeseries(
    parameter=flow_parameter,
    site=site,
    sampling_point=sampling_point
)

if flow_data.empty and 'synthetic_data' in locals():
    # Use synthetic data if needed
    flow_data = synthetic_data[
        (synthetic_data['parameter_name'] == flow_parameter) & 
        (synthetic_data['site'] == site) & 
        (synthetic_data['sampling_point'] == sampling_point)
    ]

# Calculate mass flow if we have both concentration and flow data
if not timeseries.empty and not flow_data.empty:
    mass_flow = client.calculate_mass_flow(
        concentration=timeseries,
        flow_parameter=flow_parameter,
        flow_data=flow_data,
        output_unit='kg/d'  # kilograms per day
    )
    
    print(f"Calculated {len(mass_flow)} mass flow data points")
    display(mass_flow.head())
    
    # Plot mass flow
    fig = client.plot_time_series(
        mass_flow,
        parameter_name=f"{parameter} Load",
        title=f"{parameter} Mass Flow at {site} {sampling_point}",
        include_trend=True
    )
    
    plt.tight_layout()
    plt.show()

# %% [markdown]
# ## 11. Export Data
# 
# Finally, let's export our data to different formats:

# %%
# Export to Excel
excel_file = f"{parameter}_data.xlsx"
client.export_to_excel(timeseries, excel_file)
print(f"Data exported to Excel: {excel_file}")

# Export to CSV
csv_file = f"{parameter}_data.csv"
client.export_to_csv(timeseries, csv_file)
print(f"Data exported to CSV: {csv_file}")

# %% [markdown]
# ## Conclusion
# 
# In this tutorial, we've learned how to:
# 
# 1. Import data using ProlabDep
# 2. Retrieve and analyze time series data
# 3. Calculate statistics and visualize trends
# 4. Resample data to different frequencies
# 5. Compare data from different sources
# 6. Calculate mass flow
# 7. Export data to different formats
# 
# The ProlabDep package provides a comprehensive set of tools for processing and analyzing wastewater treatment plant data from LIMS exports. 