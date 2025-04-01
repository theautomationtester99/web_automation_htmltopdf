import logging
from color_formatter import ColorFormatter  # Import the separate ColorFormatter class

class LoggerConfig:
    def __init__(self, log_file='project.log', log_level=logging.DEBUG):
        self.log_file = log_file
        self.log_level = log_level
        self.logger = self.setup_logger()

    def setup_logger(self):
        logger = logging.getLogger('ProjectLogger')
        logger.setLevel(self.log_level)

        if not logger.handlers:
            # File handler
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
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