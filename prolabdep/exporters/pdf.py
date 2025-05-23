"""
PDF exporter module
"""
import pandas as pd
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PDFExporter:
    """
    PDF exporter for wastewater treatment plant data
    
    This class provides methods for exporting data to PDF format.
    """
    
    def __init__(self):
        """Initialize PDF exporter"""
        pass
    
    def export(self, data: pd.DataFrame, output_path: str, 
              title: str = "ProlabDep Report",
              include_plots: bool = True) -> str:
        """
        Export data to PDF file
        
        Parameters
        ----------
        data : pd.DataFrame
            Data to export
        output_path : str
            Path to output file
        title : str, optional
            Report title
        include_plots : bool, optional
            Whether to include plots
            
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
                
            # Try to import reportlab
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.lib import colors
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet
                
                # Create a PDF document
                doc = SimpleDocTemplate(output_path, pagesize=A4)
                elements = []
                
                # Add title
                styles = getSampleStyleSheet()
                elements.append(Paragraph(title, styles['Title']))
                elements.append(Spacer(1, 12))
                
                # Convert data to table
                if not data.empty:
                    table_data = [list(data.columns)]
                    for _, row in data.head(50).iterrows():  # Limit to 50 rows
                        table_data.append([str(x) for x in row.values])
                    
                    # Create table
                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(t)
                
                # Build the PDF
                doc.build(elements)
                
            except ImportError:
                logger.warning("reportlab not installed, falling back to basic export")
                # Fall back to HTML export
                html = f"<html><head><title>{title}</title></head><body>"
                html += f"<h1>{title}</h1>"
                html += data.to_html()
                html += "</body></html>"
                
                with open(output_path, 'w') as f:
                    f.write(html)
            
            logger.info(f"Data exported to PDF file: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            raise
    
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
            Path to output file
        title : str, optional
            Report title
        include_plots : bool, optional
            Whether to include plots
            
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
                
            # Try to import reportlab
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.lib import colors
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet
                
                # Create a PDF document
                doc = SimpleDocTemplate(output_path, pagesize=A4)
                elements = []
                
                # Add title
                styles = getSampleStyleSheet()
                elements.append(Paragraph(title, styles['Title']))
                elements.append(Spacer(1, 12))
                
                # Add statistics table
                if stats:
                    stats_data = [['Statistic', 'Value']]
                    for key, value in stats.items():
                        stats_data.append([key, f"{value:.4f}" if isinstance(value, float) else str(value)])
                    
                    # Create table
                    t = Table(stats_data)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(t)
                    elements.append(Spacer(1, 12))
                
                # Convert data to table
                if not data.empty:
                    table_data = [list(data.columns)]
                    for _, row in data.head(50).iterrows():  # Limit to 50 rows
                        table_data.append([str(x) for x in row.values])
                    
                    # Create table
                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(t)
                
                # Build the PDF
                doc.build(elements)
                
            except ImportError:
                logger.warning("reportlab not installed, falling back to basic export")
                # Fall back to HTML export
                html = f"<html><head><title>{title}</title></head><body>"
                html += f"<h1>{title}</h1>"
                
                # Add statistics
                if stats:
                    html += "<h2>Statistics</h2>"
                    html += "<table border='1'>"
                    html += "<tr><th>Statistic</th><th>Value</th></tr>"
                    for key, value in stats.items():
                        html += f"<tr><td>{key}</td><td>{value:.4f if isinstance(value, float) else value}</td></tr>"
                    html += "</table>"
                
                html += "<h2>Data</h2>"
                html += data.to_html()
                html += "</body></html>"
                
                with open(output_path, 'w') as f:
                    f.write(html)
            
            logger.info(f"Report exported to PDF file: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting report: {str(e)}")
            raise 