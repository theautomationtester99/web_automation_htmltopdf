import asyncio
from pathlib import Path
import re
from multiprocessing import Process, Queue, freeze_support, Lock
import argparse
import sys
import tempfile
import time
import webbrowser
from config_reader import ConfigReader
import cv2
import numpy as np
import pandas as pd
import pyautogui
from excel_report_manager import ExcelReportManager
from keywords_manager import KeywordsManager
from pdf_report_manager import PdfReportManager
from utilities import Utils
from config import start_properties
import os
from logger_config import LoggerConfig
from constants import VALID_KEYWORDS


def validate_test_script(testscript_file, wafl, utils, launch_browser):
    """
    Validates the test script Excel file for format, content, and keyword correctness.

    Args:
        testscript_file (str): The path to the test script Excel file.
        wafl: Logger instance for logging.
        utils: Utility instance for helper functions.

    Returns:
        DataFrame: A validated pandas DataFrame containing the test script data.

    Raises:
        ValueError: If the test script is invalid.
    """
    wafl.info(f"Validating the test script: {testscript_file}")
    
    if not utils.is_excel_doc(testscript_file):
        wafl.error("The test script Excel file is not in the correct format.")
        raise ValueError("The test script Excel file is not in the correct format.")

    wafl.debug("Reading the test script Excel file into a pandas DataFrame.")
    df = pd.read_excel(testscript_file, dtype={"Keyword": "string", "Input1": "string", "Input2": "string", "Input3": "string"})
    
    if df['Keyword'].isnull().values.any():
        wafl.error("The 'Keyword' column in the Excel file contains empty values.")
        raise ValueError("The 'Keyword' column in the Excel file contains empty values.")

    wafl.debug("Replacing empty values in the DataFrame with empty strings.")
    df = df.replace(np.nan, '', regex=True)
    
    wafl.info("Validating the content of the test script.")
    for index, row in df.iterrows():
        keyword = str(row["Keyword"])
        wafl.debug(f"Validating row {index}: Keyword='{keyword}'")
        
        if keyword not in VALID_KEYWORDS:
            wafl.error(f"Invalid keyword '{keyword}' at row {index}.")
            raise ValueError(f"Invalid keyword '{keyword}' in the test script.")
        
        if keyword == 'tc_id':
            tc_id_value = str(row["Input3"]).strip()
            if not os.path.basename(testscript_file).split("_")[0].lower() == tc_id_value.lower():
                wafl.error(f"TC ID '{tc_id_value}' does not match the test script file name at row {index}.")
                raise ValueError(f"TC ID '{tc_id_value}' does not match the test script file name.")
        
        if keyword == 'wait_for_seconds' and not str(row["Input3"]).strip().isdigit():
            wafl.error(f"Invalid value '{row['Input3']}' for 'wait_for_seconds' at row {index}.")
            raise ValueError(f"Invalid value '{row['Input3']}' for 'wait_for_seconds'.")
        
        if keyword == 'mcnp_choose_date_from_datepicker':
            which_calendar = str(row["Input2"]).strip()
            wafl.debug(f"Validating date format for calendar '{which_calendar}' at row {index}.")
            if which_calendar == 'cn_det_ed':
                utils.check_date_format_validity(str(row["Input3"]).strip())
            elif which_calendar == 'cn_det_dd':
                utils.check_date_range_format_validity(str(row["Input3"]).strip())
        
        if keyword == 'open_browser' and launch_browser == '':
            browser_given = str(row["Input3"]).strip()
            if browser_given.lower() not in ['chrome', 'edge']:
                wafl.error(f"Invalid browser name '{browser_given}' at row {index}.")
                raise ValueError(f"Invalid browser name '{browser_given}'. It should be either 'chrome' or 'edge'.")
        
        if keyword == 'login_jnj':
            wafl.debug(f"Validating 'login_jnj' inputs at row {index}.")
            element_name_data = str(row["Input1"]).strip()
            element_locator_data = str(row["Input2"]).strip()
            login_uname_pwd_data = str(row["Input3"]).strip()

            element_name_data_lst = element_name_data.split(";")
            element_locator_data_lst = element_locator_data.split(";")
            login_uname_pwd_data_lst = login_uname_pwd_data.split(";")

            if len(list(filter(None, [item.strip() for item in login_uname_pwd_data_lst]))) != 2:
                wafl.error(f"Invalid 'Input3' data '{login_uname_pwd_data}' for 'login_jnj' at row {index}.")
                raise ValueError(f"'Input3' for 'login_jnj' must contain exactly 2 values separated by a semicolon (';').")
            
            if len(list(filter(None, [item.strip() for item in element_name_data_lst]))) != 4:
                wafl.error(f"Invalid 'Input1' data '{element_name_data}' for 'login_jnj' at row {index}.")
                raise ValueError(f"'Input1' for 'login_jnj' must contain exactly 4 values separated by a semicolon (';').")
            
            if len(list(filter(None, [item.strip() for item in element_locator_data_lst]))) != 4:
                wafl.error(f"Invalid 'Input2' data '{element_locator_data}' for 'login_jnj' at row {index}.")
                raise ValueError(f"'Input2' for 'login_jnj' must contain exactly 4 values separated by a semicolon (';').")
        
        if keyword == 'drag_drop':
            wafl.debug(f"Validating 'drag_drop' inputs at row {index}.")
            dd_element_name_data = str(row["Input1"]).strip()
            dd_element_locator_data = str(row["Input2"]).strip()

            dd_element_name_data_lst = dd_element_name_data.split(";")
            dd_element_locator_data_lst = dd_element_locator_data.split(";")

            if len(list(filter(None, [item.strip() for item in dd_element_name_data_lst]))) != 2:
                wafl.error(f"Invalid 'Input1' data '{dd_element_name_data}' for 'drag_drop' at row {index}.")
                raise ValueError(f"'Input1' for 'drag_drop' must contain exactly 2 values separated by a semicolon (';').")
            
            if len(list(filter(None, [item.strip() for item in dd_element_locator_data_lst]))) != 2:
                wafl.error(f"Invalid 'Input2' data '{dd_element_locator_data}' for 'drag_drop' at row {index}.")
                raise ValueError(f"'Input2' for 'drag_drop' must contain exactly 2 values separated by a semicolon (';').")
    
    wafl.info("Test script validation completed successfully.")
    return df

