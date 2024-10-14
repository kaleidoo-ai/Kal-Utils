import psutil
from typing import Any

from prometheus_client import Gauge, REGISTRY
from fastapi import Request

from .prometheus_base import PrometheusMetricsDecorator

class CpuUsageMonitor(PrometheusMetricsDecorator):
    """
    A class to monitor CPU usage metrics using Prometheus.

    Attributes:
        cpu_usage (Gauge): A Prometheus gauge that tracks the current CPU usage percentage.
    """

    def __init__(self, app):
        """
        Initialize the CpuUsageMonitor class.

        Args:
            app: The FastAPI application instance. This parameter is required for initializing
                 the Prometheus metrics and integrating them with the FastAPI application.
        """
        self.cpu_usage = None
        self.setup_metrics()

    def setup_metrics(self):
        """
        Initialize Prometheus metrics for tracking CPU usage.

        This method sets up:
            - cpu_usage: A Prometheus Gauge to track the current CPU usage percentage.
        """
        if 'cpu_usage_percentage' not in REGISTRY._names_to_collectors:
            self.cpu_usage = Gauge(
                'cpu_usage_percentage',
                'Current CPU usage percentage'
            )
        else:
            self.cpu_usage = REGISTRY._names_to_collectors['cpu_usage_percentage']

    def before_request(self, request: Request):
        """
        Args:
            request (Request): The incoming HTTP request object. This method does not currently
                               perform any actions.
        """
        pass

    def after_request(self, request: Request, response: Any):
        """
        Update metrics after processing each request.

        Args:
            request (Request): The incoming HTTP request object.
            response (Any): The HTTP response object.

        Actions:
            - Update the cpu_usage gauge with the current CPU usage percentage.
        """
        pass

    def update_metrics(self, request: Request, response: Any):
        """
        Update metrics after processing each request.

        Args:
            request (Request): The incoming HTTP request object.
            response (Any): The HTTP response object.

        Actions:
            - Update the cpu_usage gauge with the current CPU usage percentage.
        """
        # Update the CPU usage gauge
        cpu_percent = psutil.cpu_percent()
        self.cpu_usage.set(cpu_percent)


class MemoryUsageMonitor(PrometheusMetricsDecorator):
    """
    A class to monitor memory usage metrics using Prometheus.

    Attributes:
        memory_usage (Gauge): A Prometheus gauge that tracks the current memory usage percentage.
    """

    def __init__(self, app):
        """
        Initialize the MemoryUsageMonitor class.

        Args:
            app: The FastAPI application instance.
        """
        self.memory_usage = None
        self.setup_metrics()

    def setup_metrics(self):
        """
        Initialize Prometheus metrics for tracking memory usage.

        This method sets up:
            - memory_usage: A Prometheus Gauge to track the current memory usage percentage.
        """
        if 'memory_usage_percentage' not in REGISTRY._names_to_collectors:
            self.memory_usage = Gauge(
                'memory_usage_percentage',
                'Current memory usage percentage'
            )
        else:
            self.memory_usage = REGISTRY._names_to_collectors['memory_usage_percentage']

    def before_request(self, request: Request):
        """This method does not currently perform any actions."""
        pass

    def after_request(self, request: Request, response: Any):
        """
        Update metrics after processing each request.

        Args:
            request (Request): The incoming HTTP request object.
            response (Any): The HTTP response object.

        Actions:
            - Update the memory_usage gauge with the current memory usage percentage.
        """

    def update_metrics(self, request: Request, response: Any):
        """
        Update metrics after processing each request.

        Args:
            request (Request): The incoming HTTP request object.
            response (Any): The HTTP response object.

        Actions:
            - Update the memory_usage gauge with the current memory usage percentage.
        """
        memory_info = psutil.virtual_memory()
        self.memory_usage.set(memory_info.percent)


