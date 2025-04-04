import os
import time
import pyautogui
from logger_config import LoggerConfig
from selenium.common.exceptions import *
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64

from driver_manager import DriverManager
from utilities import Utils

class BrowserDriver(DriverManager):
    """
    A driver manager class for browser automation tasks. Provides methods for
    handling browser interactions such as opening URLs, scrolling elements into view,
    capturing browser version, taking screenshots, and fetching the page title.

    Attributes:
        logger: Logger instance for logging browser-related activities.
    """
    def __init__(self):
        """
        Initialize the BrowserDriver instance, setting up the logger instance.
        """
        super().__init__()
        self.logger = LoggerConfig().logger

    def close_browser(self):
        """
        Close the browser session gracefully.
        Logs the action and quits the browser driver.

        Raises:
            Exception: If any error occurs during the browser quit process.
        """
        self.logger.debug("Closing Browser")
        self.driver.quit()

    def get_browser_version(self):
        """
        Fetch the version of the browser being used.
        Logs the browser version retrieval process.

        Returns:
            str: The version of the browser as a string.
        """
        self.logger.debug("Capturing Browser Version")
        return str(self.driver.capabilities['browserVersion'])

    def open_url(self, url):
        """
        Open a given URL in the browser.
        Logs the URL opening process.

        Args:
            url (str): The URL to be opened in the browser.
        """
        self.logger.debug("Opening URL " + str(url))
        self.driver.get(url)

    def scroll_into_view(self, locator, locator_type, element=None):
        """
        Scroll to the web element identified by the given locator.

        Args:
            locator (str): The locator of the web element.
            locator_type (str): The type of locator (e.g., ID, XPath).
            element (WebElement, optional): Directly passed web element if available.

        Raises:
            Exception: If unable to scroll to the element.
        """
        try:
            if locator:
                element = self.get_element(locator, locator_type)
            self.driver.execute_script("arguments[0].scrollIntoView();", element)
            self.logger.debug("scrolling to element with locator: " + locator + " locator_type: " + locator_type)
        except:
            self.logger.error("cannot send data on the element with locator: " + locator + " locator_type: " + locator_type)
            raise


    def take_screenshot(self):
        """
        Capture a screenshot of the current browser view.
        Adjusts the screenshot method based on execution environment
        (headless mode, Selenium grid, or regular session).

        Returns:
            str: Screenshot data, either as a Base64-encoded string or image file.

        Raises:
            Exception: If any error occurs during screenshot capture.
        """
        utils = Utils()
        if self.is_headless or self.run_in_selenium_grid.lower() == 'yes':
            try:
                return self.take_screenshot_with_base64_watermark()
            except:
                self.logger.error("### Exception Occurred when taking screenshot")
                raise
        else:
            # return utils.take_screenshot_full(file_start)
            return utils.take_screenshot_full_src_tag()


    def take_screenshot_with_base64_watermark(self):
        """
        Capture a screenshot, overlay a date-time watermark inside
        a transparent rectangle, and encode the image into Base64 format.

        Returns:
            str: Base64-encoded string representation of the watermarked screenshot.

        Raises:
            Exception: If any error occurs during screenshot capture or processing.
        """
        try:
            # Capture screenshot as binary data
            screenshot = self.driver.get_screenshot_as_png()
            image = Image.open(BytesIO(screenshot))

            # Add the date-time watermark
            date_time_str = Utils().get_datetime_string()
            draw = ImageDraw.Draw(image)

            # Use the default font provided by Pillow
            font = ImageFont.load_default()

            # Calculate text size using the bounding box
            text_bbox = draw.textbbox((0, 0), date_time_str, font=font)  # Gets the bounding box of the text
            text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

            # Position for watermark (top-right corner)
            width, height = image.size
            padding = 10  # Padding for the rectangle and text
            rect_position = (
                width - text_width - 2 * padding,  # Left
                padding,  # Top
                width - padding,  # Right
                padding + text_height + 2 * padding  # Bottom
            )

            # Create transparent rectangle overlay
            rect_color = (0, 0, 0, 128)  # Black color with 50% opacity (RGBA)
            overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle(rect_position, fill=rect_color)

            # Add watermark text over the rectangle
            text_position = (rect_position[0] + padding, rect_position[1] + padding)
            overlay_draw.text(text_position, date_time_str, font=font, fill=(255, 255, 255, 255))  # White text

            # Combine the original image with the overlay
            image = Image.alpha_composite(image.convert("RGBA"), overlay)

            # Save the image into a BytesIO object
            buffered = BytesIO()
            image.save(buffered, format="PNG")

            # Encode the image into Base64 format
            base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

            # Return the Base64 string
            return f"data:image/png;base64,{base64_image}"

        except Exception as e:
            self.logger.error("### Exception Occurred when taking screenshot")
            raise

    def get_title(self):
        """
        Retrieve the title of the current browser page.
        Logs the process of fetching the title.

        Returns:
            str: The title of the web page as a string.
        """
        self.logger.debug("Getting the page title")
        return self.driver.title

    def get_by_type(self, locator_type):
        """
        Determine the Selenium By type corresponding to a given locator type.

        Args:
            locator_type (str): The type of locator (e.g., "id", "name", "xpath", "css", "class", "link").

        Returns:
            By: A Selenium By object corresponding to the locator type.
            bool: Returns False if the locator type is not supported.

        Raises:
            Exception: If an unsupported locator type is provided, logs a debug message.
        """
        locator_type = locator_type.lower()
        if locator_type == "id":
            return By.ID
        elif locator_type == "name":
            return By.NAME
        elif locator_type == "xpath":
            return By.XPATH
        elif locator_type == "css":
            return By.CSS_SELECTOR
        elif locator_type == "class":
            return By.CLASS_NAME
        elif locator_type == "link":
            return By.LINK_TEXT
        else:
            self.logger.debug("Locator type" + locator_type + "not correct/supported")
        return False

    def dropdown_select_element(self, locator, locator_type="id", selector="", selector_type="value"):
        """
        Select an option from a dropdown element using a selector.

        Args:
            locator (str): The locator for the dropdown element.
            locator_type (str, optional): The type of locator (default: "id").
            selector (str/int): The value, index, or text of the option to select.
            selector_type (str, optional): The type of selector ("value", "index", "text").

        Raises:
            Exception: Logs an error and raises an exception if the element could not be selected.
        """
        try:
            element = self.get_element(locator, locator_type)
            sel = Select(element)
            if selector_type == "value":
                sel.select_by_value(selector)
                time.sleep(1)
            elif selector_type == "index":
                sel.select_by_index(selector)
                time.sleep(1)
            elif selector_type == "text":
                sel.select_by_visible_text(selector)
                time.sleep(1)
            self.logger.debug("Element selected with selector: " + str(selector) +" and selectorType: " + selector_type)

        except:
            self.logger.error("Element not selected with selector: " + str(selector) + " and selectorType: " + selector_type)
            raise

    def get_dropdown_options_count(self, locator, locator_type="id"):
        """
        Get the number of options available in a dropdown element.

        Args:
            locator (str): The locator for the dropdown element.
            locator_type (str, optional): The type of locator (default: "id").

        Returns:
            list: A list of options in the dropdown element.

        Raises:
            Exception: Logs an error and raises an exception if the dropdown element could not be found.
        """
        options = None
        try:
            element = self.get_element(locator, locator_type)
            sel = Select(element)
            options = sel.options
            self.logger.debug("Element found with locator: " + locator + " and locator_type: " + locator_type)
        except:
            self.logger.error("Element not found with locator: " + locator + " and locator_type: " + locator_type)
            raise

        return options

    def get_dropdown_selected_option_text(self, locator, locator_type="id"):
        """
        Get the text of the currently selected option in a dropdown element.

        Args:
            locator (str): The locator for the dropdown element.
            locator_type (str, optional): The type of locator (default: "id").

        Returns:
            str: The text of the selected option.

        Raises:
            Exception: Logs an error and raises an exception if the selected option could not be retrieved.
        """
        selected_option_text = None
        try:
            element = self.get_element(locator, locator_type)
            sel = Select(element)
            selected_option_text = sel.first_selected_option.text
            self.logger.debug("Return the selected option of drop down list with locator: " + locator + " and locator_type: " + locator_type)
        except:
            self.logger.error("Can not return the selected option of drop down list with locator: " + locator + " and locator_type: " + locator_type)
            raise

        return selected_option_text

    def get_dropdown_selected_option_value(self, locator, locator_type="id"):
        """
        Get the value of the currently selected option in a dropdown element.

        Args:
            locator (str): The locator for the dropdown element.
            locator_type (str, optional): The type of locator (default: "id").

        Returns:
            str: The value of the selected option.

        Raises:
            Exception: Logs an error and raises an exception if the selected option value could not be retrieved.
        """
        selected_option_value = None
        try:
            element = self.get_element(locator, locator_type)
            sel = Select(element)
            selected_option_value = sel.first_selected_option.get_attribute("value")
            self.logger.debug("Return the selected option of drop down list with locator: " + locator + " and locator_type: " + locator_type)
        except:
            self.logger.error("Can not return the selected option of drop down list with locator: " + locator + " and locator_type: " + locator_type)
            raise

        return selected_option_value

    def get_element(self, locator, locator_type="id"):
        """
        Retrieve a web element based on the given locator and locator type.

        Args:
            locator (str): The locator of the web element.
            locator_type (str, optional): The type of locator (default: "id").

        Returns:
            WebElement: The located web element.

        Raises:
            Exception: Logs an error and raises an exception if the element could not be found.
        """
        element = None
        try:
            locator_type = locator_type.lower()
            by_type = self.get_by_type(locator_type)
            element = self.driver.find_element(by_type, locator)
            self.logger.debug("Element found with locator: " + locator + " and locator_type: " + locator_type)
        except:
            self.logger.error("Element not found with locator: " + locator + " and locator_type: " + locator_type)
            raise
        return element

    def is_element_selected(self, locator, locator_type):
        """
        Check whether a web element is selected.

        Args:
            locator (str): The locator of the web element.
            locator_type (str): The type of locator.

        Returns:
            bool: True if the element is selected, False otherwise.

        Raises:
            Exception: Logs an error and raises an exception if the element could not be found.
        """
        is_selected = None
        try:
            element = self.get_element(locator, locator_type)
            is_selected = element.is_selected()
            self.logger.debug("Element found with locator: " + locator +
                         " and locator_type: " + locator_type)
        except:
            self.logger.error("Element not found with locator: " + locator + " and locator_type: " + locator_type)
            raise

        return is_selected

    def get_element_list(self, locator, locator_type="id"):
        """
        Retrieve a list of web elements based on the given locator and locator type.

        Args:
            locator (str): The locator of the web elements.
            locator_type (str, optional): The type of locator (default: "id").

        Returns:
            list: A list of located web elements.

        Raises:
            Exception: Logs an error and raises an exception if the elements could not be found.
        """
        element = None
        try:
            locator_type = locator_type.lower()
            by_type = self.get_by_type(locator_type)
            element = self.driver.find_elements(by_type, locator)
            self.logger.debug("Element list found with locator: " + locator + " and locator_type: " + locator_type)
        except:
            self.logger.error("Element list not found with locator: " + locator + " and locator_type: " + locator_type)
            raise

        return element

    def element_click(self, locator="", locator_type="id", element=None):
        """
        Click on a web element.
        Either provide a pre-located element or specify a combination of locator and locator_type.

        Args:
            locator (str, optional): The locator for the web element (default: "").
            locator_type (str, optional): The type of locator (e.g., "id", "xpath", default: "id").
            element (WebElement, optional): A pre-located web element (default: None).

        Raises:
            Exception: Logs an error and raises an exception if the click action fails.
        """
        try:
            if locator:
                element = self.get_element(locator, locator_type)
            element.click()
            self.logger.debug("clicked on element with locator: " + locator + " locator_type: " + locator_type)
        except:
            self.logger.error("cannot click on the element with locator: " + locator + " locator_type: " + locator_type)
            raise

    def element_hover(self, locator="", locator_type="id", element=None):
        """
        Hover over a web element.
        Either provide a pre-located element or specify a combination of locator and locator_type.

        Args:
            locator (str, optional): The locator for the web element (default: "").
            locator_type (str, optional): The type of locator (e.g., "id", "xpath", default: "id").
            element (WebElement, optional): A pre-located web element (default: None).

        Raises:
            Exception: Logs an error and raises an exception if the hover action fails.
        """
        try:
            if locator:
                element = self.get_element(locator, locator_type)
            hover = ActionChains(self.driver).move_to_element(element)
            hover.perform()
            time.sleep(2)
            self.logger.debug("hover to element with locator: " + locator + " locator_type: " + locator_type)
        except:
            self.logger.error("cannot hover to the element with locator: " + locator + " locator_type: " + locator_type)
            raise

    def send_keys(self, data, locator="", locator_type="id", element=None):
        """
        Send keys to a web element.
        Either provide a pre-located element or specify a combination of locator and locator_type.

        Args:
            data (str): The text to send to the element.
            locator (str, optional): The locator for the web element (default: "").
            locator_type (str, optional): The type of locator (e.g., "id", "xpath", default: "id").
            element (WebElement, optional): A pre-located web element (default: None).

        Raises:
            Exception: Logs an error and raises an exception if the send keys action fails.
        """
        try:
            if locator:
                element = self.get_element(locator, locator_type)
            element.send_keys(data)
            self.logger.debug("send data on element with locator: " + locator + " locator_type: " + locator_type)
        except:
            self.logger.error("cannot send data on the element with locator: " + locator + " locator_type: " + locator_type)
            raise

    def clear_keys(self, locator="", locator_type="id", element=None):
        """
        Clear the text in a web element.
        Either provide a pre-located element or specify a combination of locator and locator_type.

        Args:
            locator (str, optional): The locator for the web element (default: "").
            locator_type (str, optional): The type of locator (e.g., "id", "xpath", default: "id").
            element (WebElement, optional): A pre-located web element (default: None).

        Raises:
            Exception: Logs an error and raises an exception if the clear action fails.
        """
        try:
            if locator:
                element = self.get_element(locator, locator_type)
            element.clear()
            self.logger.debug("Clear data of element with locator: " + locator + " locator_type: " + locator_type)
        except:
            self.logger.error("cannot clear data of the element with locator: " + locator + " locator_type: " + locator_type)
            raise Exception("cannot send data on the element with locator: " + locator +  " locator_type: " + locator_type)

    def get_text(self, locator="", locator_type="id", element=None, info=""):
        """
        Retrieve the text of a web element.
        Either provide a pre-located element or specify a combination of locator and locator_type.

        Args:
            locator (str, optional): The locator for the web element (default: "").
            locator_type (str, optional): The type of locator (e.g., "id", "xpath", default: "id").
            element (WebElement, optional): A pre-located web element (default: None).
            info (str, optional): Additional context about the element (default: "").

        Returns:
            str: The retrieved text of the web element.

        Raises:
            Exception: Logs an error and raises an exception if the text retrieval fails.
        """
        try:
            if locator:
                self.logger.debug("In locator condition")
                element = self.get_element(locator, locator_type)
            self.logger.debug("Before finding text")
            text = element.text
            self.logger.debug("After finding element, size is: " + str(len(text)))
            if len(text) == 0:
                text = element.get_attribute("innerText")
            if len(text) != 0:
                self.logger.debug("Getting text on element :: " + info)
                self.logger.debug("The text is :: '" + text + "'")
                text = text.strip()
        except:
            self.logger.error("Failed to get text on element " + info)
            text = None
            raise
        return text

    def is_element_present(self, locator="", locator_type="id", element=None):
        """
        Check if a web element is present.
        Either provide a pre-located element or specify a combination of locator and locator_type.

        Args:
            locator (str, optional): The locator for the web element (default: "").
            locator_type (str, optional): The type of locator (e.g., "id", "xpath", default: "id").
            element (WebElement, optional): A pre-located web element (default: None).

        Returns:
            bool: True if the element is present, False otherwise.

        Raises:
            Exception: Logs an error and raises an exception if the presence check fails.
        """
        try:
            if locator:
                element = self.get_element(locator, locator_type)
            if element is not None:
                self.logger.debug("Element found with locator: " + locator + " and locator_type: " + locator_type)
                return True
            else:
                self.logger.error("Element not found with locator: " + locator + " and locator_type: " + locator_type)
                return False
        except:
            self.logger.error("Element not found with locator: " + locator + " and locator_type: " + locator_type)
            return False

    def apply_style(self, s, element):
        """
        Apply a specific style to a web element using JavaScript.

        Args:
            s (str): The CSS style to apply to the web element.
            element (WebElement): The web element to which the style will be applied.
        """
        self.driver.execute_script("arguments[0].setAttribute('style', arguments[1]);", element, s)

    def highlight(self, effect_time, color, border, locator="", locator_type="id", element=None, ):
        """
        Highlight (blink) a web element by temporarily changing its border color.

        Args:
            effect_time (int): Duration for which the highlighting effect should last (in seconds).
            color (str): The color of the border for the highlight effect.
            border (int): The width of the border for the highlight effect.
            locator (str, optional): The locator for the web element (default: "").
            locator_type (str, optional): The type of locator (e.g., "id", "xpath", default: "id").
            element (WebElement, optional): A pre-located web element (default: None).

        Raises:
            Exception: Logs an error and raises an exception if the highlight action fails.
        """
        try:
            if locator:
                self.logger.debug("In locator condition")
                element = self.get_element(locator, locator_type)
            # driver = element._parent

            original_style = element.get_attribute('style')
            self.apply_style("border: {0}px solid {1};".format(border, color), element)
            time.sleep(effect_time)
            self.apply_style(original_style, element)
        except:
            self.logger.error("Cannot highlight element with locator: " + locator + " and locator_type: " + locator_type)

    def is_element_displayed(self, locator="", locator_type="id", element=None):
        """
        Check if a web element is displayed.
        Either provide a pre-located element or specify a combination of locator and locator_type.

        Args:
            locator (str, optional): The locator for the web element (default: "").
            locator_type (str, optional): The type of locator (e.g., "id", "xpath", default: "id").
            element (WebElement, optional): A pre-located web element (default: None).

        Returns:
            bool: True if the element is displayed, False otherwise.

        Raises:
            Exception: Logs an error and raises an exception if the display check fails.
        """
        is_displayed = False
        try:
            if locator:
                element = self.get_element(locator, locator_type)
            if element is not None:
                is_displayed = element.is_displayed()
                self.logger.debug("Element is displayed with locator: " + locator + " and locator_type: " + locator_type)
            else:
                self.logger.error("Element is not displayed with locator: " + locator + " and locator_type: " + locator_type)
            return is_displayed
        except:
            self.logger.error("Element is not displayed with locator: " + locator + " and locator_type: " + locator_type)
            return False

    def is_element_enabled(self, locator="", locator_type="id", element=None):
        """
        Check if a web element is enabled.
        Either provide a pre-located element or specify a combination of locator and locator_type.

        Args:
            locator (str, optional): The locator for the web element (default: "").
            locator_type (str, optional): The type of locator (e.g., "id", "xpath", default: "id").
            element (WebElement, optional): A pre-located web element (default: None).

        Returns:
            bool: True if the element is enabled, False otherwise.

        Raises:
            Exception: Logs an error and raises an exception if the enable check fails.
        """
        is_enabled = False
        try:
            if locator:
                element = self.get_element(locator, locator_type)
            if element is not None:
                is_enabled = element.is_enabled()
                if is_enabled:
                    self.logger.debug("Element is with locator: " + locator + " and locator_type: " + locator_type + " is enabled")
                else:
                    self.logger.debug("Element is with locator: " + locator + " and locator_type: " + locator_type + " is disabled")
            else:
                self.logger.error("Element is not displayed with locator: " + locator + " and locator_type: " + locator_type)
            return is_enabled
        except:
            self.logger.error("Element is not displayed with locator: " + locator + " and locator_type: " + locator_type)
            return False

    def element_presence_check(self, locator="", locator_type="id"):
        """
        Check if a web element is present on the web page.

        Args:
            locator (str, optional): The locator for the web element (default: "").
            locator_type (str, optional): The type of locator (e.g., "id", "xpath", default: "id").

        Returns:
            bool: True if the element is present, False otherwise.

        Raises:
            Exception: Logs an error and raises an exception if the presence check fails.
        """
        try:
            locator_type = locator_type.lower()
            by_type = self.get_by_type(locator_type)
            element_list = self.driver.find_elements(by_type, locator)
            if len(element_list) > 0:
                self.logger.debug("Element Found")
                return True
            else:
                self.logger.debug("Element not found")
                return False
        except:
            self.logger.debug("Element not found")
            return False

    def wait_for_element(self, locator, locator_type='id', timeout=10, pollFrequency=0.5):
        """
        Wait for a web element to be clickable within a specified timeout.

        Args:
            locator (str): The locator for the web element.
            locator_type (str, optional): The type of locator (e.g., "id", "xpath", default: "id").
            timeout (int, optional): Maximum wait time in seconds (default: 10).
            pollFrequency (float, optional): Frequency of polling for the element in seconds (default: 0.5).

        Returns:
            WebElement: The located clickable web element.

        Raises:
            Exception: Logs an error and raises an exception if the element does not appear within the timeout.
        """
        element = None
        try:
            self.logger.debug("Waiting for maximum :: " + str(timeout) + " :: seconds for element to be clickable")

            wait = WebDriverWait(self.driver, timeout, poll_frequency=pollFrequency, ignored_exceptions=[NoSuchElementException, ElementNotVisibleException, ElementNotSelectableException])
            by_type = self.get_by_type(locator_type)
            element = wait.until(ec.element_to_be_clickable((by_type, locator)))

            self.logger.debug("Element appeared on the web page")

        except:
            self.logger.debug("Element not appeared on the web page")
            raise

        return element

    def web_scroll(self, direction="up"):
        """
        Scrolls the webpage in the specified direction.

        :param direction: The direction to scroll. Use "up" to scroll upwards and "down" to scroll downwards. Defaults to "up".
        """
        if direction == "up":
            # Scroll Up
            self.driver.execute_script("window.scrollBy(0, -1000);")
        if direction == "down":
            # Scroll Down
            self.driver.execute_script("window.scrollBy(0, 1000);")

    def get_url(self):
        """
        Retrieves the current URL of the webpage.

        :return: A string representing the current URL of the webpage.
        """
        current_url = self.driver.current_url

        return current_url

    def page_back(self):
        """
        Navigates the browser to the previous page in the browser's history.
        """
        self.driver.execute_script("window.history.go(-1)")

    def get_attribute_value(self, locator="", locator_type="id", element=None, attribute=""):
        """
        Retrieves the value of a specified attribute from a web element.

        :param locator: The locator of the web element (optional).
        :param locator_type: The type of the locator (e.g., "id", "xpath"). Defaults to "id".
        :param element: The web element whose attribute value needs to be fetched (optional).
        :param attribute: The name of the attribute whose value needs to be fetched.
        :return: The value of the specified attribute, or None if it fails to retrieve the attribute value.
        :raises: Exception if the attribute value cannot be retrieved.
        """
        try:
            if locator:
                self.logger.debug("In locator condition")
                element = self.get_element(locator, locator_type)
            attribute_value = element.get_attribute(attribute)
        except:
            self.logger.error("Failed to get " + attribute + " in element with locator: " + locator + " and locator_type: " + locator_type)
            attribute_value = None
            raise
        return attribute_value

    def refresh(self):
        """
        Refreshes the current webpage.
        """
        self.driver.get(self.driver.current_url)

    def page_has_loaded(self):
        """
        Checks if the page has fully loaded by evaluating various conditions,
        including the document state, jQuery activity, and Angular HTTP requests.

        :return: True if the page has fully loaded; otherwise, False.
        """
        try:
            WebDriverWait(self.driver, 1000, poll_frequency=0.5).until(lambda driver: self.driver.execute_script('return document.readyState == "complete";'))
            WebDriverWait(self.driver, 1000, poll_frequency=0.5).until(lambda driver: self.driver.execute_script('return jQuery.active == 0'))
            WebDriverWait(self.driver, 1000, poll_frequency=0.5).until(lambda driver: self.driver.execute_script('return typeof jQuery != "undefined"'))
            WebDriverWait(self.driver, 1000, poll_frequency=0.5).until(lambda driver: self.driver.execute_script('return angular.element(document).injector().get("$http").pendingRequests.length === 0'))
        except:
            return False

    def wait_for_some_time(self, sec_to_wait):
        """
        Pauses the execution for a specified number of seconds.

        :param sec_to_wait: The number of seconds to wait.
        """
        self.is_not_used()
        time.sleep(int(sec_to_wait))

    def file_name_to_select(self, file_name):
        """
        Simulates selecting a file using its name through keyboard automation.

        :param file_name: The name of the file to select.
        """
        pyautogui.write(file_name)
        pyautogui.press('tab')
        pyautogui.press('enter')

    def is_not_used(self):
        pass
