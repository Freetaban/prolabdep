"""
Mass flow calculation module for wastewater treatment plant data
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Any, Tuple
import re
import logging

from ..utils.units import unit_manager

logger = logging.getLogger(__name__)


class MassFlowCalculator:
    """
    Mass flow calculator for wastewater treatment plant data using Pint for unit handling
    
    This class provides methods for calculating mass flows based on
    concentration data and flow rates with proper unit conversions.
    """
    
    def __init__(self):
        """Initialize mass flow calculator with Pint unit manager"""
        self.unit_manager = unit_manager
    
    def calculate_mass_flow(self, concentration: float, flow: float,
                           concentration_unit: str = 'mg/L',
                           flow_unit: str = 'm³/h',
                           output_unit: str = 'kg/h') -> float:
        """
        Calculate mass flow from concentration and flow rate using Pint
        
        Parameters
        ----------
        concentration : float
            Concentration value
        flow : float
            Flow rate value
        concentration_unit : str
            Unit of concentration (e.g., 'mg/L', 'g/L')
        flow_unit : str
            Unit of flow rate (e.g., 'm³/h', 'L/s')
        output_unit : str
            Unit of output mass flow (e.g., 'kg/h', 'kg/d')
            
        Returns
        -------
        float
            Mass flow in specified units
            
        Raises
        ------
        ValueError
            If units cannot be parsed or are incompatible
        """
        try:
            return self.unit_manager.calculate_mass_flow(
                concentration, concentration_unit,
                flow, flow_unit,
                output_unit
            )
        except Exception as e:
            logger.error(f"Mass flow calculation failed: {e}")
            raise ValueError(f"Cannot calculate mass flow: {e}")
    
    def extract_unit(self, unit_string: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract concentration and flow units from a combined unit string
        
        Parameters
        ----------
        unit_string : str
            Combined unit string (e.g., 'mg/L', 'm³/h')
            
        Returns
        -------
        Tuple[Optional[str], Optional[str]]
            Tuple of (quantity, time_unit) or (None, None) if parsing fails
        """
        if not unit_string:
            return None, None
            
        unit_string = unit_string.strip()
        
        # Extract quantity and time units using regex
        quantity_match = re.match(r'([a-zµ0-9³²]+)/([a-z]+)', unit_string.lower())
        
        if quantity_match:
            quantity = quantity_match.group(1)
            time_unit = quantity_match.group(2)
            return quantity, time_unit
        
        return unit_string, None
    
    def validate_units(self, concentration_unit: str, flow_unit: str, output_unit: str) -> bool:
        """
        Validate that the units are compatible for mass flow calculation
        
        Parameters
        ----------
        concentration_unit : str
            Concentration unit
        flow_unit : str
            Flow unit
        output_unit : str
            Output mass flow unit
            
        Returns
        -------
        bool
            True if units are valid for mass flow calculation
        """
        try:
            # Parse units using Pint
            conc_qty = self.unit_manager.parse_unit(concentration_unit)
            flow_qty = self.unit_manager.parse_unit(flow_unit)
            output_qty = self.unit_manager.parse_unit(output_unit)
            
            if any(qty is None for qty in [conc_qty, flow_qty, output_qty]):
                return False
            
            # Check dimensionalities
            conc_dim = conc_qty.dimensionality
            flow_dim = flow_qty.dimensionality
            output_dim = output_qty.dimensionality
            
            # Mass flow should be: concentration * flow = (mass/volume) * (volume/time) = mass/time
            expected_dim = conc_dim * flow_dim
            
            return str(expected_dim) == str(output_dim)
            
        except Exception as e:
            logger.warning(f"Unit validation failed: {e}")
            return False
    
    def apply_mass_flow_calculation(self, concentration_data: pd.DataFrame, 
                                  flow_data: pd.DataFrame,
                                  output_unit: str = 'kg/h') -> pd.DataFrame:
        """
        Calculate mass flow for a dataset using Pint unit handling
        
        Parameters
        ----------
        concentration_data : pd.DataFrame
            Concentration data with 'date', 'value', and optionally 'unit' columns
        flow_data : pd.DataFrame
            Flow data with 'date', 'value', and optionally 'unit' columns
        output_unit : str
            Output unit for mass flow
            
        Returns
        -------
        pd.DataFrame
            Dataframe with mass flow calculations
            
        Raises
        ------
        ValueError
            If required columns are missing or units are incompatible
        """
        # Validate input data
        for df, name in [(concentration_data, 'concentration_data'), (flow_data, 'flow_data')]:
            if 'date' not in df.columns or 'value' not in df.columns:
                raise ValueError(f"{name} must contain 'date' and 'value' columns")
        
        # Extract units (with defaults)
        conc_unit = concentration_data['unit'].iloc[0] if 'unit' in concentration_data.columns else 'mg/L'
        flow_unit = flow_data['unit'].iloc[0] if 'unit' in flow_data.columns else 'm³/h'
        
        # Validate units
        if not self.validate_units(conc_unit, flow_unit, output_unit):
            logger.warning(f"Unit validation failed for {conc_unit} * {flow_unit} -> {output_unit}")
        
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
        
        # Resample to same frequency if needed (daily average)
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
        
        # Calculate mass flow using Pint
        def calculate_single_mass_flow(row):
            try:
                return self.calculate_mass_flow(
                    row['concentration'], row['flow'],
                    concentration_unit=conc_unit,
                    flow_unit=flow_unit,
                    output_unit=output_unit
                )
            except Exception as e:
                logger.warning(f"Mass flow calculation failed for row: {e}")
                return np.nan
        
        merged_data['mass_flow'] = merged_data.apply(calculate_single_mass_flow, axis=1)
        
        # Reset index for consistent return format
        result = merged_data.reset_index()
        
        # Add metadata columns
        if 'parameter_name' in concentration_data.columns:
            result['parameter_name'] = concentration_data['parameter_name'].iloc[0]
        
        if 'site' in concentration_data.columns:
            result['site'] = concentration_data['site'].iloc[0]
            
        if 'sampling_point' in concentration_data.columns:
            result['sampling_point'] = concentration_data['sampling_point'].iloc[0]
            
        # Add unit information
        result['concentration_unit'] = conc_unit
        result['flow_unit'] = flow_unit
        result['mass_flow_unit'] = output_unit
        
        return result
    
    def convert_concentration(self, value: float, from_unit: str, to_unit: str) -> float:
        """
        Convert concentration from one unit to another
        
        Parameters
        ----------
        value : float
            Concentration value
        from_unit : str
            Source unit
        to_unit : str
            Target unit
            
        Returns
        -------
        float
            Converted concentration value
        """
        return self.unit_manager.convert_value(value, from_unit, to_unit)
    
    def convert_flow(self, value: float, from_unit: str, to_unit: str) -> float:
        """
        Convert flow from one unit to another
        
        Parameters
        ----------
        value : float
            Flow value
        from_unit : str
            Source unit
        to_unit : str
            Target unit
            
        Returns
        -------
        float
            Converted flow value
        """
        return self.unit_manager.convert_value(value, from_unit, to_unit)
    
    def get_compatible_units(self, unit_type: str) -> List[str]:
        """
        Get list of compatible units for a given type
        
        Parameters
        ----------
        unit_type : str
            Type of unit ('concentration', 'flow', or 'mass_flow')
            
        Returns
        -------
        List[str]
            List of compatible units
        """
        unit_suggestions = {
            'concentration': ['mg/L', 'g/L', 'kg/m³', 'µg/L', 'ng/L', 'ppm', 'ppb'],
            'flow': ['m³/h', 'L/s', 'L/min', 'L/h', 'm³/d'],
            'mass_flow': ['kg/h', 'kg/d', 'g/h', 'g/d', 't/year']
        }
        
        return unit_suggestions.get(unit_type, []) 