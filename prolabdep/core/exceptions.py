"""
Custom exceptions for ProlabDep
"""


class ProlabDepError(Exception):
    """Base exception for all ProlabDep errors"""
    pass


class ConfigError(ProlabDepError):
    """Error in configuration"""
    pass


class DatabaseError(ProlabDepError):
    """Error in database operations"""
    pass


class ProcessingError(ProlabDepError):
    """Error during data processing"""
    pass


class ValidationError(ProlabDepError):
    """Data validation error"""
    pass


class AnalysisError(ProlabDepError):
    """Error during data analysis"""
    pass


class ExportError(ProlabDepError):
    """Error during data export"""
    pass


class ParameterNotFoundError(ProlabDepError):
    """Parameter not found in database"""
    
    def __init__(self, parameter_name):
        self.parameter_name = parameter_name
        super().__init__(f"Parameter not found: {parameter_name}")


class SampleNotFoundError(ProlabDepError):
    """Sample not found in database"""
    
    def __init__(self, sample_id):
        self.sample_id = sample_id
        super().__init__(f"Sample not found: {sample_id}")


class InsufficientDataError(ProlabDepError):
    """Not enough data for analysis"""
    pass 