import logging
import traceback
from colorama import Fore, Style

class ColorFormatter(logging.Formatter):
    """
    A custom logging formatter that applies colored formatting to log messages based on their severity level.

    This formatter uses ANSI escape codes (via the `colorama` library) to add color to log messages, making it easier
    to distinguish between different log levels. The formatted output includes details such as the timestamp, logger name,
    log level, process ID, message, and the source file with the line number. If exception information is present, it is
    appended to the log message in a highlighted style.
    """

    def __init__(self):
        """
        Initializes the ColorFormatter with default and colored formats for different log levels.

        The default format is used when no specific color is assigned to a log level. Each log level (DEBUG, INFO, WARNING,
        ERROR, CRITICAL) is mapped to a specific color scheme using ANSI escape codes.

        Attributes:
            default_format (str): The default log message format without color.
            formats (dict): A dictionary mapping log levels to their respective colored formats.
        """
        super().__init__()
        self.default_format = '%(asctime)s - %(name)s - %(levelname)s - [PID:%(process)d] %(message)s [%(filename)s:%(lineno)d]'
        self.formats = {
            logging.DEBUG: f'{Fore.BLUE}{Style.BRIGHT}%(asctime)s - %(name)s - %(levelname)s - [PID:%(process)d] %(message)s [%(filename)s:%(lineno)d]{Style.RESET_ALL}',
            logging.INFO: f'{Fore.GREEN}%(asctime)s - %(name)s - %(levelname)s - [PID:%(process)d] %(message)s [%(filename)s:%(lineno)d]{Style.RESET_ALL}',
            logging.WARNING: f'{Fore.YELLOW}%(asctime)s - %(name)s - %(levelname)s - [PID:%(process)d] %(message)s [%(filename)s:%(lineno)d]{Style.RESET_ALL}',
            logging.ERROR: f'{Fore.RED}{Style.BRIGHT}%(asctime)s - %(name)s - %(levelname)s - [PID:%(process)d] %(message)s [%(filename)s:%(lineno)d]{Style.RESET_ALL}',
            logging.CRITICAL: f'{Fore.RED}{Style.BRIGHT}%(asctime)s - %(name)s - %(levelname)s - [PID:%(process)d] %(message)s [%(filename)s:%(lineno)d]{Style.RESET_ALL}'
        }

    def format(self, record):
        """
        Formats a log record with appropriate coloring based on its log level.

        This method dynamically applies a colored format to the log message based on the log level. If no specific color
        is defined for the log level, the default format is used. Additionally, if exception information is present in the
        log record, it is appended to the log message in a highlighted style.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log message with color and exception details (if applicable).
        """
        # Apply the standard or colored format based on the log level
        self._style._fmt = self.formats.get(record.levelno, self.default_format)
        formatted_message = super().format(record)

        # Append exception information if present
        if record.exc_info:
            exc_traceback = traceback.format_exception(*record.exc_info)
            formatted_message += f'\n{Fore.MAGENTA}{Style.BRIGHT}{"".join(exc_traceback)}{Style.RESET_ALL}'

        return formatted_message
