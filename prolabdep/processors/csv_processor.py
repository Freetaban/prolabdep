"""
CSV processor module for processing CSV files
"""
import os
import pandas as pd
import logging
from typing import Dict, Optional

from prolabdep.processors.base_processor import BaseProcessor
from prolabdep.core.config import Config
from prolabdep.core.exceptions import ProcessingError

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
    
    def process(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """
        Process data from a CSV file
        
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
            
            # Load the CSV file
            df = pd.read_csv(file_path, sep=';', encoding='latin-1', header=0)
            
            # Remove last empty column if present
            if df.columns[-1].strip() == '':
                df = df.drop(df.columns[-1], axis=1)
            
            # Store parameter descriptions (second row) before dropping it
            param_descriptions = df.iloc[0]
            
            # Drop the description row and continue with data processing
            df = df.drop(0)
            
            # 1. Get parameters dataframe from the technical headers
            pars_df = self._get_parameters(df)
            
            # Add descriptions to pars_df
            pars_df['descrizione'] = pars_df['codice_param'].map(param_descriptions)
            
            # 2. Rename columns
            column_mapping = {
                'Codice': 'codice_prelievo',
                'Attività': 'punto_prelievo',
                'Data prelievo': 'data_prelievo',
                'Motivo del prelievo': 'motivo_prelievo',
                'Modalità di campionamento': 'modo_prelievo',
                'Stato': 'stato'
            }
            df = df.rename(columns=column_mapping)
            
            # 3. Remove empty rows
            df = df.dropna(subset=['data_prelievo'])
            
            # 4. Create samples dataframe with metadata
            samp_df = df[['codice_prelievo', 'punto_prelievo',
                          'motivo_prelievo', 'modo_prelievo',
                          'data_prelievo', 'stato']].set_index('codice_prelievo')
            
            # Parse dates
            samp_df['data_prelievo'] = samp_df['data_prelievo'].apply(self._parse_date)
            
            # Extract municipality, site, and sampling point
            location_data = samp_df['punto_prelievo'].apply(self._extract_location_info)
            samp_df = pd.concat([samp_df, location_data], axis=1)

            # 5. Process measurements
            df = df.drop(['punto_prelievo', 'motivo_prelievo', 'modo_prelievo',
                          'data_prelievo', 'stato'], axis=1)
            tidy_df = pd.melt(df, 
                             id_vars=['codice_prelievo'],
                             var_name='codice_param',
                             value_name='valore').dropna()
            tidy_df = tidy_df.set_index('codice_prelievo')
            
            # Handle decimal separator for CSV files
            # Check if values are strings first
            if tidy_df['valore'].dtype == 'object':
                # Convert comma to dot for strings
                tidy_df['valore'] = tidy_df['valore'].apply(
                    lambda x: x.replace(',', '.') if isinstance(x, str) else x
                )
                
            # Convert values with detection limit handling
            conversion_map = {'Assente': '0', 'Presente': '1'}
            tidy_df['valore'] = tidy_df['valore'].apply(
                self._convert_value,
                args=(conversion_map,)
            ).astype('float64')
            
            # 6. Create final data dataframe
            data_df = pd.merge(
                samp_df,
                tidy_df,
                left_index=True,
                right_index=True
            ).reset_index().sort_values(by='data_prelievo')
            
            logger.info(f"CSV file processed successfully: {file_path}")
            
            return {
                'data': data_df,
                'parameters': pars_df,
                'samples': samp_df.reset_index()
            }
            
        except Exception as e:
            logger.error(f"Error processing CSV file {file_path}: {str(e)}")
            raise ProcessingError(f"Error processing CSV file: {str(e)}") from e 