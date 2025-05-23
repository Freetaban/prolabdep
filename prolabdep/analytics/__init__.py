"""
Analytics module for data analysis and calculations
"""

from prolabdep.analytics.timeseries import TimeSeriesAnalyzer
from prolabdep.analytics.statistics import StatisticsAnalyzer
from prolabdep.analytics.massflow import MassFlowCalculator
from prolabdep.analytics.trends import TrendAnalyzer

__all__ = [
    'TimeSeriesAnalyzer',
    'StatisticsAnalyzer',
    'MassFlowCalculator',
    'TrendAnalyzer'
] 