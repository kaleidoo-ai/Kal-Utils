from functools import wraps

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode


# def add_span_attributes(**attributes):
#     """
#     Decorator to add attributes to a span for a decorated asynchronous function.

#     This decorator creates a span for the decorated function and sets the specified
#     attributes on it. It also sets the span status to OK if the function executes
#     without errors, and to ERROR if an exception is raised.

#     Args:
#         **attributes: Arbitrary keyword arguments representing the attributes
#                       to be set on the span. For example, `key1="value1"`.

#     Returns:decorator
#         function: The decorated asynchronous function with tracing.
#     """
#     def decorator(func):
#         @wraps(func)
#         async def wrapper(*args, **kwargs):
#             tracer = trace.get_tracer(__name__)
#             # Create a new span with the function name
#             with tracer.start_as_current_span(func.__name__) as span:
#                 # Set static attributes
#                 for key, value in attributes.items():
#                     index = 0
#                     # Handle dynamic attributes
#                     if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
#                         # Extract parameter name from `{{param_name}}`
#                         param_name = value.strip("{{}}")
#                         # Get the parameter value from kwargs
#                         # if param_name in kwargs:
#                         span.set_attribute(key, args[index])
#                         index = index + 1
#                         # elif param_name in args:
#                         #     span.set_attribute(key, args[param_name])
#                     else:
#                         span.set_attribute(key, value)

#                 try:
#                     # Call the decorated function
#                     result = await func(*args, **kwargs)
#                     # Set span status to OK if no error occurs
#                     span.set_status(Status(StatusCode.OK, "Success"))
#                     return result
#                 except Exception as e:
#                     # Set span status to ERROR if an exception occurs
#                     span.set_status(Status(StatusCode.ERROR, str(e)))
#                     # Re-raise the exception to ensure proper error handling
#                     raise

#         return wrapper
#     return decorator


def add_span_attributes(**attributes):
    """
    Decorator to add attributes to a span for a decorated asynchronous function.

    This decorator creates a span for the decorated function and sets the specified
    attributes on it. It also sets the span status to OK if the function executes
    without errors, and to ERROR if an exception is raised.

    Args:
        **attributes: Arbitrary keyword arguments representing the attributes
                      to be set on the span. For example, `key1="value1"`.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            # Create a new span with the function name
            with tracer.start_as_current_span(func.__name__) as span:
                # Set static attributes
                for key, value in attributes.items():
                    if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                        # Extract parameter name from `{{param_name}}`
                        param_name = value.strip("{}")
                        # Try to get the parameter value from kwargs or args
                        if param_name in kwargs:
                            span.set_attribute(key, kwargs[param_name])
                        else:
                            # Use args and match by function signature position
                            try:
                                # Get the parameter's position from the function signature
                                func_signature = func.__code__.co_varnames
                                param_index = func_signature.index(param_name)
                                span.set_attribute(key, args[param_index])
                            except (ValueError, IndexError):
                                pass  # Parameter not found
                    else:
                        # Set static value
                        span.set_attribute(key, value)

                try:
                    # Call the decorated function
                    result = await func(*args, **kwargs)
                    # Set span status to OK if no error occurs
                    span.set_status(Status(StatusCode.OK, "Success"))
                    return result
                except Exception as e:
                    # Set span status to ERROR if an exception occurs
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    # Re-raise the exception to ensure proper error handling
                    raise

        return wrapper
    return decorator


def add_span_event(event_name):
    """
    Decorator to add an event to a span for a decorated asynchronous function.

    This decorator creates a span for the decorated function and logs an event with
    the specified name to that span. It does not modify the span status based on
    the function execution outcome.

    Args:
        event_name (str): The name of the event to be added to the span.

    Returns:
        function: The decorated asynchronous function with tracing.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(func.__name__) as span:
                span.add_event(event_name)
                return await func(*args, **kwargs)
        return wrapper
    return decorator
