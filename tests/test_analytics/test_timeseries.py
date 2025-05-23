"""
Tests for the TimeSeriesAnalyzer class in the analytics module
"""
import pytest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

from prolabdep.analytics.timeseries import TimeSeriesAnalyzer


@pytest.fixture
def time_series_data():
    """Sample time series data for testing."""
    # Create sample dates
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(10)]
    
    # Create sample values with a linear trend
    values = [100 + i * 5 + np.random.normal(0, 2) for i in range(10)]
    
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


@pytest.fixture
def time_series_analyzer():
    """TimeSeriesAnalyzer instance for testing."""
    return TimeSeriesAnalyzer()


def test_resample_daily(time_series_data, time_series_analyzer):
    """Test resampling to daily frequency."""
    # Original data is already daily, so resampling should not change the data
    resampled_data = time_series_analyzer.resample(
        time_series_data,
        frequency='D',
        method='mean'
    )
    
    # Check that the number of rows is the same
    assert len(resampled_data) == len(time_series_data)
    
    # Check that the dates are the same
    pd.testing.assert_series_equal(
        resampled_data['date'],
        time_series_data['date'],
        check_dtype=False
    )


def test_resample_weekly(time_series_data, time_series_analyzer):
    """Test resampling to weekly frequency."""
    # Resample to weekly
    resampled_data = time_series_analyzer.resample(
        time_series_data,
        frequency='W',
        method='mean'
    )
    
    # Check that the number of rows is less than the original data
    assert len(resampled_data) < len(time_series_data)
    
    # Since we have 10 days of data, we should have 2 full weeks
    assert len(resampled_data) == 2


def test_resample_method(time_series_data, time_series_analyzer):
    """Test different resampling methods."""
    # Create values with known statistics
    df = time_series_data.copy()
    df.loc[0:2, 'value'] = [10, 20, 30]  # min=10, max=30, mean=20, median=20, sum=60
    
    # Test mean method
    mean_resampled = time_series_analyzer.resample(
        df.iloc[0:3],
        frequency='3D',
        method='mean'
    )
    assert len(mean_resampled) == 1
    assert mean_resampled['value'].iloc[0] == 20.0
    
    # Test median method
    median_resampled = time_series_analyzer.resample(
        df.iloc[0:3],
        frequency='3D',
        method='median'
    )
    assert len(median_resampled) == 1
    assert median_resampled['value'].iloc[0] == 20.0
    
    # Test min method
    min_resampled = time_series_analyzer.resample(
        df.iloc[0:3],
        frequency='3D',
        method='min'
    )
    assert len(min_resampled) == 1
    assert min_resampled['value'].iloc[0] == 10.0
    
    # Test max method
    max_resampled = time_series_analyzer.resample(
        df.iloc[0:3],
        frequency='3D',
        method='max'
    )
    assert len(max_resampled) == 1
    assert max_resampled['value'].iloc[0] == 30.0
    
    # Test sum method
    sum_resampled = time_series_analyzer.resample(
        df.iloc[0:3],
        frequency='3D',
        method='sum'
    )
    assert len(sum_resampled) == 1
    assert sum_resampled['value'].iloc[0] == 60.0


def test_plot_time_series(time_series_data, time_series_analyzer):
    """Test time series plotting."""
    # Create a plot
    fig = time_series_analyzer.plot_time_series(
        time_series_data,
        parameter_name='COD',
        title='Test Plot',
        include_trend=True
    )
    
    # Check that a figure was created
    assert isinstance(fig, plt.Figure)
    
    # Check that the plot has correct title
    assert fig.axes[0].get_title() == 'Test Plot'
    
    # Check that a line was plotted
    assert len(fig.axes[0].get_lines()) >= 1  # At least one line (data)
    
    # If trend is included, there should be at least 2 lines
    if time_series_analyzer.plot_time_series == time_series_analyzer.plot_timeseries:
        assert len(fig.axes[0].get_lines()) >= 2  # Data line and trend line
    
    # Clean up
    plt.close(fig)


def test_plot_comparison(time_series_data, time_series_analyzer):
    """Test comparison plotting."""
    # Create a second dataset with different values
    df2 = time_series_data.copy()
    df2['value'] = df2['value'] * 0.7  # 70% of original values
    df2['sampling_point'] = 'Inlet'
    
    # Create a comparison plot
    fig = time_series_analyzer.plot_comparison(
        [time_series_data, df2],
        labels=['Outlet', 'Inlet'],
        title='Comparison Plot'
    )
    
    # Check that a figure was created
    assert isinstance(fig, plt.Figure)
    
    # Check that the plot has correct title
    assert fig.axes[0].get_title() == 'Comparison Plot'
    
    # Check that two lines were plotted
    assert len(fig.axes[0].get_lines()) == 2
    
    # Check that the legend has two entries
    assert len(fig.axes[0].get_legend().get_texts()) == 2
    assert fig.axes[0].get_legend().get_texts()[0].get_text() == 'Outlet'
    assert fig.axes[0].get_legend().get_texts()[1].get_text() == 'Inlet'
    
    # Clean up
    plt.close(fig)


def test_plot_box(time_series_data, time_series_analyzer):
    """Test box plotting."""
    # Create some data with different sampling points
    df = pd.concat([
        time_series_data,
        time_series_data.assign(sampling_point='Inlet', value=lambda x: x['value'] * 0.7),
        time_series_data.assign(sampling_point='Middle', value=lambda x: x['value'] * 0.85)
    ])
    
    # Create a box plot
    fig = time_series_analyzer.plot_box(
        df,
        group_by='sampling_point',
        title='Box Plot'
    )
    
    # Check that a figure was created
    assert isinstance(fig, plt.Figure)
    
    # Check that the plot has correct title
    assert fig.axes[0].get_title() == 'Box Plot'
    
    # Should have 3 boxes (one for each sampling point)
    assert len(fig.axes[0].get_xticklabels()) == 3
    
    # Clean up
    plt.close(fig) 