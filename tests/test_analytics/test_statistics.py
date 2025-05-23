"""
Tests for the StatisticsAnalyzer class in the analytics module
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from prolabdep.analytics.statistics import StatisticsAnalyzer


@pytest.fixture
def statistics_analyzer():
    """StatisticsAnalyzer instance for testing."""
    return StatisticsAnalyzer()


@pytest.fixture
def sample_data():
    """Sample data for testing statistics."""
    # Create sample dates
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(10)]
    
    # Create sample values
    values = [50, 55, 52, 48, 53, 51, 54, 49, 52, 50]
    
    # Create a dataframe
    df = pd.DataFrame({
        'date': dates,
        'value': values,
        'parameter_name': 'COD',
        'unit': 'mg/L',
        'site': 'Test Site',
        'sampling_point': 'Outlet'
    })
    
    return df


def test_calculate_statistics(sample_data, statistics_analyzer):
    """Test calculation of basic statistics."""
    # Calculate statistics
    stats = statistics_analyzer.calculate_statistics(sample_data)
    
    # Check that statistics were calculated correctly
    assert stats['mean'] == 51.4  # (50+55+52+48+53+51+54+49+52+50)/10 = 51.4
    assert stats['median'] == 51.5  # Median of [48, 49, 50, 50, 51, 52, 52, 53, 54, 55] = 51.5
    assert stats['min'] == 48
    assert stats['max'] == 55
    assert stats['count'] == 10
    assert stats['25%'] == 50.0  # First quartile
    assert stats['75%'] == 52.75  # Third quartile
    assert stats['std'] == pytest.approx(2.22, abs=0.01)  # Standard deviation


def test_detect_outliers_iqr(sample_data, statistics_analyzer):
    """Test outlier detection using IQR method."""
    # Add some outliers
    outlier_df = sample_data.copy()
    outlier_df.loc[10] = [datetime(2024, 1, 11), 80, 'COD', 'mg/L', 'Test Site', 'Outlet']  # High outlier
    outlier_df.loc[11] = [datetime(2024, 1, 12), 20, 'COD', 'mg/L', 'Test Site', 'Outlet']  # Low outlier
    
    # Calculate Q1, Q3, and IQR
    q1 = outlier_df['value'].quantile(0.25)
    q3 = outlier_df['value'].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # Detect outliers
    outliers = statistics_analyzer.detect_outliers(outlier_df, method='iqr', threshold=1.5)
    
    # Check that outliers were detected correctly
    assert 'is_outlier' in outliers.columns
    assert 'outlier_info' in outliers.columns
    assert outliers['is_outlier'].sum() == 2  # Should detect 2 outliers
    
    # Check specific outliers
    assert outliers.loc[10, 'is_outlier'] == True  # High outlier
    assert outliers.loc[11, 'is_outlier'] == True  # Low outlier
    
    # Check outlier info
    assert 'High outlier' in outliers.loc[10, 'outlier_info']
    assert 'Low outlier' in outliers.loc[11, 'outlier_info']
    
    # Check that the bounds are correct
    assert float(outliers.loc[10, 'outlier_info'].split('> ')[1].split(')')[0]) == pytest.approx(upper_bound, abs=0.1)
    assert float(outliers.loc[11, 'outlier_info'].split('< ')[1].split(')')[0]) == pytest.approx(lower_bound, abs=0.1)


def test_detect_outliers_zscore(sample_data, statistics_analyzer):
    """Test outlier detection using Z-score method."""
    # Add some outliers
    outlier_df = sample_data.copy()
    outlier_df.loc[10] = [datetime(2024, 1, 11), 200, 'COD', 'mg/L', 'Test Site', 'Outlet']  # High outlier (much higher)
    outlier_df.loc[11] = [datetime(2024, 1, 12), -100, 'COD', 'mg/L', 'Test Site', 'Outlet']  # Low outlier (much lower)
    
    # Calculate z-scores manually for debugging
    mean = outlier_df['value'].mean()
    std = outlier_df['value'].std()
    z_scores = (outlier_df['value'] - mean) / std
    print(f"Debug - Mean: {mean}, Std: {std}")
    print(f"Debug - Z-scores: {z_scores}")
    
    # Detect outliers with z-score method
    outliers = statistics_analyzer.detect_outliers(outlier_df, method='zscore', threshold=2.0)
    
    # Print outlier results for debugging
    print(f"Debug - is_outlier: {outliers['is_outlier']}")
    print(f"Debug - outlier_info: {outliers['outlier_info']}")
    
    # Check that outliers were detected correctly
    assert 'is_outlier' in outliers.columns
    assert 'outlier_info' in outliers.columns
    assert outliers['is_outlier'].sum() == 2  # Should detect 2 outliers
    
    # Check specific outliers
    assert outliers.loc[10, 'is_outlier'] == True  # High outlier
    assert outliers.loc[11, 'is_outlier'] == True  # Low outlier
    
    # Check outlier info
    assert 'High outlier' in outliers.loc[10, 'outlier_info']
    assert 'Low outlier' in outliers.loc[11, 'outlier_info']


def test_compare_sites(statistics_analyzer):
    """Test comparison of statistics across different sites."""
    # Create data for two sites
    site1_data = pd.DataFrame({
        'date': [datetime(2024, 1, i) for i in range(1, 6)],
        'value': [100, 110, 105, 95, 100],
        'parameter_name': ['COD'] * 5,
        'unit': ['mg/L'] * 5,
        'site': ['Site 1'] * 5,
        'sampling_point': ['Outlet'] * 5
    })
    
    site2_data = pd.DataFrame({
        'date': [datetime(2024, 1, i) for i in range(1, 6)],
        'value': [50, 55, 52, 48, 50],
        'parameter_name': ['COD'] * 5,
        'unit': ['mg/L'] * 5,
        'site': ['Site 2'] * 5,
        'sampling_point': ['Outlet'] * 5
    })
    
    # Compare sites
    comparison = statistics_analyzer.compare_sites(
        [site1_data, site2_data],
        ['Site 1', 'Site 2']
    )
    
    # Check comparison result structure
    assert 'statistics' in comparison
    assert 'summary' in comparison
    
    # Check statistics
    stats_df = comparison['statistics']
    assert len(stats_df) == 2
    assert stats_df.loc[0, 'site'] == 'Site 1'
    assert stats_df.loc[1, 'site'] == 'Site 2'
    
    # Check mean values
    assert stats_df.loc[0, 'mean'] == 102.0  # Site 1
    assert stats_df.loc[1, 'mean'] == 51.0   # Site 2
    
    # Check difference calculation (if available)
    if 'mean_diff_%' in stats_df.columns:
        assert stats_df.loc[1, 'mean_diff_%'] == -50.0  # Site 2 is 50% lower than Site 1
    
    # Check summary
    summary = comparison['summary']
    assert summary['num_sites'] == 2
    assert summary['total_samples'] == 10  # 5 from each site 