import logging
import json
import sys
from opentelemetry import trace
from opentelemetry.instrumentation.logging import LoggingInstrumentor

class MetricsLogFilter(logging.Filter):
    def filter(self, record):
        # More robust filtering for metrics endpoints
        return not ('/metrics' in record.getMessage() or 
                    'GET /metrics' in record.getMessage())
    
class TraceLogFilter(logging.Filter):
    def filter(self, record):
        current_span = trace.get_current_span()
        try:
            # Check if span context is valid
            span_context = current_span.get_span_context()
            
            # Use format methods to convert trace and span IDs
            record.trace_id = trace.format_trace_id(span_context.trace_id)
            record.span_id = trace.format_span_id(span_context.span_id)
        except Exception:
            # Fallback if no active span or context is invalid
            record.trace_id = "no_trace"
            record.span_id = "no_span"
        
        return True

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_message = {
            "time": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage()
        }
        return json.dumps(log_message)
    
class JsonFormatter1(logging.Formatter):
    def format(self, record):
        # Create the log message dictionary
        log_message = {
            "time": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "trace_id": getattr(record, "trace_id", "no_trace"),
            "span_id": getattr(record, "span_id", "no_span"),
            "message": record.getMessage()
        }
        return json.dumps(log_message)
    
def setup_trace_logging(root_logger):
    # # Create a formatter that includes trace and span IDs
    # formatter = logging.Formatter(
    #     '%(asctime)s - %(name)s - %(levelname)s - '
    #     'Trace ID: %(trace_id)s - Span ID: %(span_id)s - '
    #     '%(message)s'
    # )

    # Create a JSON formatter
    json_formatter = JsonFormatter1()
    
    # If you have existing handlers, modify them
    for handler in root_logger.handlers:
        handler.addFilter(TraceLogFilter())
        handler.addFilter(MetricsLogFilter())
        handler.setFormatter(json_formatter)
    
    # If no handlers exist, add a default one
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.addFilter(TraceLogFilter())
        handler.addFilter(MetricsLogFilter())
        handler.setFormatter(json_formatter)
        root_logger.addHandler(handler)

    # Suppress specific noisy loggers
    logging.getLogger('opentelemetry').setLevel(logging.ERROR)
    logging.getLogger('uvicorn.access').setLevel(logging.ERROR)
    logging.getLogger('opentelemetry.trace.status').setLevel(logging.ERROR)


def init_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(JsonFormatter())
        logger.addHandler(stream_handler)
    return logger

def init_logger1(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # Call this during application startup
    setup_trace_logging(logger)
    LoggingInstrumentor().instrument()
    return logger
