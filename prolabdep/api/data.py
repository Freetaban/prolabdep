"""
Data access API module
"""
from typing import Dict, List, Optional, Union, Any
import pandas as pd
from datetime import datetime

from prolabdep.core.database import Database


class DataAPI:
    """
    Data access API for ProlabDep
    
    This class provides methods for data retrieval and management.
    """
    
    def __init__(self, database: Database):
        """
        Initialize the data API
        
        Parameters
        ----------
        database : Database
            Database instance
        """
        self.db = database
    
    def get_parameters(self) -> pd.DataFrame:
        """
        Get all parameters
        
        Returns
        -------
        pd.DataFrame
            DataFrame containing parameter definitions
        """
        return self.db.get_parameters()
    
    def get_samples(self, municipality: Optional[str] = None, 
                   site: Optional[str] = None,
                   sampling_point: Optional[str] = None, 
                   date_from: Optional[Union[str, datetime]] = None,
                   date_to: Optional[Union[str, datetime]] = None) -> pd.DataFrame:
        """
        Get samples matching criteria
        
        Parameters
        ----------
        municipality : str, optional
            Municipality code
        site : str, optional
            Site name
        sampling_point : str, optional
            Sampling point
        date_from : Union[str, datetime], optional
            Start date
        date_to : Union[str, datetime], optional
            End date
            
        Returns
        -------
        pd.DataFrame
            DataFrame containing sample data
        """
        return self.db.get_samples(
            municipality=municipality,
            site=site,
            sampling_point=sampling_point,
            date_from=date_from,
            date_to=date_to
        )
    
    def get_parameter_data(self, parameter_name: str,
                          filter_criteria: Dict[str, Any]) -> pd.DataFrame:
        """
        Get parameter data matching criteria
        
        Parameters
        ----------
        parameter_name : str
            Parameter name
        filter_criteria : Dict[str, Any]
            Criteria for filtering samples
            
        Returns
        -------
        pd.DataFrame
            DataFrame containing parameter data
        """
        return self.db.get_parameter_data(parameter_name, filter_criteria)
    
    def get_municipalities(self) -> List[str]:
        """
        Get all municipalities
        
        Returns
        -------
        List[str]
            List of municipality codes
        """
        samples = self.db.get_samples()
        if samples.empty or 'municipality' not in samples.columns:
            return []
        return sorted(samples['municipality'].dropna().unique().tolist())
    
    def get_sites(self, municipality: Optional[str] = None) -> List[str]:
        """
        Get all sites
        
        Parameters
        ----------
        municipality : str, optional
            Municipality code
            
        Returns
        -------
        List[str]
            List of site names
        """
        if municipality:
            samples = self.db.get_samples(municipality=municipality)
        else:
            samples = self.db.get_samples()
            
        if samples.empty or 'site' not in samples.columns:
            return []
        return sorted(samples['site'].dropna().unique().tolist())
    
    def get_sampling_points(self, site: Optional[str] = None) -> List[str]:
        """
        Get all sampling points
        
        Parameters
        ----------
        site : str, optional
            Site name
            
        Returns
        -------
        List[str]
            List of sampling point names
        """
        if site:
            samples = self.db.get_samples(site=site)
        else:
            samples = self.db.get_samples()
            
        if samples.empty or 'sampling_point' not in samples.columns:
            return []
        return sorted(samples['sampling_point'].dropna().unique().tolist()) 