class DiskUsageMonitor(PrometheusMetricsDecorator):
    """
    A class to monitor disk usage metrics using Prometheus.

    Attributes:
        disk_usage (Gauge): A Prometheus gauge that tracks the current disk usage percentage.
    """

    def __init__(self, app):
        """
        Initialize the DiskUsageMonitor class.

        Args:
            app: The FastAPI application instance.
        """
        self.disk_usage = None
        self.setup_metrics()

    def setup_metrics(self):
        """
        Initialize Prometheus metrics for tracking disk usage.

        This method sets up:
            - disk_usage: A Prometheus Gauge to track the current disk usage percentage.
        """
        if 'disk_usage_percentage' not in REGISTRY._names_to_collectors:
            self.disk_usage = Gauge(
                'disk_usage_percentage',
                'Current disk usage percentage'
            )
        else:
            self.disk_usage = REGISTRY._names_to_collectors['disk_usage_percentage']

    def before_request(self, request: Request):
        """This method does not currently perform any actions."""
        pass

    def after_request(self, request: Request, response: Any):
        """
        Update metrics after processing each request.

        Args:
            request (Request): The incoming HTTP request object.
            response (Any): The HTTP response object.

        Actions:
            - Update the disk_usage gauge with the current disk usage percentage.
        """

    def update_metrics(self, request: Request, response: Any):
        """
        Update metrics after processing each request.

        Args:
            request (Request): The incoming HTTP request object.
            response (Any): The HTTP response object.

        Actions:
            - Update the disk_usage gauge with the current disk usage percentage.
        """
        disk_info = psutil.disk_usage('/')
        self.disk_usage.set(disk_info.percent)


class NetworkUsageMonitor(PrometheusMetricsDecorator):
    """
    A class to monitor network usage metrics using Prometheus.

    Attributes:
        network_bytes_sent (Gauge): A Prometheus gauge that tracks the number of bytes sent.
        network_bytes_received (Gauge): A Prometheus gauge that tracks the number of bytes received.
    """

    def __init__(self, app):
        """
        Initialize the NetworkUsageMonitor class.

        Args:
            app: The FastAPI application instance. This parameter is required for initializing
                 the Prometheus metrics and integrating them with the FastAPI application.
        """
        self.network_bytes_sent = None
        self.network_bytes_received = None
        self.setup_metrics()

    def setup_metrics(self):
        """
        Initialize Prometheus metrics for tracking network usage.

        This method sets up:
            - network_bytes_sent: A Prometheus Gauge to track the number of bytes sent.
            - network_bytes_received: A Prometheus Gauge to track the number of bytes received.
        """
        if 'network_bytes_sent' not in REGISTRY._names_to_collectors:
            self.network_bytes_sent = Gauge(
                'network_bytes_sent',
                'Total number of bytes sent'
            )
        else:
            self.network_bytes_sent = REGISTRY._names_to_collectors['network_bytes_sent']

        if 'network_bytes_received' not in REGISTRY._names_to_collectors:
            self.network_bytes_received = Gauge(
                'network_bytes_received',
                'Total number of bytes received'
            )
        else:
            self.network_bytes_received = REGISTRY._names_to_collectors['network_bytes_received']

    def before_request(self, request: Request):
        """This method does not currently perform any actions."""
        pass

    def after_request(self, request: Request, response: Any):
        """
        Update metrics after processing each request.

        Args:
            request (Request): The incoming HTTP request object.
            response (Any): The HTTP response object.

        Actions:
            - Update the network_bytes_sent and network_bytes_received gauges with the current
              network usage statistics.
        """

    def update_metrics(self, request: Request, response: Any):
        """
        Update metrics after processing each request.

        Args:
            request (Request): The incoming HTTP request object.
            response (Any): The HTTP response object.

        Actions:
            - Update the network_bytes_sent and network_bytes_received gauges with the current
              network usage statistics.
        """
        net_io = psutil.net_io_counters()
        self.network_bytes_sent.set(net_io.bytes_sent)
        self.network_bytes_received.set(net_io.bytes_recv)
