import os
import importlib
import inspect
from typing import Dict, Type, Set

def find_modules_in_directory(directory: str) -> Dict[str, str]:
    """
    Find all Python modules in the given directory.
    """
    modules = {}
    for filename in os.listdir(directory):
        if filename.endswith('.py') and filename != '__init__.py' and filename != 'prometheus_base.py' and filename != 'unifiedMetrics.py':
            module_name = filename[:-3]  # Remove .py extension
            # Convert directory structure to module path
            module_path = f"{directory.replace('/', '.')}.{module_name}"
            modules[module_name] = module_path
    return modules

def find_classes_in_module(module_path: str) -> Dict[str, Type]:
    """
    Find all classes in a given module.
    """
    module = importlib.import_module(module_path)
    # Get all classes in the module
    return {name: obj for name, obj in inspect.getmembers(module, inspect.isclass)}

def filter_metric_classes(classes: Dict[str, Type], base_module: str, filter_keyword: str = 'prometheus_client', filter_keyword1: str = 'prometheus_base') -> Dict[str, Type]:
    """
    Filter classes to include only those that match the filter keyword and are part of the base module.
    """
    filtered_classes = {}
    for name, cls in classes.items():
        # Check if the class is part of the specified base module and matches the filter keyword
        if filter_keyword not in cls.__module__ and filter_keyword1 not in cls.__module__ and cls.__module__.startswith(base_module):
            filtered_classes[name] = cls
    return filtered_classes

def get_metrics_classes() -> Dict[str, Type]:
    """
    Dynamically load and return a dictionary of available metrics classes.
    """
    from .. import prometheus
    metrics_classes = {
        "LocationRequestCounter":prometheus.locationRequestCounter.LocationRequestCounter,
        "RequestCounter":prometheus.requestMetrics.RequestCounter,
        "RequestHist":prometheus.requestMetrics.RequestHist,
        "ServerErrorMetrics":prometheus.requestMetrics.ServerErrorMetrics,
        "CpuUsageMonitor":prometheus.systemMetrics.CpuUsageMonitor,
        "MemoryUsageMonitor":prometheus.systemMetrics.MemoryUsageMonitor,
        "DiskUsageMonitor":prometheus.systemMetrics.DiskUsageMonitor,
        "NetworkUsageMonitor":prometheus.systemMetrics.NetworkUsageMonitor
    }
    # base_directory = 'prometheus'
    # base_module = 'prometheus'

    # # Find all modules in the base directory
    # modules = find_modules_in_directory(base_directory)
    # metrics_classes = {}

    # # Iterate over modules to find and filter classes
    # for module_name, module_path in modules.items():
    #     classes = find_classes_in_module(module_path)
    #     filtered_classes = filter_metric_classes(classes, base_module)
    #     metrics_classes.update(filtered_classes)

    return metrics_classes

def get_enabled_metrics() -> Set[str]:
    """
    Retrieves the enabled metrics classes from environment variables.
    """
    enabled_metrics = os.getenv('ENABLED_METRICS', 'RequestCounter,RequestHist,ServerErrorMetrics').split(',')
    return set(enabled_metrics)