def hover_mouse(row, wafl, km, object_repo_reader):
    locator_type = "xpath"
    if "_css" in str(row["Input2"]).strip().lower():
        locator_type = "css"
    if "_id" in str(row["Input2"]).strip().lower():
        locator_type = "id"
    wafl.info(f"Executing 'hover_mouse' at row {row.name}.")
    km.ge_mouse_hover(
        str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')),
        locator_type,
        str(row["Input1"]).strip()
    )

def drag_drop(row, wafl, km, object_repo_reader):
    locator_type_s = "xpath"
    locator_type_d = "xpath"
    dd_ele_name_data = str(row["Input1"]).strip()
    dd_ele_locator_data = str(row["Input2"]).strip()
    dd_ele_name_data_lst = dd_ele_name_data.split(";")
    dd_ele_locator_data_lst = dd_ele_locator_data.split(";")

    if "_css" in str(dd_ele_locator_data_lst[0]).lower():
        locator_type_s = "css"
    if "_id" in str(dd_ele_locator_data_lst[0]).lower():
        locator_type_s = "id"
    if "_css" in str(dd_ele_locator_data_lst[1]).lower():
        locator_type_d = "css"
    if "_id" in str(dd_ele_locator_data_lst[1]).lower():
        locator_type_d = "id"

    wafl.info(f"Executing 'drag_drop' at row {row.name}.")
    km.ge_drag_and_drop(
        str(object_repo_reader.get_property(locator_type_s.upper(), dd_ele_locator_data_lst[0], fallback='No')),
        locator_type_s,
        str(object_repo_reader.get_property(locator_type_d.upper(), dd_ele_locator_data_lst[1], fallback='No')),
        locator_type_d,
        dd_ele_name_data_lst[0],
        dd_ele_name_data_lst[1]
    )

def check_page_accessibility(row, wafl, km):
    """
    Checks the web page for accessibility compliance using axe-core.

    Args:
        row: The current row of the test script.
        wafl: Logger instance for logging.
        km: KeywordsManager instance for executing keywords.
    """
    wafl.info(f"Executing 'check_accessibility' at row {row.name}.")
    km.ge_is_page_accessibility_compliant()

    # # Save the results to a file
    # report_file = 'accessibility_report.json'
    # axe.write_results(results, report_file)
    # wafl.info(f"Accessibility check completed. Report saved to '{report_file}'.")

    # Check for violations

def open_browser(row, wafl, km, launch_browser):
    browser = launch_browser or str(row["Input3"]).strip()
    wafl.info(f"Executing 'open_browser' at row {row.name}. Launching browser: {browser}.")
    km.ge_open_browser(browser)

def wait_for_seconds(row, wafl, km):
    wafl.info(f"Executing 'wait_for_seconds' at row {row.name}. Waiting for {row['Input3']} seconds.")
    km.ge_wait_for_seconds(int(str(row["Input3"]).strip()))

def switch_to_default_content(row, wafl, km):
    wafl.info(f"Executing 'switch_to_default_content' at row {row.name}.")
    km.ge_switch_to_default_content()

def switch_to_iframe(row, wafl, km, object_repo_reader):
    locator_type = "xpath"
    if "_css" in str(row["Input2"]).strip().lower():
        locator_type = "css"
    if "_id" in str(row["Input2"]).strip().lower():
        locator_type = "id"
    wafl.info(f"Executing 'switch_to_iframe' at row {row.name}.")
    km.ge_switch_to_iframe(
        str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')),
        locator_type,
        str(row["Input1"]).strip()
    )

def tc_id(row, wafl, km):
    wafl.info(f"Executing 'tc_id' at row {row.name}.")
    km.ge_tcid(str(row["Input3"]).strip())

def tc_desc(row, wafl, km):
    wafl.info(f"Executing 'tc_desc' at row {row.name}.")
    km.ge_tcdesc(str(row["Input3"]).strip())

def step(row, wafl, km):
    wafl.info(f"Executing 'step' at row {row.name}.")
    km.ge_step(step=str(row["Input1"]).strip(), result=str(row["Input2"]).strip())

