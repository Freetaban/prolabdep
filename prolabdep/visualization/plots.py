"""
Visualization tools for creating plots and charts
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Union, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class Visualizer:
    """
    Visualization tools for wastewater treatment plant data
    
    This class provides methods for creating various types of plots
    and visualizations from processed data.
    """
    
    def __init__(self, style: str = 'seaborn-v0_8-whitegrid'):
        """
        Initialize visualizer
        
        Parameters
        ----------
        style : str
            Matplotlib style to use
        """
        self.style = style
        plt.style.use(self.style)
    
    def plot_time_series(self, data: pd.DataFrame, y_column: str = 'value', 
                        x_column: str = 'date', parameter_name: str = None,
                        title: str = None, ylabel: str = None, 
                        figsize: Tuple[int, int] = (10, 6),
                        include_trend: bool = True) -> plt.Figure:
        """
        Create a time series plot
        
        Parameters
        ----------
        data : pd.DataFrame
            Data to plot
        y_column : str
            Column to use for y-axis values
        x_column : str
            Column to use for x-axis values (should be a date)
        parameter_name : str, optional
            Name of the parameter being plotted
        title : str, optional
            Plot title
        ylabel : str, optional
            Y-axis label
        figsize : Tuple[int, int], optional
            Figure size (width, height) in inches
        include_trend : bool
            Whether to include trend line
            
        Returns
        -------
        plt.Figure
            Matplotlib figure object
        """
        # Check if data exists
        if data.empty:
            logger.warning("No data to plot")
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "No data available", ha='center', va='center')
            plt.tight_layout()
            return fig
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot time series
        ax.plot(data[x_column], data[y_column], 'o-', label='Data')
        
        # Add trend line if requested
        if include_trend and len(data) > 1:
            try:
                # Convert dates to numeric for regression
                x_numeric = pd.to_numeric(pd.to_datetime(data[x_column]))
                y = data[y_column]
                
                # Simple linear regression
                slope, intercept = np.polyfit(x_numeric, y, 1)
                
                # Create trend line
                x_range = np.linspace(x_numeric.min(), x_numeric.max(), 100)
                y_trend = slope * x_range + intercept
                
                # Convert x back to datetime for plotting
                x_trend = pd.to_datetime(x_range)
                
                # Plot trend line
                ax.plot(x_trend, y_trend, 'r--', label='Trend')
            except Exception as e:
                logger.warning(f"Could not calculate trend: {str(e)}")
        
        # Set title and labels
        if title:
            ax.set_title(title)
        else:
            if parameter_name:
                ax.set_title(f"{parameter_name} Time Series")
            else:
                ax.set_title("Time Series")
        
        ax.set_xlabel("Date")
        
        if ylabel:
            ax.set_ylabel(ylabel)
        else:
            if 'unit' in data.columns and not data['unit'].empty:
                unit = data['unit'].iloc[0]
                ax.set_ylabel(f"Value ({unit})")
            else:
                ax.set_ylabel("Value")
        
        # Add grid and legend
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Format x-axis dates
        fig.autofmt_xdate()
        
        # Adjust layout
        plt.tight_layout()
        
        return fig
    
    # Alias for backward compatibility
    plot_timeseries = plot_time_series
    
    def plot_box(self, data: pd.DataFrame, column: str = 'value',
                group_by: str = None, title: str = None,
                figsize: Tuple[int, int] = (10, 6)) -> plt.Figure:
        """
        Create a box plot
        
        Parameters
        ----------
        data : pd.DataFrame
            Data to plot
        column : str
            Column to use for values
        group_by : str, optional
            Column to group by
        title : str, optional
            Plot title
        figsize : Tuple[int, int], optional
            Figure size (width, height) in inches
            
        Returns
        -------
        plt.Figure
            Matplotlib figure object
        """
        # Check if data exists
        if data.empty:
            logger.warning("No data to plot")
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "No data available", ha='center', va='center')
            plt.tight_layout()
            return fig
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create box plot
        if group_by and group_by in data.columns:
            # Group data
            grouped_data = [group[column].dropna() for _, group in data.groupby(group_by)]
            labels = data[group_by].unique()
            
            # Plot
            ax.boxplot(grouped_data, labels=labels)
            ax.set_xlabel(group_by)
        else:
            # Simple box plot
            ax.boxplot(data[column].dropna())
        
        # Set title
        if title:
            ax.set_title(title)
        else:
            ax.set_title("Box Plot")
        
        # Set y-axis label
        if 'unit' in data.columns and not data['unit'].empty:
            unit = data['unit'].iloc[0]
            ax.set_ylabel(f"Value ({unit})")
        else:
            ax.set_ylabel("Value")
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Adjust layout
        plt.tight_layout()
        
        return fig
    
    def plot_histogram(self, data: pd.DataFrame, column: str = 'value',
                      bins: int = 10, title: str = None,
                      figsize: Tuple[int, int] = (10, 6)) -> plt.Figure:
        """
        Create a histogram
        
        Parameters
        ----------
        data : pd.DataFrame
            Data to plot
        column : str
            Column to use for values
        bins : int
            Number of bins
        title : str, optional
            Plot title
        figsize : Tuple[int, int], optional
            Figure size (width, height) in inches
            
        Returns
        -------
        plt.Figure
            Matplotlib figure object
        """
        # Check if data exists
        if data.empty:
            logger.warning("No data to plot")
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "No data available", ha='center', va='center')
            plt.tight_layout()
            return fig
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create histogram
        ax.hist(data[column].dropna(), bins=bins, alpha=0.7)
        
        # Add normal distribution curve
        if len(data[column].dropna()) > 1:
            try:
                # Calculate mean and standard deviation
                mean = data[column].mean()
                std = data[column].std()
                
                # Create x values for the normal curve
                x = np.linspace(data[column].min(), data[column].max(), 100)
                
                # Create normal distribution values
                y = ((1 / (np.sqrt(2 * np.pi) * std)) *
                     np.exp(-0.5 * ((x - mean) / std) ** 2))
                
                # Scale to match histogram
                hist_heights, _ = np.histogram(data[column].dropna(), bins=bins)
                y = y * (hist_heights.max() / y.max())
                
                # Plot normal curve
                ax.plot(x, y, 'r--', linewidth=2)
            except Exception as e:
                logger.warning(f"Could not plot normal distribution: {str(e)}")
        
        # Set title
        if title:
            ax.set_title(title)
        else:
            ax.set_title("Histogram")
        
        # Set axis labels
        if 'unit' in data.columns and not data['unit'].empty:
            unit = data['unit'].iloc[0]
            ax.set_xlabel(f"Value ({unit})")
        else:
            ax.set_xlabel("Value")
        
        ax.set_ylabel("Frequency")
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Adjust layout
        plt.tight_layout()
        
        return fig
    
    def plot_comparison(self, datasets: List[pd.DataFrame], labels: List[str],
                       y_column: str = 'value', x_column: str = 'date',
                       title: str = None, ylabel: str = None,
                       figsize: Tuple[int, int] = (12, 7)) -> plt.Figure:
        """
        Create a comparison plot of multiple datasets
        
        Parameters
        ----------
        datasets : List[pd.DataFrame]
            List of dataframes to plot
        labels : List[str]
            Labels for each dataset
        y_column : str
            Column to use for y-axis values
        x_column : str
            Column to use for x-axis values (should be a date)
        title : str, optional
            Plot title
        ylabel : str, optional
            Y-axis label
        figsize : Tuple[int, int], optional
            Figure size (width, height) in inches
            
        Returns
        -------
        plt.Figure
            Matplotlib figure object
        """
        # Check if data exists
        if not datasets or all(df.empty for df in datasets):
            logger.warning("No data to plot")
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "No data available", ha='center', va='center')
            plt.tight_layout()
            return fig
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot each dataset
        markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*']
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        for i, (data, label) in enumerate(zip(datasets, labels)):
            if not data.empty:
                marker = markers[i % len(markers)]
                color = colors[i % len(colors)]
                ax.plot(data[x_column], data[y_column], marker=marker, color=color, 
                       linestyle='-', label=label, alpha=0.7)
        
        # Set title
        if title:
            ax.set_title(title)
        else:
            ax.set_title("Comparison Plot")
        
        # Set axis labels
        ax.set_xlabel("Date")
        
        if ylabel:
            ax.set_ylabel(ylabel)
        else:
            units = [df['unit'].iloc[0] if 'unit' in df.columns and not df['unit'].empty else None
                   for df in datasets if not df.empty]
            
            if all(u == units[0] for u in units) and units[0] is not None:
                ax.set_ylabel(f"Value ({units[0]})")
            else:
                ax.set_ylabel("Value")
        
        # Add grid and legend
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Format x-axis dates
        fig.autofmt_xdate()
        
        # Adjust layout
        plt.tight_layout()
        
        return fig
    
    def save_figure(self, fig: plt.Figure, filename: str, dpi: int = 300) -> None:
        """
        Save figure to file
        
        Parameters
        ----------
        fig : plt.Figure
            Matplotlib figure to save
        filename : str
            Output filename
        dpi : int
            Resolution in dots per inch
        """
        try:
            fig.savefig(filename, dpi=dpi, bbox_inches='tight')
            logger.info(f"Figure saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving figure: {str(e)}")
            raise 