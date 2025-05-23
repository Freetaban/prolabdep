# ProlabDep

A comprehensive Python package for processing and analyzing wastewater treatment plant data from LIMS exports.

## Features

- Data extraction from CSV/Excel LIMS exports
- Data cleaning and standardization
- Local database storage and management
- Time series analysis
- Statistical analysis
- Mass flow calculations
- Flexible API for integration with notebooks, scripts, and applications
- Export capabilities (Excel, CSV, PDF reports)
- Web interface for data visualization

## Installation

```bash
# From PyPI (when available)
pip install prolabdep

# From source
git clone https://github.com/yourusername/prolabdep.git
cd prolabdep
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Install Jupyter notebook support
pip install -e ".[notebook]"
```

## Basic Usage

```python
from prolabdep.api import Client

# Initialize client
client = Client()

# Load and process data
data_id = client.import_data("path/to/lims_export.csv")

# Get processed data
parameters = client.get_parameters(data_id)
samples = client.get_samples(data_id, site="S. Giusto", date_from="2024-01-01")

# Analyze data
timeseries = client.get_parameter_timeseries(data_id, parameter="COD", 
                                            site="S. Giusto", 
                                            sampling_point="uscita")
stats = client.analyze_statistics(timeseries)
print(f"Average COD: {stats['mean']} mg/L")

# Create visualization
client.plot_timeseries(timeseries, title="COD Trends", save_path="cod_trends.png")

# Calculate mass flow
client.calculate_mass_flow(
    concentration=timeseries,
    flow_parameter="FLOW", 
    output_unit="kg/d"
)
```

## Architecture

The package is organized into several modules:

- `api`: High-level client API for easy interaction
- `core`: Core functionality including database, models, and configuration
- `processors`: Data import and processing
- `analytics`: Data analysis tools
- `exporters`: Data export utilities
- `web`: Web interface
- `utils`: Utility functions

## Documentation

For detailed documentation, see the [docs](docs/) directory.

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 