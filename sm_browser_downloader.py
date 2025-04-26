from driver_functions import BrowserDriver


class SMBrowserDownloader(BrowserDriver):
    """
    A manager class extending BrowserDriver that provides utilities to manage browser interactions, generate PDF reports,
    and perform common testing tasks for any application under test.

    Attributes:
        logger (logging.Logger): Logger instance for logging debug, info, and error messages.
        repo_m (PdfReportManager): An instance to manage and generate PDF reports.
        utils (Utils): An instance of utility methods for OS detection and other operations.
        chrome_logo_src_b64 (str): Base64 encoded string for Chrome logo image.
        edge_logo_src_b64 (str): Base64 encoded string for Edge logo image.
        linux_logo_src_b64 (str): Base64 encoded string for Linux logo image.
        win_logo_src_b64 (str): Base64 encoded string for Windows logo image.
    """
    def __init__(self, logger):
        super().__init__(logger)

    def setup_sm_browsers(self, browser_name):
            """
            Launches the specified browser, captures OS and browser details, and logs information in the PDF report.

            Args:
            browser_name (str): The name of the browser to launch (e.g., "Chrome", "Edge").

            Raises:
            Exception: If any error occurs while launching the browser.
            """
            try:
                self.logger.debug(f"Launching {browser_name} .......")
                self.launch_browser(browser_name)
            except Exception as e:
                self.logger.error("An error occurred: %s", e, exc_info=True)
                raise

    def close_sm_browsers(self):
            """
            Launches the specified browser, captures OS and browser details, and logs information in the PDF report.

            Args:
            browser_name (str): The name of the browser to launch (e.g., "Chrome", "Edge").

            Raises:
            Exception: If any error occurs while launching the browser.
            """
            try:
                self.close_browser()
            except Exception as e:
                self.logger.error("An error occurred: %s", e, exc_info=True)
                raise