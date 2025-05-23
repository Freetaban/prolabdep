"""
Time series analysis module for wastewater treatment plant data
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Union, Optional, Any
import logging

logger = logging.getLogger(__name__)


class TimeSeriesAnalyzer:
    """
    Time series analysis for wastewater treatment plant data
    
    This class provides methods for analyzing time series data,
    including trend analysis, statistics, and resampling.
    """
    
    def __init__(self):
        """Initialize time series analyzer"""
        pass
    
    def resample(self, data: pd.DataFrame, frequency: str = 'D', 
                method: str = 'mean') -> pd.DataFrame:
        """
        Resample time series data to a different frequency
        
        Parameters
        ----------
        data : pd.DataFrame
            Data containing a 'date' column and a 'value' column
        frequency : str
            Pandas frequency string (e.g., 'D' for daily, 'W' for weekly)
        method : str
            Aggregation method ('mean', 'median', 'min', 'max', 'sum')
            
        Returns
        -------
        pd.DataFrame
            Resampled data
        """
        # Ensure data has date column
        if 'date' not in data.columns:
            raise ValueError("Data must contain a 'date' column")
        
        # Copy data to avoid modifying original
        df = data.copy()
        
        # Set date as index
        df = df.set_index('date')
        
        # Select aggregation method
        if method == 'mean':
            agg_func = np.mean
        elif method == 'median':
            agg_func = np.median
        elif method == 'min':
            agg_func = np.min
        elif method == 'max':
            agg_func = np.max
        elif method == 'sum':
            agg_func = np.sum
        else:
            raise ValueError(f"Unknown aggregation method: {method}")
        
        # Resample numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        # Group by frequency and aggregate
        result = df[numeric_cols].resample(frequency).agg(agg_func)
        
        # Add non-numeric columns with mode aggregation
        categorical_cols = df.select_dtypes(exclude=[np.number]).columns
        if not categorical_cols.empty:
            for col in categorical_cols:
                # Use most common value for categorical data
                result[col] = df[col].resample(frequency).apply(
                    lambda x: x.mode()[0] if not x.empty and len(x.mode()) > 0 else None
                )
        
        # Reset index for consistent return format
        result = result.reset_index()
        
        return result
    
    def plot_time_series(self, data: pd.DataFrame, 
                       parameter_name: Optional[str] = None,
                       title: Optional[str] = None,
                       include_trend: bool = True) -> plt.Figure:
        """
        Create a time series plot
        
        Parameters
        ----------
        data : pd.DataFrame
            Time series data with 'date' and 'value' columns
        parameter_name : str, optional
            Parameter name for labels
        title : str, optional
            Plot title
        include_trend : bool
            Whether to include trend line
            
        Returns
        -------
        plt.Figure
            Matplotlib figure
        """
        if 'date' not in data.columns or 'value' not in data.columns:
            raise ValueError("Data must contain 'date' and 'value' columns")
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot data
        ax.plot(data['date'], data['value'], 'o-', label='Measurements')
        
        # Add trend line if requested
        if include_trend and len(data) > 1:
            try:
                # Convert dates to numeric for regression
                x = pd.to_numeric(pd.to_datetime(data['date']))
                y = data['value']
                
                # Simple linear regression
                z = np.polyfit(x, y, 1)
                p = np.poly1d(z)
                
                # Generate x values for trend line
                x_dates = pd.to_datetime(data['date'])
                x_trend = pd.date_range(min(x_dates), max(x_dates), periods=100)
                x_numeric = pd.to_numeric(x_trend)
                
                # Plot trend line
                ax.plot(x_trend, p(x_numeric), 'r--', label='Trend')
                
                # Add trend equation to legend
                slope = z[0]
                ax.legend(title=f"Trend: {'↑' if slope > 0 else '↓' if slope < 0 else '→'}")
            except Exception as e:
                logger.warning(f"Could not calculate trend line: {str(e)}")
        
        # Set labels and title
        if parameter_name:
            unit = data['unit'].iloc[0] if 'unit' in data.columns else ''
            if unit:
                ax.set_ylabel(f"{parameter_name} ({unit})")
            else:
                ax.set_ylabel(parameter_name)
        else:
            ax.set_ylabel('Value')
        
        ax.set_xlabel('Date')
        
        if title:
            ax.set_title(title)
        elif parameter_name:
            ax.set_title(f"{parameter_name} Time Series")
        else:
            ax.set_title("Time Series")
        
        # Format x-axis
        fig.autofmt_xdate()
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        return fig
    
    # Alias for backward compatibility
    plot_timeseries = plot_time_series
    
    def plot_comparison(self, data_list: List[pd.DataFrame], 
                       labels: List[str],
                       title: Optional[str] = None) -> plt.Figure:
        """
        Create a comparison plot of multiple time series
        
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
        if len(data_list) != len(labels):
            raise ValueError("Number of datasets and labels must match")
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot each dataset
        for i, data in enumerate(data_list):
            if 'date' not in data.columns or 'value' not in data.columns:
                raise ValueError(f"Dataset {i} must contain 'date' and 'value' columns")
            
            ax.plot(data['date'], data['value'], 'o-', label=labels[i])
        
        # Set labels and title
        ax.set_ylabel('Value')
        ax.set_xlabel('Date')
        
        if title:
            ax.set_title(title)
        else:
            ax.set_title("Comparison Plot")
        
        # Format x-axis
        fig.autofmt_xdate()
        
        # Add grid and legend
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        return fig
    
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
        if 'value' not in data.columns:
            raise ValueError("Data must contain a 'value' column")
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create box plot
        if group_by and group_by in data.columns:
            # Group data
            grouped = data.groupby(group_by)
            
            # Extract values for each group
            values = [group['value'].values for _, group in grouped]
            labels = list(grouped.groups.keys())
            
            # Create box plot
            ax.boxplot(values, labels=labels)
            
            # Set x-label
            ax.set_xlabel(group_by)
        else:
            # Simple box plot without grouping
            ax.boxplot(data['value'])
        
        # Set labels and title
        parameter_name = data['parameter_name'].iloc[0] if 'parameter_name' in data.columns else 'Value'
        unit = data['unit'].iloc[0] if 'unit' in data.columns else ''
        
        if unit:
            ax.set_ylabel(f"{parameter_name} ({unit})")
        else:
            ax.set_ylabel(parameter_name)
        
        if title:
            ax.set_title(title)
        else:
            ax.set_title(f"{parameter_name} Distribution")
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        return fig 