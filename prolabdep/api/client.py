"""
Main client interface for ProlabDep
"""
import os
import uuid
import logging
from typing import Dict, List, Optional, Union, Any
import pandas as pd
from datetime import datetime
from functools import lru_cache
from contextlib import contextmanager

from prolabdep.core.config import Config
from prolabdep.core.database import Database
from prolabdep.processors import CSVProcessor, ExcelProcessor
from prolabdep.analytics.timeseries import TimeSeriesAnalyzer
from prolabdep.analytics.statistics import StatisticsAnalyzer
from prolabdep.analytics.massflow import MassFlowCalculator
from prolabdep.analytics.trends import TrendAnalyzer
from prolabdep.exporters.excel import ExcelExporter
from prolabdep.exporters.csv import CSVExporter
from prolabdep.exporters.pdf import PDFExporter
from prolabdep.utils.standardization import default_mappings
from prolabdep.utils.units import unit_manager

logger = logging.getLogger(__name__)

class Client:
    """
    Main client interface for ProlabDep
    
    This class provides a high-level API for interacting with the ProlabDep
    package. It simplifies common operations such as data import, analysis,
    and visualization.
    """
    
    def __init__(self, config_path: Optional[str] = None, db_path: Optional[str] = None):
        """
        Initialize the client
        
        Parameters
        ----------
        config_path : str, optional
            Path to a custom configuration file
        db_path : str, optional
            Path to the database file
        """
        # Initialize configuration
        self.config = Config(config_path)
        
        # Initialize database
        self.db = Database(db_path or self.config.get('database', {}).get('path', 'prolabdep.db'))
        
        # Lazy initialization for processors and analyzers
        self._processors = {}
        self._analyzers = {}
        self._exporters = {}
        
        # Data cache with TTL-like behavior
        self._data_cache = {}
        self._cache_timestamps = {}
        self._cache_ttl = 300  # 5 minutes default TTL
    
    @property
    def csv_processor(self):
        """Lazy-loaded CSV processor"""
        if 'csv' not in self._processors:
            self._processors['csv'] = CSVProcessor(self.config)
        return self._processors['csv']
    
    @property
    def excel_processor(self):
        """Lazy-loaded Excel processor"""
        if 'excel' not in self._processors:
            self._processors['excel'] = ExcelProcessor(self.config)
        return self._processors['excel']
    
    @property
    def timeseries_analyzer(self):
        """Lazy-loaded timeseries analyzer"""
        if 'timeseries' not in self._analyzers:
            self._analyzers['timeseries'] = TimeSeriesAnalyzer()
        return self._analyzers['timeseries']
    
    @property
    def statistics_analyzer(self):
        """Lazy-loaded statistics analyzer"""
        if 'statistics' not in self._analyzers:
            self._analyzers['statistics'] = StatisticsAnalyzer()
        return self._analyzers['statistics']
    
    @property
    def massflow_calculator(self):
        """Lazy-loaded mass flow calculator"""
        if 'massflow' not in self._analyzers:
            self._analyzers['massflow'] = MassFlowCalculator()
        return self._analyzers['massflow']
    
    @property
    def trend_analyzer(self):
        """Lazy-loaded trend analyzer"""
        if 'trend' not in self._analyzers:
            self._analyzers['trend'] = TrendAnalyzer()
        return self._analyzers['trend']
    
    @property
    def excel_exporter(self):
        """Lazy-loaded Excel exporter"""
        if 'excel' not in self._exporters:
            self._exporters['excel'] = ExcelExporter()
        return self._exporters['excel']
    
    @property
    def csv_exporter(self):
        """Lazy-loaded CSV exporter"""
        if 'csv' not in self._exporters:
            self._exporters['csv'] = CSVExporter()
        return self._exporters['csv']
    
    @property
    def pdf_exporter(self):
        """Lazy-loaded PDF exporter"""
        if 'pdf' not in self._exporters:
            self._exporters['pdf'] = PDFExporter()
        return self._exporters['pdf']
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self._cache_timestamps:
            return False
        
        age = (datetime.now() - self._cache_timestamps[cache_key]).total_seconds()
        return age < self._cache_ttl
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if valid"""
        if cache_key in self._data_cache and self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for key: {cache_key}")
            return self._data_cache[cache_key].copy() if hasattr(self._data_cache[cache_key], 'copy') else self._data_cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, data: Any) -> None:
        """Set data in cache"""
        self._data_cache[cache_key] = data
        self._cache_timestamps[cache_key] = datetime.now()
        logger.debug(f"Cache set for key: {cache_key}")
    
    def import_data(self, file_path: str, name: Optional[str] = None) -> str:
        """
        Import data from a file with optimized processing
        
        Parameters
        ----------
        file_path : str
            Path to the data file (CSV or Excel)
        name : str, optional
            Name for the dataset
            
        Returns
        -------
        str
            Unique identifier for the imported data
        """
        # Generate a unique ID for this dataset
        data_id = str(uuid.uuid4())
        
        # Determine file type from extension
        file_extension = os.path.splitext(file_path)[1].lower()
        
        logger.info(f"Importing data from {file_path} with extension {file_extension}")
        
        # Process data based on file type
        if file_extension in ['.csv']:
            data_dict = self.csv_processor.process(file_path)
        elif file_extension in ['.xlsx', '.xls']:
            data_dict = self.excel_processor.process(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        # Store data in database
        measurements_count = self.db.store_data(data_dict)
        
        # Cache dataset information
        self._data_cache[data_id] = {
            'name': name or os.path.basename(file_path),
            'file_path': file_path,
            'import_date': datetime.now(),
            'file_type': file_extension,
            'measurements_count': measurements_count,
        }
        
        # Invalidate related caches
        self._invalidate_data_caches()
        
        logger.info(f"Successfully imported {measurements_count} measurements with ID: {data_id}")
        return data_id
    
    def _invalidate_data_caches(self):
        """Invalidate caches that depend on data"""
        cache_keys_to_remove = [
            key for key in self._data_cache.keys() 
            if key.startswith(('parameters_', 'samples_', 'timeseries_'))
        ]
        for key in cache_keys_to_remove:
            self._data_cache.pop(key, None)
            self._cache_timestamps.pop(key, None)

    @lru_cache(maxsize=100)
    def get_parameters(self, data_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get parameters from a dataset with caching
        
        Parameters
        ----------
        data_id : str, optional
            Dataset identifier (if None, returns all parameters)
            
        Returns
        -------
        pd.DataFrame
            Dataframe of parameters
        """
        cache_key = f"parameters_{data_id or 'all'}"
        
        # Check cache first
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Retrieve from database
        result = self.db.get_parameters()
        
        # Cache the result
        self._set_cache(cache_key, result)
        
        return result
    
    def get_samples(self, data_id: Optional[str] = None, 
                   municipality: Optional[str] = None, 
                   site: Optional[str] = None,
                   sampling_point: Optional[str] = None, 
                   date_from: Optional[Union[str, datetime]] = None,
                   date_to: Optional[Union[str, datetime]] = None) -> pd.DataFrame:
        """
        Get samples matching criteria
        
        Parameters
        ----------
        data_id : str, optional
            Dataset identifier
        municipality : str, optional
            Municipality code
        site : str, optional
            Site name
        sampling_point : str, optional
            Sampling point
        date_from : Union[str, datetime], optional
            Start date
        date_to : Union[str, datetime], optional
            End date
            
        Returns
        -------
        pd.DataFrame
            Dataframe of samples
        """
        # Retrieve from database
        return self.db.get_samples(
            municipality=municipality,
            site=site,
            sampling_point=sampling_point,
            date_from=date_from,
            date_to=date_to
        )
    
    def get_parameter_timeseries(self, data_id: Optional[str] = None,
                                parameter: str = "COD",
                                municipality: Optional[str] = None,
                                site: Optional[str] = None,
                                sampling_point: Optional[str] = None,
                                date_from: Optional[Union[str, datetime]] = None,
                                date_to: Optional[Union[str, datetime]] = None,
                                search_mode: str = 'exact') -> pd.DataFrame:
        """
        Get time series data for a parameter
        
        Parameters
        ----------
        data_id : str, optional
            Dataset identifier
        parameter : str
            Parameter name
        municipality : str, optional
            Municipality code
        site : str, optional
            Site name
        sampling_point : str, optional
            Sampling point
        date_from : Union[str, datetime], optional
            Start date
        date_to : Union[str, datetime], optional
            End date
        search_mode : str, optional
            Search mode: 'exact', 'contains', or 'fuzzy'
            
        Returns
        -------
        pd.DataFrame
            Dataframe with parameter time series
        """
        # Create filter criteria
        filter_criteria = {}
        if municipality:
            filter_criteria['municipality'] = municipality
        if site:
            filter_criteria['site'] = site
        if sampling_point:
            filter_criteria['sampling_point'] = sampling_point
        if date_from:
            filter_criteria['date_from'] = date_from
        if date_to:
            filter_criteria['date_to'] = date_to
        
        # Retrieve from database with specified search mode
        return self.db.get_parameter_data(parameter, filter_criteria, search_mode)
    
    def analyze_statistics(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate statistics for a time series
        
        Parameters
        ----------
        data : pd.DataFrame
            Time series data
            
        Returns
        -------
        Dict[str, float]
            Dictionary of statistics
        """
        return self.statistics_analyzer.calculate_statistics(data)
    
    def resample_timeseries(self, data: pd.DataFrame, 
                          frequency: str = 'D',
                          method: str = 'mean') -> pd.DataFrame:
        """
        Resample time series data
        
        Parameters
        ----------
        data : pd.DataFrame
            Time series data
        frequency : str
            Frequency string (e.g., 'D' for daily, 'W' for weekly)
        method : str
            Aggregation method ('mean', 'median', 'min', 'max', 'sum')
            
        Returns
        -------
        pd.DataFrame
            Resampled data
        """
        return self.timeseries_analyzer.resample(data, frequency, method)
    
    def calculate_mass_flow(self, concentration: pd.DataFrame,
                          flow_parameter: str = "FLOW",
                          flow_data: Optional[pd.DataFrame] = None,
                          output_unit: str = 'kg/h') -> pd.DataFrame:
        """
        Calculate mass flow from concentration and flow
        
        Parameters
        ----------
        concentration : pd.DataFrame
            Concentration data
        flow_parameter : str
            Name of flow parameter
        flow_data : pd.DataFrame, optional
            Flow data (if not provided, retrieved from database)
        output_unit : str
            Output unit
            
        Returns
        -------
        pd.DataFrame
            Mass flow calculations
        """
        # If flow data not provided, retrieve it
        if flow_data is None:
            # Extract site and date range from concentration data
            site = concentration['site'].iloc[0] if 'site' in concentration.columns else None
            date_from = concentration['date'].min() if 'date' in concentration.columns else None
            date_to = concentration['date'].max() if 'date' in concentration.columns else None
            
            # Get flow data for the same site and date range
            flow_data = self.get_parameter_timeseries(
                parameter=flow_parameter,
                site=site,
                date_from=date_from,
                date_to=date_to
            )
        
        # Calculate mass flow
        return self.massflow_calculator.calculate_mass_flow(concentration, flow_data, output_unit)
    
    def plot_time_series(self, data: pd.DataFrame, 
                       parameter_name: Optional[str] = None,
                       title: Optional[str] = None,
                       include_trend: bool = True,
                       save_path: Optional[str] = None) -> Any:
        """
        Create a time series plot
        
        Parameters
        ----------
        data : pd.DataFrame
            Time series data
        parameter_name : str, optional
            Parameter name
        title : str, optional
            Plot title
        include_trend : bool
            Whether to include trend line
        save_path : str, optional
            Path to save the plot
            
        Returns
        -------
        Any
            Plot object
        """
        # Get parameter name if not provided
        if parameter_name is None and 'parameter_name' in data.columns:
            parameter_name = data['parameter_name'].iloc[0]
        
        # Create plot
        fig = self.timeseries_analyzer.plot_time_series(
            data, 
            parameter_name=parameter_name,
            title=title,
            include_trend=include_trend
        )
        
        # Save if path provided
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    # Alias for backward compatibility
    plot_timeseries = plot_time_series
    
    def export_to_excel(self, data: pd.DataFrame, output_path: str) -> str:
        """
        Export data to Excel
        
        Parameters
        ----------
        data : pd.DataFrame
            Data to export
        output_path : str
            Output file path
            
        Returns
        -------
        str
            Path to the exported file
        """
        return self.excel_exporter.export(data, output_path)
    
    def export_to_csv(self, data: pd.DataFrame, output_path: str) -> str:
        """
        Export data to CSV
        
        Parameters
        ----------
        data : pd.DataFrame
            Data to export
        output_path : str
            Output file path
            
        Returns
        -------
        str
            Path to the exported file
        """
        return self.csv_exporter.export(data, output_path)
    
    def export_to_pdf(self, data: pd.DataFrame, output_path: str, 
                     title: str = "ProlabDep Report") -> str:
        """
        Export data to PDF
        
        Parameters
        ----------
        data : pd.DataFrame
            Data to export
        output_path : str
            Output file path
        title : str
            Report title
            
        Returns
        -------
        str
            Path to the exported file
        """
        return self.pdf_exporter.export(data, output_path, title=title)
    
    def detect_trends(self, data: pd.DataFrame, 
                     window: int = 5,
                     threshold: float = 0.05) -> Dict[str, Any]:
        """
        Detect trends in time series data
        
        Parameters
        ----------
        data : pd.DataFrame
            Time series data
        window : int
            Window size for trend detection
        threshold : float
            Significance threshold
            
        Returns
        -------
        Dict[str, Any]
            Dictionary with trend analysis results
        """
        return self.trend_analyzer.detect_trends(
            data, window=window, threshold=threshold
        )
    
    def find_similar_sites(self, site_name: str, cutoff: float = 0.6) -> List[str]:
        """
        Find similar site names
        
        Parameters
        ----------
        site_name : str
            Site name to find matches for
        cutoff : float, optional
            Similarity threshold (0-1)
            
        Returns
        -------
        List[str]
            List of similar site names
        """
        return default_mappings.find_similar_sites(site_name, cutoff)
    
    def find_similar_sampling_points(self, sampling_point: str, cutoff: float = 0.6) -> List[str]:
        """
        Find similar sampling point names
        
        Parameters
        ----------
        sampling_point : str
            Sampling point name to find matches for
        cutoff : float, optional
            Similarity threshold (0-1)
            
        Returns
        -------
        List[str]
            List of similar sampling point names
        """
        return default_mappings.find_similar_sampling_points(sampling_point, cutoff)
    
    def find_similar_parameters(self, parameter: str, cutoff: float = 0.6) -> List[str]:
        """
        Find similar parameter names
        
        Parameters
        ----------
        parameter : str
            Parameter name to find matches for
        cutoff : float, optional
            Similarity threshold (0-1)
            
        Returns
        -------
        List[str]
            List of similar parameter names
        """
        return default_mappings.find_similar_parameters(parameter, cutoff)
    
    def add_site_mapping(self, original: str, standardized: str) -> None:
        """
        Add a new site mapping
        
        Parameters
        ----------
        original : str
            Original site name
        standardized : str
            Standardized site name
        """
        default_mappings.add_site_mapping(original, standardized)
    
    def add_sampling_point_mapping(self, original: str, standardized: str) -> None:
        """
        Add a new sampling point mapping
        
        Parameters
        ----------
        original : str
            Original sampling point name
        standardized : str
            Standardized sampling point name
        """
        default_mappings.add_sampling_point_mapping(original, standardized)
    
    def add_parameter_mapping(self, original: str, standardized: str) -> None:
        """
        Add a new parameter mapping
        
        Parameters
        ----------
        original : str
            Original parameter name
        standardized : str
            Standardized parameter name
        """
        default_mappings.add_parameter_mapping(original, standardized)
    
    # Unit Management Methods
    
    def standardize_unit(self, unit_str: str) -> str:
        """
        Standardize a unit string using Pint
        
        Parameters
        ----------
        unit_str : str
            Unit string to standardize
            
        Returns
        -------
        str
            Standardized unit string
        """
        return unit_manager.standardize_unit(unit_str)
    
    def convert_values(self, values: Union[float, List[float], pd.Series], 
                      from_unit: str, to_unit: str) -> Union[float, List[float], pd.Series]:
        """
        Convert values from one unit to another
        
        Parameters
        ----------
        values : Union[float, List[float], pd.Series]
            Value(s) to convert
        from_unit : str
            Source unit
        to_unit : str
            Target unit
            
        Returns
        -------
        Union[float, List[float], pd.Series]
            Converted value(s)
            
        Raises
        ------
        ValueError
            If units are incompatible or cannot be parsed
        """
        if isinstance(values, (int, float)):
            return unit_manager.convert_value(values, from_unit, to_unit)
        elif isinstance(values, list):
            return [unit_manager.convert_value(v, from_unit, to_unit) for v in values]
        elif isinstance(values, pd.Series):
            return values.apply(lambda x: unit_manager.convert_value(x, from_unit, to_unit))
        else:
            raise ValueError(f"Unsupported value type: {type(values)}")
    
    def are_units_compatible(self, unit1: str, unit2: str) -> bool:
        """
        Check if two units are dimensionally compatible
        
        Parameters
        ----------
        unit1 : str
            First unit
        unit2 : str
            Second unit
            
        Returns
        -------
        bool
            True if units are compatible for conversion
        """
        return unit_manager.are_compatible(unit1, unit2)
    
    def get_unit_dimensionality(self, unit_str: str) -> str:
        """
        Get the dimensionality of a unit
        
        Parameters
        ----------
        unit_str : str
            Unit string
            
        Returns
        -------
        str
            Dimensionality (e.g., '[mass] / [length] ** 3')
        """
        return unit_manager.get_unit_dimensionality(unit_str)
    
    def suggest_compatible_units(self, unit_str: str) -> List[str]:
        """
        Suggest compatible units for a given unit
        
        Parameters
        ----------
        unit_str : str
            Unit string
            
        Returns
        -------
        List[str]
            List of compatible units
        """
        dimensionality = unit_manager.get_unit_dimensionality(unit_str)
        return unit_manager.suggest_common_units(dimensionality)
    
    def convert_parameter_data(self, data: pd.DataFrame, target_unit: str) -> pd.DataFrame:
        """
        Convert parameter data to a target unit
        
        Parameters
        ----------
        data : pd.DataFrame
            Parameter data with 'value' and 'unit' columns
        target_unit : str
            Target unit for conversion
            
        Returns
        -------
        pd.DataFrame
            Data with converted values and updated unit column
            
        Raises
        ------
        ValueError
            If data doesn't have required columns or units are incompatible
        """
        if 'value' not in data.columns:
            raise ValueError("Data must contain 'value' column")
        
        if 'unit' not in data.columns:
            raise ValueError("Data must contain 'unit' column")
        
        # Create a copy to avoid modifying original data
        result = data.copy()
        
        # Get the source unit (assuming all rows have the same unit)
        source_unit = data['unit'].iloc[0]
        
        # Check compatibility
        if not self.are_units_compatible(source_unit, target_unit):
            raise ValueError(f"Cannot convert from {source_unit} to {target_unit}: units are not compatible")
        
        # Convert values
        result['value'] = self.convert_values(data['value'], source_unit, target_unit)
        result['unit'] = target_unit
        
        return result
    
    def calculate_mass_flow_advanced(self, concentration_data: pd.DataFrame, 
                                   flow_data: pd.DataFrame,
                                   concentration_unit: Optional[str] = None,
                                   flow_unit: Optional[str] = None,
                                   target_unit: str = 'kg/h') -> pd.DataFrame:
        """
        Calculate mass flow with explicit unit handling
        
        Parameters
        ----------
        concentration_data : pd.DataFrame
            Concentration data
        flow_data : pd.DataFrame
            Flow data
        concentration_unit : str, optional
            Unit for concentration (if not in data)
        flow_unit : str, optional
            Unit for flow (if not in data)
        target_unit : str
            Target unit for mass flow
            
        Returns
        -------
        pd.DataFrame
            Mass flow calculations with proper unit handling
        """
        # Extract units from data or use provided units
        conc_unit = concentration_unit or concentration_data.get('unit', pd.Series()).iloc[0] if len(concentration_data) > 0 else 'mg/L'
        f_unit = flow_unit or flow_data.get('unit', pd.Series()).iloc[0] if len(flow_data) > 0 else 'm³/h'
        
        # Use the mass flow calculator with explicit units
        return self.massflow_calculator.apply_mass_flow_calculation(
            concentration_data, flow_data, target_unit
        )
    
    def get_parameter_units_summary(self) -> pd.DataFrame:
        """
        Get a summary of all parameter units in the database
        
        Returns
        -------
        pd.DataFrame
            Summary of parameters with unit information
        """
        # Get all parameters
        parameters = self.get_parameters()
        
        if parameters.empty:
            return pd.DataFrame()
        
        # Add unit metadata for each parameter
        unit_info = []
        for _, param in parameters.iterrows():
            unit = param.get('unit', '')
            try:
                unit_info.append({
                    'parameter_code': param.get('code', ''),
                    'parameter_name': param.get('name', ''),
                    'unit': unit,
                    'unit_standardized': unit_manager.standardize_unit(unit),
                    'dimensionality': unit_manager.get_unit_dimensionality(unit),
                    'compatible_units': ', '.join(unit_manager.suggest_common_units(
                        unit_manager.get_unit_dimensionality(unit)
                    ))
                })
            except Exception as e:
                logger.warning(f"Could not process unit for parameter {param.get('code', '')}: {e}")
                unit_info.append({
                    'parameter_code': param.get('code', ''),
                    'parameter_name': param.get('name', ''),
                    'unit': unit,
                    'unit_standardized': unit,
                    'dimensionality': 'unknown',
                    'compatible_units': ''
                })
        
        return pd.DataFrame(unit_info) 