"""
ProlabDep - A comprehensive package for wastewater treatment plant data analysis

Performance-optimized version with improved database operations, 
vectorized data processing, and intelligent caching.
"""

# Apply performance optimizations on import
def _initialize_performance():
    """Initialize performance optimizations"""
    try:
        from prolabdep.utils.performance import optimize_pandas_settings
        optimize_pandas_settings()
    except ImportError:
        pass  # Gracefully handle if psutil is not available

_initialize_performance()

# Import main components
from prolabdep.processors import CSVProcessor, ExcelProcessor, DataValidator, DataProcessor
from prolabdep.core.database import Database
from prolabdep.analytics.timeseries import TimeSeriesAnalyzer
from prolabdep.analytics.statistics import StatisticsAnalyzer
from prolabdep.analytics.massflow import MassFlowCalculator
from prolabdep.analytics.trends import TrendAnalyzer
from prolabdep.visualization import Visualizer

# Performance utilities
try:
    from prolabdep.utils.performance import performance_monitor, monitor_performance
    __all__ = [
        'DataProcessor',
        'CSVProcessor',
        'ExcelProcessor',
        'DataValidator',
        'Database',
        'TimeSeriesAnalyzer',
        'StatisticsAnalyzer',
        'MassFlowCalculator',
        'TrendAnalyzer',
        'Visualizer',
        'performance_monitor',
        'monitor_performance',
    ]
except ImportError:
    __all__ = [
        'DataProcessor',
        'CSVProcessor',
        'ExcelProcessor',
        'DataValidator',
        'Database',
        'TimeSeriesAnalyzer',
        'StatisticsAnalyzer',
        'MassFlowCalculator',
        'TrendAnalyzer',
        'Visualizer',
    ]

__version__ = '0.2.0'  # Increment version for optimized release 