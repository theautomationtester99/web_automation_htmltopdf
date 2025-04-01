import logging
from colorama import Fore, Style

class ColorFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        self.default_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self.formats = {
            logging.DEBUG: f'{Fore.BLUE}{Style.BRIGHT}%(asctime)s - %(name)s - %(levelname)s - %(message)s{Style.RESET_ALL}',
            logging.INFO: f'{Fore.GREEN}%(asctime)s - %(name)s - %(levelname)s - %(message)s{Style.RESET_ALL}',
            logging.WARNING: f'{Fore.YELLOW}%(asctime)s - %(name)s - %(levelname)s - %(message)s{Style.RESET_ALL}',
            logging.ERROR: f'{Fore.RED}{Style.BRIGHT}%(asctime)s - %(name)s - %(levelname)s - %(message)s{Style.RESET_ALL}',
            logging.CRITICAL: f'{Fore.RED}{Style.BRIGHT}%(asctime)s - %(name)s - %(levelname)s - %(message)s{Style.RESET_ALL}'
        }

    def format(self, record):
        self._style._fmt = self.formats.get(record.levelno, self.default_format)
        return super().format(record)
