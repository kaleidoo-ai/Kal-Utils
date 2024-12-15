import logging
from opentelemetry import trace

class MetricsLogFilter(logging.Filter):
    def filter(self, record):
        """
        Filters out log messages related to the `/metrics` endpoint.
        
        - Prevents cluttering of logs with frequent and repetitive requests to `/metrics`.
        - Useful in environments where a metrics endpoint is polled regularly (e.g., by Prometheus).
        - Filters out log messages containing '/metrics' or 'GET /metrics'.
        
        Args:
            record (logging.LogRecord): The log record to be evaluated.

        Returns:
            bool: Returns False if the log message contains `/metrics`, effectively excluding it.
        """
        return not ('/metrics' in record.getMessage() or 
                    'GET /metrics' in record.getMessage())
    
class TraceLogFilter(logging.Filter):
    def filter(self, record):
        """
        Adds trace and span IDs from the OpenTelemetry context to log records.
        
        - Retrieves the current span using OpenTelemetry's `trace.get_current_span()`.
        - Attempts to extract the span context (`trace_id` and `span_id`) from the current span.
        - Formats the IDs into strings for inclusion in the log record.
        - Handles exceptions gracefully, assigning default values (`"no_trace"` and `"no_span"`)
          if there is no active span or the span context is invalid.
        
        Args:
            record (logging.LogRecord): The log record to be modified.

        Returns:
            bool: Always returns True to allow the record to be logged.
        """
        current_span = trace.get_current_span()  # Retrieve the current active span
        try:
            # Get the span context (trace_id and span_id)
            span_context = current_span.get_span_context()
            
            # Format trace_id and span_id to hexadecimal strings
            record.trace_id = trace.format_trace_id(span_context.trace_id)
            record.span_id = trace.format_span_id(span_context.span_id)
        except Exception:
            # If no span or invalid span context, set default values
            record.trace_id = "no_trace"
            record.span_id = "no_span"
        
        return True  # Allow all records to pass through the filter