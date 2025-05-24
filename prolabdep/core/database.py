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
from sqlalchemy import create_engine, select, text, or_, func, Index, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from functools import lru_cache

from prolabdep.core.models import Base, Sample, Parameter, Measurement
from prolabdep.core.config import config
from prolabdep.utils.standardization import default_mappings

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
            # Use default path in user's home directory
            home_dir = os.path.expanduser("~")
            db_dir = os.path.join(home_dir, ".prolabdep")
            
            # Create directory if it doesn't exist
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)
                
            db_path = os.path.join(db_dir, "prolabdep.db")
            
        logger.info(f"Using database at {db_path}")
        
        # Create database engine with optimizations
        if db_path == ":memory:" or "sqlite" in db_path.lower():
            # SQLite-specific configuration
            self.engine = create_engine(
                f"sqlite:///{db_path}",
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for query debugging
            )
        else:
            # Other database configurations (PostgreSQL, MySQL, etc.)
            self.engine = create_engine(
                f"sqlite:///{db_path}",
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for query debugging
            )
        
        # Set up SQLite optimization pragmas using events
        self._setup_sqlite_pragmas()
        
        self.Session = sessionmaker(bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        
        # Create additional indexes for performance
        self._create_indexes()
        
        logger.info(f"Database initialized at {db_path}")
    
    def _setup_sqlite_pragmas(self):
        """Set up SQLite pragma optimizations using SQLAlchemy events"""
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for better performance"""
            cursor = dbapi_connection.cursor()
            try:
                # Performance optimizations
                cursor.execute("PRAGMA synchronous = OFF")  # Faster writes
                cursor.execute("PRAGMA cache_size = 100000")  # 100MB cache
                cursor.execute("PRAGMA temp_store = memory")  # Store temp data in memory
                cursor.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
                cursor.execute("PRAGMA mmap_size = 268435456")  # 256MB memory map
                cursor.execute("PRAGMA page_size = 4096")  # Optimize page size
                cursor.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
            except Exception as e:
                logger.warning(f"Could not set SQLite pragmas: {e}")
            finally:
                cursor.close()
    
    def _create_indexes(self):
        """Create additional indexes for better query performance"""
        try:
            with self.engine.connect() as conn:
                # Composite indexes for common query patterns
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_samples_site_date 
                    ON samples (site, date)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_samples_site_std_date 
                    ON samples (site_std, date)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_measurements_param_value 
                    ON measurements (parameter_code, value)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_parameters_name_std 
                    ON parameters (name_std)
                """))
                conn.commit()
        except Exception as e:
            logger.warning(f"Could not create additional indexes: {e}")
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions with automatic cleanup"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def store_data(self, data_dict: Dict[str, pd.DataFrame]) -> int:
        """
        Store processed data in the database with batch operations
        
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
        
        with self.get_session() as session:
            # 1. Store parameters (batch upsert)
            self._store_parameters_batch(session, parameters_df)
            
            # 2. Store samples (batch upsert)
            self._store_samples_batch(session, samples_df)
            
            # 3. Store measurements (batch insert)
            measurements_count = self._store_measurements_batch(session, data_df)
            
            logger.info(f"Stored {measurements_count} measurements in database")
            return measurements_count
    
    def _store_parameters_batch(self, session: Session, parameters_df: pd.DataFrame) -> None:
        """
        Store parameter definitions using batch operations
        """
        # Convert to dict records for bulk operations
        param_records = []
        for _, row in parameters_df.iterrows():
            # Handle both CSV processor format and direct database format
            code = row.get('codice_param') or row.get('code')
            if not code or pd.isna(code):
                continue
                
            record = {
                'code': code,
                'name': row.get('nome_param') or row.get('name', ''),
                'name_std': row.get('nome_param_std') or row.get('name_std', ''),
                'method': row.get('metodo') or row.get('method', ''),
                'unit': row.get('udm') or row.get('unit', ''),
                'description': row.get('descrizione') or row.get('description', '')
            }
            param_records.append(record)
        
        # Use bulk insert/update on conflict
        if param_records:
            # SQLite-specific upsert using INSERT OR REPLACE
            for record in param_records:
                session.execute(text("""
                    INSERT OR REPLACE INTO parameters 
                    (code, name, name_std, method, unit, description)
                    VALUES (:code, :name, :name_std, :method, :unit, :description)
                """), record)
    
    def _store_samples_batch(self, session: Session, samples_df: pd.DataFrame) -> None:
        """
        Store sample metadata using batch operations
        """
        # Prepare data for bulk insert
        sample_records = []
        for _, row in samples_df.iterrows():
            # Try different column names for sample ID
            sample_id = row.get('id') or row.get('codice_prelievo') or row.name
            if not sample_id or pd.isna(sample_id):
                continue
                
            # Convert pandas Timestamp to Python datetime if needed
            date_value = row.get('date') or row.get('data_prelievo')
            if pd.notna(date_value):
                if hasattr(date_value, 'to_pydatetime'):
                    date_value = date_value.to_pydatetime()
                elif hasattr(date_value, 'date'):
                    date_value = date_value.date()
            else:
                date_value = None
                
            record = {
                'id': str(sample_id),  # Ensure ID is stored as string
                'date': date_value,
                'municipality': row.get('municipality', ''),
                'site': row.get('site', ''),
                'site_std': row.get('site_std', row.get('site', '')),
                'sampling_point': row.get('sampling_point', ''),
                'sampling_point_std': row.get('sampling_point_std', row.get('sampling_point', '')),
                'reason': row.get('reason', row.get('motivo_prelievo', '')),
                'sampling_method': row.get('sampling_method', row.get('modo_prelievo', '')),
                'status': row.get('status', row.get('stato', ''))
            }
            sample_records.append(record)
        
        # Batch upsert
        if sample_records:
            for record in sample_records:
                session.execute(text("""
                    INSERT OR REPLACE INTO samples 
                    (id, date, municipality, site, site_std, sampling_point, 
                     sampling_point_std, reason, sampling_method, status)
                    VALUES (:id, :date, :municipality, :site, :site_std, 
                            :sampling_point, :sampling_point_std, :reason, 
                            :sampling_method, :status)
                """), record)
    
    def _store_measurements_batch(self, session: Session, data_df: pd.DataFrame) -> int:
        """
        Store measurements using bulk insert operations
        """
        measurement_records = []
        
        for _, row in data_df.iterrows():
            # Handle both CSV processor format and direct database format
            sample_id = row.get('codice_prelievo') or row.get('sample_id') or row.name
            parameter_code = row.get('codice_param') or row.get('parameter_code')
            value = row.get('valore') or row.get('value')
            
            # Skip invalid records
            if not sample_id or not parameter_code or pd.isna(value):
                continue
                
            measurement_records.append({
                'sample_id': sample_id,
                'parameter_code': parameter_code,
                'value': float(value)
            })
        
        # Batch insert with individual statements to avoid foreign key issues
        if measurement_records:
            for record in measurement_records:
                session.execute(text("""
                    INSERT OR REPLACE INTO measurements 
                    (sample_id, parameter_code, value)
                    VALUES (:sample_id, :parameter_code, :value)
                """), record)
        
        return len(measurement_records)
    
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
            
            # Handle date ranges - use date() function to compare only dates, not timestamps
            if date_from:
                if isinstance(date_from, str):
                    date_from = pd.Timestamp(date_from).date()
                elif isinstance(date_from, datetime):
                    date_from = date_from.date()
                query = query.filter(func.date(Sample.date) >= date_from)
                
            if date_to:
                if isinstance(date_to, str):
                    date_to = pd.Timestamp(date_to).date()
                elif isinstance(date_to, datetime):
                    date_to = date_to.date()
                query = query.filter(func.date(Sample.date) <= date_to)
            
            # Execute query and convert to dataframe
            results = query.all()
            
            if not results:
                return pd.DataFrame()
                
            data = [sample.to_dict() for sample in results]
            return pd.DataFrame(data)
            
        finally:
            session.close()
    
    def get_parameter_data(self, parameter_name: str, 
                          filter_criteria: Dict[str, Any] = None,
                          search_mode: str = 'exact') -> pd.DataFrame:
        """
        Get time series data for a specific parameter
        
        Parameters
        ----------
        parameter_name : str
            Name of the parameter
        filter_criteria : Dict[str, Any], optional
            Criteria for filtering samples
        search_mode : str, optional
            Search mode: 'exact', 'contains', or 'fuzzy'
            
        Returns
        -------
        pd.DataFrame
            Dataframe with parameter time series
        """
        if filter_criteria is None:
            filter_criteria = {}
            
        # Standardize parameter name for searching
        std_parameter = default_mappings.standardize_parameter(parameter_name)
        
        session = self.Session()
        try:
            # Build query to join samples, parameters, and measurements
            query = session.query(
                Sample.id.label('sample_id'),
                Sample.date,
                Sample.municipality,
                Sample.site,
                Sample.site_std,
                Sample.sampling_point,
                Sample.sampling_point_std,
                Parameter.name.label('parameter_name'),
                Parameter.name_std.label('parameter_name_std'),
                Parameter.unit,
                Measurement.value
            ).join(
                Measurement, Sample.id == Measurement.sample_id
            ).join(
                Parameter, Measurement.parameter_code == Parameter.code
            )
            
            # Apply parameter filter based on search mode
            if search_mode == 'exact':
                # Try both standardized and original parameter names
                query = query.filter(or_(
                    Parameter.name == parameter_name,
                    Parameter.name_std == std_parameter
                ))
            elif search_mode == 'contains':
                # Use LIKE for partial matches
                query = query.filter(or_(
                    Parameter.name.like(f"%{parameter_name}%"),
                    Parameter.name_std.like(f"%{std_parameter}%")
                ))
            elif search_mode == 'fuzzy':
                # For fuzzy matching, we need to post-process the results
                # First, get a broader set of results - use a very loose filter
                # to ensure we get potential matches even with short strings like 'CD'
                if len(parameter_name) <= 2:
                    # For very short strings, get all parameters and filter later
                    pass  # No filter, get all parameters
                else:
                    # For longer strings, use a prefix filter to reduce the result set
                    query = query.filter(or_(
                        Parameter.name.like(f"%{parameter_name[:2]}%"),
                        Parameter.name_std.like(f"%{std_parameter[:2]}%")
                    ))
            else:
                # Default to exact match
                query = query.filter(or_(
                    Parameter.name == parameter_name,
                    Parameter.name_std == std_parameter
                ))
            
            # Apply filters
            if 'municipality' in filter_criteria:
                query = query.filter(Sample.municipality == filter_criteria['municipality'])
                
            if 'site' in filter_criteria:
                site = filter_criteria['site']
                std_site = default_mappings.standardize_site(site)
                
                # Try both standardized and original site names
                query = query.filter(or_(
                    Sample.site.like(f"%{site}%"),
                    Sample.site_std.like(f"%{std_site}%")
                ))
                
            if 'sampling_point' in filter_criteria:
                sp = filter_criteria['sampling_point']
                std_sp = default_mappings.standardize_sampling_point(sp)
                
                # Try both standardized and original sampling points
                query = query.filter(or_(
                    Sample.sampling_point.like(f"%{sp}%"),
                    Sample.sampling_point_std.like(f"%{std_sp}%")
                ))
                
            # Handle date range
            if 'date_from' in filter_criteria:
                date_from = filter_criteria['date_from']
                if isinstance(date_from, str):
                    date_from = pd.Timestamp(date_from).date()
                elif isinstance(date_from, datetime):
                    date_from = date_from.date()
                query = query.filter(func.date(Sample.date) >= date_from)
                
            if 'date_to' in filter_criteria:
                date_to = filter_criteria['date_to']
                if isinstance(date_to, str):
                    date_to = pd.Timestamp(date_to).date()
                elif isinstance(date_to, datetime):
                    date_to = date_to.date()
                query = query.filter(func.date(Sample.date) <= date_to)
            
            # Order by date
            query = query.order_by(Sample.date)
            
            # Execute query with a timeout to prevent connection pool exhaustion
            # Limit to 1000 results max to prevent memory issues
            query = query.limit(1000)
            results = query.all()
            
            if not results:
                # If no results, try to find similar parameters
                similar_params = default_mappings.find_similar_parameters(parameter_name)
                if similar_params:
                    logger.info(f"No exact match for '{parameter_name}', suggesting: {similar_params}")
                return pd.DataFrame()
                
            data = []
            for row in results:
                data.append({
                    'sample_id': row.sample_id,
                    'date': row.date,
                    'municipality': row.municipality,
                    'site': row.site,
                    'site_std': row.site_std,
                    'sampling_point': row.sampling_point,
                    'sampling_point_std': row.sampling_point_std,
                    'parameter_name': row.parameter_name,
                    'parameter_name_std': row.parameter_name_std,
                    'unit': row.unit,
                    'value': row.value
                })
            
            result_df = pd.DataFrame(data)
            
            # If using fuzzy search, post-process to get only the closest matches
            if search_mode == 'fuzzy' and not result_df.empty:
                from difflib import SequenceMatcher
                
                def similarity_score(s1, s2):
                    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
                
                # Calculate similarity scores
                result_df['similarity'] = result_df['parameter_name'].apply(
                    lambda x: similarity_score(x, parameter_name)
                )
                
                # Filter by similarity threshold
                result_df = result_df[result_df['similarity'] > 0.6]
                
                # Sort by similarity and drop the column
                result_df = result_df.sort_values('similarity', ascending=False)
                result_df = result_df.drop('similarity', axis=1)
            
            return result_df
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_parameter_data: {str(e)}")
            return pd.DataFrame()
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