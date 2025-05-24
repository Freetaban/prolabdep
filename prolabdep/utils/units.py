"""
Unit management utilities using Pint for proper unit handling and conversions

This module provides a comprehensive unit handling system for wastewater treatment
plant data analysis, supporting proper unit conversions, dimensional analysis,
and standardization of various unit formats.
"""
import logging
import re
from typing import Dict, List, Optional, Tuple, Union, Any
from functools import lru_cache

import pint
from pint import UnitRegistry, Quantity, DimensionalityError

logger = logging.getLogger(__name__)


class UnitManager:
    """
    Unit management system using Pint for proper unit handling
    
    This class provides standardized unit handling, conversion, and validation
    for wastewater treatment plant parameters using the Pint library.
    """
    
    def __init__(self):
        """Initialize unit manager with custom definitions for wastewater parameters"""
        self.ureg = UnitRegistry()
        
        # Define custom units specific to wastewater treatment
        self._setup_custom_units()
        
        # Common unit aliases and mappings
        self._setup_unit_mappings()
        
        # Cache for parsed units to improve performance
        self._unit_cache = {}
    
    def _setup_custom_units(self):
        """Setup custom units and aliases for wastewater treatment"""
        try:
            # Add common aliases for concentrations
            self.ureg.define("ppm = mg/L")  # parts per million
            self.ureg.define("ppb = µg/L")  # parts per billion
            
            # Add dimensionless pH unit
            self.ureg.define("pH_unit = []")  # dimensionless pH
            
            # Add common flow units if not already defined
            if "l/s" not in str(self.ureg):
                self.ureg.define("l_per_s = L/s")
            
        except Exception as e:
            logger.warning(f"Could not define custom units: {e}")
    
    def _setup_unit_mappings(self):
        """Setup mappings for common non-standard unit formats"""
        self.unit_mappings = {
            # Concentration units (various cases and formats)
            'mg/l': 'mg/L',
            'MG/L': 'mg/L',
            'g/l': 'g/L',
            'G/L': 'g/L',
            'µg/l': 'µg/L',
            'UG/L': 'µg/L',
            'ug/l': 'µg/L',
            'ng/l': 'ng/L',
            'NG/L': 'ng/L',
            'ppm': 'mg/L',
            'PPM': 'mg/L',
            'ppb': 'µg/L',
            'PPB': 'µg/L',
            
            # Flow units
            'm3/h': 'm³/h',
            'M3/H': 'm³/h',
            'm3/d': 'm³/d',
            'M3/D': 'm³/d',
            'l/s': 'L/s',
            'L/S': 'L/s',
            'l/min': 'L/min',
            'L/MIN': 'L/min',
            'l/h': 'L/h',
            'L/H': 'L/h',
            
            # Mass flow units
            'kg/h': 'kg/h',
            'KG/H': 'kg/h',
            'kg/d': 'kg/d',
            'KG/D': 'kg/d',
            'g/h': 'g/h',
            'G/H': 'g/h',
            'g/d': 'g/d',
            'G/D': 'g/d',
            't/y': 't/year',
            'T/Y': 't/year',
            
            # Dimensionless units
            '-': 'dimensionless',
            'pH': 'pH_unit',
            'PH': 'pH_unit',
            '': 'dimensionless',
            'adim': 'dimensionless',
            'ADIM': 'dimensionless',
            
            # Temperature
            '°C': 'celsius',
            'degC': 'celsius',
            'DEGC': 'celsius',
            '°F': 'fahrenheit',
            'degF': 'fahrenheit',
            'DEGF': 'fahrenheit',
        }
    
    @lru_cache(maxsize=1000)
    def parse_unit(self, unit_str: str) -> Optional[Quantity]:
        """
        Parse a unit string and return a Pint Quantity
        
        Parameters
        ----------
        unit_str : str
            Unit string to parse
            
        Returns
        -------
        Optional[Quantity]
            Pint Quantity object or None if parsing fails
        """
        if not unit_str or unit_str.strip() == '':
            return self.ureg.dimensionless
        
        # Clean the unit string
        clean_unit = unit_str.strip()
        
        # Check if we have a direct mapping
        if clean_unit in self.unit_mappings:
            clean_unit = self.unit_mappings[clean_unit]
        
        try:
            # Try to parse with Pint
            return self.ureg.parse_expression(clean_unit)
        except Exception as e:
            logger.warning(f"Could not parse unit '{unit_str}': {e}")
            # Try some common substitutions
            try:
                # Replace common problematic characters
                clean_unit = clean_unit.replace('³', '3').replace('²', '2')
                return self.ureg.parse_expression(clean_unit)
            except Exception:
                logger.error(f"Failed to parse unit '{unit_str}' even after substitutions")
                return None
    
    def standardize_unit(self, unit_str: str) -> str:
        """
        Standardize a unit string to a consistent format
        
        Parameters
        ----------
        unit_str : str
            Unit string to standardize
            
        Returns
        -------
        str
            Standardized unit string
        """
        if not unit_str:
            return 'dimensionless'
        
        # Parse the unit
        unit = self.parse_unit(unit_str)
        if unit is None:
            return unit_str  # Return original if parsing fails
        
        # Return the standard string representation
        return str(unit.units)
    
    def convert_value(self, value: float, from_unit: str, to_unit: str) -> float:
        """
        Convert a value from one unit to another
        
        Parameters
        ----------
        value : float
            Value to convert
        from_unit : str
            Source unit
        to_unit : str
            Target unit
            
        Returns
        -------
        float
            Converted value
            
        Raises
        ------
        DimensionalityError
            If units are not compatible
        ValueError
            If units cannot be parsed
        """
        if value is None:
            return None
        
        # Parse both units
        from_qty = self.parse_unit(from_unit)
        to_qty = self.parse_unit(to_unit)
        
        if from_qty is None:
            raise ValueError(f"Cannot parse source unit: {from_unit}")
        if to_qty is None:
            raise ValueError(f"Cannot parse target unit: {to_unit}")
        
        # Create quantity with value and source unit
        source_quantity = value * from_qty
        
        # Convert to target unit
        try:
            converted = source_quantity.to(to_qty.units)
            return converted.magnitude
        except DimensionalityError as e:
            raise DimensionalityError(f"Cannot convert from {from_unit} to {to_unit}: {e}")
    
    def are_compatible(self, unit1: str, unit2: str) -> bool:
        """
        Check if two units are dimensionally compatible
        
        Parameters
        ----------
        unit1 : str
            First unit
        unit2 : str
            Second unit
            
        Returns
        -------
        bool
            True if units are compatible
        """
        try:
            qty1 = self.parse_unit(unit1)
            qty2 = self.parse_unit(unit2)
            
            if qty1 is None or qty2 is None:
                return False
            
            # Try to convert between them
            test_value = 1.0 * qty1
            test_value.to(qty2.units)
            return True
        except (DimensionalityError, Exception):
            return False
    
    def get_unit_dimensionality(self, unit_str: str) -> str:
        """
        Get the dimensionality of a unit (e.g., mass, length, etc.)
        
        Parameters
        ----------
        unit_str : str
            Unit string
            
        Returns
        -------
        str
            Dimensionality string
        """
        unit = self.parse_unit(unit_str)
        if unit is None:
            return "unknown"
        
        return str(unit.dimensionality)
    
    def extract_unit_from_parameter_code(self, parameter_code: str) -> str:
        """
        Extract unit from parameter code in format "PARAM@METHOD@UNIT"
        
        Parameters
        ----------
        parameter_code : str
            Parameter code
            
        Returns
        -------
        str
            Extracted unit or empty string
        """
        if not parameter_code or '@' not in parameter_code:
            return ''
        
        parts = parameter_code.split('@')
        if len(parts) >= 3:
            return parts[-1]  # Last part is the unit
        return ''
    
    def calculate_mass_flow(self, concentration: float, concentration_unit: str,
                           flow: float, flow_unit: str, 
                           target_unit: str = 'kg/h') -> float:
        """
        Calculate mass flow using proper unit conversions
        
        Parameters
        ----------
        concentration : float
            Concentration value
        concentration_unit : str
            Concentration unit
        flow : float
            Flow value
        flow_unit : str
            Flow unit
        target_unit : str
            Target mass flow unit
            
        Returns
        -------
        float
            Mass flow in target units
        """
        try:
            # Create quantities
            conc_qty = concentration * self.parse_unit(concentration_unit)
            flow_qty = flow * self.parse_unit(flow_unit)
            
            # Calculate mass flow
            mass_flow_qty = conc_qty * flow_qty
            
            # Convert to target unit
            target_qty = self.parse_unit(target_unit)
            result = mass_flow_qty.to(target_qty.units)
            
            return result.magnitude
        except Exception as e:
            logger.error(f"Error calculating mass flow: {e}")
            raise ValueError(f"Cannot calculate mass flow: {e}")
    
    def suggest_common_units(self, dimensionality: str) -> List[str]:
        """
        Suggest common units for a given dimensionality
        
        Parameters
        ----------
        dimensionality : str
            Dimensionality (e.g., '[mass] / [length] ** 3')
            
        Returns
        -------
        List[str]
            List of common units for this dimensionality
        """
        common_units = {
            '[mass] / [length] ** 3': ['mg/L', 'g/L', 'kg/m³', 'µg/L'],
            '[length] ** 3 / [time]': ['m³/h', 'L/s', 'L/min', 'm³/d'],
            '[mass] / [time]': ['kg/h', 'kg/d', 'g/h', 't/year'],
            '[temperature]': ['celsius', 'fahrenheit', 'kelvin'],
            '[]': ['dimensionless', 'pH_unit', 'percent'],
        }
        
        return common_units.get(dimensionality, [])


# Global unit manager instance
unit_manager = UnitManager() 