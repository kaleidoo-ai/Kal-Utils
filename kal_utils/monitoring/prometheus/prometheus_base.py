from abc import ABC, abstractmethod
from contextlib import contextmanager
from functools import wraps
import time
from typing import Callable, Any

from fastapi import FastAPI, Request, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Summary, Histogram, REGISTRY
from fastapi.security import HTTPBasicCredentials
from fastapi import Depends

from utils.basic_authentication import authenticate


# Available Prometheus metrics types:
# 1. Counter: Cumulative metric that only increases or resets to zero
#    Example: from prometheus_client import Counter
#             request_count = Counter('request_count', 'Total request count')
#
# 2. Gauge: Single numerical value that can go up and down
#    Example: from prometheus_client import Gauge
#             cpu_usage = Gauge('cpu_usage', 'CPU usage in percent')
#
# 3. Histogram: Samples observations and counts them in configurable buckets
#    Example: from prometheus_client import Histogram
#             request_latency = Histogram('request_latency_seconds', 'Request latency in seconds')
#
# 4. Summary: Similar to Histogram, but calculates configurable quantiles over a sliding time window
#    Example: from prometheus_client import Summary
#             request_latency = Summary('request_latency_seconds', 'Request latency in seconds')
#
# 5. Info: Gauge with a constant value of 1 and label values that can change
#    Example: from prometheus_client import Info
#             app_info = Info('app_info', 'Application information')
#
# 6. Enum: Gauge with a predefined set of possible values
#    Example: from prometheus_client import Enum
#             http_status = Enum('http_status', 'HTTP status', states=['200', '404', '500'])


class PrometheusMetricsDecorator(ABC):
    """
    An abstract base class for creating Prometheus metrics decorators.

    This class provides a framework for implementing Prometheus metrics
    in a FastAPI application. To use this class, create a subclass and
    implement the abstract methods.

    Raises:
        NotImplementedError: If any of the abstract methods are not implemented in the subclass.
    """

    def __init__(self, app: FastAPI):
        """
        Initialize the metrics decorator.
        Calls setup_metrics() which should be implemented in the subclass.
        """
        self.metrics = {}
        # Define the metrics if they don't already exist in the registry
        if 'db_time_seconds' not in REGISTRY._names_to_collectors:
            self.metrics['db_time'] = Summary(
                'db_time_seconds',
                'Time taken for database operations'
            )
        else:
            self.metrics['db_time'] = REGISTRY._names_to_collectors['db_time_seconds']

        if 'print_time_seconds' not in REGISTRY._names_to_collectors:
            self.metrics['print_time'] = Summary(
                'print_time_seconds',
                'Time taken for print operations'
            )
        else:
            self.metrics['print_time'] = REGISTRY._names_to_collectors['print_time_seconds']

        if 'produce_time_seconds' not in REGISTRY._names_to_collectors:
            self.metrics['produce_time'] = Histogram(
                'produce_time_seconds',
                'Time taken to produce messages in seconds'
            )
        else:
            self.metrics['produce_time'] = REGISTRY._names_to_collectors['produce_time_seconds']

        if 'consume_time_seconds' not in REGISTRY._names_to_collectors:
            self.metrics['consume_time'] = Histogram(
                'consume_time_seconds',
                'Time taken to consume messages in seconds'
            )
        else:
            self.metrics['consume_time'] = REGISTRY._names_to_collectors['consume_time_seconds']
        self.setup_metrics()
        self.add_metrics_endpoint(app)

    @abstractmethod
    def setup_metrics(self):
        """
        Abstract method to set up Prometheus metrics.

        Implement this method in your subclass to initialize all the
        Prometheus metrics you want to track (e.g., Counters, Gauges, Histograms).

        Raises:
            NotImplementedError: If not implemented in the subclass.
        """
        raise NotImplementedError("setup_metrics() must be implemented in the subclass")

    def add_metrics_endpoint(self, app: FastAPI):
        """
        Add a /metrics endpoint to the FastAPI app for Prometheus to scrape.

        Args:
            app (FastAPI): The FastAPI application instance.
        """
        @app.get("/metrics")
        async def metrics(credentials: HTTPBasicCredentials = Depends(authenticate)):
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
        

    def instrument(self) -> Callable:
        """
        Decorator to instrument FastAPI route handlers.

        This method returns a decorator that wraps route handlers to execute
        before_request() and after_request() methods around each request.

        Returns:
            Callable: A decorator function.
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
                self.before_request(request)
                response = await func(request, *args, **kwargs)
                self.after_request(request, response)
                return response
            return wrapper
        return decorator

    @abstractmethod
    def before_request(self, request: Request):
        """
        Abstract method to be called before each request is processed.

        Implement this method in your subclass to perform any pre-request
        actions, such as incrementing request counters or starting timers.

        Args:
            request (Request): The FastAPI Request object.

        Raises:
            NotImplementedError: If not implemented in the subclass.
        """
        raise NotImplementedError("before_request() must be implemented in the subclass")

    @abstractmethod
    def after_request(self, request: Request, response: Any):
        """
        Abstract method to be called after each request is processed.

        Implement this method in your subclass to perform any post-request
        actions, such as recording response times or updating response status metrics.

        Args:
            request (Request): The FastAPI Request object.
            response (Any): The response returned by the route handler.

        Raises:
            NotImplementedError: If not implemented in the subclass.
        """
        raise NotImplementedError("after_request() must be implemented in the subclass")
    
    @abstractmethod
    def update_metrics(self, request: Request, response: Any):
        """
        Abstract method to be called after each request is processed.

        Implement this method in your subclass to perform any post-request
        actions, such as recording response times or updating response status metrics.

        Args:
            request (Request): The FastAPI Request object.
            response (Any): The response returned by the route handler.

        Raises:
            NotImplementedError: If not implemented in the subclass.
        """
        raise NotImplementedError("after_request() must be implemented in the subclass")

    @contextmanager
    def db_time(self):
        """
        Context manager for tracking DB operation time.

        This context manager measures the time taken for database operations
        and records this duration as a Prometheus metric.

        Example:
            with self.db_time():
                # Perform database operations here
                result = perform_database_query()
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_metric('db_time', duration)

    @contextmanager
    def print_time(self):
        """
        Context manager for tracking print operation time.

        This context manager measures the time taken for print operations
        or similar tasks and records this duration as a Prometheus metric.

        Example:
            with self.print_time():
                # Perform print operations here
                print("Logging some information...")
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_metric('print_time', duration)

    @contextmanager
    def produce_time(self):
        """
        Context manager for tracking the time taken to produce a message.

        This context manager measures the time taken for produce operations
        and records this duration as a Prometheus metric.

        Example:
            with self.produce_time():
                # Perform produce operations here
                produce_message()
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_metric('produce_time', duration)

    @contextmanager
    def consume_time(self):
        """
        Context manager for tracking the time taken to produce a message.

        This context manager measures the time taken for produce operations
        and records this duration as a Prometheus metric.

        Example:
            with self.produce_time():
                # Perform produce operations here
                produce_message()
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_metric('consume_time', duration)

    def record_metric(self, name: str, duration: float):
        """
        Record the metric with the given name and duration.

        Args:
            name (str): The name of the metric.
            duration (float): The duration of the operation.
        """
        if name in self.metrics:
            self.metrics[name].observe(duration)

    def handle_exception(self, name: str, exc_type: type, exc_val: Exception):
        """
        Handle exceptions in context managers if needed.

        Args:
            name (str): The name of the metric.
            exc_type (type): The type of exception.
            exc_val (Exception): The exception value.
        """
        pass
