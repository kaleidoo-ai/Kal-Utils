from fastapi import FastAPI, Request
from opentelemetry import trace

from ..tempo.tracing_manager import (
    OTLPTracingConfig,
    JaegerTracingConfig,
)
from .config_managers import EnvConfigManager
import httpx
import requests
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry.context import attach, detach
from opentelemetry.propagate import extract, inject
from opentelemetry.trace import SpanKind, format_trace_id, Status, StatusCode



def configure_tracing(app: FastAPI):
    """
    Configures tracing based on the environment variables.

    This function initializes the tracing configuration by loading settings from
    environment variables. It then selects and configures the appropriate tracing
    implementation based on the specified exporter type.

    The environment variables used for configuration are:
    - `OTEL_SERVICE_NAME`: The name of the service for tracing.
    - `OTEL_ENDPOINT`: The endpoint URL for the tracing exporter.
    - `OTEL_EXPORTER_TYPE`: The type of tracing exporter to use (e.g., 'otlp', 'jaeger').
    - `OTEL_INSECURE`: Indicates if the connection is insecure (e.g., 'true', 'false').

    Raises:
        ValueError: If the specified exporter type is not supported.

    The function performs the following steps:
    1. Loads the configuration values from environment variables using `EnvConfigManager`.
    2. Based on the `exporter_type`, it selects the corresponding tracing configuration class (`OTLPTracingConfig` or `JaegerTracingConfig`).
    3. Calls the `configure_tracing` method on the selected tracing configuration to set up tracing.
    """
    # Load configuration from environment variables
    config_manager = EnvConfigManager()
    service_name = config_manager.get_service_name()
    endpoint = config_manager.get_endpoint()
    exporter_type = config_manager.get_exporter_type()
    insecure = config_manager.get_insecure()

    # Select the appropriate tracing configuration
    if exporter_type == "otlp":
        tracing_config = OTLPTracingConfig(service_name, endpoint, insecure)
    elif exporter_type == "jaeger":
        tracing_config = JaegerTracingConfig(service_name, endpoint)
    else:
        raise ValueError(f"Unsupported exporter type: {exporter_type}")

    # Configure tracing
    tracing_config.configure_tracing()
    #Custom middleware to control tracing
    @app.middleware("http")
    async def tracing_middleware(request: Request, call_next):
        if "/metrics" in request.url.path:
            response = await call_next(request)
            return response
        else:
            # Find the route handler function name
            route_name = request.url.path
            # for route in app.router.routes:
            #     if route.path == request.url.path:
            #         route_name = route.path
            #         # route_name = route.endpoint.__name__
            #         break

            if not route_name:
                route_name = "unknown_function"

            # Trace the request with the function name
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(route_name) as span:
                # Optionally add more details to the span
                span.set_attribute("http.method", request.method)
                span.set_attribute("http.url", str(request.url))
                response = await call_next(request)
            return response

def configure_tracing1():
    """
    Configures tracing based on the environment variables.

    This function initializes the tracing configuration by loading settings from
    environment variables. It then selects and configures the appropriate tracing
    implementation based on the specified exporter type.

    The environment variables used for configuration are:
    - `OTEL_SERVICE_NAME`: The name of the service for tracing.
    - `OTEL_ENDPOINT`: The endpoint URL for the tracing exporter.
    - `OTEL_EXPORTER_TYPE`: The type of tracing exporter to use (e.g., 'otlp', 'jaeger').
    - `OTEL_INSECURE`: Indicates if the connection is insecure (e.g., 'true', 'false').

    Raises:
        ValueError: If the specified exporter type is not supported.

    The function performs the following steps:
    1. Loads the configuration values from environment variables using `EnvConfigManager`.
    2. Based on the `exporter_type`, it selects the corresponding tracing configuration class (`OTLPTracingConfig` or `JaegerTracingConfig`).
    3. Calls the `configure_tracing` method on the selected tracing configuration to set up tracing.
    """
    # Load configuration from environment variables
    config_manager = EnvConfigManager()
    service_name = config_manager.get_service_name()
    endpoint = config_manager.get_endpoint()
    exporter_type = config_manager.get_exporter_type()
    insecure = config_manager.get_insecure()

    # Select the appropriate tracing configuration
    if exporter_type == "otlp":
        tracing_config = OTLPTracingConfig(service_name, endpoint, insecure)
    elif exporter_type == "jaeger":
        tracing_config = JaegerTracingConfig(service_name, endpoint)
    else:
        raise ValueError(f"Unsupported exporter type: {exporter_type}")

    # Configure tracing
    tracing_config.configure_tracing()

