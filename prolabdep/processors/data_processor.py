"""
Data processing module for handling LIMS export data
"""
import os
from typing import Dict, Union, Optional, Any

import pandas as pd
import logging

from prolabdep.core.config import Config
from prolabdep.core.exceptions import ProcessingError, ValidationError
from prolabdep.processors.csv_processor import CSVProcessor
from prolabdep.processors.excel_processor import ExcelProcessor
from prolabdep.processors.validator import DataValidator

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Class for processing LIMS export data
    
    This class provides a high-level interface to the processor modules
    for loading, cleaning, and transforming data from LIMS export files.
    """
    
    def __init__(self, custom_config: Dict[str, Any] = None):
        """
        Initialize the data processor
        
        Parameters
        ----------
        custom_config : Dict[str, Any], optional
            Custom configuration settings
        """
        self.config = Config()
        if custom_config:
            self.config._update_settings(custom_config)
        
        # Initialize processors
        self.csv_processor = CSVProcessor(self.config)
        self.excel_processor = ExcelProcessor(self.config)
        self.validator = DataValidator(self.config)
    
    def load_from_file(self, filepath: str, validate: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Load and process data from a LIMS export file
        
        Parameters
        ----------
        filepath : str
            Path to the LIMS export file (CSV or Excel)
        validate : bool
            Whether to validate the processed data
            
        Returns
        -------
        Dict[str, pd.DataFrame]
            Dictionary containing processed dataframes:
            - 'data': Main processed data
            - 'parameters': Parameter definitions
            - 'samples': Sample metadata
            
        Raises
        ------
        ProcessingError
            If there is an error processing the file
        ValidationError
            If validation is enabled and fails
        """
        logger.info(f"Loading data from {filepath}")
        
        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File not found: {filepath}")
            
            # Determine file type from extension
            file_extension = os.path.splitext(filepath)[1].lower()
            
            # Process data based on file type
            if file_extension == '.csv':
                data_dict = self.csv_processor.process(filepath)
            elif file_extension in ['.xlsx', '.xls']:
                data_dict = self.excel_processor.process(filepath)
            else:
                raise ProcessingError(f"Unsupported file format: {file_extension}")
            
            # Validate data if requested
            if validate:
                validation_results = self.validator.validate(data_dict)
                
                # Check if validation failed
                if not validation_results['valid']:
                    errors = "\n".join(validation_results['errors'])
                    raise ValidationError(f"Data validation failed: {errors}")
                
                # Log warnings
                for warning in validation_results.get('warnings', []):
                    logger.warning(warning)
                
                # Add validation results to data_dict
                data_dict['validation'] = validation_results
            
            logger.info("Data loaded and processed successfully")
            return data_dict
        
        except Exception as e:
            if isinstance(e, (ProcessingError, ValidationError, FileNotFoundError)):
                raise
            else:
                logger.error(f"Error loading data: {str(e)}")
                raise ProcessingError(f"Error loading data: {str(e)}") from e
    
    def extract_parameter_series(self, data: pd.DataFrame, parameter_name: str, 
                                filter_criteria: Dict[str, str] = None) -> pd.DataFrame:
        """
        Extract time series data for a specific parameter
        
        Parameters
        ----------
        data : pd.DataFrame
            Processed data dataframe
        parameter_name : str
            Name of the parameter to extract
        filter_criteria : Dict[str, str], optional
            Criteria for filtering data
            
        Returns
        -------
        pd.DataFrame
            Dataframe with time series data for the parameter
        """
        if filter_criteria is None:
            filter_criteria = {}
        
        # Create a copy of the data
        df = data.copy()
        
        # Filter by parameter name
        df = df[df['nome_param'] == parameter_name]
        
        # Apply additional filters
        for key, value in filter_criteria.items():
            if key in df.columns:
                df = df[df[key] == value]
        
        # Sort by date
        if 'data_prelievo' in df.columns:
            df = df.sort_values('data_prelievo')
        
        return df 