from typing import Type, Set, Any
from urllib.request import Request

from fastapi import FastAPI

from prometheus.prometheus_base import PrometheusMetricsDecorator
from core.metrics import get_metrics_classes, get_enabled_metrics


def create_unified_metrics_class(app: FastAPI) -> Type[PrometheusMetricsDecorator]:
    """
    Creates a unified metrics class based on the metrics enabled via environment variables.

    This function constructs a `UnifiedMetrics` class, which combines multiple metrics classes
    into a single interface for managing metrics. The metrics classes to be included are determined
    by the `ENABLED_METRICS` environment variable.

    Args:
        app (FastAPI): The FastAPI application instance. This is used to initialize each metric class.

    Returns:
        Type[PrometheusMetricsDecorator]: A subclass of `PrometheusMetricsDecorator` with the
        combined functionality of all enabled metrics classes.
    """
    metrics_classes = get_metrics_classes()
    enabled_metrics = get_enabled_metrics()

    class UnifiedMetrics(PrometheusMetricsDecorator):
        """
        A unified metrics class that integrates multiple metrics classes into a single interface.

        Attributes:
            metrics_initialized (Set[PrometheusMetricsDecorator]): A set of initialized metrics instances
            that are active for this application.
        """

        def __init__(self, app: FastAPI):
            """
            Initializes the UnifiedMetrics class.

            This constructor sets up metrics by initializing the metrics classes that are enabled,
            as determined by the environment variables.

            Args:
                app (FastAPI): The FastAPI application instance used to initialize each metric class.
            """
            super().__init__(app)
            self.metrics_initialized: Set[PrometheusMetricsDecorator] = set()
            self.initialize_metrics(app, metrics_classes, enabled_metrics)

        def initialize_metrics(self, app: FastAPI, metrics_classes: dict, enabled_metrics: Set[str]):
            """
            Initializes metrics instances based on the enabled metrics classes.

            This method checks the enabled metrics and creates instances of the corresponding
            metrics classes. Each initialized metric instance is added to the `metrics_initialized`
            set to ensure that each metric is only initialized once.

            Args:
                app (FastAPI): The FastAPI application instance used for initializing each metric class.
                metrics_classes (dict): A dictionary mapping metric class names to their corresponding
                metric classes.
                enabled_metrics (Set[str]): A set of names for the metrics classes that are enabled
                according to the environment variables.
            """
            for metric_class_name in enabled_metrics:
                metric_class = metrics_classes.get(metric_class_name)
                if metric_class:
                    metric_instance = metric_class(app)
                    # Initialize metrics if not already done
                    if metric_instance not in self.metrics_initialized:
                        self.metrics_initialized.add(metric_instance)

        def setup_metrics(self):
            """
            Sets up metrics for all enabled metrics classes.

            This method is currently a placeholder and does not perform any actions. It is intended
            to be used for additional setup if needed in the future. The actual setup is performed
            by individual metric classes during their initialization.
            """
            pass

        async def dispatch(self, request: Request, call_next):
            # Define the path to exclude from metrics collection
            excluded_paths = ["/metrics"]  # Add other paths to exclude as needed

            if request.url.path in excluded_paths:
                # Skip metrics collection for excluded paths
                response = await call_next(request)
                self.update_metrics(request, response)
                return response

            self.before_request(request)

            response = await call_next(request)

            self.after_request(request, response)

            return response

        def before_request(self, request: Request):
            """
            Invokes the `before_request` method for all initialized metrics classes.

            This method is called before processing each request. It allows each metrics instance
            to perform any necessary actions or preparations before the request is handled.

            Args:
                request (Request): The incoming HTTP request object.
            """
            for metric_instance in self.metrics_initialized:
                metric_instance.before_request(request)

        def after_request(self, request: Request, response: Any):
            """
            Invokes the `after_request` method for all initialized metrics classes.

            This method is called after processing each request. It allows each metrics instance
            to perform any necessary actions or updates based on the request and response.

            Args:
                request (Request): The incoming HTTP request object.
                response (Any): The HTTP response object.
            """
            for metric_instance in self.metrics_initialized:
                metric_instance.after_request(request, response)

        def update_metrics(self, request: Request, response: Any):
            """
            Invokes the `after_request` method for all initialized metrics classes.

            This method is called after processing each request. It allows each metrics instance
            to perform any necessary actions or updates based on the request and response.

            Args:
                request (Request): The incoming HTTP request object.
                response (Any): The HTTP response object.
            """
            for metric_instance in self.metrics_initialized:
                metric_instance.update_metrics(request, response)

    return UnifiedMetrics