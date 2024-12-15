import logging
import json
    
class JsonFormatter(logging.Formatter):
    def format(self, record):
        """
        Formats log records into a structured JSON format.
        
        - Enhances logs by including trace and span IDs (if available) for distributed tracing.
        - Provides a fallback for trace and span IDs when they are not present in the log record.
        - Ensures consistent and machine-readable log output using JSON.

        Args:
            record (logging.LogRecord): The log record to be formatted.

        Returns:
            str: A JSON-formatted string representing the log message.
        """
        # Create the log message dictionary
        log_message = {
            "time": self.formatTime(record, self.datefmt),  # Formats the timestamp of the log
            "name": record.name,  # Logger name (e.g., "example_logger")
            "level": record.levelname,  # Log level (e.g., "INFO", "ERROR")
            "trace_id": getattr(record, "trace_id", "no_trace"),  # Trace ID for distributed tracing
            "span_id": getattr(record, "span_id", "no_span"),  # Span ID for distributed tracing
            "message": record.getMessage()  # The actual log message
        }
        return json.dumps(log_message)  # Convert the log message dictionary to a JSON string
