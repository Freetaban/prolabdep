"""
Statistics analysis module for wastewater treatment plant data
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Any
import logging

logger = logging.getLogger(__name__)


class StatisticsAnalyzer:
    """
    Statistics analyzer for wastewater treatment plant data
    
    This class provides methods for calculating statistical metrics
    on wastewater treatment plant data.
    """
    
    def __init__(self):
        """Initialize statistics analyzer"""
        pass
    
    def calculate_statistics(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate basic statistics for time series data
        
        Parameters
        ----------
        data : pd.DataFrame
            Data containing a 'value' column
            
        Returns
        -------
        Dict[str, float]
            Dictionary with statistics
        """
        if 'value' not in data.columns:
            raise ValueError("Data must contain a 'value' column")
        
        # Calculate statistics
        stats = {
            'mean': data['value'].mean(),
            'median': data['value'].median(),
            'std': data['value'].std(),
            'min': data['value'].min(),
            'max': data['value'].max(),
            'count': data['value'].count(),
            '25%': data['value'].quantile(0.25),
            '75%': data['value'].quantile(0.75)
        }
        
        # Calculate trend with linear regression
        if len(data) > 1 and 'date' in data.columns:
            try:
                # Convert dates to numeric for regression
                x = pd.to_numeric(pd.to_datetime(data['date']))
                y = data['value']
                
                # Simple linear regression
                slope, intercept = np.polyfit(x, y, 1)
                
                # Add trend to statistics
                stats['trend'] = slope
            except Exception as e:
                logger.warning(f"Could not calculate trend: {str(e)}")
        
        return stats
    
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
        if len(data_list) != len(site_names):
            raise ValueError("Number of datasets and site names must match")
        
        # Calculate statistics for each site
        stats_list = []
        for i, data in enumerate(data_list):
            if 'value' not in data.columns:
                raise ValueError(f"Dataset {i} must contain a 'value' column")
            
            stats = self.calculate_statistics(data)
            stats['site'] = site_names[i]
            stats_list.append(stats)
        
        # Create comparison dataframe
        comparison_df = pd.DataFrame(stats_list)
        
        # Calculate relative differences
        if len(stats_list) > 1:
            # Use first site as reference
            reference = stats_list[0]
            
            for i in range(1, len(stats_list)):
                for key in ['mean', 'median', 'max', 'min']:
                    if key in reference and key in stats_list[i]:
                        diff_key = f"{key}_diff_%"
                        if reference[key] != 0:
                            comparison_df.loc[i, diff_key] = (
                                (stats_list[i][key] - reference[key]) / reference[key] * 100
                            )
        
        # Return results
        return {
            'statistics': comparison_df,
            'summary': {
                'parameter': data_list[0]['parameter_name'].iloc[0] if 'parameter_name' in data_list[0].columns else None,
                'unit': data_list[0]['unit'].iloc[0] if 'unit' in data_list[0].columns else None,
                'num_sites': len(site_names),
                'total_samples': sum(len(data) for data in data_list)
            }
        }
    
    def detect_outliers(self, data: pd.DataFrame, 
                       method: str = 'iqr',
                       threshold: float = 1.5) -> pd.DataFrame:
        """
        Detect outliers in data
        
        Parameters
        ----------
        data : pd.DataFrame
            Data containing a 'value' column
        method : str
            Detection method ('iqr' or 'zscore')
        threshold : float
            Threshold for outlier detection
            
        Returns
        -------
        pd.DataFrame
            Dataframe with outlier flags
        """
        if 'value' not in data.columns:
            raise ValueError("Data must contain a 'value' column")
        
        # Copy data to avoid modifying original
        result = data.copy()
        
        # Detect outliers based on method
        if method == 'iqr':
            # Interquartile range method
            q1 = data['value'].quantile(0.25)
            q3 = data['value'].quantile(0.75)
            iqr = q3 - q1
            
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            
            result['is_outlier'] = (
                (data['value'] < lower_bound) | 
                (data['value'] > upper_bound)
            )
            
            result['outlier_info'] = np.where(
                result['is_outlier'],
                np.where(
                    data['value'] < lower_bound,
                    f"Low outlier (< {lower_bound:.2f})",
                    f"High outlier (> {upper_bound:.2f})"
                ),
                "Normal"
            )
            
        elif method == 'zscore':
            # Z-score method
            mean = data['value'].mean()
            std = data['value'].std()
            
            if std == 0:
                result['is_outlier'] = False
                result['outlier_info'] = "Normal"
            else:
                z_scores = (data['value'] - mean) / std
                
                # Flag outliers where absolute z-score exceeds threshold
                result['is_outlier'] = abs(z_scores) > threshold
                
                # Loop through rows to add specific z-score info
                result['outlier_info'] = "Normal"  # Default value
                
                for idx in result.index:
                    if abs(z_scores[idx]) > threshold:
                        if data.loc[idx, 'value'] < mean:
                            result.loc[idx, 'outlier_info'] = f"Low outlier (z-score: {z_scores[idx]:.2f})"
                        else:
                            result.loc[idx, 'outlier_info'] = f"High outlier (z-score: {z_scores[idx]:.2f})"
        else:
            raise ValueError(f"Unknown outlier detection method: {method}")
        
        return result 