"""
Main client interface for ProlabDep
"""
import os
import uuid
from typing import Dict, List, Optional, Union, Any
import pandas as pd
from datetime import datetime

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
        
        # Initialize processors
        self.csv_processor = CSVProcessor(self.config)
        self.excel_processor = ExcelProcessor(self.config)
        
        # Initialize analyzers
        self.timeseries_analyzer = TimeSeriesAnalyzer()
        self.statistics_analyzer = StatisticsAnalyzer()
        self.massflow_calculator = MassFlowCalculator()
        self.trend_analyzer = TrendAnalyzer()
        
        # Initialize exporters
        self.excel_exporter = ExcelExporter()
        self.csv_exporter = CSVExporter()
        self.pdf_exporter = PDFExporter()
        
        # Data cache
        self._data_cache = {}
    
    def import_data(self, file_path: str, name: Optional[str] = None) -> str:
        """
        Import data from a file
        
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
        
        # Process data based on file type
        if file_extension in ['.csv']:
            data_dict = self.csv_processor.process(file_path)
        elif file_extension in ['.xlsx', '.xls']:
            data_dict = self.excel_processor.process(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        # Store data in database
        self.db.store_data(data_dict)
        
        # Cache dataset information
        self._data_cache[data_id] = {
            'name': name or os.path.basename(file_path),
            'file_path': file_path,
            'import_date': datetime.now(),
            'file_type': file_extension,
        }
        
        return data_id
    
    def get_parameters(self, data_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get parameters from a dataset
        
        Parameters
        ----------
        data_id : str, optional
            Dataset identifier (if None, returns all parameters)
            
        Returns
        -------
        pd.DataFrame
            Dataframe of parameters
        """
        # Retrieve from database
        return self.db.get_parameters()
    
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
                                date_to: Optional[Union[str, datetime]] = None) -> pd.DataFrame:
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
        
        # Retrieve from database
        return self.db.get_parameter_data(parameter, filter_criteria)
    
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