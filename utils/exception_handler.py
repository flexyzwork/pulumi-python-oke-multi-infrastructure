import logging
from functools import wraps

# Use the global logger
logger = logging.getLogger('global_logger')


def handle_exceptions(func):
    """Decorator to handle exceptions and log them."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log the error with stack trace
            logger.error(f'Error in {func.__name__}: {e}', exc_info=True)
            raise

    return wrapper


def apply_exception_handler(cls):
    """Class decorator to apply exception handler to all methods in a class."""
    for attr_name, attr_value in cls.__dict__.items():
        if callable(attr_value) and not attr_name.startswith('__'):
            setattr(cls, attr_name, handle_exceptions(attr_value))
    return cls