def login_jnj(row, wafl, km, object_repo_reader):
    wafl.info(f"Executing 'login_jnj' at row {row.name}.")
    login_jnj_name_data = str(row["Input1"]).strip()
    login_jnj_locator_data = str(row["Input2"]).strip()
    login_jnj_uname_pwd_data = str(row["Input3"]).strip()

    login_jnj_name_data_lst = login_jnj_name_data.split(";")
    login_jnj_locator_data_lst = login_jnj_locator_data.split(";")
    login_jnj_uname_pwd_data_lst = login_jnj_uname_pwd_data.split(";")
    login_jnj_dict = {
        'locator_type': 'xpath',
        'uname_data': login_jnj_uname_pwd_data_lst[0],
        'pwd_data': login_jnj_uname_pwd_data_lst[1]
    }
    for i in range(len(login_jnj_name_data_lst)):
        if i == 0:
            login_jnj_dict['uname_element_name'] = login_jnj_name_data_lst[i]
            login_jnj_dict['uname_locator'] = str(object_repo_reader.get_property('XPATH', login_jnj_locator_data_lst[i], fallback='No'))
        if i == 1:
            login_jnj_dict['proceed_element_name'] = login_jnj_name_data_lst[i]
            login_jnj_dict['proceed_locator'] = str(object_repo_reader.get_property('XPATH', login_jnj_locator_data_lst[i], fallback='No'))
        if i == 2:
            login_jnj_dict['jnjpwd_element_name'] = login_jnj_name_data_lst[i]
            login_jnj_dict['jnjpwd_locator'] = str(object_repo_reader.get_property('XPATH', login_jnj_locator_data_lst[i], fallback='No'))
        if i == 3:
            login_jnj_dict['signon_element_name'] = login_jnj_name_data_lst[i]
            login_jnj_dict['signon_locator'] = str(object_repo_reader.get_property('XPATH', login_jnj_locator_data_lst[i], fallback='No'))
    km.login_jnj(**login_jnj_dict)

def enter_url(row, wafl, km):
    wafl.info(f"Executing 'enter_url' at row {row.name}. URL: {row['Input3']}.")
    km.ge_enter_url(str(row["Input3"]).strip())

def type_keyword(row, wafl, km, object_repo_reader, utils):
    locator_type = "xpath"
    if "_css" in str(row["Input2"]).strip().lower():
        locator_type = "css"
    if "_id" in str(row["Input2"]).strip().lower():
        locator_type = "id"
    wafl.info(f"Executing 'type' at row {row.name}.")
    if str(row["Input3"]).strip().lower() == 'random_notification_id':
        km.ge_type(
            str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')),
            locator_type,
            utils.generate_random_notif_id(),
            str(row["Input1"]).strip()
        )
    else:
        km.ge_type(
            str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')),
            locator_type,
            row["Input3"],
            str(row["Input1"]).strip()
        )

def check_element_enabled(row, wafl, km, object_repo_reader):
    locator_type = "xpath"
    if "_css" in str(row["Input2"]).strip().lower():
        locator_type = "css"
    if "_id" in str(row["Input2"]).strip().lower():
        locator_type = "id"
    wafl.info(f"Executing 'check_element_enabled' at row {row.name}.")
    km.ge_is_element_enabled(
        str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')),
        locator_type,
        str(row["Input1"]).strip()
    )

def check_element_disabled(row, wafl, km, object_repo_reader):
    locator_type = "xpath"
    if "_css" in str(row["Input2"]).strip().lower():
        locator_type = "css"
    if "_id" in str(row["Input2"]).strip().lower():
        locator_type = "id"
    wafl.info(f"Executing 'check_element_disabled' at row {row.name}.")
    km.ge_is_element_disabled(
        str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')),
        locator_type,
        str(row["Input1"]).strip()
    )

def check_element_displayed(row, wafl, km, object_repo_reader):
    locator_type = "xpath"
    if "_css" in str(row["Input2"]).strip().lower():
        locator_type = "css"
    if "_id" in str(row["Input2"]).strip().lower():
        locator_type = "id"
    wafl.info(f"Executing 'check_element_displayed' at row {row.name}.")
    km.ge_is_element_displayed(
        str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')),
        locator_type,
        str(row["Input1"]).strip()
    )

def verify_displayed_text(row, wafl, km, object_repo_reader):
    locator_type = "xpath"
    if "_css" in str(row["Input2"]).strip().lower():
        locator_type = "css"
    if "_id" in str(row["Input2"]).strip().lower():
        locator_type = "id"
    wafl.info(f"Executing 'verify_displayed_text' at row {row.name}.")
    km.ge_verify_displayed_text(
        str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')),
        locator_type,
        row["Input3"],
        str(row["Input1"]).strip()
    )

def click(row, wafl, km, object_repo_reader):
    locator_type = "xpath"
    if "_css" in str(row["Input2"]).strip().lower():
        locator_type = "css"
    if "_id" in str(row["Input2"]).strip().lower():
        locator_type = "id"
    wafl.info(f"Executing 'click' at row {row.name}.")
    km.ge_click(
        str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')),
        locator_type,
        str(row["Input1"]).strip()
    )

def select_file(row, wafl, km, object_repo_reader):
    locator_type = "xpath"
    if "_css" in str(row["Input2"]).strip().lower():
        locator_type = "css"
    if "_id" in str(row["Input2"]).strip().lower():
        locator_type = "id"
    wafl.info(f"Executing 'select_file' at row {row.name}.")
    km.ge_select_file(
        str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')),
        locator_type,
        str(row["Input3"]).strip()
    )

