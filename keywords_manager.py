from config import start_properties
from constants import CHROME_LOGO_SRC_B64, EDGE_LOGO_SRC_B64, LINUX_LOGO_SRC_B64, SE_GRID_B64, WIN_LOGO_SRC_B64
from driver_functions import BrowserDriver
from pdf_report_manager import PdfReportManager
from utilities import Utils
from datetime import datetime
import asyncio
from axe_selenium_python import Axe

class KeywordsManager(BrowserDriver):
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
    def __init__(self, logger, retry_count=1):
        super().__init__(logger)
        self.screenshot_strategy = self._get_screenshot_strategy()
        self.highlight_enabled = self._get_highlight_element_strategy()
        self.screenshot_no = 0
        self.screenshot_first_str = ""
        self.logger = logger
        self.retry_count = retry_count
        self.repo_m = PdfReportManager(self.logger)
        self.repo_m.current_retry = self.retry_count
        self.utils = Utils(self.logger)
        self.chrome_logo_src_b64 = CHROME_LOGO_SRC_B64
        self.edge_logo_src_b64 = EDGE_LOGO_SRC_B64
        self.linux_logo_src_b64 = LINUX_LOGO_SRC_B64
        self.win_logo_src_b64 = WIN_LOGO_SRC_B64
        self.se_grid_b64 = SE_GRID_B64

    def update_retry_count(self, retry_count):
        """
        Updates the retry count in KeywordsManager and propagates it to PdfReportManager.

        Args:
            retry_count (int): The updated retry count.
        """
        self.retry_count = retry_count
        self.repo_m.current_retry = retry_count  # Update retry count in PdfReportManager
        # self.repo_m.step_no = 1  # Reset step number for the new retry
        self.logger.debug(f"Retry count updated to {retry_count}")

    '''
    The below are the keywords that can be used generically for any application under testing.
    '''
    
    def _get_screenshot_strategy(self):
        """
        Fetches the screenshot_return value from the start.properties file.

        Args:
            start_props_reader (ConfigReader): Reader for the 'start.properties' configuration file.

        Returns:
            str: The value of screenshot_return (always, on-error, or never).
        """
        strategy = str(start_properties.SCREENSHOT_STRATEGY).lower()

        # Validate the strategy and default to "always" if invalid
        if strategy not in ["always", "on-error", "never"]:
            self.logger.warning(f"Invalid screenshot_strategy '{strategy}' found in configuration. Defaulting to 'always'.")
            strategy = "always"
        
        if strategy == "never":
            self.logger.info("Mapping 'never' screenshot strategy to 'on-error'.")
            strategy = "on-error"

        return strategy
    
    def _get_highlight_element_strategy(self):
        """
        Fetches the screenshot_return value from the start.properties file.

        Args:
            start_props_reader (ConfigReader): Reader for the 'start.properties' configuration file.

        Returns:
            str: The value of screenshot_return (always, on-error, or never).
        """
        highlight_enabled = start_properties.HIGHLIGHT_ELEMENTS.lower() == 'yes'

        return highlight_enabled

    def ge_switch_to_default_content(self):
        """
        Switches to the specified iframe and logs the result in the PDF report.

        Args:
            locator (str): The locator for the iframe.
            locator_type (str): The type of locator.
            element_name (str): The user-friendly name of the iframe.

        Raises:
            Exception: If any error occurs while switching to the iframe.
        """
        try:
            self.switch_to_default_content()
        except Exception as e:
            self.logger.error("An error occurred: %s", e, exc_info=True)
            raise
    
    def ge_switch_to_iframe(self, locator, locator_type, element_name):
        """
        Switches to the specified iframe using traditional locators.

        Args:
            locator (str): The locator for the iframe.
            locator_type (str): The type of locator.
            element_name (str): The user-friendly name of the iframe.

        Raises:
            Exception: If any error occurs while switching to the iframe.
        """
        try:
            self.logger.debug(f"Attempting to switch to iframe '{element_name}' using traditional locators.")
            # Traditional locator-based identification
            self.wait_for_element(locator, locator_type)
            self.scroll_into_view(locator, locator_type)
            if self.highlight_enabled:
                self.highlight(1, "blue", 2, locator, locator_type)
            self.switch_to_iframe(locator, locator_type)

            # Handle screenshot strategy
            if self.screenshot_strategy == "always":
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Switch to Iframe '{element_name}'",
                    sub_step_message="Switched to Iframe successfully",
                    sub_step_status='Pass',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Switch to Iframe '{element_name}'",
                    sub_step_message="Switched to Iframe successfully",
                    sub_step_status='Pass'
                )
        except Exception as e:
            self.logger.error(f"Failed to switch to iframe '{element_name}': {e}", exc_info=True)

            # Handle screenshot strategy for errors
            if self.screenshot_strategy in ["always", "on-error"]:
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Switch to Iframe '{element_name}'",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Switch to Iframe '{element_name}'",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail'
                )
            raise
    
    def ge_close(self):
        """
        Creates a PDF report and closes the browser instance.

        Logs the closure of the browser and generates a PDF report using the PdfReportManager.
        """
        self.logger.debug("Started creating pdf report")
        asyncio.run(self.repo_m.create_report())
        self.logger.debug("Closing the browser")
        self.close_browser()
    
    def ge_close_browser(self):
        """
        Creates a PDF report and closes the browser instance.

        Logs the closure of the browser and generates a PDF report using the PdfReportManager.
        """
        self.logger.debug("Closing the browser")
        self.close_browser()

    def ge_tcid(self, tc_id):
        """
        Sets the test case ID in the PDF report.

        Args:
            tc_id (str): The identifier of the test case to be included in the report.
        """
        self.logger.debug("Setting the test report of the PDF report")
        self.repo_m.page_title = "Test Report"
        self.repo_m.tc_id = tc_id

    def ge_tcdesc(self, tc_desc):
        """
        Sets the description of the test case in the PDF report.

        Args:
            tc_desc (str): The description of the test case.
        """
        pass
        self.logger.debug("Setting the test description in the PDF report")
        self.repo_m.test_description = tc_desc

    def ge_step(self, **data):
        """
        Populates the test details table in the PDF report with data provided.

        Args:
            **data: Arbitrary keyword arguments representing test details.
        """
        self.logger.debug("Populating the test details table in the PDF report")
        self.repo_m.add_report_data(**data)

    def ge_wait_for_seconds(self, how_seconds):
        """
        Pauses execution for the specified number of seconds.

        Args:
            how_seconds (str): The duration in seconds to pause execution.
        """
        self.logger.debug("Pausing the execution for " + str(how_seconds) + " seconds")
        self.wait_for_some_time(how_seconds)

    def ge_open_browser(self, browser_name):
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
            self.logger.debug("Capturing the OS where the browser is running.")

            # Determine OS and browser details
            if self.run_in_selenium_grid.lower() == "yes":
                self.logger.debug("Capturing the OS where the browser is running in Selenium Grid.")
                os_name = self.grid_os_info
                self.repo_m.grid_img_src = self.se_grid_b64
            else:
                self.logger.debug("Capturing the OS where the browser is running in local machine.")
                os_name = self.utils.detect_os()

            # Populate OS details in the PDF report
            if str(os_name).lower() == "linux":
                self.logger.debug(f"Populating the OS details in the PDF report as {os_name}")
                self.repo_m.os_img_src = self.linux_logo_src_b64
                self.repo_m.os_img_alt = os_name
            elif str(os_name).lower() == "windows":
                self.logger.debug(f"Populating the OS details in the PDF report as {os_name}")
                self.repo_m.os_img_src = self.win_logo_src_b64
                self.repo_m.os_img_alt = os_name

            # Populate browser details in the PDF report
            if browser_name.lower() == 'chrome':
                self.logger.debug(f"Populating the browser details in the PDF report as {browser_name}")
                self.repo_m.browser_img_src = self.chrome_logo_src_b64
                self.repo_m.browser_img_alt = browser_name.upper()
                self.repo_m.browser_version = self.ge_browser_version()
            elif browser_name.lower() == 'edge':
                self.logger.debug(f"Populating the browser details in the PDF report as {browser_name}")
                self.repo_m.browser_img_src = self.edge_logo_src_b64
                self.repo_m.browser_img_alt = browser_name.upper()
                self.repo_m.browser_version = self.ge_browser_version()

            self.logger.debug("Populating the step result details in the PDF report.")
            self.screenshot_first_str = f"{self.repo_m.tc_id}_{self.repo_m.browser_img_alt}"

            # Handle screenshot strategy
            if self.is_headless or self.is_running_grid:
                self.repo_m.add_report_data(
                    sub_step="Open Browser",
                    sub_step_message="The browser opened successfully",
                    sub_step_status="Pass"
                )
            else:
                if self.screenshot_strategy == "always":
                    self.screenshot_no += 1
                    self.repo_m.add_report_data(
                        sub_step="Open Browser",
                        sub_step_message="The browser opened successfully",
                        sub_step_status="Pass",
                        image_src=self.take_screenshot(
                            f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                        ),
                        image_alt=self.repo_m.browser_img_alt
                    )
                else:
                    self.repo_m.add_report_data(
                        sub_step="Open Browser",
                        sub_step_message="The browser opened successfully",
                        sub_step_status="Pass"
                    )
        except Exception as e:
            self.logger.error("An error occurred: %s", e, exc_info=True)
            self.logger.debug("Populating the step result details in the PDF report.")

            # Handle screenshot strategy for errors
            if self.screenshot_strategy in ["always", "on-error"]:
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Open Browser {browser_name}",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Open Browser {browser_name}",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail'
                )
            raise
    
    def ge_browser_version(self):
        """
        Retrieves the version of the currently active browser.

        Returns:
            str: The browser version.
        """
        self.logger.debug("Returning Browser Version.")
        return self.get_browser_version()

    def ge_is_element_loaded(self, locator, locator_type):
        """
        Verifies if the element specified by the locator and type is loaded on the page.

        Args:
            locator (str): The locator for the element (e.g., XPath, CSS selector).
            locator_type (str): The type of locator (e.g., "id", "xpath", "css").

        Returns:
            bool: True if the element is loaded, False otherwise.
        """
        self.logger.debug("Checking if element is loaded.")
        try:
            return self.is_element_present(locator, locator_type)
        except Exception as e:
            self.logger.debug("An error occurred: %s", e, exc_info=True)
            return False
            raise
    
    def ge_is_page_accessibility_compliant(self):
        """
        Checks the web page for accessibility compliance using axe-core.

        Args:
            row: The current row of the test script.
            wafl: Logger instance for logging.
            km: KeywordsManager instance for executing keywords.
        """
        try:
            axe = Axe(self.driver)
            axe.inject()  # Inject axe-core into the page
            results = axe.run()

            # Save the results to a file
            # report_file = 'accessibility_report.json'
            # axe.write_results(results, report_file)
            # self.logger.info(f"Accessibility check completed. Report saved to '{report_file}'.")

            # Check for violations
            page_title = self.get_title()
            violations = results.get('violations', [])
            if violations:
                self.logger.error(f"Accessibility check failed with {len(violations)} violations.")
                all_violations = "\n"
                for violation in violations:
                    self.logger.error(f"Violation: {violation['id']}")
                    all_violations += f"\nViolation: {violation['id']}\n"
                    all_violations += f"Description: {violation['description']}\n"
                    all_violations += f"Impact: {violation['impact']}\n"
                    all_violations += f"Help URL: {violation['helpUrl']}\n"
                    self.logger.error(f"Description: {violation['description']}")
                    self.logger.error(f"Impact: {violation['impact']}")
                    self.logger.error(f"Help URL: {violation['helpUrl']}")
                # raise Exception(f"Accessibility check failed with {len(violations)} violations.")
                self.repo_m.add_report_data(
                        sub_step=f"Check if the page '{page_title}' is accessibility compliant",
                        sub_step_message=f"The element '{page_title}' is NOT accessibility compliant. Below are the violations: {all_violations}",
                        sub_step_status='Fail'
                    )
            else:
                self.logger.info("Accessibility check passed with no violations.")
                self.repo_m.add_report_data(
                        sub_step=f"Check if the page '{page_title}' is accessibility compliant",
                        sub_step_message=f"The element '{page_title}' is accessibility compliant",
                        sub_step_status='Pass'
                    )
        except Exception as e:
            self.logger.error(f"An error occurred during accessibility check: {e}", exc_info=True)
            self.repo_m.add_report_data(
                    sub_step=f"Check if the page '{page_title}' is accessibility compliant",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail'
                )
            raise
            
    
    def ge_drag_and_drop(self, source_locator, source_locator_type, target_locator, target_locator_type, source_element_name, target_element_name):
        """
        Performs a drag-and-drop action from a source element to a target element and logs the result in the PDF report.

        Args:
            source_locator (str): The locator for the source element.
            source_locator_type (str): The type of locator for the source element (e.g., "id", "xpath").
            target_locator (str): The locator for the target element.
            target_locator_type (str): The type of locator for the target element (e.g., "id", "xpath").
            source_element_name (str): The user-friendly name of the source element.
            target_element_name (str): The user-friendly name of the target element.

        Raises:
            Exception: If any error occurs during the drag-and-drop action.
        """
        self.logger.debug(f"Performing drag-and-drop from '{source_element_name}' to '{target_element_name}'.")
        try:
            # Call the drag_and_drop function from driver_functions.py
            self.drag_and_drop(source_locator, source_locator_type, target_locator, target_locator_type)

            # Handle screenshot strategy
            if self.screenshot_strategy == "always":
                self.ge_wait_for_seconds(2)
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Drag and Drop '{source_element_name}' to '{target_element_name}'",
                    sub_step_message="Drag-and-drop action completed successfully",
                    sub_step_status='Pass',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Drag and Drop '{source_element_name}' to '{target_element_name}'",
                    sub_step_message="Drag-and-drop action completed successfully",
                    sub_step_status='Pass'
                )
        except Exception as e:
            self.logger.error(f"An error occurred during drag-and-drop: {e}", exc_info=True)

            # Handle screenshot strategy for errors
            if self.screenshot_strategy in ["always", "onerror"]:
                self.ge_wait_for_seconds(2)
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Drag and Drop '{source_element_name}' to '{target_element_name}'",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Drag and Drop '{source_element_name}' to '{target_element_name}'",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail'
                )
            raise
        
    def ge_mouse_hover(self, locator, locator_type, element_name):
        """
        Performs a mouse hover action on the specified element and logs the result in the PDF report.

        Args:
            locator (str): The locator for the element.
            locator_type (str): The type of locator (e.g., "id", "xpath").
            element_name (str): The user-friendly name of the element.

        Raises:
            Exception: If any error occurs during the mouse hover action.
        """
        self.logger.debug(f"Performing mouse hover on '{element_name}'.")
        try:
            if self.highlight_enabled:
                self.highlight(1, "blue", 2, locator, locator_type)
            # Call the mouse_hover function from driver_functions.py
            self.element_hover(locator, locator_type)

            # Handle screenshot strategy
            if self.screenshot_strategy == "always":
                self.ge_wait_for_seconds(2)
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Mouse Hover on '{element_name}'",
                    sub_step_message="Mouse hover action completed successfully",
                    sub_step_status='Pass',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Mouse Hover on '{element_name}'",
                    sub_step_message="Mouse hover action completed successfully",
                    sub_step_status='Pass'
                )
        except Exception as e:
            self.logger.error(f"An error occurred during mouse hover: {e}", exc_info=True)

            # Handle screenshot strategy for errors
            if self.screenshot_strategy in ["always", "onerror"]:
                self.ge_wait_for_seconds(2)
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Mouse Hover on '{element_name}'",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Mouse Hover on '{element_name}'",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail'
                )
            raise

    def ge_is_element_enabled(self, locator, locator_type, element_name):
        """
        Checks if the specified element is enabled and logs the result in the PDF report.

        Args:
            locator (str): The locator for the element.
            locator_type (str): The type of locator.
            element_name (str): The user-friendly name of the element.

        Raises:
            Exception: If any error occurs while checking element status.
        """
        self.logger.debug("Checking if element is enabled.")
        try:
            if self.highlight_enabled:
                self.highlight(1, "blue", 2, locator, locator_type)
            is_enabled = self.is_element_enabled(locator, locator_type)
            if is_enabled:
                self.logger.debug("Element is enabled.")

                # Handle screenshot strategy
                
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Check if the element '{element_name}' is enabled",
                    sub_step_message=f"The element '{element_name}' is enabled",
                    sub_step_status='Pass',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
                
            else:
                self.logger.debug("Element is NOT enabled.")

                # Handle screenshot strategy
               
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Check if the element '{element_name}' is enabled",
                    sub_step_message=f"The element '{element_name}' is NOT enabled",
                    sub_step_status='Fail',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
                
        except Exception as e:
            self.logger.error("An error occurred: %s", e, exc_info=True)

            # Handle screenshot strategy for errors
            
            self.screenshot_no += 1
            self.repo_m.add_report_data(
                sub_step=f"Check if the element '{element_name}' is enabled",
                sub_step_message=f"Error Occurred: {str(e)}",
                sub_step_status='Fail',
                image_src=self.take_screenshot(
                    f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                ),
                image_alt=self.repo_m.browser_img_alt
            )
            
            raise
    
    def ge_is_chk_radio_element_selected(self, locator, locator_type, element_name):
        """
        Checks if the specified element is enabled and logs the result in the PDF report.

        Args:
            locator (str): The locator for the element.
            locator_type (str): The type of locator.
            element_name (str): The user-friendly name of the element.

        Raises:
            Exception: If any error occurs while checking element status.
        """
        self.logger.debug("Checking if element is selected.")
        try:
            if self.highlight_enabled:
                self.highlight(1, "blue", 2, locator, locator_type)
            is_selected = self.is_chk_radio_element_selected(locator, locator_type)
            if is_selected:
                self.logger.debug("Element is selected.")

                # Handle screenshot strategy
                
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Check if the element '{element_name}' is selected",
                    sub_step_message=f"The element '{element_name}' is selected",
                    sub_step_status='Pass',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
                
            else:
                self.logger.debug("Element is NOT selected.")

                # Handle screenshot strategy
               
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Check if the element '{element_name}' is selected",
                    sub_step_message=f"The element '{element_name}' is NOT selected",
                    sub_step_status='Fail',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
                
        except Exception as e:
            self.logger.error("An error occurred: %s", e, exc_info=True)

            # Handle screenshot strategy for errors
            
            self.screenshot_no += 1
            self.repo_m.add_report_data(
                sub_step=f"Check if the element '{element_name}' is selected",
                sub_step_message=f"Error Occurred: {str(e)}",
                sub_step_status='Fail',
                image_src=self.take_screenshot(
                    f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                ),
                image_alt=self.repo_m.browser_img_alt
            )
            
            raise
    
    def ge_is_chk_radio_element_not_selected(self, locator, locator_type, element_name):
        """
        Checks if the specified element is enabled and logs the result in the PDF report.

        Args:
            locator (str): The locator for the element.
            locator_type (str): The type of locator.
            element_name (str): The user-friendly name of the element.

        Raises:
            Exception: If any error occurs while checking element status.
        """
        self.logger.debug("Checking if element is NOT selected.")
        try:
            if self.highlight_enabled:
                self.highlight(1, "blue", 2, locator, locator_type)
            is_not_selected = not self.is_chk_radio_element_selected(locator, locator_type)
            if is_not_selected:
                self.logger.debug("Element is NOT selected.")

                # Handle screenshot strategy
                
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Check if the element '{element_name}' is NOT selected",
                    sub_step_message=f"The element '{element_name}' is NOT selected",
                    sub_step_status='Pass',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
                
            else:
                self.logger.debug("Element is selected.")

                # Handle screenshot strategy
               
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Check if the element '{element_name}' is NOT selected",
                    sub_step_message=f"The element '{element_name}' is selected",
                    sub_step_status='Fail',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
                
        except Exception as e:
            self.logger.error("An error occurred: %s", e, exc_info=True)

            # Handle screenshot strategy for errors
            
            self.screenshot_no += 1
            self.repo_m.add_report_data(
                sub_step=f"Check if the element '{element_name}' is NOT selected",
                sub_step_message=f"Error Occurred: {str(e)}",
                sub_step_status='Fail',
                image_src=self.take_screenshot(
                    f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                ),
                image_alt=self.repo_m.browser_img_alt
            )
            
            raise

    def ge_is_element_disabled(self, locator, locator_type, element_name):
        """
        Checks if the specified element is disabled and logs the result in the PDF report.

        Args:
            locator (str): The locator for the element.
            locator_type (str): The type of locator.
            element_name (str): The user-friendly name of the element.

        Raises:
            Exception: If any error occurs while checking element status.
        """
        self.logger.debug("Checking if element is disabled.")
        try:
            if self.highlight_enabled:
                self.highlight(1, "blue", 2, locator, locator_type)
            is_disabled = not self.is_element_enabled(locator, locator_type)
            if is_disabled:
                self.logger.debug("Element is disabled.")

                # Handle screenshot strategy
                
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Check if the element '{element_name}' is disabled",
                    sub_step_message=f"The element '{element_name}' is disabled",
                    sub_step_status='Pass',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
               
            else:
                self.logger.debug("Element is NOT disabled.")

                # Handle screenshot strategy
                
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Check if the element '{element_name}' is disabled",
                    sub_step_message=f"The element '{element_name}' is NOT disabled",
                    sub_step_status='Fail',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
                
        except Exception as e:
            self.logger.error("An error occurred: %s", e, exc_info=True)

            # Handle screenshot strategy for errors
            
            self.screenshot_no += 1
            self.repo_m.add_report_data(
                sub_step=f"Check if the element '{element_name}' is disabled",
                sub_step_message=f"Error Occurred: {str(e)}",
                sub_step_status='Fail',
                image_src=self.take_screenshot(
                    f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                ),
                image_alt=self.repo_m.browser_img_alt
            )
        
            raise

    def ge_is_element_displayed(self, locator, locator_type, element_name):
        """
        Checks if the specified element is displayed on the page and logs the result in the PDF report.

        Args:
            locator (str): The locator for the element.
            locator_type (str): The type of locator.
            element_name (str): The user-friendly name of the element.

        Raises:
            Exception: If any error occurs while checking if the element is displayed.
        """
        self.logger.debug("Checking if element is displayed.")
        try:
            is_displayed = self.is_element_present(locator, locator_type)
            if is_displayed:
                self.logger.debug("Element is displayed.")

                # Handle screenshot strategy
                
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Check if the element '{element_name}' is displayed",
                    sub_step_message=f"The element '{element_name}' is displayed",
                    sub_step_status='Pass',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
                
            else:
                self.logger.debug("Element is NOT displayed.")

                # Handle screenshot strategy
               
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Check if the element '{element_name}' is displayed",
                    sub_step_message=f"The element '{element_name}' is NOT displayed",
                    sub_step_status='Fail',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
                
        except Exception as e:
            self.logger.error("An error occurred: %s", e, exc_info=True)

            # Handle screenshot strategy for errors
            
            self.screenshot_no += 1
            self.repo_m.add_report_data(
                sub_step=f"Check if the element '{element_name}' is displayed",
                sub_step_message=f"Error Occurred: {str(e)}",
                sub_step_status='Fail',
                image_src=self.take_screenshot(
                    f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                ),
                image_alt=self.repo_m.browser_img_alt
            )
            
            raise

    def ge_enter_url(self, url):
        """
        Opens the specified URL in the browser and logs the result in the PDF report.

        Args:
            url (str): The URL to open.

        Raises:
            Exception: If any error occurs while trying to open the URL.
        """
        self.logger.debug("Opening URL")
        try:
            self.open_url(url)
            self.page_has_loaded()
            self.wait_for_some_time(2)
            self.logger.debug("Populating the step result details in the PDF report.")

            # Handle screenshot strategy
            if self.screenshot_strategy == "always":
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Enter URL '{url}'",
                    sub_step_message="The URL is entered successfully",
                    sub_step_status='Pass',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Enter URL '{url}'",
                    sub_step_message="The URL is entered successfully",
                    sub_step_status='Pass'
                )
        except Exception as e:
            self.logger.error("An error occurred: %s", e, exc_info=True)
            self.logger.debug("Populating the step result details in the PDF report.")

            # Handle screenshot strategy for errors
            if self.screenshot_strategy in ["always", "on-error"]:
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Enter URL '{url}'",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Enter URL '{url}'",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail'
                )
            raise

    def ge_type(self, locator, locator_type, text_to_type, element_name):
        """
        Types the specified text into the given element and logs the result in the PDF report.

        Args:
            locator (str): The locator for the element.
            locator_type (str): The type of locator.
            text_to_type (str): The text to type into the element.
            element_name (str): The user-friendly name of the element.

        Raises:
            Exception: If any error occurs while typing the text.
        """
        self.logger.debug("Typing text " + text_to_type)
        len_input = len(text_to_type)
        nbr_spaces = self.utils.count_spaces_in_string(text_to_type)
        percent_spaces = self.utils.is_what_percent_of(nbr_spaces, len_input)
        if percent_spaces > 2:
            report_txt_to_type = text_to_type
        else:
            report_txt_to_type = self.utils.make_string_manageable(text_to_type, 25)

        try:
            if self.highlight_enabled:
                self.highlight(1, "blue", 2, locator, locator_type)
            self.element_click(locator, locator_type)
            self.send_keys(text_to_type, locator, locator_type)
            self.wait_for_some_time(1)
            self.logger.debug("Populating the step result details in the PDF report.")

            # Handle screenshot strategy
            if self.screenshot_strategy == "always":
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Type the text '{report_txt_to_type}' in '{element_name}'",
                    sub_step_message="The text should be typed successfully",
                    sub_step_status='Pass',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Type the text '{report_txt_to_type}' in '{element_name}'",
                    sub_step_message="The text should be typed successfully",
                    sub_step_status='Pass'
                )
        except Exception as e:
            self.logger.error("An error occurred: %s", e, exc_info=True)
            self.logger.debug("Populating the step result details in the PDF report.")

            # Handle screenshot strategy for errors
            if self.screenshot_strategy in ["always", "on-error"]:
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Type the text '{report_txt_to_type}' in '{element_name}'",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Type the text '{report_txt_to_type}' in '{element_name}'",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail'
                )
            raise

    def ge_verify_displayed_text(self, locator, locator_type, expected_text, element_name):
        """
        Verifies if the displayed text of the specified element matches the expected text and logs the result in the PDF report.

        Args:
            locator (str): The locator for the element.
            locator_type (str): The type of locator.
            expected_text (str): The text expected to be displayed by the element.
            element_name (str): The user-friendly name of the element.

        Raises:
            Exception: If any error occurs while verifying the displayed text.
        """
        try:
            self.wait_for_element(locator, locator_type)
            if self.highlight_enabled:
                self.highlight(1, "blue", 2, locator, locator_type)
            actual_text = self.get_text(locator, locator_type, element_name)
            is_matched = (actual_text == expected_text)

            # Handle screenshot strategy
            if is_matched:
                self.logger.debug("Populating the step result details in the PDF report.")
                
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Verifying the text '{expected_text}' in '{element_name}'",
                    sub_step_message=f"The text is '{actual_text}'",
                    sub_step_status='Pass',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
                
            else:
                self.logger.debug("Populating the step result details in the PDF report.")
                
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Verifying the text '{expected_text}' in '{element_name}'",
                    sub_step_message=f"The text is '{actual_text}'",
                    sub_step_status='Fail',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
                
        except Exception as e:
            self.logger.error("An error occurred: %s", e, exc_info=True)

            # Handle screenshot strategy for errors
            
            self.screenshot_no += 1
            self.repo_m.add_report_data(
                sub_step=f"Verifying the text '{expected_text}' in '{element_name}'",
                sub_step_message=f"Error Occurred: {str(e)}",
                sub_step_status='Fail',
                image_src=self.take_screenshot(
                    f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                ),
                image_alt=self.repo_m.browser_img_alt
                )
            
            raise

    def ge_click(self, locator, locator_type, element_name):
        """
        Clicks on the specified element and logs the result in the PDF report.

        Args:
            locator (str): The locator for the element.
            locator_type (str): The type of locator.
            element_name (str): The user-friendly name of the element.

        Raises:
            Exception: If any error occurs while performing the click action.
        """
        try:
            self.scroll_into_view(locator, locator_type)
            if self.highlight_enabled:
                self.highlight(1, "blue", 2, locator, locator_type)
            self.element_click(locator, locator_type)
            self.wait_for_some_time(2)
            self.logger.debug("Populating the step result details in the PDF report.")

            # Handle screenshot strategy
            if self.screenshot_strategy == "always":
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Click on the element '{element_name}'",
                    sub_step_message="The click is successful",
                    sub_step_status='Pass',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Click on the element '{element_name}'",
                    sub_step_message="The click is successful",
                    sub_step_status='Pass'
                )
        except Exception as e:
            self.logger.error("An error occurred: %s", e, exc_info=True)
            self.logger.debug("Populating the step result details in the PDF report.")

            # Handle screenshot strategy for errors
            if self.screenshot_strategy in ["always", "on-error"]:
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Click on the element '{element_name}'",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Click on the element '{element_name}'",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail'
                )
            raise

    def ge_select_file(self, locator, locator_type, file_paths):
        """
        Selects a file to upload using the provided locator and file paths, then logs the result in the PDF report.

        Args:
            locator (str): The locator for the file input element.
            locator_type (str): The type of locator (e.g., "id", "xpath", "css").
            file_paths (str): The path(s) to the file(s) to be uploaded.

        Raises:
            Exception: If any error occurs during the file selection process.
        """
        try:
            self.file_name_to_select(file_paths)
            self.wait_for_element(locator, locator_type)
            self.scroll_into_view(locator, locator_type)
            self.logger.debug("Populating the step result details in the PDF report.")

            # Handle screenshot strategy
            if self.screenshot_strategy == "always":
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Upload the file '{file_paths}'",
                    sub_step_message="The file is added successfully",
                    sub_step_status='Pass',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Upload the file '{file_paths}'",
                    sub_step_message="The file is added successfully",
                    sub_step_status='Pass'
                )
        except Exception as e:
            self.logger.error("An error occurred: %s", e, exc_info=True)
            self.logger.debug("Populating the step result details in the PDF report.")

            # Handle screenshot strategy for errors
            if self.screenshot_strategy in ["always", "on-error"]:
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Upload the file '{file_paths}'",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail',
                    image_src=self.take_screenshot(
                        f"{self.screenshot_first_str}_{self.utils.format_number_zeropad_4char(self.screenshot_no)}"
                    ),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Upload the file '{file_paths}'",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail'
                )
            raise

    '''
    The below are the keywords that are specific to MCNP application.
    '''

    def choose_date_from_date_picker(self, **kwargs):
        """
        Selects a date or date range from a date picker, using the provided calendar details.

        Args:
            **kwargs: Arbitrary keyword arguments required for date selection:
                    - "which_calender" (str): Specifies the calendar type (e.g., 'cn_det_dd', 'cn_det_ed').
                    - "date_to_choose" (str): The date or date range to select.
                    - "locator_type" (str): The type of locator for calendar elements.
                    - Other parameters needed for navigation and selection in the date picker.

        Raises:
            Exception: If any error occurs during the date selection process.
        """
        try:
            util_t = Utils()
            which_calender = kwargs.get("which_calender")
            expected_date = kwargs.get("date_to_choose")

            if which_calender == 'cn_det_dd':
                first_date = " ".join(expected_date.split()[0:3])
                first_mon_yr = " ".join(first_date.split()[1:3])
                first_yr = int(first_date.split()[2])
                first_mon = str(first_date.split()[1])
                first_mon_nbr = util_t.get_mtn_number(first_mon)
                first_day = str(first_date.split()[0])

                second_date = " ".join(expected_date.split()[4:7])
                second_mon_yr = " ".join(second_date.split()[1:3])
                second_yr = int(second_date.split()[2])
                second_mon = str(second_date.split()[1])
                second_mon_nbr = util_t.get_mtn_number(second_mon)
                second_day = str(second_date.split()[0])

                # Navigate to the first date
                while True:
                    displayed_month = self.get_text(kwargs.get('cn_det_ddate_mon_txt_xpath'),
                                                    kwargs.get("locator_type"),
                                                    kwargs.get("locator_name"))
                    disp_yr = int(displayed_month.split()[1])
                    disp_mon = str(displayed_month.split()[0])
                    disp_mon_nbr = util_t.get_mtn_number(disp_mon)
                    if displayed_month == first_mon_yr:
                        break
                    if disp_yr > first_yr:
                        self.element_click(kwargs.get('cn_det_ddate_pre_button_xpath'), kwargs.get("locator_type"))
                    elif disp_yr < first_yr:
                        self.element_click(kwargs.get('cn_det_ddate_nxt_button_xpath'), kwargs.get("locator_type"))
                    else:
                        if disp_mon_nbr > first_mon_nbr:
                            self.element_click(kwargs.get('cn_det_ddate_pre_button_xpath'), kwargs.get("locator_type"))
                        else:
                            self.element_click(kwargs.get('cn_det_ddate_nxt_button_xpath'), kwargs.get("locator_type"))

                date_element_list = self.get_element_list(kwargs.get('cn_det_ddate_date_list_xpath'),
                                                        kwargs.get("locator_type"))
                for testscript_file in date_element_list:
                    disp_day = self.get_text("", "", testscript_file)
                    disp_day_two_dig = "%02d" % (int(disp_day),)
                    if disp_day_two_dig == first_day:
                        self.element_click("", "", testscript_file)
                        break

                # Navigate to the second date in the range
                while True:
                    displayed_month = self.get_text(kwargs.get('cn_det_ddate_mon_txt_xpath'),
                                                    kwargs.get("locator_type"),
                                                    kwargs.get("locator_name"))
                    disp_yr = int(displayed_month.split()[1])
                    disp_mon = str(displayed_month.split()[0])
                    disp_mon_nbr = util_t.get_mtn_number(disp_mon)
                    if displayed_month == second_mon_yr:
                        break
                    if disp_yr > second_yr:
                        self.element_click(kwargs.get('cn_det_ddate_pre_button_xpath'), kwargs.get("locator_type"))
                    elif disp_yr < second_yr:
                        self.element_click(kwargs.get('cn_det_ddate_nxt_button_xpath'), kwargs.get("locator_type"))
                    else:
                        if disp_mon_nbr > second_mon_nbr:
                            self.element_click(kwargs.get('cn_det_ddate_pre_button_xpath'), kwargs.get("locator_type"))
                        else:
                            self.element_click(kwargs.get('cn_det_ddate_nxt_button_xpath'), kwargs.get("locator_type"))

                date_element_list = self.get_element_list(kwargs.get('cn_det_ddate_date_list_xpath'),
                                                        kwargs.get("locator_type"))
                for testscript_file in date_element_list:
                    disp_day = self.get_text("", "", testscript_file)
                    disp_day_two_dig = "%02d" % (int(disp_day),)
                    if disp_day_two_dig == second_day:
                        self.element_click("", "", testscript_file)
                        break

            if which_calender == 'cn_det_ed':
                mon_yr = " ".join(expected_date.split()[1:3])
                yr = int(expected_date.split()[2])
                mon = str(expected_date.split()[1])
                mon_nbr = util_t.get_mtn_number(mon)
                day = str(expected_date.split()[0])

                # Navigate to the date
                while True:
                    displayed_month = self.get_text(kwargs.get('cn_det_edate_mon_txt_xpath'),
                                                    kwargs.get("locator_type"),
                                                    kwargs.get("locator_name"))
                    disp_yr = int(displayed_month.split()[1])
                    disp_mon = str(displayed_month.split()[0])
                    disp_mon_nbr = util_t.get_mtn_number(disp_mon)
                    if displayed_month == mon_yr:
                        break
                    if disp_yr > yr:
                        self.element_click(kwargs.get('cn_det_edate_pre_button_xpath'), kwargs.get("locator_type"))
                    elif disp_yr < yr:
                        self.element_click(kwargs.get('cn_det_edate_nxt_button_xpath'), kwargs.get("locator_type"))
                    else:
                        if disp_mon_nbr > mon_nbr:
                            self.element_click(kwargs.get('cn_det_edate_pre_button_xpath'), kwargs.get("locator_type"))
                        else:
                            self.element_click(kwargs.get('cn_det_edate_nxt_button_xpath'), kwargs.get("locator_type"))

                date_element_list = self.get_element_list(kwargs.get('cn_det_edate_date_list_xpath'),
                                                        kwargs.get("locator_type"))
                for testscript_file in date_element_list:
                    disp_day = self.get_text("", "", testscript_file)
                    disp_day_two_dig = "%02d" % (int(disp_day),)
                    if disp_day_two_dig == day:
                        self.element_click("", "", testscript_file)
                        break

            # Handle screenshot strategy
            if self.screenshot_strategy == "always":
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Choosing the date '{expected_date}' in '{kwargs.get('locator_name')}'",
                    sub_step_message="The date is chosen successfully",
                    sub_step_status='Pass',
                    image_src=self.take_screenshot(self.screenshot_first_str + "_" + self.utils.format_number_zeropad_4char(self.screenshot_no)),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Choosing the date '{expected_date}' in '{kwargs.get('locator_name')}'",
                    sub_step_message="The date is chosen successfully",
                    sub_step_status='Pass'
                )
        except Exception as e:
            self.logger.error("An error occurred: %s", e, exc_info=True)

            # Handle screenshot strategy for errors
            if self.screenshot_strategy in ["always", "on-error"]:
                self.screenshot_no += 1
                self.repo_m.add_report_data(
                    sub_step=f"Choosing the date '{expected_date}' in '{kwargs.get('locator_name')}'",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail',
                    image_src=self.take_screenshot(self.screenshot_first_str + "_" + self.utils.format_number_zeropad_4char(self.screenshot_no)),
                    image_alt=self.repo_m.browser_img_alt
                )
            else:
                self.repo_m.add_report_data(
                    sub_step=f"Choosing the date '{expected_date}' in '{kwargs.get('locator_name')}'",
                    sub_step_message=f"Error Occurred: {str(e)}",
                    sub_step_status='Fail'
                )
            raise

    def login_jnj(self, **kwargs):
        """
        Performs the login operation for the application specific.

        This method interacts with the provided UI elements to enter the username and password,
        and handles navigation through the login process. If the password field is detected,
        it proceeds to complete the login process by entering the password and submitting the form.

        Args:
            **kwargs: Arbitrary keyword arguments containing locators, locator types, element names,
                    and user credentials required for the login operation. Expected keys include:
                    - "uname_locator" (str): Locator for the username field.
                    - "locator_type" (str): Type of the locators (e.g., "id", "xpath", "css").
                    - "uname_element_name" (str): User-friendly name for the username field.
                    - "uname_data" (str): Username data to be entered.
                    - "proceed_locator" (str): Locator for the proceed button.
                    - "proceed_element_name" (str): User-friendly name for the proceed button.
                    - "jnjpwd_locator" (str): Locator for the password field.
                    - "jnjpwd_element_name" (str): User-friendly name for the password field.
                    - "pwd_data" (str): Password data to be entered.
                    - "signon_locator" (str): Locator for the sign-on button.
                    - "signon_element_name" (str): User-friendly name for the sign-on button.

        Raises:
            Exception: If any error occurs during the login process.
        """
        self.ge_click(kwargs.get("uname_locator"), kwargs.get(
            "locator_type"), kwargs.get("uname_element_name"))
        self.ge_type(kwargs.get("uname_locator"), kwargs.get("locator_type"), kwargs.get("uname_data"),
                     kwargs.get("uname_element_name"))
        self.ge_click(kwargs.get("proceed_locator"), kwargs.get(
            "locator_type"), kwargs.get("proceed_element_name"))
        start = datetime.now()
        while True:
            end = datetime.now()
            if int((end - start).total_seconds()) >= 5:
                break
            if self.ge_is_element_loaded(kwargs.get("jnjpwd_locator"), kwargs.get("locator_type")):
                self.ge_click(kwargs.get("jnjpwd_locator"), kwargs.get("locator_type"),
                              kwargs.get("jnjpwd_element_name"))
                self.ge_type(kwargs.get("jnjpwd_locator"), kwargs.get("locator_type"), kwargs.get("pwd_data"),
                             kwargs.get("jnjpwd_element_name"))
                self.ge_click(kwargs.get("signon_locator"), kwargs.get("locator_type"),
                              kwargs.get("signon_element_name"))
                break

    def is_not_used(self):
        pass
