"""
Base processor module for data processing
"""
import os
import re
import pandas as pd
import numpy as np
from datetime import datetime as dt
import logging
from typing import Dict, Union, Any, Tuple, Optional

from prolabdep.core.config import Config
from prolabdep.core.exceptions import ProcessingError, ValidationError

logger = logging.getLogger(__name__)


class BaseProcessor:
    """
    Base class for data processors
    
    This class provides common functionality for processing data from
    different file formats.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the processor
        
        Parameters
        ----------
        config : Config, optional
            Configuration object
        """
        self.config = config or Config()
    
    def process(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """
        Process data from a file
        
        Parameters
        ----------
        file_path : str
            Path to the data file
            
        Returns
        -------
        Dict[str, pd.DataFrame]
            Dictionary containing processed dataframes:
            - 'data': Main processed data
            - 'parameters': Parameter definitions
            - 'samples': Sample metadata
            
        Raises
        ------
        NotImplementedError
            This method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement process method")
    
    def _get_parameters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract parameter information from dataframe headers
        
        Parameters
        ----------
        df : pd.DataFrame
            Raw dataframe with parameter headers
            
        Returns
        -------
        pd.DataFrame
            Dataframe with parameter definitions
        """
        pars_df = df.iloc[0:1, 1:].transpose().reset_index()
        pars_df = pars_df[pars_df.iloc[:, 0].str.contains('@')]
        pars_df.columns = ['codice_param', 'testo_param']
        
        # Split parameter code into components
        pars_df[['nome_param', 'metodo', 'udm']] = pars_df['codice_param'].str.split(
            pat='@', n=2, expand=True
        )
        
        # Clean parameter names by removing "DEP" suffix
        pars_df['nome_param'] = pars_df['nome_param'].apply(
            lambda x: re.sub(r'DEP$', '', x)
        )
        
        # Reset index and filter out unwanted methods
        pars_df = pars_df.reset_index(drop=True)
        pars_df = pars_df[~pars_df.metodo.isin(['LABEST', 'CALC'])]
        
        return pars_df
    
    def _parse_date(self, date_str: str) -> dt:
        """
        Parse date string into datetime object
        
        Parameters
        ----------
        date_str : str
            Date string to parse
            
        Returns
        -------
        datetime
            Parsed datetime object
        """
        if not isinstance(date_str, str):
            return date_str
        
        for date_format in self.config.date_formats:
            try:
                return dt.strptime(date_str.strip(), date_format)
            except ValueError:
                continue
        
        raise ValueError(f"Could not parse date: {date_str}")
    
    def _extract_location_info(self, activity_str: str) -> pd.Series:
        """
        Extract location information from activity string
        
        Parameters
        ----------
        activity_str : str
            Activity string (e.g., "SN Dep. S. Giusto uscita - Scandicci - 10624")
            
        Returns
        -------
        pd.Series
            Series with municipality, site, and sampling point
        """
        if not isinstance(activity_str, str):
            return pd.Series({
                'municipality': None,
                'site': None,
                'sampling_point': None
            })
        
        # Default values
        municipality = None
        site = None
        sampling_point = None
        
        # Extract municipality (first two capitalized letters)
        muni_match = re.match(r'^([A-Z]{2})\s+', activity_str)
        if muni_match:
            municipality = muni_match.group(1)
        
        # Extract site and sampling point
        # Common patterns for sampling points
        sampling_points = ['ingresso', 'uscita', 'linea', 'punto', 'vasca', 'a monte', 'a valle']
        
        # Try to find site and sampling point based on known patterns
        parts = activity_str.split(' - ')
        if len(parts) > 0:
            # First part typically contains site and sampling point
            first_part = parts[0]
            
            # Remove municipality prefix if present
            if muni_match:
                first_part = first_part[len(muni_match.group(0)):].strip()
            
            # Try to find sampling point
            for point in sampling_points:
                if point in first_part.lower():
                    idx = first_part.lower().find(point)
                    site = first_part[:idx].strip()
                    sampling_point = first_part[idx:].strip()
                    break
            
            # If no sampling point found, use the whole string as site
            if site is None:
                site = first_part
        
        # Don't use parts[1] as municipality - it's usually a city name, not a code
        
        return pd.Series({
            'municipality': municipality,
            'site': site,
            'sampling_point': sampling_point
        })
    
    def _convert_value(self, value: str, conversion_map: Dict[str, str] = None) -> float:
        """
        Convert string value to float, handling special cases
        
        Parameters
        ----------
        value : str
            Value to convert
        conversion_map : Dict[str, str], optional
            Map of string values to convert
            
        Returns
        -------
        float
            Converted value
        """
        if not isinstance(value, str):
            return value
        
        # Apply conversion map
        if conversion_map and value in conversion_map:
            return float(conversion_map[value])
        
        # Handle detection limits
        if value.startswith('<'):
            # Extract the numeric part
            numeric_part = value.strip('< ')
            try:
                # Convert to float and divide by detection limit fraction
                return float(numeric_part.replace(',', '.')) / self.config.detection_limit_fraction
            except ValueError:
                logger.warning(f"Could not convert detection limit value: {value}")
                return np.nan
        
        # Handle greater than values
        if value.startswith('>'):
            # Extract the numeric part
            numeric_part = value.strip('> ')
            try:
                return float(numeric_part.replace(',', '.'))
            except ValueError:
                logger.warning(f"Could not convert greater than value: {value}")
                return np.nan
        
        # Handle normal numeric values with potential comma decimal separator
        try:
            return float(value.replace(',', '.'))
        except ValueError:
            logger.warning(f"Could not convert value: {value}")
            return np.nan 