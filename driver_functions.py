import os
import time
from traceback import print_stack

import pyautogui
from selenium.common.exceptions import *
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
import logging

from driver_manager import DriverManager
from utilities import Utils

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.WARN)


class BrowserDriver(DriverManager):

    def __init__(self):
        super().__init__()

    def close_browser(self):
        self.driver.quit()

    def get_browser_version(self):
        return str(self.driver.capabilities['browserVersion'])

    def open_url(self, url):
        self.driver.get(url)

    def scroll_into_view(self, locator, locator_type, element=None):
        try:
            if locator:
                element = self.get_element(locator, locator_type)
            self.driver.execute_script("arguments[0].scrollIntoView();", element)
            logging.info("scrolling to element with locator: " + locator +
                         " locator_type: " + locator_type)
        except:
            logging.error("cannot send data on the element with locator: " + locator +
                          " locator_type: " + locator_type)
            print_stack()
            raise Exception("cannot send data on the element with locator: " + locator +
                            " locator_type: " + locator_type)

    # def take_screenshot(self, result_message):
    #     """
    #     Take a screenshot of the current open web page
    #     """
    #     file_name = result_message + "." + str(round(time.time() * 1000)) + ".png"
    #     if len(file_name) >= 200:
    #         file_name = str(round(time.time() * 1000)) + ".png"
    #     screenshot_directory = "../screenshots/"
    #     relative_file_name = screenshot_directory + file_name
    #     current_directory = os.path.dirname(__file__)
    #     destination_file = os.path.join(current_directory, relative_file_name)
    #     destination_directory = os.path.join(current_directory, screenshot_directory)
    #
    #     try:
    #         if not os.path.exists(destination_directory):
    #             os.makedirs(destination_directory)
    #         self.driver.save_screenshot(destination_file)
    #         logging.info("Screenshot save to directory: " + destination_file)
    #     except:
    #         logging.error("### Exception Occurred when taking screenshot")
    #         print_stack()
    #         raise Exception("cannot send data on the element with locator: "
    #                         " locator_type: ")
    def take_screenshot(self, file_start):
        """
        Take a screenshot of the current open web page
        """
        utils = Utils()
        if self.run_in_selenium_grid.lower() == 'yes':
            try:
                date_time_str = utils.get_datetime_string()
                image_name = file_start + "_" + date_time_str
                full_img_path = utils.images_folder + "\\" + image_name + ".png"
                self.driver.save_screenshot(full_img_path)
                logging.info("Screenshot save to directory: " + full_img_path)
                utils.add_date_time_watermark_to_image(full_img_path, date_time_str)
                return full_img_path
            except:
                logging.error("### Exception Occurred when taking screenshot")
                print_stack()
                raise Exception("Exception Occurred when taking screenshot")
        else:
            return utils.take_screenshot_full(file_start)

    def get_title(self):
        return self.driver.title

    def get_by_type(self, locator_type):
        self.is_not_used()
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
            logging.info("Locator type" + locator_type + "not correct/supported")
        return False

    def dropdown_select_element(self, locator, locator_type="id", selector="", selector_type="value"):
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
            logging.info("Element selected with selector: " + str(selector) +
                         " and selectorType: " + selector_type)

        except:
            logging.error("Element not selected with selector: " + str(selector) +
                          " and selectorType: " + selector_type)
            print_stack()
            raise Exception("cannot send data on the element with locator: " + locator +
                            " locator_type: " + locator_type)

    def get_dropdown_options_count(self, locator, locator_type="id"):
        """
        get the number of options of drop down list
        :return: number of Options of drop down list
        """
        options = None
        try:
            element = self.get_element(locator, locator_type)
            sel = Select(element)
            options = sel.options
            logging.info("Element found with locator: " + locator +
                         " and locator_type: " + locator_type)
        except:
            logging.error("Element not found with locator: " + locator +
                          " and locator_type: " + locator_type)
            raise Exception("cannot send data on the element with locator: " + locator +
                            " locator_type: " + locator_type)

        return options

    def get_dropdown_selected_option_text(self, locator, locator_type="id"):
        """
        get the text of selected option in drop down list
        :return: the text of selected option in drop down list
        """
        selected_option_text = None
        try:
            element = self.get_element(locator, locator_type)
            sel = Select(element)
            selected_option_text = sel.first_selected_option.text
            logging.info("Return the selected option of drop down list with locator: " + locator +
                         " and locator_type: " + locator_type)
        except:
            logging.error("Can not return the selected option of drop down list with locator: " + locator +
                          " and locator_type: " + locator_type)
            raise Exception("cannot send data on the element with locator: " + locator +
                            " locator_type: " + locator_type)

        return selected_option_text

    def get_dropdown_selected_option_value(self, locator, locator_type="id"):
        """
        get the value of selected option in drop down list
        :return: the value of selected option in drop down list
        """
        selected_option_value = None
        try:
            element = self.get_element(locator, locator_type)
            sel = Select(element)
            selected_option_value = sel.first_selected_option.get_attribute("value")
            logging.info("Return the selected option of drop down list with locator: " + locator +
                         " and locator_type: " + locator_type)
        except:
            logging.error("Can not return the selected option of drop down list with locator: " + locator +
                          " and locator_type: " + locator_type)
            raise Exception("cannot send data on the element with locator: " + locator +
                            " locator_type: " + locator_type)

        return selected_option_value

    def get_element(self, locator, locator_type="id"):
        element = None
        try:
            locator_type = locator_type.lower()
            by_type = self.get_by_type(locator_type)
            element = self.driver.find_element(by_type, locator)
            logging.info("Element found with locator: " + locator +
                         " and locator_type: " + locator_type)
        except:
            logging.error("Element not found with locator: " + locator +
                          " and locator_type: " + locator_type)
            raise Exception("cannot send data on the element with locator: " + locator +
                            " locator_type: " + locator_type)
        return element

    def is_element_selected(self, locator, locator_type):
        is_selected = None
        try:
            element = self.get_element(locator, locator_type)
            is_selected = element.is_selected()
            logging.info("Element found with locator: " + locator +
                         " and locator_type: " + locator_type)
        except:
            logging.error("Element not found with locator: " + locator +
                          " and locator_type: " + locator_type)
            raise Exception("cannot send data on the element with locator: " + locator +
                            " locator_type: " + locator_type)

        return is_selected

    def get_element_list(self, locator, locator_type="id"):
        """
        Get list of elements
        """
        element = None
        try:
            locator_type = locator_type.lower()
            by_type = self.get_by_type(locator_type)
            element = self.driver.find_elements(by_type, locator)
            logging.info("Element list found with locator: " + locator +
                         " and locator_type: " + locator_type)
        except:
            logging.error("Element list not found with locator: " + locator +
                          " and locator_type: " + locator_type)
            raise Exception("cannot send data on the element with locator: " + locator +
                            " locator_type: " + locator_type)

        return element

    def element_click(self, locator="", locator_type="id", element=None):
        """
        Either provide element or a combination of locator and locator_type
        """

        try:
            if locator:
                element = self.get_element(locator, locator_type)
            element.click()
            logging.info("clicked on element with locator: " + locator +
                         " locator_type: " + locator_type)
        except:
            logging.error("cannot click on the element with locator: " + locator +
                          " locator_type: " + locator_type)
            print_stack()
            raise Exception("cannot send data on the element with locator: " + locator +
                            " locator_type: " + locator_type)

    def element_hover(self, locator="", locator_type="id", element=None):
        """
        Either provide element or a combination of locator and locator_type
        """

        try:
            if locator:
                element = self.get_element(locator, locator_type)
            hover = ActionChains(self.driver).move_to_element(element)
            hover.perform()
            time.sleep(2)
            logging.info("hover to element with locator: " + locator +
                         " locator_type: " + locator_type)
        except:
            logging.error("cannot hover to the element with locator: " + locator +
                          " locator_type: " + locator_type)
            print_stack()
            raise Exception("cannot send data on the element with locator: " + locator +
                            " locator_type: " + locator_type)

    def send_keys(self, data, locator="", locator_type="id", element=None):
        """
        Send keys to an element
        Either provide element or a combination of locator and locator_type
        """
        try:
            if locator:
                element = self.get_element(locator, locator_type)
            element.send_keys(data)
            logging.info("send data on element with locator: " + locator +
                         " locator_type: " + locator_type)
        except:
            logging.error("cannot send data on the element with locator: " + locator +
                          " locator_type: " + locator_type)
            raise Exception("cannot send data on the element with locator: " + locator +
                            " locator_type: " + locator_type)

    def clear_keys(self, locator="", locator_type="id", element=None):
        """
        Clear keys of an element
        Either provide element or a combination of locator and locator_type
        """
        try:
            if locator:
                element = self.get_element(locator, locator_type)
            element.clear()
            logging.info("Clear data of element with locator: " + locator +
                         " locator_type: " + locator_type)
        except:
            logging.error("cannot clear data of the element with locator: " + locator +
                          " locator_type: " + locator_type)
            print_stack()
            raise Exception("cannot send data on the element with locator: " + locator +
                            " locator_type: " + locator_type)

    def get_text(self, locator="", locator_type="id", element=None, info=""):
        """
        Get 'Text' on an element
        Either provide element or a combination of locator and locator_type
        """
        try:
            if locator:
                logging.debug("In locator condition")
                element = self.get_element(locator, locator_type)
            logging.debug("Before finding text")
            text = element.text
            logging.debug("After finding element, size is: " + str(len(text)))
            if len(text) == 0:
                text = element.get_attribute("innerText")
            if len(text) != 0:
                logging.info("Getting text on element :: " + info)
                logging.info("The text is :: '" + text + "'")
                text = text.strip()
        except:
            logging.error("Failed to get text on element " + info)
            print_stack()
            text = None
            raise Exception("cannot send data on the element with locator: " + locator +
                            " locator_type: " + locator_type)
        return text

    def is_element_present(self, locator="", locator_type="id", element=None):
        """
        Check if element is present
        Either provide element or a combination of locator and locator_type
        """
        try:
            if locator:
                element = self.get_element(locator, locator_type)
            if element is not None:
                logging.info("Element found with locator: " + locator +
                             " and locator_type: " + locator_type)
                return True
            else:
                logging.error("Element not found with locator: " + locator +
                              " and locator_type: " + locator_type)
                return False
        except:
            logging.error("Element not found with locator: " + locator +
                          " and locator_type: " + locator_type)
            return False

    def apply_style(self, s, element):
        self.driver.execute_script("arguments[0].setAttribute('style', arguments[1]);",
                                   element, s)

    def highlight(self, effect_time, color, border, locator="", locator_type="id", element=None, ):
        """Highlights (blinks) a Selenium Webdriver element"""
        try:
            if locator:
                logging.debug("In locator condition")
                element = self.get_element(locator, locator_type)
            # driver = element._parent

            original_style = element.get_attribute('style')
            self.apply_style("border: {0}px solid {1};".format(border, color), element)
            time.sleep(effect_time)
            self.apply_style(original_style, element)
        except:
            logging.error("Cannot highlight element with locator: " + locator +
                          " and locator_type: " + locator_type)

    def is_element_displayed(self, locator="", locator_type="id", element=None):
        """
        Check if element is displayed
        Either provide element or a combination of locator and locator_type
        """
        is_displayed = False
        try:
            if locator:
                element = self.get_element(locator, locator_type)
            if element is not None:
                is_displayed = element.is_displayed()
                logging.info("Element is displayed with locator: " + locator +
                             " and locator_type: " + locator_type)
            else:
                logging.error("Element is not displayed with locator: " + locator +
                              " and locator_type: " + locator_type)
            return is_displayed
        except:
            logging.error("Element is not displayed with locator: " + locator +
                          " and locator_type: " + locator_type)
            return False

    def is_element_enabled(self, locator="", locator_type="id", element=None):
        """
        Check if element is displayed
        Either provide element or a combination of locator and locator_type
        """
        is_enabled = False
        try:
            if locator:
                element = self.get_element(locator, locator_type)
            if element is not None:
                is_enabled = element.is_enabled()
                if is_enabled:
                    logging.info("Element is with locator: " + locator +
                                 " and locator_type: " + locator_type + " is enabled")
                else:
                    logging.info("Element is with locator: " + locator +
                                 " and locator_type: " + locator_type + " is disabled")
            else:
                logging.error("Element is not displayed with locator: " + locator +
                              " and locator_type: " + locator_type)
            return is_enabled
        except:
            logging.error("Element is not displayed with locator: " + locator +
                          " and locator_type: " + locator_type)
            return False

    def element_presence_check(self, locator="", locator_type="id"):
        try:
            locator_type = locator_type.lower()
            by_type = self.get_by_type(locator_type)
            element_list = self.driver.find_elements(by_type, locator)
            if len(element_list) > 0:
                logging.info("Element Found")
                return True
            else:
                logging.info("Element not found")
                return False
        except:
            logging.info("Element not found")
            return False

    def wait_for_element(self, locator, locator_type='id', timeout=10, pollFrequency=0.5):
        element = None
        try:
            logging.info("Waiting for maximum :: " + str(timeout) + " :: seconds for element to be clickable")

            wait = WebDriverWait(self.driver, timeout, poll_frequency=pollFrequency,
                                 ignored_exceptions=[NoSuchElementException,
                                                     ElementNotVisibleException,
                                                     ElementNotSelectableException])
            by_type = self.get_by_type(locator_type)
            element = wait.until(ec.element_to_be_clickable((by_type, locator)))

            logging.info("Element appeared on the web page")

        except:
            logging.info("Element not appeared on the web page")
            print_stack()
            raise Exception("cannot send data on the element with locator: " + locator +
                            " locator_type: " + locator_type)

        return element

    def web_scroll(self, direction="up"):
        if direction == "up":
            # Scroll Up
            self.driver.execute_script("window.scrollBy(0, -1000);")
        if direction == "down":
            # Scroll Down
            self.driver.execute_script("window.scrollBy(0, 1000);")

    def get_url(self):
        """
        Get the current URL        :return:
        """
        current_url = self.driver.current_url

        return current_url

    def page_back(self):
        """
        page back the browser
        """
        self.driver.execute_script("window.history.go(-1)")

    def get_attribute_value(self, locator="", locator_type="id", element=None, attribute=""):
        """
        get attribute value
        """
        try:
            if locator:
                logging.debug("In locator condition")
                element = self.get_element(locator, locator_type)
            attribute_value = element.get_attribute(attribute)
        except:
            logging.error("Failed to get " + attribute + " in element with locator: " +
                          locator + " and locator_type: " + locator_type)
            print_stack()
            attribute_value = None
            raise Exception("cannot send data on the element with locator: " + locator +
                            " locator_type: " + locator_type)
        return attribute_value

    def refresh(self):
        self.driver.get(self.driver.current_url)

    def page_has_loaded(self):
        try:
            WebDriverWait(self.driver, 1000, poll_frequency=0.5).until(
                lambda driver: self.driver.execute_script('return document.readyState == "complete";'))
            WebDriverWait(self.driver, 1000, poll_frequency=0.5).until(
                lambda driver: self.driver.execute_script('return jQuery.active == 0'))
            WebDriverWait(self.driver, 1000, poll_frequency=0.5).until(
                lambda driver: self.driver.execute_script('return typeof jQuery != "undefined"'))
            WebDriverWait(self.driver, 1000, poll_frequency=0.5).until(lambda driver: self.driver.execute_script(
                'return angular.element(document).injector().get("$http").pendingRequests.length === 0'))
        except:
            return False

    def wait_for_some_time(self, sec_to_wait):
        self.is_not_used()
        time.sleep(int(sec_to_wait))

    def file_name_to_select(self, file_name):
        self.is_not_used()
        pyautogui.write(file_name)
        pyautogui.press('tab')
        pyautogui.press('enter')

    def is_not_used(self):
        pass
