from contextlib import contextmanager
from typing import Optional, Dict, Any

from opentelemetry import trace


@contextmanager
def span_with_attributes(attributes, span_name="custom-span"):
    """
    Context manager for creating a span with specified attributes.

    This context manager starts a new OpenTelemetry span with the given span name
    and sets the provided attributes on that span. It ensures that the span is closed
    after exiting the context.

    Args:
        attributes (dict): A dictionary of attributes to set on the span.
        span_name (str, optional): The name of the span. Defaults to "custom-span".

    Yields:
        Span: The created span with the given attributes set.
    """
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(span_name) as span:
        # Set the specified attributes on the span
        for key, value in attributes.items():
            span.set_attribute(key, value)
        # Yield the span to the context
        yield span


@contextmanager
def span_with_event(event_name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Context manager for adding an event with optional attributes to the current active span.

    This context manager adds an event with the specified name and attributes to the current
    active OpenTelemetry span. If no active span is available, it does nothing.

    Args:
        event_name (str): The name of the event to add to the span.
        attributes (Optional[Dict[str, Any]]): A dictionary of attributes to set on the event.

    Yields:
        Span: The current active span with the event and attributes added, or None if no span.
    """
    # Ensure you are using the correct tracer
    tracer = trace.get_tracer(__name__)

    # Get the current active span
    current_span = trace.get_current_span()

    if not current_span or not current_span.is_recording():
        # If no active span or span is not recording, do nothing
        yield None
        return

    # Add the event to the current span with optional attributes
    current_span.add_event(event_name, attributes=attributes)

    # Yield the current span with the event and attributes added
    try:
        yield current_span
    finally:
        pass  # If you want to clean up anything after the block ends
