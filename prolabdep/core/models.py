"""
Data models for ProlabDep
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import pandas as pd


Base = declarative_base()


class Sample(Base):
    """Sample metadata table"""
    __tablename__ = 'samples'
    
    id = Column(String, primary_key=True)  # codice_prelievo
    date = Column(DateTime, index=True)
    municipality = Column(String, index=True)
    site = Column(String, index=True)
    site_std = Column(String, index=True)  # Standardized site name
    sampling_point = Column(String, index=True)
    sampling_point_std = Column(String, index=True)  # Standardized sampling point
    reason = Column(String)
    sampling_method = Column(String)
    status = Column(String)
    
    # Relationship with measurements
    measurements = relationship("Measurement", back_populates="sample")
    
    def __repr__(self):
        return f"<Sample(id='{self.id}', date='{self.date}', site='{self.site}')>"
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> list:
        """
        Create Sample objects from a dataframe
        
        Parameters
        ----------
        df : pd.DataFrame
            Dataframe with sample data
            
        Returns
        -------
        list
            List of Sample objects
        """
        samples = []
        
        # Handle both index and column-based sample IDs
        id_column = 'codice_prelievo' if 'codice_prelievo' in df.columns else 'id'
        date_column = 'data_prelievo' if 'data_prelievo' in df.columns else 'date'
        
        for _, row in df.iterrows():
            # Get sample ID from column or index
            sample_id = row.get(id_column, None)
            if sample_id is None and id_column in df.index.names:
                sample_id = row.name if not isinstance(row.name, tuple) else row.name[df.index.names.index(id_column)]
            
            # Skip if no valid ID
            if sample_id is None:
                continue
                
            sample = cls(
                id=sample_id,
                date=row.get(date_column),
                municipality=row.get('municipality'),
                site=row.get('site'),
                site_std=row.get('site_std', row.get('site')),  # Use standardized if available
                sampling_point=row.get('sampling_point'),
                sampling_point_std=row.get('sampling_point_std', row.get('sampling_point')),  # Use standardized if available
                reason=row.get('motivo_prelievo', row.get('reason')),
                sampling_method=row.get('modo_prelievo', row.get('sampling_method')),
                status=row.get('stato', row.get('status'))
            )
            samples.append(sample)
        return samples
    
    def to_dict(self) -> dict:
        """
        Convert Sample to dictionary
        
        Returns
        -------
        dict
            Dictionary representation of Sample
        """
        return {
            'id': self.id,
            'date': self.date,
            'municipality': self.municipality,
            'site': self.site,
            'site_std': self.site_std,
            'sampling_point': self.sampling_point,
            'sampling_point_std': self.sampling_point_std,
            'reason': self.reason,
            'sampling_method': self.sampling_method,
            'status': self.status
        }


class Parameter(Base):
    """Parameter definition table"""
    __tablename__ = 'parameters'
    
    code = Column(String, primary_key=True)  # codice_param
    name = Column(String, index=True)
    name_std = Column(String, index=True)  # Standardized parameter name
    method = Column(String)
    unit = Column(String)
    description = Column(String)
    
    # Relationship with measurements
    measurements = relationship("Measurement", back_populates="parameter")
    
    def __repr__(self):
        return f"<Parameter(code='{self.code}', name='{self.name}', unit='{self.unit}')>"
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> list:
        """
        Create Parameter objects from a dataframe
        
        Parameters
        ----------
        df : pd.DataFrame
            Dataframe with parameter data
            
        Returns
        -------
        list
            List of Parameter objects
        """
        parameters = []
        
        # Map various column names to standard names
        code_col = next((col for col in ['codice_param', 'code'] if col in df.columns), None)
        name_col = next((col for col in ['nome_param', 'name'] if col in df.columns), None)
        name_std_col = next((col for col in ['nome_param_std', 'name_std'] if col in df.columns), None)
        method_col = next((col for col in ['metodo', 'method'] if col in df.columns), None)
        unit_col = next((col for col in ['udm', 'unit'] if col in df.columns), None)
        desc_col = next((col for col in ['descrizione', 'description'] if col in df.columns), None)
        
        if not all([code_col, name_col]):
            # Cannot create parameters without code and name
            return []
            
        for _, row in df.iterrows():
            param = cls(
                code=row[code_col],
                name=row[name_col],
                name_std=row[name_std_col] if name_std_col and name_std_col in row else row[name_col],  # Use standardized if available
                method=row[method_col] if method_col else None,
                unit=row[unit_col] if unit_col else None,
                description=row[desc_col] if desc_col else ''
            )
            parameters.append(param)
        return parameters
    
    def to_dict(self) -> dict:
        """
        Convert Parameter to dictionary
        
        Returns
        -------
        dict
            Dictionary representation of Parameter
        """
        return {
            'code': self.code,
            'name': self.name,
            'name_std': self.name_std,
            'method': self.method,
            'unit': self.unit,
            'description': self.description
        }


class Measurement(Base):
    """Measurement values table"""
    __tablename__ = 'measurements'
    
    id = Column(Integer, primary_key=True)
    sample_id = Column(String, ForeignKey('samples.id'), index=True)
    parameter_code = Column(String, ForeignKey('parameters.code'), index=True)
    value = Column(Float)
    
    # Relationships
    sample = relationship("Sample", back_populates="measurements")
    parameter = relationship("Parameter", back_populates="measurements")
    
    def __repr__(self):
        return f"<Measurement(sample_id='{self.sample_id}', parameter_code='{self.parameter_code}', value={self.value})>"
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> list:
        """
        Create Measurement objects from a dataframe
        
        Parameters
        ----------
        df : pd.DataFrame
            Dataframe with measurement data
            
        Returns
        -------
        list
            List of Measurement objects
        """
        measurements = []
        
        # Map various column names to standard names
        sample_id_col = next((col for col in ['codice_prelievo', 'sample_id', 'id'] if col in df.columns), None)
        param_code_col = next((col for col in ['codice_param', 'parameter_code'] if col in df.columns), None)
        value_col = next((col for col in ['valore', 'value'] if col in df.columns), None)
        
        if not all([sample_id_col, param_code_col, value_col]):
            # Cannot create measurements without required columns
            return []
            
        for _, row in df.iterrows():
            measurement = cls(
                sample_id=row[sample_id_col],
                parameter_code=row[param_code_col],
                value=float(row[value_col]) if pd.notna(row[value_col]) else None
            )
            measurements.append(measurement)
        return measurements
    
    def to_dict(self) -> dict:
        """
        Convert Measurement to dictionary
        
        Returns
        -------
        dict
            Dictionary representation of Measurement
        """
        return {
            'id': self.id,
            'sample_id': self.sample_id,
            'parameter_code': self.parameter_code,
            'value': self.value
        } 