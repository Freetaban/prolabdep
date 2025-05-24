"""
Time series analysis module for wastewater treatment plant data
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Union, Optional, Any
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class TimeSeriesAnalyzer:
    """
    Time series analysis for wastewater treatment plant data
    
    This class provides methods for analyzing time series data,
    including trend analysis, statistics, and resampling.
    """
    
    def __init__(self):
        """Initialize time series analyzer"""
        # Set matplotlib backend for better performance
        plt.rcParams['figure.max_open_warning'] = 50
        plt.rcParams['agg.path.chunksize'] = 10000
    
    def resample(self, data: pd.DataFrame, frequency: str = 'D', 
                method: str = 'mean') -> pd.DataFrame:
        """
        Resample time series data to a different frequency with optimized performance
        
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
        
        # Ensure date column is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        
        # Set date as index
        df = df.set_index('date')
        
        # Validate aggregation method
        valid_methods = ['mean', 'median', 'min', 'max', 'sum', 'std', 'count']
        if method not in valid_methods:
            raise ValueError(f"Unknown aggregation method: {method}. Valid methods: {valid_methods}")
        
        # Select numeric columns for aggregation
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(exclude=[np.number]).columns
        
        # Prepare result dataframe
        result_parts = []
        
        # Resample numeric columns
        if not numeric_cols.empty:
            numeric_resampled = df[numeric_cols].resample(frequency).agg(method)
            result_parts.append(numeric_resampled)
        
        # Handle categorical columns separately
        if not categorical_cols.empty:
            categorical_resampled = df[categorical_cols].resample(frequency).agg(
                lambda x: x.mode().iloc[0] if not x.empty and not x.mode().empty else None
            )
            result_parts.append(categorical_resampled)
        
        # Combine results
        if result_parts:
            result = pd.concat(result_parts, axis=1)
        else:
            result = pd.DataFrame()
        
        # Reset index for consistent return format
        result = result.reset_index()
        
        return result
    
    def plot_time_series(self, data: pd.DataFrame, 
                       parameter_name: Optional[str] = None,
                       title: Optional[str] = None,
                       include_trend: bool = True,
                       figsize: tuple = (12, 6),
                       style: str = 'seaborn-v0_8') -> plt.Figure:
        """
        Create an optimized time series plot
        
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
        figsize : tuple
            Figure size (width, height)
        style : str
            Plot style
            
        Returns
        -------
        plt.Figure
            Matplotlib figure
        """
        if 'date' not in data.columns or 'value' not in data.columns:
            raise ValueError("Data must contain 'date' and 'value' columns")
        
        # Remove rows with NaN values for better plotting
        clean_data = data.dropna(subset=['date', 'value'])
        
        if clean_data.empty:
            raise ValueError("No valid data points to plot")
        
        # Set plot style
        with plt.style.context(style):
            # Create figure with optimized settings
            fig, ax = plt.subplots(figsize=figsize, dpi=100)
            
            # Convert dates to datetime if needed
            dates = pd.to_datetime(clean_data['date'])
            values = clean_data['value'].astype(float)
            
            # Plot data with optimized parameters
            line = ax.plot(dates, values, 'o-', 
                          linewidth=1.5, 
                          markersize=4, 
                          alpha=0.8,
                          label='Measurements')
            
            # Add trend line if requested and feasible
            if include_trend and len(clean_data) > 1:
                try:
                    self._add_trend_line(ax, dates, values)
                except Exception as e:
                    logger.warning(f"Could not calculate trend line: {str(e)}")
            
            # Optimize axis formatting
            self._format_plot(ax, parameter_name, title, clean_data)
            
            # Tight layout for better spacing
            fig.tight_layout()
            
            return fig
    
    def _add_trend_line(self, ax: plt.Axes, dates: pd.Series, values: pd.Series) -> None:
        """Add trend line to plot with optimized calculation"""
        # Convert dates to numeric for regression
        x_numeric = dates.astype(np.int64) // 10**9  # Convert to seconds
        
        # Use numpy for faster polynomial fitting
        coeffs = np.polyfit(x_numeric, values, 1)
        trend_line = np.poly1d(coeffs)
        
        # Generate smooth trend line
        x_trend = np.linspace(x_numeric.min(), x_numeric.max(), 100)
        dates_trend = pd.to_datetime(x_trend * 10**9)
        y_trend = trend_line(x_trend)
        
        # Plot trend line
        ax.plot(dates_trend, y_trend, 'r--', 
               linewidth=2, alpha=0.7, label='Trend')
        
        # Add trend info to legend
        slope = coeffs[0]
        trend_direction = '↑' if slope > 0 else '↓' if slope < 0 else '→'
        ax.legend(title=f"Trend: {trend_direction}")
    
    def _format_plot(self, ax: plt.Axes, parameter_name: Optional[str], 
                    title: Optional[str], data: pd.DataFrame) -> None:
        """Format plot with optimized settings"""
        # Set labels
        if parameter_name:
            unit = data['unit'].iloc[0] if 'unit' in data.columns and not data['unit'].empty else ''
            ylabel = f"{parameter_name} ({unit})" if unit else parameter_name
        else:
            ylabel = 'Value'
        
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_xlabel('Date', fontsize=12)
        
        # Set title
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        elif parameter_name:
            ax.set_title(f"{parameter_name} Time Series", fontsize=14)
        else:
            ax.set_title("Time Series", fontsize=14)
        
        # Format axes
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.tick_params(axis='both', which='major', labelsize=10)
        
        # Auto-format date axis
        fig = ax.get_figure()
        fig.autofmt_xdate()
        
        # Add statistics text box if data is available
        if len(data) > 0:
            self._add_stats_box(ax, data['value'])
    
    def _add_stats_box(self, ax: plt.Axes, values: pd.Series) -> None:
        """Add statistics text box to plot"""
        stats = {
            'Count': len(values),
            'Mean': f"{values.mean():.2f}",
            'Std': f"{values.std():.2f}",
            'Min': f"{values.min():.2f}",
            'Max': f"{values.max():.2f}"
        }
        
        stats_text = '\n'.join([f"{k}: {v}" for k, v in stats.items()])
        
        # Add text box
        ax.text(0.02, 0.98, stats_text, 
               transform=ax.transAxes, 
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
               fontsize=9)
    
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