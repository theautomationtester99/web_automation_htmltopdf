import logging
import os
import sys
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from multiprocessing import Queue
from color_formatter import ColorFormatter
from config import start_properties


class LoggerConfig:
    """
    A multiprocessing-safe logger configuration class with ColorFormatter support for colored console output.
    
    DEBUG (10) Used for detailed information, typically useful for diagnosing problems. For example, you might use DEBUG messages to understand the flow of your program during development.

    INFO (20) General information about program execution, such as confirming that a particular process has started or finished successfully.

    WARNING (30) Indicates something unexpected happened or could happen in the future, but the program continues to operate. For example, using deprecated features or approaching resource limits.

    ERROR (40) A serious issue that has occurred, preventing a part of the program from functioning properly. Examples include failed database connections or missing files.

    CRITICAL (50) A very severe issue indicating the program might not be able to continue running, such as system crashes or unhandled exceptions.
    """

    def __init__(self, log_file='', log_queue=None):
        """
        Initializes the LoggerConfig object for multiprocessing.

        Args:
            log_file (str, optional): Path to the log file. Defaults to 'logs/waf.log'.
            log_queue (multiprocessing.Queue, optional): Queue for handling log messages.
        """
        if getattr(sys, 'frozen', False):  # Check if running as a frozen executable
            script_dir = os.path.dirname(sys.executable)  # Use the directory of the executable
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))  # Normal script behavior

        generic_path = os.path.join(script_dir, "logs")
        log_file = os.path.join(generic_path, 'waf.log')

        self.log_file = log_file
        self.log_level = self.get_log_level_from_config()
        self.log_queue = log_queue or Queue()  # Use provided Queue or create a new one
        self.logger = self.setup_logger()

    def get_log_level_from_config(self):
        """
        Retrieves the logging level from the configuration file.
        """
        log_level_str = start_properties.LOG_LEVEL.upper()
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
        file_handler.setLevel(logging.DEBUG)
        # file_handler.setLevel(self.log_level)
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