def mcnp_choose_date_from_datepicker(row, wafl, km, object_repo_reader):
    wafl.info(f"Executing 'mcnp_choose_date_from_datepicker' at row {row.name}.")
    which_calendar = str(row["Input2"]).strip()
    date_to_choose = str(row["Input3"]).strip()
    locator_type = "xpath"
    locator_name = str(row["Input1"]).strip()
    cn_det_ddate_mon_txt_xpath = str(object_repo_reader.get_property('XPATH', 'cn_det_ddate_mon_txt_xpath', fallback='No'))
    cn_det_ddate_pre_button_xpath = str(object_repo_reader.get_property('XPATH', 'cn_det_ddate_pre_button_xpath', fallback='No'))
    cn_det_ddate_nxt_button_xpath = str(object_repo_reader.get_property('XPATH', 'cn_det_ddate_nxt_button_xpath', fallback='No'))
    cn_det_ddate_date_list_xpath = str(object_repo_reader.get_property('XPATH', 'cn_det_ddate_date_list_xpath', fallback='No'))
    cn_det_edate_mon_txt_xpath = str(object_repo_reader.get_property('XPATH', 'cn_det_edate_mon_txt_xpath', fallback='No'))
    cn_det_edate_pre_button_xpath = str(object_repo_reader.get_property('XPATH', 'cn_det_edate_pre_button_xpath', fallback='No'))
    cn_det_edate_nxt_button_xpath = str(object_repo_reader.get_property('XPATH', 'cn_det_edate_nxt_button_xpath', fallback='No'))
    cn_det_edate_date_list_xpath = str(object_repo_reader.get_property('XPATH', 'cn_det_edate_date_list_xpath', fallback='No'))

    km.choose_date_from_date_picker(
        which_calender=which_calendar,
        date_to_choose=date_to_choose,
        locator_type=locator_type,
        locator_name=locator_name,
        cn_det_ddate_mon_txt_xpath=cn_det_ddate_mon_txt_xpath,
        cn_det_ddate_pre_button_xpath=cn_det_ddate_pre_button_xpath,
        cn_det_ddate_nxt_button_xpath=cn_det_ddate_nxt_button_xpath,
        cn_det_ddate_date_list_xpath=cn_det_ddate_date_list_xpath,
        cn_det_edate_mon_txt_xpath=cn_det_edate_mon_txt_xpath,
        cn_det_edate_pre_button_xpath=cn_det_edate_pre_button_xpath,
        cn_det_edate_nxt_button_xpath=cn_det_edate_nxt_button_xpath,
        cn_det_edate_date_list_xpath=cn_det_edate_date_list_xpath
    )

def check_radio_chk_selected(row, wafl, km, object_repo_reader):
    locator_type = "xpath"
    if "_css" in str(row["Input2"]).strip().lower():
        locator_type = "css"
    if "_id" in str(row["Input2"]).strip().lower():
        locator_type = "id"
    wafl.info(f"Executing 'check_radio_chk_selected' at row {row.name}.")
    km.ge_is_chk_radio_element_selected(
        str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')),
        locator_type,
        str(row["Input1"]).strip()
    )

def check_radio_chk_not_selected(row, wafl, km, object_repo_reader):
    locator_type = "xpath"
    if "_css" in str(row["Input2"]).strip().lower():
        locator_type = "css"
    if "_id" in str(row["Input2"]).strip().lower():
        locator_type = "id"
    wafl.info(f"Executing 'check_radio_chk_not_selected' at row {row.name}.")
    km.ge_is_chk_radio_element_not_selected(
        str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')),
        locator_type,
        str(row["Input1"]).strip()
    )

