"""
CSV processor module for processing CSV files
"""
import os
import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from prolabdep.processors.base_processor import BaseProcessor
from prolabdep.core.config import Config
from prolabdep.core.exceptions import ProcessingError
from prolabdep.utils.standardization import standardize_location_info, default_mappings

logger = logging.getLogger(__name__)


class CSVProcessor(BaseProcessor):
    """
    Processor for CSV files
    
    This class processes data from CSV files exported from LIMS.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the CSV processor
        
        Parameters
        ----------
        config : Config, optional
            Configuration object
        """
        super().__init__(config)
        # Cache for standardization to avoid repeated lookups
        self._standardization_cache = {}
    
    def process(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """
        Process data from a CSV file with optimized performance
        
        Parameters
        ----------
        file_path : str
            Path to the CSV file
            
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
        FileNotFoundError
            If the file does not exist
        """
        logger.info(f"Processing CSV file: {file_path}")
        
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Validate file extension
            if not file_path.lower().endswith('.csv'):
                raise ProcessingError(f"Not a CSV file: {file_path}")
            
            # Load the CSV file with optimized parameters
            df = pd.read_csv(
                file_path, 
                sep=';', 
                encoding='latin-1', 
                header=0,
                low_memory=False,  # Read all data into memory for better performance
                na_filter=True,    # Enable NA detection
                skip_blank_lines=True  # Skip blank lines
            )
            
            # Remove last empty column if present
            if df.columns[-1].strip() == '':
                df = df.drop(df.columns[-1], axis=1)
            
            # Store parameter descriptions (second row) before dropping it
            param_descriptions = df.iloc[0]
            
            # Drop the description row and continue with data processing
            df = df.drop(0).reset_index(drop=True)  # Reset index for better performance
            
            # 1. Get parameters dataframe from the technical headers
            pars_df = self._get_parameters_optimized(df, param_descriptions)
            
            # 2. Rename columns efficiently
            column_mapping = {
                'Codice': 'codice_prelievo',
                'Attività': 'punto_prelievo',
                'Data prelievo': 'data_prelievo',
                'Motivo del prelievo': 'motivo_prelievo',
                'Modalità di campionamento': 'modo_prelievo',
                'Stato': 'stato'
            }
            df = df.rename(columns=column_mapping)
            
            # 3. Remove empty rows more efficiently
            df = df.dropna(subset=['data_prelievo']).reset_index(drop=True)
            
            # 4. Create samples dataframe with metadata
            samp_df = self._create_samples_dataframe_optimized(df)
            
            # 5. Process measurements with vectorized operations
            data_df = self._process_measurements_optimized(df, samp_df)
            
            logger.info(f"CSV file processed successfully: {file_path}")
            
            return {
                'data': data_df,
                'parameters': pars_df,
                'samples': samp_df
            }
            
        except Exception as e:
            logger.error(f"Error processing CSV file {file_path}: {str(e)}")
            raise ProcessingError(f"Error processing CSV file: {str(e)}") from e
    
    def _get_parameters_optimized(self, df: pd.DataFrame, param_descriptions: pd.Series) -> pd.DataFrame:
        """
        Extract parameters with optimized operations
        """
        # Define metadata columns (before renaming)
        metadata_columns = {
            'Codice', 'Attività', 'Data prelievo', 'Motivo del prelievo', 
            'Modalità di campionamento', 'Stato'
        }
        
        # Get parameter columns - all non-metadata columns that contain data
        param_cols = [col for col in df.columns 
                     if col not in metadata_columns and col.strip() and 
                     not col.startswith('Unnamed:')]
        
        # Parse parameter information from column names
        params_data = []
        for col in param_cols:
            if '@' in col:
                # Parse standard format like "COD@M1@mg/l"
                parts = col.split('@')
                nome_param = parts[0]
                metodo = parts[1] if len(parts) > 1 else ""
                udm = parts[2] if len(parts) > 2 else ""
            else:
                # Handle non-standard format (like "ECOLISemina")
                nome_param = col
                metodo = ""
                udm = ""
            
            params_data.append({
                'codice_param': col,
                'nome_param': nome_param,
                'metodo': metodo,
                'udm': udm,
                'descrizione': param_descriptions.get(col, '')
            })
        
        # Create parameters dataframe
        pars_df = pd.DataFrame(params_data)
        
        # Vectorized standardization
        if not pars_df.empty:
            pars_df['nome_param_std'] = pars_df['nome_param'].apply(
                self._cached_standardize_parameter
            )
        
        return pars_df
    
    def _cached_standardize_parameter(self, param: str) -> str:
        """Cached parameter standardization to avoid repeated computations"""
        if param not in self._standardization_cache:
            self._standardization_cache[param] = default_mappings.standardize_parameter(param)
        return self._standardization_cache[param]
    
    def _create_samples_dataframe_optimized(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create samples dataframe with vectorized operations
        """
        # Select sample columns
        sample_cols = ['codice_prelievo', 'punto_prelievo', 'motivo_prelievo', 
                      'modo_prelievo', 'data_prelievo', 'stato']
        samp_df = df[sample_cols].drop_duplicates().set_index('codice_prelievo')
        
        # Vectorized date parsing
        samp_df['data_prelievo'] = pd.to_datetime(
            samp_df['data_prelievo'], 
            format='%d/%m/%Y',
            errors='coerce'
        )
        
        # Vectorized location extraction (without standardization)
        location_data = samp_df['punto_prelievo'].apply(self._extract_location_info)
        
        # Convert location data to DataFrame columns
        location_df = pd.DataFrame(location_data.tolist(), index=samp_df.index)
        
        # Add location data to samples dataframe
        samp_df = pd.concat([samp_df, location_df], axis=1)
        
        # Create standardized versions of sites and sampling points
        samp_df['site_std'] = samp_df['site'].apply(default_mappings.standardize_site)
        samp_df['sampling_point_std'] = samp_df['sampling_point'].apply(
            default_mappings.standardize_sampling_point
        )
        
        return samp_df.reset_index()
    
    def _process_measurements_optimized(self, df: pd.DataFrame, samp_df: pd.DataFrame) -> pd.DataFrame:
        """
        Process measurements with optimized melting and conversion
        """
        # Drop metadata columns and keep only measurement data
        measurement_cols = [col for col in df.columns if col not in [
            'punto_prelievo', 'motivo_prelievo', 'modo_prelievo',
            'data_prelievo', 'stato'
        ]]
        
        measurement_df = df[measurement_cols]
        
        # Optimized melt operation
        tidy_df = pd.melt(
            measurement_df, 
            id_vars=['codice_prelievo'],
            var_name='codice_param',
            value_name='valore'
        ).dropna()
        
        # Vectorized value conversion
        tidy_df['valore'] = self._convert_values_vectorized(tidy_df['valore'])
        
        # Merge with sample data efficiently
        data_df = pd.merge(
            samp_df,
            tidy_df,
            on='codice_prelievo',
            how='inner'
        ).sort_values(by='data_prelievo')
        
        return data_df
    
    def _convert_values_vectorized(self, values: pd.Series) -> pd.Series:
        """
        Vectorized value conversion with better performance
        """
        # Convert to string first to handle mixed types
        values = values.astype(str)
        
        # Handle special cases vectorized
        values = values.replace({
            'Assente': '0',
            'Presente': '1',
            'valore non pervenuto': np.nan,
            'nan': np.nan
        })
        
        # Replace comma with dot for decimal separator
        values = values.str.replace(',', '.', regex=False)
        
        # Handle detection limits (e.g., "<0.5" -> "0.25")
        mask_lt = values.str.startswith('<', na=False)
        if mask_lt.any():
            values.loc[mask_lt] = values.loc[mask_lt].str.slice(1).astype(float) / 2
        
        # Convert to numeric, errors='coerce' will set invalid values to NaN
        return pd.to_numeric(values, errors='coerce')
    
    def _extract_location_info(self, activity_string: str) -> dict:
        """
        Extract location information from activity string
        
        Parameters
        ----------
        activity_string : str
            Activity string containing location information
            
        Returns
        -------
        dict
            Dictionary with municipality, site, and sampling_point
        """
        if not activity_string or pd.isna(activity_string):
            return {
                'municipality': None,
                'site': None,
                'sampling_point': None
            }
        
        activity = activity_string.strip()
        
        # Extract municipality (first 2 characters if they match known codes)
        municipality_codes = ['SN', 'AA', 'BB', 'CC']  # Add more as needed
        municipality = None
        for code in municipality_codes:
            if activity.startswith(code + ' '):
                municipality = code
                activity = activity[3:]  # Remove municipality code and space
                break
        
        # Split by ' - ' to separate location from city/postal code
        parts = activity.split(' - ')
        location_part = parts[0] if parts else activity
        
        # Extract sampling point
        sampling_point = None
        sampling_point_keywords = ['ingresso', 'uscita', 'entrata', 'inlet', 'outlet']
        site = location_part  # Start with full location part
        
        for keyword in sampling_point_keywords:
            if keyword in location_part.lower():
                sampling_point = keyword
                # Remove sampling point from location to get site, but preserve the rest
                # Use case-insensitive replacement
                site = location_part.lower().replace(keyword, '').strip()
                break
        
        # Clean up site name but preserve important parts like "Dep."
        if site:
            # Remove extra spaces but preserve structure
            site = ' '.join(site.split())
            # Capitalize properly while preserving abbreviations and Italian articles
            words = site.split()
            capitalized_words = []
            for i, word in enumerate(words):
                word_lower = word.lower()
                if word_lower in ['dep.', 'dep', 'st.', 'st']:
                    # Capitalize abbreviations
                    capitalized_words.append(word.capitalize())
                elif word_lower in ['di', 'del', 'della', 'dei', 'delle', 'da', 'dal', 'dalla', 'monitoraggio']:
                    # Keep Italian articles and common words lowercase
                    capitalized_words.append(word_lower)
                else:
                    # Capitalize all other words (proper nouns, etc.)
                    capitalized_words.append(word.capitalize())
            site = ' '.join(capitalized_words)
        
        return {
            'municipality': municipality,
            'site': site,
            'sampling_point': sampling_point
        }
    
    def _parse_date(self, date_string: str) -> datetime:
        """
        Parse date string in various formats
        
        Parameters
        ----------
        date_string : str
            Date string to parse
            
        Returns
        -------
        datetime
            Parsed datetime object
        """
        if not date_string or pd.isna(date_string):
            raise ValueError("Invalid date string")
        
        date_string = str(date_string).strip()
        
        # Try different date formats
        formats = [
            '%d/%m/%Y',  # 01/01/2024
            '%Y-%m-%d',  # 2024-01-01
            '%d.%m.%Y',  # 01.01.2024
            '%d-%m-%Y',  # 01-01-2024
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse date: {date_string}")
    
    def _convert_value(self, value, conversion_map=None):
        """
        Convert a value with special handling for detection limits and other cases
        
        Parameters
        ----------
        value : any
            Value to convert
        conversion_map : dict, optional
            Custom conversion mapping
            
        Returns
        -------
        float or NaN
            Converted numeric value
        """
        if pd.isna(value):
            return np.nan
        
        # If value is already numeric, return as is
        if isinstance(value, (int, float)):
            return float(value)
        
        # Convert to string for processing
        str_value = str(value).strip()
        
        # Apply conversion map if provided
        if conversion_map and str_value in conversion_map:
            str_value = conversion_map[str_value]
        
        # Handle special cases
        if str_value.lower() in ['assente', 'absent']:
            return 0.0
        elif str_value.lower() in ['presente', 'present']:
            return 1.0
        elif str_value.lower() in ['valore non pervenuto', 'n/a', '']:
            return np.nan
        
        # Replace comma with dot for decimal separator
        str_value = str_value.replace(',', '.')
        
        # Handle detection limits
        if str_value.startswith('<'):
            try:
                limit_value = float(str_value[1:])
                return limit_value / 2.0  # Return half of detection limit
            except ValueError:
                return np.nan
        elif str_value.startswith('>'):
            try:
                return float(str_value[1:])  # Return the value after >
            except ValueError:
                return np.nan
        
        # Try to convert to float
        try:
            return float(str_value)
        except ValueError:
            return np.nan 