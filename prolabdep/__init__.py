"""
ProlabDep - A comprehensive package for wastewater treatment plant data analysis
"""

from prolabdep.processors import CSVProcessor, ExcelProcessor, DataValidator, DataProcessor
from prolabdep.core.database import Database
from prolabdep.analytics.timeseries import TimeSeriesAnalyzer
from prolabdep.analytics.statistics import StatisticsAnalyzer
from prolabdep.analytics.massflow import MassFlowCalculator
from prolabdep.analytics.trends import TrendAnalyzer
from prolabdep.visualization import Visualizer

__version__ = '0.1.0'

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