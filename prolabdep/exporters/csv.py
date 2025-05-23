"""
CSV exporter module
"""
import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CSVExporter:
    """
    CSV exporter for wastewater treatment plant data
    
    This class provides methods for exporting data to CSV format.
    """
    
    def __init__(self):
        """Initialize CSV exporter"""
        pass
    
    def export(self, data: pd.DataFrame, output_path: str, 
              sep: str = ',', encoding: str = 'utf-8') -> str:
        """
        Export data to CSV file
        
        Parameters
        ----------
        data : pd.DataFrame
            Data to export
        output_path : str
            Path to output file
        sep : str, optional
            Separator character
        encoding : str, optional
            File encoding
            
        Returns
        -------
        str
            Path to the exported file
        """
        try:
            # Create directory if it doesn't exist
            import os
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            # Export to CSV
            data.to_csv(output_path, sep=sep, index=False, encoding=encoding)
            
            logger.info(f"Data exported to CSV file: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise 