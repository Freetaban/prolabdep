"""
Performance monitoring and optimization utilities
"""
import time
import logging
import functools
import psutil
import os
from typing import Dict, Any, Callable, Optional, List
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    execution_time: float = 0.0
    memory_usage_mb: float = 0.0
    peak_memory_mb: float = 0.0
    cpu_percent: float = 0.0
    function_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceMonitor:
    """
    Performance monitoring utility class
    """
    
    def __init__(self):
        self.metrics_history: Dict[str, list] = {}
        self.process = psutil.Process(os.getpid())
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        return self.process.cpu_percent()
    
    @contextmanager
    def monitor(self, operation_name: str):
        """
        Context manager for monitoring performance
        
        Parameters
        ----------
        operation_name : str
            Name of the operation being monitored
        """
        start_time = time.time()
        start_memory = self.get_memory_usage()
        peak_memory = start_memory
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self.get_memory_usage()
            peak_memory = max(peak_memory, end_memory)
            cpu_usage = self.get_cpu_usage()
            
            metrics = PerformanceMetrics(
                execution_time=end_time - start_time,
                memory_usage_mb=end_memory - start_memory,
                peak_memory_mb=peak_memory,
                cpu_percent=cpu_usage,
                function_name=operation_name
            )
            
            self._store_metrics(operation_name, metrics)
            
            logger.debug(
                f"Performance metrics for {operation_name}: "
                f"Time: {metrics.execution_time:.3f}s, "
                f"Memory: {metrics.memory_usage_mb:.2f}MB, "
                f"CPU: {metrics.cpu_percent:.1f}%"
            )
    
    def _store_metrics(self, operation_name: str, metrics: PerformanceMetrics):
        """Store metrics in history"""
        if operation_name not in self.metrics_history:
            self.metrics_history[operation_name] = []
        
        self.metrics_history[operation_name].append(metrics)
        
        # Keep only last 100 entries per operation
        if len(self.metrics_history[operation_name]) > 100:
            self.metrics_history[operation_name] = self.metrics_history[operation_name][-100:]
    
    def get_metrics_summary(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary of performance metrics
        
        Parameters
        ----------
        operation_name : str, optional
            Specific operation to get metrics for. If None, returns all operations.
        
        Returns
        -------
        Dict[str, Any]
            Summary of performance metrics
        """
        if operation_name:
            if operation_name not in self.metrics_history:
                return {}
            
            metrics_list = self.metrics_history[operation_name]
            return self._calculate_summary(metrics_list)
        else:
            summary = {}
            for op_name, metrics_list in self.metrics_history.items():
                summary[op_name] = self._calculate_summary(metrics_list)
            return summary
    
    def _calculate_summary(self, metrics_list: list) -> Dict[str, Any]:
        """Calculate summary statistics for a list of metrics"""
        if not metrics_list:
            return {}
        
        execution_times = [m.execution_time for m in metrics_list]
        memory_usages = [m.memory_usage_mb for m in metrics_list]
        cpu_usages = [m.cpu_percent for m in metrics_list]
        
        return {
            'count': len(metrics_list),
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'max_execution_time': max(execution_times),
            'min_execution_time': min(execution_times),
            'avg_memory_usage': sum(memory_usages) / len(memory_usages),
            'max_memory_usage': max(memory_usages),
            'avg_cpu_usage': sum(cpu_usages) / len(cpu_usages),
            'last_execution': metrics_list[-1].timestamp
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(operation_name: Optional[str] = None):
    """
    Decorator for monitoring function performance
    
    Parameters
    ----------
    operation_name : str, optional
        Name for the operation. If None, uses function name.
    
    Returns
    -------
    Callable
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with performance_monitor.monitor(name):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


@contextmanager
def memory_profiler():
    """
    Context manager for memory profiling
    """
    import tracemalloc
    
    tracemalloc.start()
    try:
        yield
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        logger.info(
            f"Memory profiling: Current={current / 1024 / 1024:.2f}MB, "
            f"Peak={peak / 1024 / 1024:.2f}MB"
        )


def optimize_pandas_settings():
    """
    Apply pandas optimizations for better performance
    """
    import pandas as pd
    
    # Set pandas options for better performance
    pd.set_option('compute.use_bottleneck', True)
    pd.set_option('compute.use_numexpr', True)
    
    # Increase precision for display but maintain performance
    pd.set_option('display.precision', 3)
    
    logger.info("Applied pandas performance optimizations")


def get_system_info() -> Dict[str, Any]:
    """
    Get system information for performance analysis
    
    Returns
    -------
    Dict[str, Any]
        System information
    """
    return {
        'cpu_count': psutil.cpu_count(),
        'memory_total_gb': psutil.virtual_memory().total / 1024**3,
        'memory_available_gb': psutil.virtual_memory().available / 1024**3,
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage_percent': psutil.disk_usage('/').percent,
        'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
    }


def suggest_optimizations() -> List[str]:
    """
    Suggest optimizations based on system characteristics
    
    Returns
    -------
    List[str]
        List of optimization suggestions
    """
    suggestions = []
    system_info = get_system_info()
    
    # Memory-based suggestions
    if system_info['memory_percent'] > 80:
        suggestions.append("High memory usage detected. Consider processing data in chunks.")
    
    if system_info['memory_total_gb'] < 8:
        suggestions.append("Limited memory available. Enable low_memory mode in pandas operations.")
    
    # CPU-based suggestions
    if system_info['cpu_count'] > 4:
        suggestions.append("Multi-core system detected. Consider enabling parallel processing.")
    
    # Disk-based suggestions
    if system_info['disk_usage_percent'] > 90:
        suggestions.append("Low disk space. Consider data compression or cleanup.")
    
    return suggestions 