def configure_distributed_tracing(app: FastAPI):
    """
    Configure distributed tracing for a FastAPI application.
    
    This function sets up:
    - Trace context propagation
    - Automatic instrumentation for HTTP clients
    - Distributed tracing middleware
    - Span creation for incoming requests
    
    Args:
        app (FastAPI): The FastAPI application to configure tracing for
    """
    # Load configuration from environment variables
    config_manager = EnvConfigManager()
    service_name = config_manager.get_service_name()
    endpoint = config_manager.get_endpoint()
    exporter_type = config_manager.get_exporter_type()
    insecure = config_manager.get_insecure()

    # Select the appropriate tracing configuration
    if exporter_type == "otlp":
        tracing_config = OTLPTracingConfig(service_name, endpoint, insecure)
    elif exporter_type == "jaeger":
        tracing_config = JaegerTracingConfig(service_name, endpoint)
    else:
        raise ValueError(f"Unsupported exporter type: {exporter_type}")

    # Configure tracing
    tracing_config.configure_tracing()

    # Instrument HTTP clients for automatic context propagation
    HTTPXClientInstrumentor().instrument()
    RequestsInstrumentor().instrument()

    # Distributed Tracing Middleware
    class DistributedTracingMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            # Skip tracing for metrics endpoint
            if "/metrics" in request.url.path:
                return await call_next(request)

            # Extract the parent context from incoming request headers
            context = extract(request.headers)
            token = attach(context)
            
            try:
                # Start a new span for the incoming request
                tracer = trace.get_tracer(__name__)
                with tracer.start_as_current_span(
                    request.url.path, 
                    kind=SpanKind.SERVER
                ) as span:
                    # Get the current trace and span IDs
                    current_span = trace.get_current_span()
                    trace_id = format_trace_id(current_span.get_span_context().trace_id)
                    span_id = format_trace_id(current_span.get_span_context().span_id)

                    # Log trace information
                    # logger.info(
                    #     f"Trace Information - "
                    #     f"Service: {service_name}, "
                    #     f"Trace ID: {trace_id}, "
                    #     f"Span ID: {span_id}, "
                    #     f"Path: {request.url.path}"
                    # )

                    # Add comprehensive span attributes
                    span.set_attribute("http.method", request.method)
                    span.set_attribute("http.url", str(request.url))
                    span.set_attribute("service.name", service_name)
                    span.set_attribute("trace.id", trace_id)
                    span.set_attribute("span.id", span_id)
                    
                    # Process the request
                    response = await call_next(request)
                    
                    # Add response attributes
                    span.set_attribute("http.status_code", response.status_code)

                    # Set span status based on response
                    if 400 <= response.status_code < 600:
                        span.set_status(Status(StatusCode.ERROR, f"HTTP error: {response.status_code}"))
                    else:
                        span.set_status(Status(StatusCode.OK))
                    
                    return response
            except Exception as e:
                    # Handle and record any exceptions
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
            finally:
                # Detach the context
                detach(token)

    # Add the distributed tracing middleware
    app.add_middleware(DistributedTracingMiddleware)

    # Optional utility functions for more controlled tracing
    async def make_traced_httpx_request(url, method='GET', headers=None, data=None):
        """
        Make a traced request using httpx with explicit context propagation.
        
        Args:
            url (str): The URL to send the request to
            method (str, optional): HTTP method. Defaults to 'GET'.
            headers (dict, optional): Additional headers. Defaults to None.
            data (dict, optional): Request payload. Defaults to None.
        
        Returns:
            httpx.Response: The response from the request
        """
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span(
            f"http.{method.lower()}", 
            kind=SpanKind.CLIENT
        ) as span:
            # Prepare headers with trace context
            request_headers = headers or {}
            inject(request_headers)
            
            # Make the HTTP request
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method, 
                    url, 
                    headers=request_headers, 
                    data=data
                )
                
                # Add request and response details to the span
                span.set_attribute("http.url", url)
                span.set_attribute("http.method", method)
                span.set_attribute("http.status_code", response.status_code)
                
                return response

    def make_traced_requests(url, method='GET', headers=None, data=None):
        """
        Make a traced request using requests with explicit context propagation.
        
        Args:
            url (str): The URL to send the request to
            method (str, optional): HTTP method. Defaults to 'GET'.
            headers (dict, optional): Additional headers. Defaults to None.
            data (dict, optional): Request payload. Defaults to None.
        
        Returns:
            requests.Response: The response from the request
        """
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span(
            f"http.{method.lower()}", 
            kind=SpanKind.CLIENT
        ) as span:
            # Prepare headers with trace context
            request_headers = headers or {}
            inject(request_headers)
            
            # Make the HTTP request
            response = requests.request(
                method, 
                url, 
                headers=request_headers, 
                data=data
            )
                
            # Add request and response details to the span
            span.set_attribute("http.url", url)
            span.set_attribute("http.method", method)
            span.set_attribute("http.status_code", response.status_code)
            
            return response

    # Attach utility functions to the app if needed
    app.make_traced_httpx_request = make_traced_httpx_request
    app.make_traced_requests = make_traced_requests