def execute_test_script(df, wafl, km, object_repo_reader, utils, launch_browser):
    """
    Executes the test script based on the validated DataFrame.

    Args:
        df (DataFrame): The validated pandas DataFrame containing the test script data.
        wafl: Logger instance for logging.
        km: KeywordsManager instance for executing keywords.
        object_repo_reader: ConfigReader instance for object repository.
        utils: Utility instance for helper functions.
        launch_browser (str): Specifies the browser to launch.

    Raises:
        Exception: If an error occurs during test script execution.
    """
    wafl.info("Starting test script execution.")

    # Define a dispatch dictionary mapping keywords to their corresponding functions
    keyword_dispatch = {
        'hover_mouse': lambda row: hover_mouse(row, wafl, km, object_repo_reader),
        'drag_drop': lambda row: drag_drop(row, wafl, km, object_repo_reader),
        'open_browser': lambda row: open_browser(row, wafl, km, launch_browser),
        'wait_for_seconds': lambda row: wait_for_seconds(row, wafl, km),
        'switch_to_default_content': lambda row: switch_to_default_content(row, wafl, km),
        'switch_to_iframe': lambda row: switch_to_iframe(row, wafl, km, object_repo_reader),
        'tc_id': lambda row: tc_id(row, wafl, km),
        'tc_desc': lambda row: tc_desc(row, wafl, km),
        'step': lambda row: step(row, wafl, km),
        'login_jnj': lambda row: login_jnj(row, wafl, km, object_repo_reader),
        'enter_url': lambda row: enter_url(row, wafl, km),
        'type': lambda row: type_keyword(row, wafl, km, object_repo_reader, utils),
        'check_element_enabled': lambda row: check_element_enabled(row, wafl, km, object_repo_reader),
        'check_element_disabled': lambda row: check_element_disabled(row, wafl, km, object_repo_reader),
        'check_element_displayed': lambda row: check_element_displayed(row, wafl, km, object_repo_reader),
        'verify_displayed_text': lambda row: verify_displayed_text(row, wafl, km, object_repo_reader),
        'click': lambda row: click(row, wafl, km, object_repo_reader),
        'select_file': lambda row: select_file(row, wafl, km, object_repo_reader),
        'mcnp_choose_date_from_datepicker': lambda row: mcnp_choose_date_from_datepicker(row, wafl, km, object_repo_reader),
        'check_radio_chk_selected': lambda row: check_radio_chk_selected(row, wafl, km, object_repo_reader),
        'check_radio_chk_not_selected': lambda row: check_radio_chk_not_selected(row, wafl, km, object_repo_reader),
        'check_page_accessibility': lambda row: check_page_accessibility(row, wafl, km),
        # Add other keywords and their corresponding functions here...
    }

    for index, row in df.iterrows():
        keyword = str(row["Keyword"])
        wafl.debug(f"Processing row {index}: Keyword='{keyword}'")

        try:
            if keyword in keyword_dispatch:
                keyword_dispatch[keyword](row)
            else:
                wafl.warning(f"Keyword '{keyword}' at row {index} is not implemented.")
        except Exception as e:
            wafl.error(f"Error executing keyword '{keyword}' at row {index}: {e}")
            raise

    wafl.info("Test script execution completed successfully.")

def start_runner(testscript_file, rlog_queue, rlock, object_repo_reader, utils, launch_browser=''):
    """
    Initializes and executes the test script.

    Args:
        testscript_file (str): The path to the test script Excel file.
        rlog_queue (Queue): A multiprocessing queue for logging.
        rlock (Lock): A multiprocessing lock for thread-safe operations.
        start_props_reader (ConfigReader): Reader for the 'start.properties' configuration file.
        object_repo_reader (ConfigReader): Reader for the 'object_repository.properties' configuration file.
        launch_browser (str, optional): Specifies the browser to launch. Defaults to an empty string.

    Raises:
        ValueError: If invalid configurations or test script data are encountered.
        Exception: If an error occurs during test script execution.
    """
    logger_config = LoggerConfig(log_queue=rlog_queue)
    wafl = logger_config.logger
    # utils = Utils(wafl)

    wafl.info("Starting test script execution.")
    wafl.debug(f"Test script file: {testscript_file}")
    wafl.debug(f"Launch browser parameter: {launch_browser}")

    data_run_in_selenium_grid = str(start_properties.RUN_IN_SELENIUM_GRID).lower()
    data_run_in_appium_grid = str(start_properties.RUN_IN_APPIUM_GRID).lower()

    if data_run_in_selenium_grid == data_run_in_appium_grid == 'yes':
        wafl.error("Both 'run_in_appium_grid' and 'run_in_selenium_grid' are set to 'Yes' in 'start.properties'. Only one should be set to 'Yes'.")
        raise ValueError("In 'start.properties' file, both 'run_in_appium_grid' and 'run_in_selenium_grid' are set as 'Yes'. Only one should be set as 'Yes'.")

    wafl.debug("Instantiating excel report manager")
    e_report = ExcelReportManager(wafl, rlock)
    
    wafl.debug("Checking if the test script excel file name ends with 'testscript.xlsx'")

    if "testscript.xlsx" in testscript_file:
        wafl.debug("The test script Excel file name ends with 'testscript.xlsx'. Proceeding with execution.")
        df = validate_test_script(testscript_file, wafl, utils, launch_browser)

        retry_count = 1
        wafl.debug("Instantiating the keyword manager.")
        km = KeywordsManager(wafl, retry_count)
        retries = 0
        max_retries = get_max_retries(rlog_queue)

        while retries <= max_retries:
            # wafl.info("waiting for 20 seconds before retrying.")
            # km.wait_for_some_time(20)
            # object_repo_reader = ConfigReader("object_repository.properties")
            km.update_retry_count(retries + 1)
            try:
                execute_test_script(df, wafl, km, object_repo_reader, utils, launch_browser)
                wafl.info(f"Test script '{testscript_file}' executed successfully.")
                break
            except Exception as e:
                wafl.error(f"Test script '{testscript_file}' failed on attempt {retries}. Error: {e}")
                if retries >= max_retries:
                    wafl.error(f"Test script '{testscript_file}' failed after {retries + 1} attempts.")
                    break
                else:
                    km.ge_close_browser()
                retries += 1

        logged_user_name = str(utils.get_logged_in_user_name())
        test_result = [km.repo_m.tc_id, km.repo_m.test_description, km.repo_m.overall_status_text, km.repo_m.os_img_alt + " " + km.repo_m.browser_img_alt + " " + km.repo_m.browser_version + " ( User: " + logged_user_name + " )", km.repo_m.executed_date]
        wafl.debug("Adding row to test summary results excel file.")
        e_report.add_row(test_result)

        wafl.debug("Closing the test and creating the test result pdf file.")
        km.ge_close()

