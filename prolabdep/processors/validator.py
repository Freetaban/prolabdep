"""
Data validator module for validating processed data
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Any

from prolabdep.core.config import Config
from prolabdep.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validator for processed data
    
    This class provides methods for validating data processed
    by the CSV and Excel processors.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the validator
        
        Parameters
        ----------
        config : Config, optional
            Configuration object
        """
        self.config = config or Config()
    
    def validate(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Validate processed data
        
        Parameters
        ----------
        data_dict : Dict[str, pd.DataFrame]
            Dictionary of processed data
            
        Returns
        -------
        Dict[str, Any]
            Validation results
        
        Raises
        ------
        ValidationError
            If validation fails
        """
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'summary': {
                'total_samples': 0,
                'total_measurements': 0,
                'total_parameters': 0
            }
        }
        
        try:
            # Check for required keys
            required_keys = ['data', 'parameters', 'samples']
            for key in required_keys:
                if key not in data_dict:
                    validation_results['valid'] = False
                    validation_results['errors'].append(f"Missing required dataframe: '{key}'")
                elif data_dict[key].empty:
                    validation_results['valid'] = False
                    validation_results['errors'].append(f"Empty dataframe: '{key}'")
            
            # If missing required data, return early
            if not validation_results['valid']:
                return validation_results
            
            # Validate data structure
            data_df = data_dict['data']
            params_df = data_dict['parameters']
            samples_df = data_dict['samples']
            
            # Validate data types in data dataframe
            if 'data_prelievo' in data_df.columns and not pd.api.types.is_datetime64_any_dtype(data_df['data_prelievo']):
                validation_results['warnings'].append("'data_prelievo' column is not datetime type")
            
            if 'valore' in data_df.columns and not pd.api.types.is_float_dtype(data_df['valore']):
                validation_results['warnings'].append("'valore' column is not float type")
            
            # Check for required columns in data dataframe
            required_data_cols = ['codice_prelievo', 'data_prelievo', 'codice_param', 'valore']
            missing_cols = [col for col in required_data_cols if col not in data_df.columns]
            if missing_cols:
                validation_results['valid'] = False
                validation_results['errors'].append(f"Missing required columns in data: {missing_cols}")
            
            # Check for required columns in parameters dataframe
            required_param_cols = ['codice_param', 'nome_param', 'metodo', 'udm']
            missing_cols = [col for col in required_param_cols if col not in params_df.columns]
            if missing_cols:
                validation_results['valid'] = False
                validation_results['errors'].append(f"Missing required columns in parameters: {missing_cols}")
            
            # Check for required columns in samples dataframe
            required_sample_cols = ['codice_prelievo', 'data_prelievo']
            missing_cols = [col for col in required_sample_cols if col not in samples_df.columns]
            if missing_cols:
                validation_results['valid'] = False
                validation_results['errors'].append(f"Missing required columns in samples: {missing_cols}")
            
            # Return early if basic validation failed
            if not validation_results['valid']:
                return validation_results
            
            # Check for duplicate measurements (same sample_id and parameter_code)
            if 'codice_prelievo' in data_df.columns and 'codice_param' in data_df.columns:
                duplicates = data_df.duplicated(subset=['codice_prelievo', 'codice_param'], keep='first')
                if duplicates.any():
                    validation_results['valid'] = False
                    dup_rows = data_df[duplicates]
                    dup_info = [f"{row['codice_prelievo']}-{row['codice_param']}" for _, row in dup_rows.iterrows()]
                    validation_results['errors'].append(f"Duplicate measurements found: {', '.join(dup_info[:5])}" + 
                                                       (f"... and {len(dup_info) - 5} more" if len(dup_info) > 5 else ""))
            
            # Check for consistency between data and parameters
            unique_params_in_data = data_df['codice_param'].unique()
            params_in_params_df = set(params_df['codice_param'])
            
            params_in_data_not_in_params = [p for p in unique_params_in_data if p not in params_in_params_df]
            if params_in_data_not_in_params:
                validation_results['valid'] = False
                validation_results['errors'].append(
                    f"Unknown parameters in data not found in parameters dataframe: {', '.join(params_in_data_not_in_params[:5])}"
                    + (f"... and {len(params_in_data_not_in_params) - 5} more" 
                       if len(params_in_data_not_in_params) > 5 else "")
                )
            
            # Check for consistency between data and samples
            unique_samples_in_data = data_df['codice_prelievo'].unique()
            samples_in_samples_df = set(samples_df['codice_prelievo'])
            
            samples_in_data_not_in_samples = [s for s in unique_samples_in_data if s not in samples_in_samples_df]
            if samples_in_data_not_in_samples:
                validation_results['warnings'].append(
                    f"Samples in data not found in samples dataframe: {', '.join(samples_in_data_not_in_samples[:5])}"
                    + (f"... and {len(samples_in_data_not_in_samples) - 5} more" 
                       if len(samples_in_data_not_in_samples) > 5 else "")
                )
            
            # Check for missing values
            if data_df['valore'].isna().any():
                missing_values = data_df[data_df['valore'].isna()]
                validation_results['warnings'].append(
                    f"Missing values found in {len(missing_values)} measurements"
                )
            
            # Check for extreme values
            if 'valore' in data_df.columns:
                # Find values that are more than 3 standard deviations away from the mean
                grouped = data_df.groupby('codice_param')
                
                extreme_values = []
                for param, group in grouped:
                    if len(group) < 3:
                        continue
                        
                    mean = group['valore'].mean()
                    std = group['valore'].std()
                    
                    if std == 0:
                        continue
                        
                    z_scores = (group['valore'] - mean) / std
                    extreme_in_group = group[abs(z_scores) > 3]
                    
                    if not extreme_in_group.empty:
                        extreme_values.append({
                            'parameter': param,
                            'count': len(extreme_in_group),
                            'examples': extreme_in_group.head(3)[['codice_prelievo', 'valore']].to_dict('records')
                        })
                
                if extreme_values:
                    validation_results['warnings'].append(
                        f"Found {sum(e['count'] for e in extreme_values)} potential extreme values across "
                        f"{len(extreme_values)} parameters"
                    )
                    validation_results['extreme_values'] = extreme_values
            
            # Add summary statistics
            validation_results['summary']['total_samples'] = len(samples_df)
            validation_results['summary']['total_measurements'] = len(data_df)
            validation_results['summary']['total_parameters'] = len(params_df)
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            validation_results['valid'] = False
            validation_results['errors'].append(f"Validation error: {str(e)}")
            return validation_results 