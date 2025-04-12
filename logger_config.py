import logging
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
import os
from multiprocessing import Queue
from color_formatter import ColorFormatter
from config_reader import ConfigReader


class LoggerConfig:
    """
    A multiprocessing-safe logger configuration class with ColorFormatter support for colored console output.
    """

    def __init__(self, log_file=os.path.join('logs', 'waf.log'), log_queue=None):
        """
        Initializes the LoggerConfig object for multiprocessing.

        Args:
            log_file (str, optional): Path to the log file. Defaults to 'logs/waf.log'.
            log_queue (multiprocessing.Queue, optional): Queue for handling log messages.
        """
        self.log_file = log_file
        self.config_reader = ConfigReader("start.properties")
        self.log_level = self.get_log_level_from_config()
        self.log_queue = log_queue or Queue()  # Use provided Queue or create a new one
        self.logger = self.setup_logger()

    def get_log_level_from_config(self):
        """
        Retrieves the logging level from the configuration file.
        """
        log_level_str = self.config_reader.get_property('Logging', 'LogLevel', fallback='DEBUG').upper()
        return getattr(logging, log_level_str, logging.DEBUG)

    def setup_logger(self):
        """
        Configures and returns a multiprocessing-safe logger instance with process details.
        """
        logger = logging.getLogger('WafLogger')
        logger.setLevel(self.log_level)

        if not logger.handlers:
            # QueueHandler to send log messages to the listener
            queue_handler = QueueHandler(self.log_queue)
            logger.addHandler(queue_handler)

        return logger

    def start_listener(self):
        """
        Starts a QueueListener to process log messages from the queue.
        """
        # Create the directory for logs if it doesn't already exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

        # Rotating File Handler
        file_handler = RotatingFileHandler(self.log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d] [PID:%(process)d] %(message)s'
        ))

        # Console handler with ColorFormatter
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(ColorFormatter())  # Use ColorFormatter for colored console output

        # QueueListener processes messages from the queue
        listener = QueueListener(self.log_queue, file_handler, console_handler)
        listener.start()
        return listener