def get_max_retries(rq):
    """
    Reads the max_retries value from the properties file and enforces a maximum limit of 3.

    Args:
        start_props_reader: The properties reader object used to fetch configuration values.

    Returns:
        int: The validated max_retries value.
    """
    logger_config = LoggerConfig(log_queue=rq)
    lgr = logger_config.logger
    try:
        max_retries = int(start_properties.MAX_RETRIES)
    except:
        lgr.error("Invalid value for max_retries in properties file. Defaulting to 0.")
        max_retries = 0
    
    # Enforce the maximum limit of 2
    if max_retries > 2:
        max_retries = 2
    
    return max_retries

def take_recording(process_name: Process, record_name, logger):
    """
    Records the screen while the specified process is running.

    This function captures the screen and saves it as a video file. It stops recording when the specified process ends.

    Args:
        process_name (Process): The process to monitor for recording.
        record_name (str): The name of the output video file.

    Raises:
        Exception: If an error occurs during recording.
    """
    try:
        # logger = LoggerConfig().logger
        logger.debug("Gathering screen size for recording.")

        SCREEN_SIZE = tuple(pyautogui.size())
        fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        fps = 60.0
        logger.debug("Setting FPS for recording.")

        output_path = os.path.join(utils.get_test_recordings_folder(), f"{record_name}_{utils.get_datetime_string()}.mp4")

        out = cv2.VideoWriter(output_path, fourcc, fps, SCREEN_SIZE)

        logger.debug("Starting recording.")

        while True:
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            out.write(frame)
            if not process_name.is_alive():
                break
        cv2.destroyAllWindows()
        out.release()
        logger.debug("Finished recording.")
    except Exception as e:
        logger.error("An error occurred: %s", e, exc_info=True)
        pass

def check_before_start(utils):
    """
    Performs pre-execution checks and setup.

    This function deletes specified folders and files, creates necessary directories, and validates the contents
    of the `test_scripts` folder to ensure there are no duplicate test scripts in the `chrome` and `edge` subfolders.

    Args:
        start_props_reader (ConfigReader): Reader for the 'start.properties' configuration file.

    Raises:
        ValueError: If duplicate test scripts are found in the `test_scripts` folder and its subfolders.
    """
    logger.debug("Loading 'start.properties' file.")

    delete_test_results_images_recordings_folders_before_start = str(start_properties.DELETE_TEST_RESULTS).lower()

    logger.debug("Checking if in 'start.properties' file option to delete results and recording folders is set to 'yes'.")

    if delete_test_results_images_recordings_folders_before_start.lower() == 'yes':
        logger.debug("Deleting the test_results and recordings folders.")
        utils.delete_folder_and_contents("images")
        utils.delete_folder_and_contents("recordings")
        utils.delete_folder_and_contents("test_results")

    # logger.debug("Deleting the output.xlsx file.")
    # utils.delete_file("output.xlsx")
    logger.debug("Creating the test_results and recordings folders.")
    utils.create_image_and_test_results_folders()

    logger.debug("Starting analysis of the contents of the test_scripts folders.")

    generic_path = os.path.join(".", "test_scripts")

    root_folder = utils.get_abs_path_folder_matching_string_within_folder(generic_path, 'test_scripts')
    chrome_folder = utils.get_abs_path_folder_matching_string_within_folder(generic_path,'chrome')
    edge_folder = utils.get_abs_path_folder_matching_string_within_folder(generic_path,'edge')

    logger.debug("Checking if test_scripts folder and chrome folder contains the same files.")

    if os.path.exists(chrome_folder) and os.path.isdir(chrome_folder):
        if utils.check_if_two_folder_contain_same_files(root_folder, chrome_folder):
            logger.error("The 'test_scripts' folder and 'chrome' folder contains same test script excel files. Make the files unique per folder.")
            raise ValueError("The 'test_scripts' folder and 'chrome' folder contains same test script excel files. Make the files unique per folder.")

    logger.debug("Checking if test_scripts folder and edge folder contains the same files.")
    if os.path.exists(edge_folder) and os.path.isdir(edge_folder):
        if utils.check_if_two_folder_contain_same_files(root_folder, edge_folder):
            logger.error("The 'test_scripts' folder and 'edge' folder contains same test script excel files. Make the files unique per folder.")
            raise ValueError("The 'test_scripts' folder and 'edge' folder contains same test script excel files. Make the files unique per folder.")

