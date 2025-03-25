import logging

from driver_functions import BrowserDriver
from pdf_report_manager import PdfReportManager
from utilities import Utils
import sys
from datetime import datetime

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.INFO)


class KeywordsManager(BrowserDriver):
    def __init__(self):
        super().__init__()
        self.repo_m = PdfReportManager()
        self.utils = Utils()

    '''
    The below are the keywords that can be used generically for any application under testing.
    '''

    def ge_wait_for_seconds(self, how_seconds):
        self.wait_for_some_time(how_seconds)

    def ge_open_browser(self, browser_name):
        try:
            self.launch_browser(browser_name)
            self.repo_m.add_step_data("Open Browser " + browser_name, "The browser should open "
                                                                      "successfully",
                                      "The browser "
                                      "opened ",
                                      "Passed", self.take_screenshot(self.repo_m.tca_id))
        except Exception as e:
            print(e)
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno

            print("Exception type: ", exception_type)
            print("File name: ", filename)
            print("Line number: ", line_number)

            self.repo_m.add_step_data("Open Browser " + browser_name, "The browser should open "
                                                                      "successfully",
                                      "Error Occured" + "\n\r" + str(e), "Failed",
                                      self.take_screenshot(self.repo_m.tca_id))

            self.repo_m.tca_overall_status = 'Failed'
            raise e

    def ge_browser_version(self):
        return self.get_browser_version()

    def ge_is_element_loaded(self, locator, locator_type):
        try:
            return self.is_element_present(locator, locator_type)
        except Exception as e:
            return False
            raise e

    def ge_is_element_enabled(self, locator, locator_type, element_name):
        try:
            is_enabled = self.is_element_enabled(locator, locator_type)
            if is_enabled:
                self.repo_m.add_step_data("Check if the element " + element_name
                                          + " is enabled", "The element " + element_name + " must be enabled",
                                          "The element " + element_name + " is enabled", "Passed",
                                          self.take_screenshot(self.repo_m.tca_id))
            else:
                self.repo_m.tca_overall_status = 'Failed'
                self.repo_m.add_step_data("Check if the element " + element_name
                                          + " is enabled", "The element " + element_name + " must be enabled",
                                          "The element " + element_name + " is disabled", "Failed",
                                          self.take_screenshot(self.repo_m.tca_id))
        except Exception as e:
            self.repo_m.tca_overall_status = 'Failed'
            self.repo_m.add_step_data("Check if the element " + element_name
                                      + " is enabled", "The element " + element_name + " must be enabled",
                                      "Error Occurred" + "\n\r" + str(e), "Failed",
                                      self.take_screenshot(self.repo_m.tca_id))
            raise e

    def ge_is_element_disabled(self, locator, locator_type, element_name):
        try:
            is_disabled = self.is_element_enabled(locator, locator_type)
            if is_disabled is False:
                self.repo_m.add_step_data("Check if the element " + element_name
                                          + " is disabled", "The element " + element_name + " must be disabled",
                                          "The element " + element_name + " is disabled", "Passed",
                                          self.take_screenshot(self.repo_m.tca_id))
            else:
                self.repo_m.tca_overall_status = 'Failed'
                self.repo_m.add_step_data("Check if the element " + element_name
                                          + " is disabled", "The element " + element_name + " must be disabled",
                                          "The element " + element_name + " is enabled", "Failed",
                                          self.take_screenshot(self.repo_m.tca_id))
        except Exception as e:
            self.repo_m.tca_overall_status = 'Failed'
            self.repo_m.add_step_data("Check if the element " + element_name
                                      + " is disabled", "The element " + element_name + " must be disabled",
                                      "Error Occurred" + "\n\r" + str(e), "Failed",
                                      self.take_screenshot(self.repo_m.tca_id))
            raise e

    def ge_is_element_displayed(self, locator, locator_type, element_name):
        try:
            is_displayed = self.is_element_enabled(locator, locator_type)
            if is_displayed:
                self.repo_m.add_step_data("Check if the element " + element_name
                                          + " is displayed", "The element " + element_name + " must be displayed",
                                          "The element " + element_name + " is displayed", "Passed",
                                          self.take_screenshot(self.repo_m.tca_id))
            else:
                self.repo_m.tca_overall_status = 'Failed'
                self.repo_m.add_step_data("Check if the element " + element_name
                                          + " is displayed", "The element " + element_name + " must be displayed",
                                          "The element " + element_name + " is NOT displayed", "Failed",
                                          self.take_screenshot(self.repo_m.tca_id))
        except Exception as e:
            self.repo_m.tca_overall_status = 'Failed'
            self.repo_m.add_step_data("Check if the element " + element_name
                                      + " is displayed", "The element " + element_name + " must be displayed",
                                      "Error Occurred" + "\n\r" + str(e), "Failed",
                                      self.take_screenshot(self.repo_m.tca_id))
            raise e

    def ge_enter_url(self, url):
        try:
            self.open_url(url)
            self.page_has_loaded()
            self.wait_for_some_time(2)
            self.repo_m.add_step_data("Enter URL " + url, "The URL should be entered "
                                                          "successfully",
                                      "The URL is entered successfully ", "Passed",
                                      self.take_screenshot(self.repo_m.tca_id))
        except Exception as e:
            self.repo_m.add_step_data("Enter URL " + url, "The URL should be entered "
                                                          "successfully",
                                      "Error Occurred" + "\n\r" + str(e), "Failed",
                                      self.take_screenshot(self.repo_m.tca_id))

            self.repo_m.tca_overall_status = 'Failed'
            raise e

    def ge_type(self, locator, locator_type, text_to_type, element_name):
        len_input = len(text_to_type)
        nbr_spaces = self.utils.count_spaces_in_string(text_to_type)
        percent_spaces = self.utils.is_what_percent_of(nbr_spaces,len_input)
        if percent_spaces > 2:
            report_txt_to_type = text_to_type
        else:
            report_txt_to_type = self.utils.make_string_manageable(text_to_type, 25)

        try:
            self.highlight(1, "blue", 2, locator, locator_type)
            self.element_click(locator, locator_type)
            self.send_keys(text_to_type, locator, locator_type)
            self.wait_for_some_time(1)
            self.repo_m.add_step_data("Type the text '" + report_txt_to_type + "'in '" + element_name
                                      + "'", "The URL should be entered successfully",
                                      "The text should be typed successfully", "Passed",
                                      self.take_screenshot(self.repo_m.tca_id))
        except Exception as e:
            self.repo_m.add_step_data("Type the text '" + report_txt_to_type + "'in '" + element_name
                                      + "'", "The URL should be entered successfully",
                                      "Error Occurred" + "\n\r" + str(e), "Failed",
                                      self.take_screenshot(self.repo_m.tca_id))

            self.repo_m.tca_overall_status = 'Failed'
            raise e

    def ge_verify_displayed_text(self, locator, locator_type, expected_text, element_name):
        try:
            self.wait_for_element(locator, locator_type)
            self.highlight(1, "blue", 2, locator, locator_type)
            actual_text = self.get_text(locator, locator_type, element_name)
            is_matched = (actual_text == expected_text)
            if is_matched:
                self.repo_m.add_step_data("Verifying the text '" + expected_text + "'in '" + element_name + "'",
                                          "The text should be " + expected_text,
                                          "The text is  " + actual_text, "Passed",
                                          self.take_screenshot(self.repo_m.tca_id))

            else:
                self.repo_m.add_step_data("Verifying the text '" + expected_text + "'in '" + element_name + "'",
                                          "The text should be " + expected_text,
                                          "The text is  " + actual_text, "Failed",
                                          self.take_screenshot(self.repo_m.tca_id))

                self.repo_m.tca_overall_status = 'Failed'
        except Exception as e:
            self.repo_m.add_step_data("Verifying the text '" + expected_text + "'in '" + element_name + "'",
                                      "The text should be " + expected_text,
                                      "Error Occurred" + "\n\r" + str(e), "Failed",
                                      self.take_screenshot(self.repo_m.tca_id))

            self.repo_m.tca_overall_status = 'Failed'
            raise e

    def ge_click(self, locator, locator_type, element_name):
        try:
            self.scroll_into_view(locator, locator_type)
            self.highlight(1, "blue", 2, locator, locator_type)
            self.element_click(locator, locator_type)
            self.wait_for_some_time(2)
            self.repo_m.add_step_data("Click on the element '" + element_name + "'",
                                      "The click should be successful", "The click is successful", "Passed",
                                      self.take_screenshot(self.repo_m.tca_id))
        except Exception as e:
            self.repo_m.add_step_data("Click on the element '" + element_name + "'",
                                      "The click should be successful", "Error Occurred" + "\n\r" + str(e),
                                      "Failed",
                                      self.take_screenshot(self.repo_m.tca_id))

            self.repo_m.tca_overall_status = 'Failed'
            raise e

    def ge_select_file(self, locator, locator_type, file_paths):
        try:
            self.file_name_to_select(file_paths)
            self.wait_for_element(locator, locator_type)
            self.scroll_into_view(locator, locator_type)
            self.repo_m.add_step_data("Upload the file '" + file_paths + "'",
                                      "The file should be added successfully", "The file is added successful",
                                      "Passed",
                                      self.take_screenshot(self.repo_m.tca_id))
        except Exception as e:
            self.repo_m.add_step_data("Upload the file '" + file_paths + "'",
                                      "The file should be added successfully",
                                      "Error Occurred" + "\n\r" + str(e),
                                      "Failed",
                                      self.take_screenshot(self.repo_m.tca_id))

            self.repo_m.tca_overall_status = 'Failed'
            raise e

    '''
    The below are the keywords that are specific to MCNP application.
    '''

    def choose_date_from_date_picker(self, **kwargs):
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
                            self.element_click(kwargs.get('cn_det_ddate_pre_button_xpath'),
                                               kwargs.get("locator_type"))
                        else:
                            self.element_click(kwargs.get('cn_det_ddate_nxt_button_xpath'),
                                               kwargs.get("locator_type"))
                date_element_list = self.get_element_list(kwargs.get('cn_det_ddate_date_list_xpath'),
                                                          kwargs.get("locator_type"))
                for testscript_file in date_element_list:
                    disp_day = self.get_text("", "", testscript_file)
                    disp_day_two_dig = "%02d" % (int(disp_day),)
                    if disp_day_two_dig == first_day:
                        self.element_click("", "", testscript_file)
                        break
                # Second date in date range
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
                        self.element_click(kwargs.get('cn_det_ddate_pre_button_xpath'),
                                           kwargs.get("locator_type"))
                    elif disp_yr < second_yr:
                        self.element_click(kwargs.get('cn_det_ddate_nxt_button_xpath'),
                                           kwargs.get("locator_type"))
                    else:
                        if disp_mon_nbr > second_mon_nbr:
                            self.element_click(kwargs.get('cn_det_ddate_pre_button_xpath'),
                                               kwargs.get("locator_type"))
                        else:
                            self.element_click(kwargs.get('cn_det_ddate_nxt_button_xpath'),
                                               kwargs.get("locator_type"))
                date_element_list = self.get_element_list(
                    kwargs.get('cn_det_ddate_date_list_xpath'), kwargs.get("locator_type"))
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
                        self.element_click(kwargs.get('cn_det_edate_pre_button_xpath'),
                                           kwargs.get("locator_type"))
                    elif disp_yr < yr:
                        self.element_click(kwargs.get('cn_det_edate_nxt_button_xpath'),
                                           kwargs.get("locator_type"))
                    else:
                        if disp_mon_nbr > mon_nbr:
                            self.element_click(kwargs.get('cn_det_edate_pre_button_xpath'),
                                               kwargs.get("locator_type"))
                        else:
                            self.element_click(kwargs.get('cn_det_edate_nxt_button_xpath'),
                                               kwargs.get("locator_type"))
                date_element_list = self.get_element_list(
                    kwargs.get('cn_det_edate_date_list_xpath'), kwargs.get("locator_type"))
                for testscript_file in date_element_list:
                    disp_day = self.get_text("", "", testscript_file)
                    disp_day_two_dig = "%02d" % (int(disp_day),)
                    if disp_day_two_dig == day:
                        self.element_click("", "", testscript_file)
                        break

            self.repo_m.add_step_data(
                "Choosing the date '" + expected_date + "'in '" + kwargs.get("locator_name") + "'",
                "The date should be chosen successfully",
                "The date is chosen successfully", "Passed",
                self.take_screenshot(self.repo_m.tca_id))
        except Exception as e:
            self.repo_m.add_step_data(
                "Choosing the date '" + expected_date + "'in '" + kwargs.get("locator_name") + "'",
                "The date should be chosen successfully",
                "Error Occurred" + "\n\r" + str(e), "Failed",
                self.take_screenshot(self.repo_m.tca_id))

            self.repo_m.tca_overall_status = 'Failed'
            raise e

    def login_jnj(self, **kwargs):
        self.ge_click(kwargs.get("uname_locator"), kwargs.get("locator_type"), kwargs.get("uname_element_name"))
        self.ge_type(kwargs.get("uname_locator"), kwargs.get("locator_type"), kwargs.get("uname_data"),
                     kwargs.get("uname_element_name"))
        self.ge_click(kwargs.get("proceed_locator"), kwargs.get("locator_type"), kwargs.get("proceed_element_name"))
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
