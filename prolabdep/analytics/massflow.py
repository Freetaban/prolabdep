"""
Mass flow calculation module for wastewater treatment plant data
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Any, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class MassFlowCalculator:
    """
    Mass flow calculator for wastewater treatment plant data
    
    This class provides methods for calculating mass flows based on
    concentration data and flow rates.
    """
    
    # Unit conversion factors
    CONVERSION_FACTORS = {
        'concentration': {
            'mg/l': 1.0,
            'g/l': 1000.0,
            'µg/l': 0.001,
            'ng/l': 0.000001,
            'MG/L': 1.0,
            'G/L': 1000.0,
            'UG/L': 0.001,
            'NG/L': 0.000001
        },
        'flow': {
            'm3/h': 1.0,
            'm3/d': 1.0/24.0,
            'l/s': 3.6,
            'l/min': 0.06,
            'l/h': 0.001
        },
        'mass_flow': {
            'kg/h': 1.0,
            'kg/d': 1.0/24.0,
            'g/h': 0.001,
            'g/d': 0.001/24.0,
            't/y': 8760.0  # kg/h to tonnes/year
        }
    }
    
    def __init__(self):
        """Initialize mass flow calculator"""
        pass
    
    def calculate_mass_flow(self, concentration: float, flow: float,
                           concentration_unit: str = 'mg/l',
                           flow_unit: str = 'm3/h',
                           output_unit: str = 'kg/h') -> float:
        """
        Calculate mass flow from concentration and flow rate
        
        Parameters
        ----------
        concentration : float
            Concentration value
        flow : float
            Flow rate value
        concentration_unit : str
            Unit of concentration (e.g., 'mg/l', 'g/l')
        flow_unit : str
            Unit of flow rate (e.g., 'm3/h', 'l/s')
        output_unit : str
            Unit of output mass flow (e.g., 'kg/h', 'kg/d')
            
        Returns
        -------
        float
            Mass flow in specified units
        """
        # Validate units
        if concentration_unit not in self.CONVERSION_FACTORS['concentration']:
            raise ValueError(f"Unknown concentration unit: {concentration_unit}")
        if flow_unit not in self.CONVERSION_FACTORS['flow']:
            raise ValueError(f"Unknown flow unit: {flow_unit}")
        if output_unit not in self.CONVERSION_FACTORS['mass_flow']:
            raise ValueError(f"Unknown mass flow unit: {output_unit}")
        
        # Convert concentration to mg/l
        conc_in_mg_l = concentration * self.CONVERSION_FACTORS['concentration'][concentration_unit]
        
        # Convert flow to m3/h
        flow_in_m3_h = flow * self.CONVERSION_FACTORS['flow'][flow_unit]
        
        # Calculate mass flow in kg/h
        mass_flow_kg_h = conc_in_mg_l * flow_in_m3_h / 1000000  # mg/l * m3/h / 1000000 = kg/h
        
        # Convert to desired output unit
        mass_flow = mass_flow_kg_h / self.CONVERSION_FACTORS['mass_flow'][output_unit]
        
        return mass_flow
    
    def extract_unit(self, unit_string: str) -> Tuple[str, str]:
        """
        Extract concentration and flow units from a combined unit string
        
        Parameters
        ----------
        unit_string : str
            Combined unit string (e.g., 'mg/l', 'm3/h')
            
        Returns
        -------
        Tuple[str, str]
            Tuple of (quantity, time_unit)
        """
        # Common patterns for units
        if not unit_string:
            return None, None
            
        unit_string = unit_string.lower()
        
        # Extract quantity and time units
        quantity_match = re.match(r'([a-zµ0-9]+)/([a-z]+)', unit_string)
        
        if quantity_match:
            quantity = quantity_match.group(1)
            time_unit = quantity_match.group(2)
            return quantity, time_unit
        
        return unit_string, None
    
    def apply_mass_flow_calculation(self, concentration_data: pd.DataFrame, 
                                  flow_data: pd.DataFrame,
                                  output_unit: str = 'kg/h') -> pd.DataFrame:
        """
        Calculate mass flow for a dataset
        
        Parameters
        ----------
        concentration_data : pd.DataFrame
            Concentration data with 'date' and 'value' columns
        flow_data : pd.DataFrame
            Flow data with 'date' and 'value' columns
        output_unit : str
            Output unit for mass flow
            
        Returns
        -------
        pd.DataFrame
            Dataframe with mass flow calculations
        """
        # Validate input data
        for df, name in [(concentration_data, 'concentration_data'), (flow_data, 'flow_data')]:
            if 'date' not in df.columns or 'value' not in df.columns:
                raise ValueError(f"{name} must contain 'date' and 'value' columns")
        
        # Extract units
        conc_unit = concentration_data['unit'].iloc[0] if 'unit' in concentration_data.columns else 'mg/l'
        flow_unit = flow_data['unit'].iloc[0] if 'unit' in flow_data.columns else 'm3/h'
        
        # Set datetime index for merging
        conc_df = concentration_data.copy()
        flow_df = flow_data.copy()
        
        # Ensure datetime format
        conc_df['date'] = pd.to_datetime(conc_df['date'])
        flow_df['date'] = pd.to_datetime(flow_df['date'])
        
        # Set date as index
        conc_df.set_index('date', inplace=True)
        flow_df.set_index('date', inplace=True)
        
        # Extract only numeric columns for resampling
        conc_numeric = conc_df[['value']].copy()
        flow_numeric = flow_df[['value']].copy()
        
        # Resample to same frequency if needed
        conc_resampled = conc_numeric.resample('D').mean()
        flow_resampled = flow_numeric.resample('D').mean()
        
        # Align indexes
        common_dates = conc_resampled.index.intersection(flow_resampled.index)
        
        if len(common_dates) == 0:
            logger.warning("No common dates between concentration and flow data")
            return pd.DataFrame()
        
        # Merge data
        merged_data = pd.DataFrame({
            'concentration': conc_resampled.loc[common_dates, 'value'],
            'flow': flow_resampled.loc[common_dates, 'value']
        })
        
        # Calculate mass flow
        merged_data['mass_flow'] = merged_data.apply(
            lambda row: self.calculate_mass_flow(
                row['concentration'], row['flow'], 
                concentration_unit=conc_unit,
                flow_unit=flow_unit,
                output_unit=output_unit
            ),
            axis=1
        )
        
        # Reset index for consistent return format
        result = merged_data.reset_index()
        
        # Add metadata columns
        if 'parameter_name' in concentration_data.columns:
            result['parameter_name'] = concentration_data['parameter_name'].iloc[0]
        
        if 'site' in concentration_data.columns:
            result['site'] = concentration_data['site'].iloc[0]
            
        if 'sampling_point' in concentration_data.columns:
            result['sampling_point'] = concentration_data['sampling_point'].iloc[0]
            
        result['unit'] = output_unit
        
        return result 