if __name__ == '__main__':
    freeze_support()
    """
    Entry point for the script.

    This script performs various operations based on the command-line arguments provided by the user. It supports
    the following features:
    - Starting test execution.
    - Displaying version information.
    - Encrypting a specified file.
    - Generating test summary reports.

    Command-line Arguments:
        --start: Starts the test execution.
        --start-parallel: Starts parallel test execution.
        --version: Displays the version information.
        --encrypt-file: Encrypts the specified file.
        --output-file: Specifies the name of the output file (used with --encrypt-file).
        --help-html: Opens the default browser to display dynamic help.

    Raises:
        ValueError: If invalid arguments are provided or errors occur during execution.
        SystemExit: If the program exits successfully after completing a specific operation.
    """
    try:
        # base_dir = Path(sys.argv[0]).parent.resolve()
        base_dir = Path(sys.argv[0]).parent.resolve()
        lock = Lock()
        log_queue = Queue()
        
        object_repo_reader = ConfigReader(base_dir/"config"/"object_repository.properties")
        
        logger_config = LoggerConfig(log_queue=log_queue)
        listener = logger_config.start_listener()
        logger = logger_config.logger

        utils = Utils(logger)
        utils.stop_driver_processes()
        prm = PdfReportManager(logger)

        logger.debug("Execution Started ----------------.")
        logger.debug("Parsing the input arguments.")
        parser = argparse.ArgumentParser()
        parser.add_argument("--start", action="store_true", help="Start the execution.")
        parser.add_argument("--start-parallel", action="store_true", help="Start parallel execution.")
        parser.add_argument("--version", help="Display the Version", action="store_true")
        parser.add_argument("--delete-tr-google-drive", help="Deletes test results from google drive", action="store_true")
        parser.add_argument("--encrypt-file", help="Encrypts the file", type=str)
        parser.add_argument("--encrypt-str", help="Encrypts the string", type=str)
        parser.add_argument("--output-file", help="Specify the output file name", type=str)
        parser.add_argument("--help-html", action="store_true", help="Open the default browser to display dynamic help.")
        args = parser.parse_args()

        logger.debug("Counting the number of input arguments.")
        active_args = sum(bool(arg) for arg in [args.start, args.start_parallel, args.version, args.encrypt_file, args.delete_tr_google_drive, args.help_html, args.encrypt_str])

        if active_args > 1:
            logger.error("Only one of '--start', --start-parallel, '--version', '--encrypt-file', '--encrypt-str', --delete-tr-google-drive or '--help-html' can be used at a time.")
            raise ValueError("Only one of '--start', --start-parallel, '--version', '--encrypt-file', '--encrypt-str', --delete-tr-google-drive or '--help-html' can be used at a time.")

        if args.output_file and not args.encrypt_file:
            logger.error("'--output-file' can only be used with '--encrypt-file'.")
            raise ValueError("'--output-file' can only be used with '--encrypt-file'.")

        if args.help_html:
            html_content = utils.decrypt_file(base_dir / "resources" / "enc_help_doc.enc")
            with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as temp_file:
                temp_file.write(html_content)
                temp_file.flush()
                temp_file_path = temp_file.name

            webbrowser.open(f"file://{temp_file_path}")
            logger.debug(f"Temporary file created at: {temp_file_path}")
            logger.debug("Please close the browser manually when you're done.")

        if args.encrypt_file:
            logger.debug("Started encrypting file " + args.encrypt_file + ".")
            if not os.path.isfile(args.encrypt_file):
                logger.error("The provided input is not a valid file.")
                raise ValueError("The provided input is not a valid file.")
            else:
                output_file = args.output_file or "default_encrypted_file"
                utils.encrypt_file(str(args.encrypt_file), str(output_file))
                logger.debug(f"Finished encrypting file {args.encrypt_file} to {output_file}")
                sys.exit(0)  # Exit the program successfully after encrypting the file
        
        if args.encrypt_str:
            logger.debug("Started encrypting file " + args.encrypt_str + ".")
            encrypted_str = utils.encrypt_string(str(args.encrypt_str))
            logger.debug(f"Finished encrypting string {args.encrypt_str} to {encrypted_str}")
            sys.exit(0)  # Exit the program successfully after encrypting the file

        if args.version:
            logger.info("Version: 3.0")
            print("Version: 3.0")
            sys.exit(0)  # Exit the program successfully after encrypting the file
            
        if args.delete_tr_google_drive:
            logger.debug("Deleting test results from Google Drive.")
            utils.delete_test_results_from_drive()
            logger.debug("Finished deleting test results from Google Drive.")
            sys.exit(0)  # Exit the program successfully after encrypting the file

        if args.start:
            st = time.time()
            check_before_start(utils)
            run_headless = True if str(start_properties.HEADLESS).lower() == 'yes' else False
            run_in_grid =  str(start_properties.RUN_IN_SELENIUM_GRID).lower()
            run_in_appium =  str(start_properties.RUN_IN_APPIUM_GRID).lower()
            
            upload_tr =  True if str(start_properties.UPLOAD_TEST_RESULTS).lower() == 'yes' else False

            logger.debug("Gathering all files present in the test_scripts folder.")

            generic_path = os.path.join(".", "test_scripts")

            for x in utils.get_absolute_file_paths_in_dir(generic_path):
                logger.debug("Getting the file path " + x + ".")
                logger.debug("Checking if the file path contains 'testscript.xlsx' in the end.")

                if "testscript.xlsx" in x:
                    logger.debug("The file path " + x + " contains 'testscript.xlsx' in the end.")
                    logger.debug("Checking if the file name starts with 'ts' (case insensitive).")

                    p = re.compile(r'^qs[a-zA-Z0-9]*_testscript\.xlsx$', re.I)
                    if p.match(os.path.basename(x)):
                        logger.debug("The file name " + os.path.basename(x) + " starts with 'ts' (case insensitive).")
                        logger.debug("Checking if the file " + os.path.basename(x) + " is present in chrome or edge folder.")
                        if os.path.dirname(x).split(os.sep)[-1].lower() == 'chrome':
                            logger.debug("The file " + os.path.basename(x) + " is present in chrome folder. Launching the execution of test script on chrome browser.")
                            proc1 = Process(target=start_runner,args=(x, log_queue, lock,object_repo_reader, utils,'chrome', ))
                            proc1.start()
                            proc2 = None
                            if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                                logger.debug("Starting the execution recording.")
                                proc2 = Process(target=take_recording(proc1, os.path.basename(x).replace("testscript.xlsx", ""),logger))
                                proc2.start()

                            proc1.join()
                            if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                                proc2.join()
                        elif os.path.dirname(x).split(os.sep)[-1].lower() == 'edge':
                            logger.debug("The file " + os.path.basename(x) + " is present in edge folder. Launching the execution of test script on edge browser.")
                            proc1 = Process(target=start_runner, args=(x, log_queue, lock,object_repo_reader, utils, 'edge',))
                            proc1.start()
                            proc2 = None
                            if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                                logger.debug("Starting the execution recording.")
                                proc2 = Process(target=take_recording(proc1, os.path.basename(x).replace("testscript.xlsx", ""), logger))
                                proc2.start()

                            proc1.join()
                            if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                                proc2.join()
                        elif os.path.dirname(x).split(os.sep)[-1].lower() == 'test_scripts':
                            logger.debug("The file " + os.path.basename(x) + " is present in test_scripts folder. Launching the execution and browser will be choosen from test script.")
                            proc1 = Process(target=start_runner, args=(x,log_queue, lock,object_repo_reader, utils,))
                            proc1.start()
                            proc2 = None
                            if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                                logger.debug("Starting the execution recording.")
                                proc2 = Process(target=take_recording(proc1, os.path.basename(x).replace("testscript.xlsx", ""), logger))
                                proc2.start()

                            proc1.join()
                            if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                                proc2.join()
            et = time.time()

            elapsed_time = round(et - st)
            logger.info(utils.format_elapsed_time(elapsed_time))
            asyncio.run(prm.generate_test_summary_pdf())
            utils.merge_pdfs_in_parts()
            utils.send_email_with_attachment()
            
        if args.start_parallel:
            st = time.time()
            check_before_start(utils)
            run_headless = True if str(start_properties.HEADLESS).lower() == 'yes' else False
            run_in_grid =  True if str(start_properties.RUN_IN_SELENIUM_GRID).lower() == 'yes' else False
            run_in_appium =  True if str(start_properties.RUN_IN_APPIUM_GRID).lower() == 'yes' else False
            number_threads =  int(start_properties.NO_THREADS)
            upload_tr =  True if str(start_properties.UPLOAD_TEST_RESULTS).lower() == 'yes' else False

            if number_threads > 5:
                raise ValueError("number of threads cannot be more than 5")

            if not run_headless and not run_in_grid:
                logger.error("Parallel execution can only be run in headless mode.")
                raise ValueError("Parallel execution can only be run in headless mode.")

            logger.debug("Gathering all files present in the test_scripts folder.")

            generic_path = os.path.join(".", "test_scripts")

            processes = []

            for x in utils.get_absolute_file_paths_in_dir(generic_path):
                logger.debug("Getting the file path " + x + ".")
                logger.debug("Checking if the file path contains 'testscript.xlsx' in the end.")

                if "testscript.xlsx" in x:
                    logger.debug("The file path " + x + " contains 'testscript.xlsx' in the end.")
                    logger.debug("Checking if the file name starts with 'ts' (case insensitive).")

                    p = re.compile(r'^qs[a-zA-Z0-9]*_testscript\.xlsx$', re.I)
                    if p.match(os.path.basename(x)):
                        logger.debug("The file name " + os.path.basename(x) + " starts with 'ts' (case insensitive).")
                        logger.debug("Checking if the file " + os.path.basename(x) + " is present in chrome or edge folder.")
                        if os.path.dirname(x).split(os.sep)[-1].lower() == 'chrome':
                            logger.debug("The file " + os.path.basename(x) + " is present in chrome folder. Launching the execution of test script on chrome browser.")
                            processes.append(Process(target=start_runner,args=(x,log_queue, lock,object_repo_reader, utils, 'chrome',)))
                        elif os.path.dirname(x).split(os.sep)[-1].lower() == 'edge':
                            logger.debug("The file " + os.path.basename(x) + " is present in edge folder. Launching the execution of test script on edge browser.")
                            processes.append(Process(target=start_runner,args=(x,log_queue, lock,object_repo_reader, utils, 'edge',)))
                        elif os.path.dirname(x).split(os.sep)[-1].lower() == 'test_scripts':
                            logger.debug("The file " + os.path.basename(x) + " is present in test_scripts folder. Launching the execution and browser will be choosen from test script.")
                            processes.append(Process(target=start_runner, args=(x,log_queue, lock,object_repo_reader, utils,)))

            for batch_start in range(0, len(processes), number_threads):
                batch = processes[batch_start:batch_start + number_threads]

                for process in batch:
                    process.start()

                for process in batch:
                    process.join()

            et = time.time()

            elapsed_time = round(et - st)
            logger.info(utils.format_elapsed_time(elapsed_time))

            asyncio.run(prm.generate_test_summary_pdf())
            utils.merge_pdfs_in_parts()
            utils.send_email_with_attachment()

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
    finally:
        log_queue.put(None)
        listener.stop()
        logger.info("Application ended in main method.")
