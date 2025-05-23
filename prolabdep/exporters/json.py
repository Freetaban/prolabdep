"""
JSON exporter module
"""
import pandas as pd
import json
import logging
from typing import Dict, Union, Optional, Any

logger = logging.getLogger(__name__)


class JSONExporter:
    """
    JSON exporter for wastewater treatment plant data
    
    This class provides methods for exporting data to JSON format.
    """
    
    def __init__(self):
        """Initialize JSON exporter"""
        pass
    
    def export(self, data: Union[pd.DataFrame, Dict], output_path: str,
              orient: str = 'records', indent: int = 2) -> str:
        """
        Export data to JSON file
        
        Parameters
        ----------
        data : Union[pd.DataFrame, Dict]
            Data to export (DataFrame or Dictionary)
        output_path : str
            Path to output file
        orient : str, optional
            DataFrame orientation ('records', 'columns', 'index', etc.)
        indent : int, optional
            JSON indentation level
            
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
                
            # Export to JSON
            if isinstance(data, pd.DataFrame):
                data.to_json(output_path, orient=orient, indent=indent)
            else:
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=indent)
            
            logger.info(f"Data exported to JSON file: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {str(e)}")
            raise 