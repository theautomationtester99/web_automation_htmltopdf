import logging
from logging.handlers import RotatingFileHandler
import os
from color_formatter import ColorFormatter
from config_reader import ConfigReader

class LoggerConfig:
    """
    A configuration class for setting up a logger with both file and console outputs.

    This class is responsible for reading logging configurations from a properties file,
    setting up a logger with rotating file handling, console output, and applying custom formatting.

    Attributes:
        log_file (str): The file path for storing log output.
        config_reader (ConfigReader): A configuration reader for fetching properties from a file.
        log_level (int): The logging level (e.g., DEBUG, INFO) derived from configuration.
        logger (logging.Logger): The configured logger instance.
    """
    def __init__(self, log_file=os.path.join('logs', 'waf.log')):
        """
        Initializes the LoggerConfig object.

        Args:
            log_file (str, optional): Path to the log file. Defaults to 'logs/waf.log'.
        """
        self.log_file = log_file
        self.config_reader = ConfigReader("start.properties")  # Use provided ConfigReader or create a default one
        self.log_level = self.get_log_level_from_config()
        self.logger = self.setup_logger()

    def get_log_level_from_config(self):
        """
        Retrieves the logging level from the configuration file.

        Reads the logging level from the 'Logging' section in the properties file
        and converts it into a logging module constant (e.g., DEBUG, INFO).

        Returns:
            int: Logging level as a constant from the logging module (e.g., logging.DEBUG).
        """
        log_level_str = self.config_reader.get_property('Logging', 'LogLevel', fallback='DEBUG').upper()
        return getattr(logging, log_level_str, logging.DEBUG)

    def setup_logger(self):
        """
        Configures and returns a logger instance.

        Sets up a logger with the specified logging level, a rotating file handler
        (with a size limit and backup count), and a console handler. Applies formatting
        for both file and console outputs.

        Returns:
            logging.Logger: The configured logger instance.
        """
        logger = logging.getLogger('WafLogger')
        logger.setLevel(self.log_level)

        if not logger.handlers:
            # Create the directory for logs if it doesn't already exist
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

            # Rotating File Handler (rolls over log files after reaching 5MB)
            file_handler = RotatingFileHandler(self.log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]'))

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(ColorFormatter())  # Use ColorFormatter for console output

            # Add handlers to logger
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger