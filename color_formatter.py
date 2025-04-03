import logging
import traceback
from colorama import Fore, Style

class ColorFormatter(logging.Formatter):
    def __init__(self):
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
    
    
