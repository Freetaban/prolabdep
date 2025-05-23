"""
Trend analysis module for wastewater treatment plant data
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Any
import logging
from scipy import stats

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """
    Trend analyzer for wastewater treatment plant data
    
    This class provides methods for detecting and analyzing trends
    in time series data.
    """
    
    def __init__(self):
        """Initialize trend analyzer"""
        pass
    
    def detect_trends(self, data: pd.DataFrame, 
                     window: int = 5,
                     threshold: float = 0.05) -> Dict[str, Any]:
        """
        Detect trends in time series data
        
        Parameters
        ----------
        data : pd.DataFrame
            Data containing 'date' and 'value' columns
        window : int
            Window size for trend detection
        threshold : float
            Significance threshold
            
        Returns
        -------
        Dict[str, Any]
            Dictionary with trend analysis results
        """
        if 'date' not in data.columns or 'value' not in data.columns:
            raise ValueError("Data must contain 'date' and 'value' columns")
        
        if len(data) < 3:
            return {
                'has_trend': False,
                'trend_type': None,
                'p_value': None,
                'slope': None,
                'confidence': None
            }
        
        # Ensure data is sorted by date
        df = data.sort_values('date').copy()
        
        # Convert dates to numeric for regression
        x = pd.to_numeric(pd.to_datetime(df['date']))
        y = df['value']
        
        # Normalize x to avoid numerical issues
        x_norm = (x - x.min()) / (x.max() - x.min())
        
        # Calculate trend with linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_norm, y)
        
        # Calculate moving average
        df['rolling_mean'] = df['value'].rolling(window=window, min_periods=1).mean()
        
        # Calculate rate of change
        df['rate_of_change'] = df['value'].pct_change(periods=window)
        
        # Determine trend type
        has_trend = p_value < threshold
        trend_type = 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
        confidence = 1 - p_value
        
        # Calculate trend periods
        trend_periods = self._identify_trend_periods(df, window)
        
        return {
            'has_trend': has_trend,
            'trend_type': trend_type if has_trend else 'no significant trend',
            'p_value': p_value,
            'slope': slope,
            'confidence': confidence,
            'r_squared': r_value ** 2,
            'std_error': std_err,
            'trend_periods': trend_periods
        }
    
    def _identify_trend_periods(self, data: pd.DataFrame, window: int) -> List[Dict[str, Any]]:
        """
        Identify periods of consistent trends
        
        Parameters
        ----------
        data : pd.DataFrame
            Data with 'date', 'value', and 'rate_of_change' columns
        window : int
            Window size for trend detection
            
        Returns
        -------
        List[Dict[str, Any]]
            List of trend periods
        """
        if len(data) < window * 2:
            return []
        
        # Initialize variables
        trend_periods = []
        current_trend = None
        start_idx = 0
        
        # Function to determine trend direction
        def get_trend_direction(rate):
            if pd.isna(rate):
                return None
            if rate > 0.05:  # 5% increase
                return 'increasing'
            elif rate < -0.05:  # 5% decrease
                return 'decreasing'
            else:
                return 'stable'
        
        # Iterate through data
        for i in range(window, len(data)):
            trend = get_trend_direction(data['rate_of_change'].iloc[i])
            
            if trend is None:
                continue
                
            if current_trend is None:
                # Start new trend
                current_trend = trend
                start_idx = i - window
            elif trend != current_trend:
                # End current trend and start new one
                if i - start_idx >= window:  # Only record if trend lasted minimum window
                    trend_periods.append({
                        'start_date': data['date'].iloc[start_idx],
                        'end_date': data['date'].iloc[i-1],
                        'trend': current_trend,
                        'duration': i - start_idx,
                        'start_value': data['value'].iloc[start_idx],
                        'end_value': data['value'].iloc[i-1],
                        'change': data['value'].iloc[i-1] - data['value'].iloc[start_idx],
                        'percent_change': (data['value'].iloc[i-1] / data['value'].iloc[start_idx] - 1) * 100 if data['value'].iloc[start_idx] != 0 else None
                    })
                
                current_trend = trend
                start_idx = i - window
        
        # Add final trend period if it exists
        if current_trend is not None and len(data) - start_idx >= window:
            trend_periods.append({
                'start_date': data['date'].iloc[start_idx],
                'end_date': data['date'].iloc[-1],
                'trend': current_trend,
                'duration': len(data) - start_idx,
                'start_value': data['value'].iloc[start_idx],
                'end_value': data['value'].iloc[-1],
                'change': data['value'].iloc[-1] - data['value'].iloc[start_idx],
                'percent_change': (data['value'].iloc[-1] / data['value'].iloc[start_idx] - 1) * 100 if data['value'].iloc[start_idx] != 0 else None
            })
        
        return trend_periods
    
    def seasonal_decomposition(self, data: pd.DataFrame,
                              period: int = 12,
                              model: str = 'additive') -> Dict[str, pd.DataFrame]:
        """
        Perform seasonal decomposition of time series
        
        Parameters
        ----------
        data : pd.DataFrame
            Data containing 'date' and 'value' columns
        period : int
            Period for seasonal decomposition (e.g., 12 for monthly data with yearly seasonality)
        model : str
            Model type ('additive' or 'multiplicative')
            
        Returns
        -------
        Dict[str, pd.DataFrame]
            Dictionary with decomposition results
        """
        try:
            from statsmodels.tsa.seasonal import seasonal_decompose
        except ImportError:
            logger.error("statsmodels package is required for seasonal decomposition")
            raise ImportError("statsmodels package is required for seasonal decomposition")
        
        if 'date' not in data.columns or 'value' not in data.columns:
            raise ValueError("Data must contain 'date' and 'value' columns")
        
        if len(data) < period * 2:
            raise ValueError(f"Data length ({len(data)}) must be at least twice the period ({period})")
        
        # Ensure data is sorted by date
        df = data.sort_values('date').copy()
        
        # Set date as index
        df = df.set_index('date')
        
        # Perform decomposition
        result = seasonal_decompose(df['value'], model=model, period=period)
        
        # Convert results to dataframes
        trend = result.trend.reset_index()
        seasonal = result.seasonal.reset_index()
        residual = result.resid.reset_index()
        
        return {
            'trend': trend,
            'seasonal': seasonal,
            'residual': residual
        } 