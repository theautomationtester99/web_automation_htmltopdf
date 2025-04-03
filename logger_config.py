import logging
from logging.handlers import RotatingFileHandler
import os
from color_formatter import ColorFormatter  # Import the separate ColorFormatter class
import configparser

class LoggerConfig:
    def __init__(self, log_file=os.path.join('logs', 'waf.log'), config_file="start.properties"):
        self.log_file = log_file
        self.config_file = config_file
        self.log_level = self.get_log_level_from_config()
        self.logger = self.setup_logger()

    def get_log_level_from_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            log_level_str = config.get('Logging', 'LogLevel', fallback='DEBUG').upper()
            return getattr(logging, log_level_str, logging.DEBUG)
        return logging.DEBUG  # Default to DEBUG if config file or property is missing

    def setup_logger(self):
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

if __name__ == "__main__":
    logger = LoggerConfig().logger
    logger.debug("Testing debug message.")     # Blue
    logger.info("Testing info message.")       # Green
    logger.warning("Testing warning message.") # Yellow
    logger.error("Testing error message.")     # Bold Red
    logger.critical("Testing critical message.") # Bold Red