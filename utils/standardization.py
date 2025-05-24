"""
Standardization utilities for data normalization and flexible searching
"""
import re
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from difflib import get_close_matches

logger = logging.getLogger(__name__)


class StandardizationMappings:
    """
    Provides standardization mappings and utilities for normalizing data
    
    This class handles the standardization of non-standardized fields like
    site names, sampling points, and parameter names.
    """
    
    # Default mappings for common site names
    DEFAULT_SITE_MAPPINGS = {
        "dep. s. giusto": "San Giusto",
        "dep. centrale": "Centrale",
        "dep. san colombano": "San Colombano",
        "s. colombano": "San Colombano",
        # Add more mappings as needed
    }
    
    # Default mappings for common sampling points
    DEFAULT_SAMPLING_POINT_MAPPINGS = {
        "ingresso": "inlet",
        "uscita": "outlet",
        "entrata": "inlet",
        "in": "inlet",
        "out": "outlet",
        # Add more mappings as needed
    }
    
    # Default mappings for common parameter names
    DEFAULT_PARAMETER_MAPPINGS = {
        "cod": "COD",
        "bod": "BOD",
        "bod5": "BOD",
        "tss": "TSS",
        "solidi sospesi": "TSS",
        "azoto totale": "TN",
        "tn": "TN",
        "fosforo totale": "TP",
        "tp": "TP",
        # Add more mappings as needed
    }
    
    def __init__(
        self,
        site_mappings: Optional[Dict[str, str]] = None,
        sampling_point_mappings: Optional[Dict[str, str]] = None,
        parameter_mappings: Optional[Dict[str, str]] = None
    ):
        """
        Initialize standardization mappings
        
        Parameters
        ----------
        site_mappings : Dict[str, str], optional
            Custom mappings for site names
        sampling_point_mappings : Dict[str, str], optional
            Custom mappings for sampling points
        parameter_mappings : Dict[str, str], optional
            Custom mappings for parameter names
        """
        # Initialize with default mappings, update with custom mappings if provided
        self.site_mappings = self.DEFAULT_SITE_MAPPINGS.copy()
        if site_mappings:
            self.site_mappings.update(site_mappings)
            
        self.sampling_point_mappings = self.DEFAULT_SAMPLING_POINT_MAPPINGS.copy()
        if sampling_point_mappings:
            self.sampling_point_mappings.update(sampling_point_mappings)
            
        self.parameter_mappings = self.DEFAULT_PARAMETER_MAPPINGS.copy()
        if parameter_mappings:
            self.parameter_mappings.update(parameter_mappings)
    
    def standardize_site(self, site: str) -> str:
        """
        Standardize a site name
        
        Parameters
        ----------
        site : str
            Original site name
            
        Returns
        -------
        str
            Standardized site name
        """
        if not site:
            return ""
        
        site_lower = site.lower().strip()
        
        # Direct mapping lookup
        if site_lower in self.site_mappings:
            return self.site_mappings[site_lower]
        
        # Try to find a partial match
        for key, value in self.site_mappings.items():
            if key in site_lower:
                return value
        
        # If no match found, return the original with proper capitalization
        return site.strip()
    
    def standardize_sampling_point(self, sampling_point: str) -> str:
        """
        Standardize a sampling point
        
        Parameters
        ----------
        sampling_point : str
            Original sampling point
            
        Returns
        -------
        str
            Standardized sampling point
        """
        if not sampling_point:
            return ""
        
        sp_lower = sampling_point.lower().strip()
        
        # Direct mapping lookup
        if sp_lower in self.sampling_point_mappings:
            return self.sampling_point_mappings[sp_lower]
        
        # Try to find a partial match
        for key, value in self.sampling_point_mappings.items():
            if key in sp_lower:
                return value
        
        # If no match found, return the original
        return sampling_point.strip()
    
    def standardize_parameter(self, parameter: str) -> str:
        """
        Standardize a parameter name
        
        Parameters
        ----------
        parameter : str
            Original parameter name
            
        Returns
        -------
        str
            Standardized parameter name
        """
        if not parameter:
            return ""
        
        param_lower = parameter.lower().strip()
        
        # Direct mapping lookup
        if param_lower in self.parameter_mappings:
            return self.parameter_mappings[param_lower]
        
        # Try to find a partial match
        for key, value in self.parameter_mappings.items():
            if key in param_lower:
                return value
        
        # If no match found, return the original with proper capitalization
        return parameter.strip()
    
    def find_similar_sites(self, site: str, cutoff: float = 0.6) -> List[str]:
        """
        Find similar site names using fuzzy matching
        
        Parameters
        ----------
        site : str
            Site name to find matches for
        cutoff : float, optional
            Similarity threshold (0-1)
            
        Returns
        -------
        List[str]
            List of similar site names
        """
        if not site:
            return []
        
        site_lower = site.lower().strip()
        keys = list(self.site_mappings.keys())
        matches = get_close_matches(site_lower, keys, n=5, cutoff=cutoff)
        
        # Return the standardized versions of the matches
        return [self.site_mappings[match] for match in matches]
    
    def find_similar_sampling_points(self, sampling_point: str, cutoff: float = 0.6) -> List[str]:
        """
        Find similar sampling point names using fuzzy matching
        
        Parameters
        ----------
        sampling_point : str
            Sampling point name to find matches for
        cutoff : float, optional
            Similarity threshold (0-1)
            
        Returns
        -------
        List[str]
            List of similar sampling point names
        """
        if not sampling_point:
            return []
        
        sp_lower = sampling_point.lower().strip()
        keys = list(self.sampling_point_mappings.keys())
        matches = get_close_matches(sp_lower, keys, n=5, cutoff=cutoff)
        
        # Return the standardized versions of the matches
        return [self.sampling_point_mappings[match] for match in matches]
    
    def find_similar_parameters(self, parameter: str, cutoff: float = 0.6) -> List[str]:
        """
        Find similar parameter names using fuzzy matching
        
        Parameters
        ----------
        parameter : str
            Parameter name to find matches for
        cutoff : float, optional
            Similarity threshold (0-1)
            
        Returns
        -------
        List[str]
            List of similar parameter names
        """
        if not parameter:
            return []
        
        param_lower = parameter.lower().strip()
        keys = list(self.parameter_mappings.keys())
        matches = get_close_matches(param_lower, keys, n=5, cutoff=cutoff)
        
        # Return the standardized versions of the matches
        return [self.parameter_mappings[match] for match in matches]
    
    def add_site_mapping(self, original: str, standardized: str) -> None:
        """
        Add a new site mapping
        
        Parameters
        ----------
        original : str
            Original site name
        standardized : str
            Standardized site name
        """
        self.site_mappings[original.lower().strip()] = standardized
    
    def add_sampling_point_mapping(self, original: str, standardized: str) -> None:
        """
        Add a new sampling point mapping
        
        Parameters
        ----------
        original : str
            Original sampling point name
        standardized : str
            Standardized sampling point name
        """
        self.sampling_point_mappings[original.lower().strip()] = standardized
    
    def add_parameter_mapping(self, original: str, standardized: str) -> None:
        """
        Add a new parameter mapping
        
        Parameters
        ----------
        original : str
            Original parameter name
        standardized : str
            Standardized parameter name
        """
        self.parameter_mappings[original.lower().strip()] = standardized


# Create a singleton instance for global use
default_mappings = StandardizationMappings()


def standardize_location_info(location_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardize location information
    
    Parameters
    ----------
    location_info : Dict[str, Any]
        Dictionary containing location information
        
    Returns
    -------
    Dict[str, Any]
        Dictionary with standardized location information
    """
    result = location_info.copy()
    
    if 'site' in result and result['site']:
        result['site'] = default_mappings.standardize_site(result['site'])
    
    if 'sampling_point' in result and result['sampling_point']:
        result['sampling_point'] = default_mappings.standardize_sampling_point(result['sampling_point'])
    
    return result 