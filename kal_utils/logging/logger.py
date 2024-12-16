import logging
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from .filters import MetricsLogFilter, TraceLogFilter
from .formats import JsonFormatter

def modify_existing_handlers(root_logger, json_formatter):
    """
    Modifies the existing handlers of the root logger by adding filters and a new JSON formatter.
    Filters applied: TraceLogFilter and MetricsLogFilter.
    """
    for handler in root_logger.handlers:
        # Add filters to the handler to capture trace and span IDs, and exclude metrics logs
        handler.addFilter(TraceLogFilter())
        handler.addFilter(MetricsLogFilter())
        # Set the JSON formatter for consistent log formatting
        handler.setFormatter(json_formatter)


def add_default_handler_if_needed(root_logger, json_formatter):
    """
    Adds a default stream handler to the logger if no handlers exist.
    The default handler will output logs to the console and apply necessary filters and the JSON formatter.
    """
    if not root_logger.handlers:
        # Create a stream handler to output logs to the console
        handler = logging.StreamHandler()
        # Add filters to capture trace and span data and exclude metrics logs
        handler.addFilter(TraceLogFilter())
        handler.addFilter(MetricsLogFilter())
        # Set the JSON formatter for this handler
        handler.setFormatter(json_formatter)
        # Add the handler to the root logger
        root_logger.addHandler(handler)

def suppress_noisy_loggers():
    """
    Suppresses verbose logs from specific noisy loggers (e.g., OpenTelemetry and Uvicorn).
    Sets the log level to ERROR to reduce unnecessary log output.
    """
    logging.getLogger('opentelemetry').setLevel(logging.ERROR)
    # logging.getLogger('uvicorn.access').setLevel(logging.ERROR)
    logging.getLogger('opentelemetry.trace.status').setLevel(logging.ERROR)

def setup_trace_logging(root_logger):
    """
    Sets up the trace logging configuration for the root logger.
    This includes creating a JSON formatter, modifying existing handlers,
    adding a default handler if needed, and suppressing noisy loggers.
    """
    # Create the JSON formatter for structured logging
    json_formatter = JsonFormatter()

    # Modify existing handlers with filters and the JSON formatter
    modify_existing_handlers(root_logger, json_formatter)

    # If no handlers exist, add a default stream handler with necessary filters and formatter
    add_default_handler_if_needed(root_logger, json_formatter)

    # Suppress noisy loggers that log excessive information (e.g., OpenTelemetry and Uvicorn)
    suppress_noisy_loggers()


def init_logger(name):
    """
    Initializes the logger with the specified name, sets its log level, and sets up trace logging.
    This should be called during application startup to configure logging.
    """
    # Create a logger with the provided name
    logger = logging.getLogger(name)
    # Set the log level to INFO, so it captures logs of level INFO or higher
    logger.setLevel(logging.INFO)

    # Set up trace logging (filters, formatter, and noisy loggers)
    setup_trace_logging(logger)

    # Enable OpenTelemetry logging instrumentation to track trace data
    LoggingInstrumentor().instrument()

    # Return the configured logger for use in the application
    return logger
