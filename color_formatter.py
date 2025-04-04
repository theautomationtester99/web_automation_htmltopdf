import logging
import traceback
from colorama import Fore, Style

class ColorFormatter(logging.Formatter):
    """
    A custom logging formatter that applies colored formatting based on log levels.

    This formatter uses ANSI escape codes to add color to log messages based on their severity level.
    The formatted output includes information such as timestamp, logger name, log level, and the source file with line number.
    Exception information, if present, is appended to the log message in a highlighted format.

    Attributes:
        default_format (str): The default format string for log messages.
        formats (dict): A dictionary mapping log levels to their respective format strings.
    """
    def __init__(self):
        """
        Initializes the ColorFormatter with default and colored formats for log levels.

        The format strings include placeholders for timestamp, logger name, log level, message, source file, and line number.
        The formats attribute maps each log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) to a specific color scheme.

        """
        super().__init__()
        self.default_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]'
        self.formats = {
            logging.DEBUG: f'{Fore.BLUE}{Style.BRIGHT}%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]{Style.RESET_ALL}',
            logging.INFO: f'{Fore.GREEN}%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]{Style.RESET_ALL}',
            logging.WARNING: f'{Fore.YELLOW}%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]{Style.RESET_ALL}',
            logging.ERROR: f'{Fore.RED}{Style.BRIGHT}%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]{Style.RESET_ALL}',
            logging.CRITICAL: f'{Fore.RED}{Style.BRIGHT}%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]{Style.RESET_ALL}'
        }
    
    def format(self, record):
        """
        Formats a log record with appropriate coloring based on its log level.

        This method first applies the standard format, then checks the log level and assigns a colored format.
        If exception information is present, it appends the formatted traceback to the log message in a highlighted style.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log message.
        """
        # Apply the standard format first
        self._style._fmt = self.formats.get(record.levelno, self.default_format)
        formatted_message = super().format(record)

        # Check for exception information
        if record.exc_info:
            exc_traceback = traceback.format_exception(*record.exc_info)
            formatted_message += f'\n{Fore.MAGENTA}{Style.BRIGHT}{"".join(exc_traceback)}{Style.RESET_ALL}'
            # exc_traceback = "".join(traceback.format_tb(record.exc_info[2]))  # Only the traceback
            # formatted_message += f'\n{Fore.MAGENTA}{Style.BRIGHT}{exc_traceback}{Style.RESET_ALL}'
                    
        return formatted_message
    
    
