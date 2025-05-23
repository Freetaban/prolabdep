"""
Export API module
"""
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import matplotlib.pyplot as plt

from prolabdep.exporters.excel import ExcelExporter
from prolabdep.exporters.csv import CSVExporter
from prolabdep.exporters.pdf import PDFExporter
from prolabdep.exporters.json import JSONExporter


class ExportAPI:
    """
    Export API for ProlabDep
    
    This class provides methods for exporting data to various formats.
    """
    
    def __init__(self):
        """Initialize the export API"""
        self.excel_exporter = ExcelExporter()
        self.csv_exporter = CSVExporter()
        self.pdf_exporter = PDFExporter()
        self.json_exporter = JSONExporter()
    
    def to_excel(self, data: pd.DataFrame, output_path: str, 
                sheet_name: str = "Data") -> str:
        """
        Export data to Excel
        
        Parameters
        ----------
        data : pd.DataFrame
            Data to export
        output_path : str
            Output file path
        sheet_name : str
            Name of the sheet
            
        Returns
        -------
        str
            Path to the exported file
        """
        return self.excel_exporter.export(data, output_path, sheet_name=sheet_name)
    
    def to_csv(self, data: pd.DataFrame, output_path: str,
              sep: str = ',', encoding: str = 'utf-8') -> str:
        """
        Export data to CSV
        
        Parameters
        ----------
        data : pd.DataFrame
            Data to export
        output_path : str
            Output file path
        sep : str
            Separator character
        encoding : str
            File encoding
            
        Returns
        -------
        str
            Path to the exported file
        """
        return self.csv_exporter.export(
            data, output_path, sep=sep, encoding=encoding
        )
    
    def to_pdf(self, data: pd.DataFrame, output_path: str,
              title: str = "ProlabDep Report",
              include_plots: bool = True) -> str:
        """
        Export data to PDF
        
        Parameters
        ----------
        data : pd.DataFrame
            Data to export
        output_path : str
            Output file path
        title : str
            Report title
        include_plots : bool
            Whether to include plots
            
        Returns
        -------
        str
            Path to the exported file
        """
        return self.pdf_exporter.export(
            data, output_path, title=title, include_plots=include_plots
        )
    
    def to_json(self, data: Union[pd.DataFrame, Dict], output_path: str,
               orient: str = 'records', indent: int = 2) -> str:
        """
        Export data to JSON
        
        Parameters
        ----------
        data : Union[pd.DataFrame, Dict]
            Data to export
        output_path : str
            Output file path
        orient : str
            Orientation format for DataFrame
        indent : int
            Indentation level
            
        Returns
        -------
        str
            Path to the exported file
        """
        return self.json_exporter.export(
            data, output_path, orient=orient, indent=indent
        )
    
    def export_figure(self, figure: plt.Figure, output_path: str,
                     dpi: int = 300, format: str = None) -> str:
        """
        Export a figure to a file
        
        Parameters
        ----------
        figure : plt.Figure
            Figure to export
        output_path : str
            Output file path
        dpi : int
            Resolution in dots per inch
        format : str, optional
            File format (e.g., 'png', 'pdf')
            
        Returns
        -------
        str
            Path to the exported file
        """
        figure.savefig(output_path, dpi=dpi, format=format, bbox_inches='tight')
        return output_path
    
    def export_report(self, data: pd.DataFrame, stats: Dict[str, float],
                     output_path: str, title: str = "Analysis Report",
                     include_plots: bool = True) -> str:
        """
        Export a complete report
        
        Parameters
        ----------
        data : pd.DataFrame
            Data to include in the report
        stats : Dict[str, float]
            Statistics to include
        output_path : str
            Output file path
        title : str
            Report title
        include_plots : bool
            Whether to include plots
            
        Returns
        -------
        str
            Path to the exported file
        """
        return self.pdf_exporter.export_report(
            data, stats, output_path, title=title, include_plots=include_plots
        ) 