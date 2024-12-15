from fastapi import FastAPI
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


def create_tracing_configuration(config_manager):
    """
    Create the appropriate tracing configuration based on environment settings.
    
    Args:
        config_manager (EnvConfigManager): Configuration management instance
    
    Returns:
        A tracing configuration object
    
    Raises:
        ValueError: If an unsupported exporter type is specified
    """
    # Retrieve tracing configuration parameters from environment
    service_name = config_manager.get_service_name()
    endpoint = config_manager.get_endpoint()
    exporter_type = config_manager.get_exporter_type()
    insecure = config_manager.get_insecure()

    # Select and instantiate the appropriate tracing configuration
    if exporter_type == "otlp":
        return OTLPTracingConfig(service_name, endpoint, insecure)
    elif exporter_type == "jaeger":
        return JaegerTracingConfig(service_name, endpoint)
    else:
        raise ValueError(f"Unsupported exporter type: {exporter_type}")

def instrument_http_clients():
    """
    Instrument HTTP clients to enable automatic trace context propagation.
    
    This function adds tracing capabilities to standard HTTP client libraries.
    """
    HTTPXClientInstrumentor().instrument()
    RequestsInstrumentor().instrument()

def create_distributed_tracing_middleware(service_name):
    """
    Create a middleware for distributed tracing with comprehensive span creation.
    
    Args:
        service_name (str): Name of the current service
    
    Returns:
        A middleware class for handling distributed tracing
    """
    class DistributedTracingMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            # Skip tracing for metrics endpoint to avoid overhead
            if "/metrics" in request.url.path:
                return await call_next(request)

            # Extract trace context from incoming request headers
            context = extract(request.headers)
            token = attach(context)
            
            try:
                # Start a new span for the incoming request
                tracer = trace.get_tracer(__name__)
                with tracer.start_as_current_span(
                    request.url.path, 
                    kind=SpanKind.SERVER
                ) as span:
                    # Annotate the span with request metadata
                    current_span = trace.get_current_span()
                    trace_id = format_trace_id(current_span.get_span_context().trace_id)
                    span_id = format_trace_id(current_span.get_span_context().span_id)

                    span.set_attribute("http.method", request.method)
                    span.set_attribute("http.url", str(request.url))
                    span.set_attribute("service.name", service_name)
                    span.set_attribute("trace.id", trace_id)
                    span.set_attribute("span.id", span_id)
                    
                    # Process the request and capture response
                    response = await call_next(request)
                    
                    # Record response details and status
                    span.set_attribute("http.status_code", response.status_code)
                    span.set_status(
                        Status(StatusCode.ERROR, f"HTTP error: {response.status_code}") 
                        if 400 <= response.status_code < 600 
                        else Status(StatusCode.OK)
                    )
                    
                    return response
            except Exception as e:
                # Capture and log any exceptions during request processing
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
            finally:
                # Always detach the context to prevent leaks
                detach(token)

    return DistributedTracingMiddleware

def create_traced_request_utilities(service_name):
    """
    Create utility functions for making traced HTTP requests.
    
    Args:
        service_name (str): Name of the current service
    
    Returns:
        A dictionary of request utility functions
    """
    async def make_traced_httpx_request(url, method='GET', headers=None, data=None):
        """
        Make a traced request using httpx with explicit context propagation.
        
        Args:
            url (str): Target URL
            method (str): HTTP method
            headers (dict, optional): Additional headers
            data (dict, optional): Request payload
        
        Returns:
            httpx.Response: HTTP response
        """
        tracer = trace.get_tracer(__name__)
        
        async with tracer.start_as_current_span(
            f"http.{method.lower()}", 
            kind=SpanKind.CLIENT
        ) as span:
            # Prepare headers with trace context
            request_headers = headers or {}
            inject(request_headers)
            
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method, 
                    url, 
                    headers=request_headers, 
                    data=data
                )
                
                # Record request and response details
                span.set_attribute("http.url", url)
                span.set_attribute("http.method", method)
                span.set_attribute("http.status_code", response.status_code)
                
                return response

    # Note: The synchronous requests function remains unchanged
    def make_traced_requests(url, method='GET', headers=None, data=None):
        """
        Make a traced request using requests with explicit context propagation.
        
        Args:
            url (str): Target URL
            method (str): HTTP method
            headers (dict, optional): Additional headers
            data (dict, optional): Request payload
        
        Returns:
            requests.Response: HTTP response
        """
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span(
            f"http.{method.lower()}", 
            kind=SpanKind.CLIENT
        ) as span:
            # Prepare headers with trace context
            request_headers = headers or {}
            inject(request_headers)
            
            response = requests.request(
                method, 
                url, 
                headers=request_headers, 
                data=data
            )
                
            # Record request and response details
            span.set_attribute("http.url", url)
            span.set_attribute("http.method", method)
            span.set_attribute("http.status_code", response.status_code)
            
            return response

    return {
        'make_traced_httpx_request': make_traced_httpx_request,
        'make_traced_requests': make_traced_requests
    }

def configure_distributed_tracing(app: FastAPI):
    """
    Configure comprehensive distributed tracing for a FastAPI application.
    
    This function sets up:
    - Trace context configuration
    - HTTP client instrumentation
    - Distributed tracing middleware
    - Tracing utility functions
    
    Args:
        app (FastAPI): The FastAPI application to configure
    """
    # Load configuration from environment variables
    config_manager = EnvConfigManager()
    service_name = config_manager.get_service_name()

    # Create and configure tracing
    tracing_config = create_tracing_configuration(config_manager)
    tracing_config.configure_tracing()

    # Instrument HTTP clients
    instrument_http_clients()

    # Create and add distributed tracing middleware
    DistributedTracingMiddleware = create_distributed_tracing_middleware(service_name)
    app.add_middleware(DistributedTracingMiddleware)

    # Create and attach request tracing utilities
    request_utilities = create_traced_request_utilities(service_name)
    app.make_traced_httpx_request = request_utilities['make_traced_httpx_request']
    app.make_traced_requests = request_utilities['make_traced_requests']