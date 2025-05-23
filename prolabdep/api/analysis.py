"""
Analysis API module
"""
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import matplotlib.pyplot as plt

from prolabdep.analytics.timeseries import TimeSeriesAnalyzer
from prolabdep.analytics.statistics import StatisticsAnalyzer
from prolabdep.analytics.massflow import MassFlowCalculator
from prolabdep.analytics.trends import TrendAnalyzer


class AnalysisAPI:
    """
    Analysis API for ProlabDep
    
    This class provides methods for data analysis.
    """
    
    def __init__(self):
        """Initialize the analysis API"""
        self.timeseries_analyzer = TimeSeriesAnalyzer()
        self.statistics_analyzer = StatisticsAnalyzer()
        self.massflow_calculator = MassFlowCalculator()
        self.trend_analyzer = TrendAnalyzer()
    
    def calculate_statistics(self, data: pd.DataFrame) -> Dict[str, float]:
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
                          flow_data: pd.DataFrame,
                          output_unit: str = 'kg/h') -> pd.DataFrame:
        """
        Calculate mass flow from concentration and flow
        
        Parameters
        ----------
        concentration : pd.DataFrame
            Concentration data
        flow_data : pd.DataFrame
            Flow data
        output_unit : str
            Output unit
            
        Returns
        -------
        pd.DataFrame
            Mass flow calculations
        """
        return self.massflow_calculator.calculate_mass_flow(
            concentration, flow_data, output_unit
        )
    
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
    
    def compare_sites(self, data_list: List[pd.DataFrame], 
                     site_names: List[str]) -> Dict[str, Any]:
        """
        Compare data from multiple sites
        
        Parameters
        ----------
        data_list : List[pd.DataFrame]
            List of dataframes for different sites
        site_names : List[str]
            Names of the sites
            
        Returns
        -------
        Dict[str, Any]
            Dictionary with comparison results
        """
        return self.statistics_analyzer.compare_sites(data_list, site_names)
    
    def plot_time_series(self, data: pd.DataFrame, 
                       parameter_name: Optional[str] = None,
                       title: Optional[str] = None,
                       include_trend: bool = True) -> plt.Figure:
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
            
        Returns
        -------
        plt.Figure
            Matplotlib figure
        """
        return self.timeseries_analyzer.plot_time_series(
            data, 
            parameter_name=parameter_name,
            title=title,
            include_trend=include_trend
        )
    
    # Alias for backward compatibility
    plot_timeseries = plot_time_series
    
    def plot_comparison(self, data_list: List[pd.DataFrame], 
                       labels: List[str],
                       title: Optional[str] = None) -> plt.Figure:
        """
        Create a comparison plot
        
        Parameters
        ----------
        data_list : List[pd.DataFrame]
            List of dataframes to compare
        labels : List[str]
            Labels for each dataset
        title : str, optional
            Plot title
            
        Returns
        -------
        plt.Figure
            Matplotlib figure
        """
        return self.timeseries_analyzer.plot_comparison(
            data_list, labels, title=title
        )
    
    def plot_box(self, data: pd.DataFrame, 
                group_by: Optional[str] = None,
                title: Optional[str] = None) -> plt.Figure:
        """
        Create a box plot
        
        Parameters
        ----------
        data : pd.DataFrame
            Data to plot
        group_by : str, optional
            Column to group by
        title : str, optional
            Plot title
            
        Returns
        -------
        plt.Figure
            Matplotlib figure
        """
        return self.timeseries_analyzer.plot_box(
            data, group_by=group_by, title=title
        ) 