"""
Database module for storing and retrieving wastewater treatment plant data
"""
import os
import logging
from typing import Dict, List, Union, Optional, Any, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
import sqlalchemy as sa
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker, Session

from prolabdep.core.models import Base, Sample, Parameter, Measurement
from prolabdep.core.config import config

logger = logging.getLogger(__name__)


class Database:
    """
    Database manager for wastewater treatment plant data
    
    This class handles storage and retrieval of data using SQLAlchemy.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection
        
        Parameters
        ----------
        db_path : str, optional
            Path to the SQLite database file
        """
        if db_path is None:
            db_path = config.database_config['path']
        
        # Create absolute path if relative
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)
            
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Create engine
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.Session = sessionmaker(bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        
        logger.info(f"Database initialized at {db_path}")
    
    def store_data(self, data_dict: Dict[str, pd.DataFrame]) -> int:
        """
        Store processed data in the database
        
        Parameters
        ----------
        data_dict : Dict[str, pd.DataFrame]
            Dictionary containing processed dataframes:
            - 'data': Main processed data
            - 'parameters': Parameter definitions
            - 'samples': Sample metadata
            
        Returns
        -------
        int
            Number of measurements stored
        """
        # Extract dataframes
        data_df = data_dict.get('data')
        parameters_df = data_dict.get('parameters')
        samples_df = data_dict.get('samples')
        
        if data_df is None or parameters_df is None or samples_df is None:
            raise ValueError("Missing required dataframes in data_dict")
        
        session = self.Session()
        try:
            # 1. Store parameters
            self._store_parameters(session, parameters_df)
            
            # 2. Store samples
            self._store_samples(session, samples_df)
            
            # 3. Store measurements
            measurements_count = self._store_measurements(session, data_df)
            
            session.commit()
            logger.info(f"Stored {measurements_count} measurements in database")
            return measurements_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing data: {str(e)}")
            raise
        finally:
            session.close()
    
    def _store_parameters(self, session: Session, parameters_df: pd.DataFrame) -> None:
        """
        Store parameter definitions in database
        
        Parameters
        ----------
        session : sqlalchemy.Session
            Database session
        parameters_df : pd.DataFrame
            Parameters dataframe
        """
        parameters = Parameter.from_dataframe(parameters_df)
        
        for param in parameters:
            # Check if parameter already exists
            existing = session.query(Parameter).filter_by(code=param.code).first()
            if not existing:
                session.add(param)
            else:
                # Update if needed
                existing.name = param.name
                existing.method = param.method
                existing.unit = param.unit
                existing.description = param.description
    
    def _store_samples(self, session: Session, samples_df: pd.DataFrame) -> None:
        """
        Store sample metadata in database
        
        Parameters
        ----------
        session : sqlalchemy.Session
            Database session
        samples_df : pd.DataFrame
            Samples dataframe
        """
        samples = Sample.from_dataframe(samples_df)
        
        for sample in samples:
            # Check if sample already exists
            existing = session.query(Sample).filter_by(id=sample.id).first()
            if not existing:
                session.add(sample)
            else:
                # Update if needed
                existing.date = sample.date
                existing.municipality = sample.municipality
                existing.site = sample.site
                existing.sampling_point = sample.sampling_point
                existing.reason = sample.reason
                existing.sampling_method = sample.sampling_method
                existing.status = sample.status
    
    def _store_measurements(self, session: Session, data_df: pd.DataFrame) -> int:
        """
        Store measurements in database
        
        Parameters
        ----------
        session : sqlalchemy.Session
            Database session
        data_df : pd.DataFrame
            Data dataframe
            
        Returns
        -------
        int
            Number of measurements stored
        """
        count = 0
        measurements = Measurement.from_dataframe(data_df)
        
        for measurement in measurements:
            # Check if measurement already exists
            existing = session.query(Measurement).filter_by(
                sample_id=measurement.sample_id,
                parameter_code=measurement.parameter_code
            ).first()
            
            if not existing:
                # Create new measurement
                session.add(measurement)
                count += 1
            else:
                # Update existing measurement
                existing.value = measurement.value
        
        return count
    
    def get_samples(self, municipality: Optional[str] = None, site: Optional[str] = None, 
                   sampling_point: Optional[str] = None, date_from: Optional[Union[str, datetime]] = None,
                   date_to: Optional[Union[str, datetime]] = None) -> pd.DataFrame:
        """
        Retrieve samples matching criteria
        
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
            Dataframe with matching samples
        """
        session = self.Session()
        try:
            query = session.query(Sample)
            
            # Apply filters
            if municipality:
                query = query.filter(Sample.municipality == municipality)
            if site:
                query = query.filter(Sample.site.like(f"%{site}%"))
            if sampling_point:
                query = query.filter(Sample.sampling_point == sampling_point)
            
            # Handle date ranges
            if date_from:
                if isinstance(date_from, str):
                    date_from = pd.Timestamp(date_from)
                query = query.filter(Sample.date >= date_from)
                
            if date_to:
                if isinstance(date_to, str):
                    date_to = pd.Timestamp(date_to)
                query = query.filter(Sample.date <= date_to)
            
            # Execute query and convert to dataframe
            results = query.all()
            
            if not results:
                return pd.DataFrame()
                
            data = [sample.to_dict() for sample in results]
            return pd.DataFrame(data)
            
        finally:
            session.close()
    
    def get_parameter_data(self, parameter_name: str, 
                          filter_criteria: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Get time series data for a specific parameter
        
        Parameters
        ----------
        parameter_name : str
            Name of the parameter
        filter_criteria : Dict[str, Any], optional
            Criteria for filtering samples
            
        Returns
        -------
        pd.DataFrame
            Dataframe with parameter time series
        """
        if filter_criteria is None:
            filter_criteria = {}
            
        session = self.Session()
        try:
            # Build query to join samples, parameters, and measurements
            query = session.query(
                Sample.id.label('sample_id'),
                Sample.date,
                Sample.municipality,
                Sample.site,
                Sample.sampling_point,
                Parameter.name.label('parameter_name'),
                Parameter.unit,
                Measurement.value
            ).join(
                Measurement, Sample.id == Measurement.sample_id
            ).join(
                Parameter, Measurement.parameter_code == Parameter.code
            ).filter(
                Parameter.name == parameter_name
            )
            
            # Apply filters
            if 'municipality' in filter_criteria:
                query = query.filter(Sample.municipality == filter_criteria['municipality'])
            if 'site' in filter_criteria:
                query = query.filter(Sample.site.like(f"%{filter_criteria['site']}%"))
            if 'sampling_point' in filter_criteria:
                query = query.filter(Sample.sampling_point == filter_criteria['sampling_point'])
                
            # Handle date range
            if 'date_from' in filter_criteria:
                date_from = filter_criteria['date_from']
                if isinstance(date_from, str):
                    date_from = pd.Timestamp(date_from)
                query = query.filter(Sample.date >= date_from)
                
            if 'date_to' in filter_criteria:
                date_to = filter_criteria['date_to']
                if isinstance(date_to, str):
                    date_to = pd.Timestamp(date_to)
                query = query.filter(Sample.date <= date_to)
            
            # Order by date
            query = query.order_by(Sample.date)
            
            # Execute query and convert to dataframe
            results = query.all()
            
            if not results:
                # Try to find by parameter code if name doesn't work
                param_query = session.query(Parameter).filter(
                    Parameter.code.like(f"%{parameter_name}%")
                ).first()
                
                if param_query:
                    # Retry with the found parameter name
                    return self.get_parameter_data(param_query.name, filter_criteria)
                return pd.DataFrame()
                
            data = []
            for row in results:
                data.append({
                    'sample_id': row.sample_id,
                    'date': row.date,
                    'municipality': row.municipality,
                    'site': row.site,
                    'sampling_point': row.sampling_point,
                    'parameter_name': row.parameter_name,
                    'unit': row.unit,
                    'value': row.value
                })
            
            return pd.DataFrame(data)
            
        finally:
            session.close()
    
    def get_parameters(self) -> pd.DataFrame:
        """
        Get all parameter definitions
        
        Returns
        -------
        pd.DataFrame
            Dataframe with parameter definitions
        """
        session = self.Session()
        try:
            # Query all parameters
            parameters = session.query(Parameter).all()
            
            if not parameters:
                return pd.DataFrame()
                
            data = [param.to_dict() for param in parameters]
            return pd.DataFrame(data)
            
        finally:
            session.close()
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Execute a custom SQL query
        
        Parameters
        ----------
        query : str
            SQL query to execute
        params : Dict[str, Any], optional
            Query parameters
            
        Returns
        -------
        pd.DataFrame
            Query results as a dataframe
        """
        if params is None:
            params = {}
            
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            columns = result.keys()
            data = result.fetchall()
            
            if not data:
                return pd.DataFrame()
                
            return pd.DataFrame(data, columns=columns)
    
    def backup(self, backup_path: str) -> str:
        """
        Create a backup of the database
        
        Parameters
        ----------
        backup_path : str
            Path to save the backup
            
        Returns
        -------
        str
            Path to the backup file
        """
        import shutil
        
        # Get current database path
        db_path = self.engine.url.database
        
        # Create backup directory if it doesn't exist
        backup_dir = os.path.dirname(backup_path)
        if backup_dir and not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        logger.info(f"Database backed up to {backup_path}")
        return backup_path 