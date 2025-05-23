"""
Excel exporter module
"""
import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ExcelExporter:
    """
    Excel exporter for wastewater treatment plant data
    
    This class provides methods for exporting data to Excel format.
    """
    
    def __init__(self):
        """Initialize Excel exporter"""
        pass
    
    def export(self, data: pd.DataFrame, output_path: str, 
              sheet_name: str = "Data") -> str:
        """
        Export data to Excel file
        
        Parameters
        ----------
        data : pd.DataFrame
            Data to export
        output_path : str
            Path to output file
        sheet_name : str, optional
            Name of the worksheet
            
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
                
            # Export to Excel
            data.to_excel(output_path, sheet_name=sheet_name, index=False)
            
            logger.info(f"Data exported to Excel file: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            raise 