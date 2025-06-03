import logging


# Create a global logger
def setup_global_logger(log_file='app.log', level=logging.INFO):
    """Set up a global logger."""
    logger = logging.getLogger('global_logger')
    logger.setLevel(level)

    # Formatter for log messages
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File handler for logging to a file
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Stream handler for logging to the console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Add handlers to the logger if not already added
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


global_logger = setup_global_logger()
