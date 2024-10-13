from fastapi import FastAPI, Request
from opentelemetry import trace

from tempo.tracing_manager import (
    OTLPTracingConfig,
    JaegerTracingConfig,
)
from core.config_managers import EnvConfigManager


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
    