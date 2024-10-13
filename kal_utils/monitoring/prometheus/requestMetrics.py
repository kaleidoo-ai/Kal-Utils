from typing import Any
import time

from fastapi import Request
from prometheus_client import Counter, Histogram, REGISTRY

from prometheus.prometheus_base import PrometheusMetricsDecorator


class RequestCounter(PrometheusMetricsDecorator):
    """
    A class to monitor HTTP request metrics using Prometheus.

    Attributes:
        total_requests (Counter): A Prometheus counter that tracks the total number of requests
            received, labeled by HTTP status code.
    """

    def __init__(self, app):
        """
        Initialize the RequestCounter class.

        Args:
            app: The FastAPI application instance. This parameter is required for initializing
                 the Prometheus metrics and integrating them with the FastAPI application.
        """
        self.total_requests = None
        self.setup_metrics()

    def setup_metrics(self):
        """
        Initialize Prometheus metrics for tracking request metrics.

        This method sets up:
            - `total_requests`: A Prometheus Counter to track the number of requests received,
              with labels for HTTP status codes. If the counter already exists in the Prometheus
              registry, it will reuse the existing one.
        """
        if 'total_requests' not in REGISTRY._names_to_collectors:
            self.total_requests = Counter(
                'total_requests',
                'Total number of requests received by status code',
                ['status_code']
            )
        else:
            self.total_requests = REGISTRY._names_to_collectors['total_requests']

    def before_request(self, request: Request):
        """
        Args:
            request (Request): The incoming HTTP request object. This method does not currently
                               perform any actions.
        """

    def after_request(self, request: Request, response: Any):
        """
        Update metrics after processing each request.

        Args:
            request (Request): The incoming HTTP request object.
            response (Any): The HTTP response object.

        Actions:
            - Increment the `total_requests` counter, labeled by the status code of the response.
        """
        # Determine the status code and increment the corresponding counter
        status_code = response.status_code
        self.total_requests.labels(status_code=str(status_code)).inc()

    def update_metrics(self, request: Request, response: Any):
        pass


class RequestHist(PrometheusMetricsDecorator):
    """
    A class to monitor request metrics using Prometheus.

    Attributes:
        request_latency (Histogram): A Prometheus histogram to track the latency of requests in seconds.
    """

    def __init__(self, app):
        """
        Initialize RequestHist class.

        Args:
            app: The FastAPI application instance.
        """
        self.request_latency = None
        self.request_start_time = None
        self.setup_metrics()

    def setup_metrics(self):
        """
        Initialize Prometheus metrics for tracking request metrics.

        Sets up:
            - request_latency: A histogram to measure the latency of requests in seconds.
        """
        if 'request_latency_seconds' not in REGISTRY._names_to_collectors:
            self.request_latency = Histogram('request_latency_seconds',
                                             'Request latency in seconds')
        else:
            self.request_latency = REGISTRY._names_to_collectors['request_latency_seconds']

    def before_request(self, request: Request):
        """
        Prepare to track request latency.

        Args:
            request (Request): The incoming HTTP request object.

        Actions:
            - Record the start time of the request to measure latency.
        """
        self.request_start_time = time.time()  # Store the start time

    def after_request(self, request: Request, response: Any):
        """
        Update metrics after processing each request.

        Args:
            request (Request): The incoming HTTP request object.
            response (Any): The HTTP response object.

        Actions:
            - Calculate and record the request latency in the request_latency histogram.
        """

        # Measure and record the request latency
        latency = time.time() - self.request_start_time
        self.request_latency.observe(latency)

    def update_metrics(self, request: Request, response: Any):
        pass


class ServerErrorMetrics(PrometheusMetricsDecorator):
    """
    A class to monitor server errors using Prometheus.

    Attributes:
        server_errors (Counter): A Prometheus counter to track the number of server errors (5xx status codes).
    """

    def __init__(self, app):
        """
        Initialize ServerErrorMetrics class.

        Args:
            app: The FastAPI application instance.
        """
        self.server_errors = None
        self.setup_metrics()

    def setup_metrics(self):
        """
        Initialize Prometheus metrics for tracking server errors.

        Sets up:
            - server_errors: A counter to track the number of server errors (5xx status codes).
        """
        # Check if the server_errors counter is already in the registry
        if 'server_errors' not in REGISTRY._names_to_collectors:
            self.server_errors = Counter('server_errors',
                                         'Total number of server errors (5xx status codes)')
        else:
            self.server_errors = REGISTRY._names_to_collectors['server_errors']

    def before_request(self, request: Request):
        """
        Prepare to track request latency.

        Args:
            request (Request): The incoming HTTP request object.

        Actions:
            - Record the start time of the request to measure latency.
        """
        pass

    def after_request(self, request: Request, response: Any):
        """
        Update metrics after processing each request.

        Args:
            request (Request): The incoming HTTP request object.
            response (Any): The HTTP response object.

        Actions:
            - Increment the server_errors counter for server errors (5xx status codes).
        """
        # Increment the server_errors counter for 5xx status codes
        if 500 <= response.status_code < 600:
            self.server_errors.inc()

    def update_metrics(self, request: Request, response: Any):
        pass