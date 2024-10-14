from abc import ABC, abstractmethod

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.trace import set_tracer_provider, get_tracer_provider
from opentelemetry.exporter.jaeger.thrift import JaegerExporter


class TracingConfig(ABC):
    """
    Abstract base class for configuring tracing with different exporters.

    This class defines the interface for configuring tracing. Concrete implementations
    should provide specific configurations for various tracing exporters.

    Attributes:
        service_name (str): The name of the service for tracing.
        endpoint (str): The endpoint URL for the tracing exporter.
        insecure (bool): Whether the connection is insecure (default is True).
    """

    def __init__(self, service_name: str, endpoint: str, insecure: bool = True):
        """
        Initializes the TracingConfig with the given parameters.

        Args:
            service_name (str): The name of the service for tracing.
            endpoint (str): The endpoint URL for the tracing exporter.
            insecure (bool, optional): Whether the connection is insecure (default is True).
        """
        self.service_name = service_name
        self.endpoint = endpoint
        self.insecure = insecure

    @abstractmethod
    def configure_tracing(self):
        """
        Abstract method to configure tracing based on the exporter.

        Concrete implementations must provide their own configuration logic.
        """
        pass


class OTLPTracingConfig(TracingConfig):
    """
    Concrete implementation of TracingConfig for OTLP exporter.

    This class configures tracing using the OTLP exporter.

    Methods:
        configure_tracing: Configures OpenTelemetry tracing with OTLP exporter.
    """

    def configure_tracing(self):
        """
        Configures tracing using the OTLP exporter.

        This method sets up OpenTelemetry Tracing with the OTLP exporter, including:
        - Setting the tracer provider with a resource that includes the service name.
        - Creating an OTLPSpanExporter and a BatchSpanProcessor.
        - Adding the span processor to the tracer provider.
        """
        # Set up OpenTelemetry Tracing
        set_tracer_provider(
            TracerProvider(
                resource=Resource.create({SERVICE_NAME: self.service_name})
            )
        )
        tracer_provider = get_tracer_provider()

        # Configure OTLP exporter
        exporter = OTLPSpanExporter(endpoint=self.endpoint, insecure=self.insecure)
        span_processor = BatchSpanProcessor(exporter)
        tracer_provider.add_span_processor(span_processor)


class JaegerTracingConfig(TracingConfig):
    """
    Concrete implementation of TracingConfig for Jaeger exporter.

    This class configures tracing using the Jaeger exporter.

    Methods:
        configure_tracing: Configures OpenTelemetry tracing with Jaeger exporter.
    """

    def configure_tracing(self):
        """
        Configures tracing using the Jaeger exporter.

        This method sets up OpenTelemetry Tracing with the Jaeger exporter, including:
        - Setting the tracer provider with a resource that includes the service name.
        - Creating a JaegerExporter and a BatchSpanProcessor.
        - Adding the span processor to the tracer provider.
        """
        # Set up OpenTelemetry Tracing
        set_tracer_provider(
            TracerProvider(
                resource=Resource.create({SERVICE_NAME: self.service_name})
            )
        )
        tracer_provider = get_tracer_provider()

        # Configure Jaeger exporter
        exporter = JaegerExporter(agent_endpoint=self.endpoint)
        span_processor = BatchSpanProcessor(exporter)
        tracer_provider.add_span_processor(span_processor)
