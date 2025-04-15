import asyncio
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
import os
from logger_config import LoggerConfig
from constants import VALID_KEYWORDS

def validate_test_script(testscript_file, wafl, utils):
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
    wafl.debug("Validating if the test script Excel file is in the correct format.")
    if not utils.is_excel_doc(testscript_file):
        wafl.error("The test script Excel file is not in the correct format.")
        raise ValueError("The test script Excel file is not in the correct format.")

    wafl.debug("Reading the test script Excel file into a pandas DataFrame.")
    df = pd.read_excel(testscript_file, dtype={"Keyword": "string", "Input1": "string", "Input2": "string", "Input3": "string"})
    wafl.debug("Checking if the 'Keyword' column of the test script Excel file contains any empty values.")
    if df['Keyword'].isnull().values.any():
        wafl.error("The 'Keyword' column in the Excel file contains empty values. Please check and correct the file.")
        raise ValueError("The 'Keyword' column in the Excel file contains empty values. Please check and correct the file.")

    wafl.debug("Replacing all empty values in the pandas DataFrame with empty strings ('').")
    df = df.replace(np.nan, '', regex=True)
    wafl.debug("Iterating through the DataFrame to validate its content.")
    for index, row in df.iterrows():
        wafl.debug(f"Processing row number {index}.")
        wafl.debug(f"Validating the keyword '{row['Keyword']}' in row number {index}.")
        if str(row["Keyword"]) not in VALID_KEYWORDS:
            wafl.error(f"The keyword '{row['Keyword']}' in row number {index} is invalid. Please check the test script.")
            raise ValueError(f"The keyword '{row['Keyword']}' in the test script is invalid. Please check the test script.")
        wafl.debug(f"The keyword '{row['Keyword']}' in row number {index} is valid.")
        if str(row["Keyword"]) == 'wait_for_seconds':
            wafl.debug("Validating the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to be a valid integer.")
            if not str(row["Input3"]).strip().isdigit():
                wafl.error(f"The value '{row['Input3']}' in the 'wait_for_seconds' keyword is invalid. It should be a positive integer.")
                raise ValueError(f"The value '{row['Input3']}' in the 'wait_for_seconds' keyword is invalid. It should be a positive integer.")

        if str(row["Keyword"]) == 'mcnp_choose_date_from_datepicker':
            wafl.debug("Validating the date format for the 'mcnp_choose_date_from_datepicker' keyword.")
            which_calender = str(row["Input2"]).strip()
            if which_calender == 'cn_det_ed':
                wafl.debug(f"Validating the date format for the calendar '{which_calender}'.")
                utils.check_date_format_validity(str(row["Input3"]).strip())
            if which_calender == 'cn_det_dd':
                wafl.debug(f"Validating the date range format for the calendar '{which_calender}'.")
                utils.check_date_range_format_validity(str(row["Input3"]).strip())

        if str(row["Keyword"]) == 'open_browser':
            browser_given = str(row["Input3"]).strip()
            wafl.debug("Validating the browser name provided in the test script.")
            if browser_given.lower() not in ['chrome', 'edge']:
                wafl.error(f"The browser name '{browser_given}' provided in the test script is invalid. It should be either 'chrome' or 'edge'.")
                raise ValueError(f"The browser name '{browser_given}' provided in the test script is invalid. It should be either 'chrome' or 'edge'. Please check.")

        if str(row["Keyword"]) == 'login_jnj':
            wafl.debug("Validating the input data for the 'login_jnj' keyword.")
            element_name_data = str(row["Input1"]).strip()
            element_locator_data = str(row["Input2"]).strip()
            login_uname_pwd_data = str(row["Input3"]).strip()

            element_name_data_lst = element_name_data.split(";")
            element_locator_data_lst = element_locator_data.split(";")
            login_uname_pwd_data_lst = login_uname_pwd_data.split(";")

            if len(list(filter(None, [item.strip() for item in login_uname_pwd_data_lst]))) != 2:
                wafl.error(f"The data '{login_uname_pwd_data}' in the 'Input3' column for the 'login_jnj' keyword is invalid. It should contain exactly 2 values separated by a semicolon (';').")
                raise ValueError(f"The data '{login_uname_pwd_data}' in the 'Input3' column for the 'login_jnj' keyword is invalid. It should contain exactly 2 values separated by a semicolon (';').")
            
            if len(list(filter(None, [item.strip() for item in element_name_data_lst]))) != 4:
                wafl.error(f"The data '{element_name_data}' in the 'Input1' column for the 'login_jnj' keyword is invalid. It should contain exactly 4 values separated by a semicolon (';').")
                raise ValueError(f"The data '{element_name_data}' in the 'Input1' column for the 'login_jnj' keyword is invalid. It should contain exactly 4 values separated by a semicolon (';').")
            
            if len(list(filter(None, [item.strip() for item in element_locator_data_lst]))) != 4:
                wafl.error(f"The data '{element_locator_data}' in the 'Input2' column for the 'login_jnj' keyword is invalid. It should contain exactly 4 values separated by a semicolon (';').")
                raise ValueError(f"The data '{element_locator_data}' in the 'Input2' column for the 'login_jnj' keyword is invalid. It should contain exactly 4 values separated by a semicolon (';').")

        if str(row["Keyword"]) == 'drag_drop':
            wafl.debug("Validating the input data for the 'drag_drop' keyword.")
            dd_element_name_data = str(row["Input1"]).strip()
            dd_element_locator_data = str(row["Input2"]).strip()

            dd_element_name_data_lst = dd_element_name_data.split(";")
            dd_element_locator_data_lst = dd_element_locator_data.split(";")

            if len(list(filter(None, [item.strip() for item in dd_element_name_data_lst]))) != 2:
                wafl.error(f"The data '{dd_element_name_data}' in the 'Input1' column for the 'drag_drop' keyword is invalid. It should contain exactly 2 values separated by a semicolon (';').")
                raise ValueError(f"The data '{dd_element_name_data}' in the 'Input1' column for the 'drag_drop' keyword is invalid. It should contain exactly 2 values separated by a semicolon (';').")

            if len(list(filter(None, [item.strip() for item in dd_element_locator_data_lst]))) != 2:
                wafl.error(f"The data '{dd_element_locator_data}' in the 'Input2' column for the 'drag_drop' keyword is invalid. It should contain exactly 2 values separated by a semicolon (';').")
                raise ValueError(f"The data '{dd_element_locator_data}' in the 'Input2' column for the 'drag_drop' keyword is invalid. It should contain exactly 2 values separated by a semicolon (';').")
    return df


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
    wafl.debug("Looping through the data frame to execute the test script.")
    for index, row in df.iterrows():
        wafl.debug("Reading Row Number " + str(index))

        if str(row["Keyword"]) == 'hover_mouse':
            locator_type = "xpath"
            if "_css" in str(row["Input2"]).strip().lower():
                locator_type = "css"
            if "_id" in str(row["Input2"]).strip().lower():
                locator_type = "id"
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
            km.ge_mouse_hover(str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')), locator_type,str(row["Input1"]).strip())
        
        if str(row["Keyword"]) == 'drag_drop':
            locator_type_s = "xpath"
            locator_type_d = "xpath"
            
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
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
            
            km.ge_drag_and_drop(str(object_repo_reader.get_property(locator_type_s.upper(), dd_ele_locator_data_lst[0], fallback='No')), locator_type_s,str(object_repo_reader.get_property(locator_type_d.upper(), dd_ele_locator_data_lst[1], fallback='No')), locator_type_d, dd_ele_name_data_lst[0], dd_ele_name_data_lst[1])
        
        if str(row["Keyword"]) == 'check_radio_chk_not_selected':
            locator_type = "xpath"
            if "_css" in str(row["Input2"]).strip().lower():
                locator_type = "css"
            if "_id" in str(row["Input2"]).strip().lower():
                locator_type = "id"
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
            km.ge_is_chk_radio_element_not_selected(str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')), locator_type,str(row["Input1"]).strip())
        
        if str(row["Keyword"]) == 'check_radio_chk_selected':
            locator_type = "xpath"
            if "_css" in str(row["Input2"]).strip().lower():
                locator_type = "css"
            if "_id" in str(row["Input2"]).strip().lower():
                locator_type = "id"
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
            km.ge_is_chk_radio_element_selected(str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')), locator_type,str(row["Input1"]).strip())
        
        if str(row["Keyword"]) == 'switch_to_default_content':
            km.ge_switch_to_default_content()
            
        if str(row["Keyword"]) == 'switch_to_iframe':
            locator_type = "xpath"
            if "_css" in str(row["Input2"]).strip().lower():
                locator_type = "css"
            if "_id" in str(row["Input2"]).strip().lower():
                locator_type = "id"
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
            km.ge_switch_to_iframe(str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')), locator_type,str(row["Input1"]).strip())

        if str(row["Keyword"]) == 'tc_id':
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
            km.ge_tcid(str(row["Input3"]).strip())

        if str(row["Keyword"]) == 'tc_desc':
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
            km.ge_tcdesc(str(row["Input3"]).strip())

        if str(row["Keyword"]) == 'step':
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input1"]) + "' to the keyword manager.")
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
            km.ge_step(step=str(row["Input1"]).strip(), result=str(row["Input2"]).strip())

        if str(row["Keyword"]) == 'wait_for_seconds':
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
            km.ge_wait_for_seconds(int(str(row["Input3"]).strip()))

        if str(row["Keyword"]) == 'open_browser':
            wafl.debug("Checking if 'launch_browser' paramater is empty.")
            if launch_browser == '':
                wafl.debug("The 'launch_browser' paramater is empty. Taking this paramater from test script excel file.")
                wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                km.ge_open_browser(str(row["Input3"]).strip())
            else:
                wafl.debug("The 'launch_browser' paramater is available. Using it.")
                wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(launch_browser) + "' to the keyword manager.")
                km.ge_open_browser(str(launch_browser))

        if str(row["Keyword"]) == 'login_jnj':
            login_jnj_name_data = str(row["Input1"]).strip()
            login_jnj_locator_data = str(row["Input2"]).strip()
            login_jnj_uname_pwd_data = str(row["Input3"]).strip()

            login_jnj_name_data_lst = login_jnj_name_data.split(";")
            login_jnj_locator_data_lst = login_jnj_locator_data.split(";")
            login_jnj_uname_pwd_data_lst = login_jnj_uname_pwd_data.split(";")
            login_jnj_dict = {'locator_type': 'xpath', 'uname_data': login_jnj_uname_pwd_data_lst[0], 'pwd_data': login_jnj_uname_pwd_data_lst[1]}
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

        if str(row["Keyword"]) == 'enter_url':
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
            km.ge_enter_url(str(row["Input3"]).strip())

        if str(row["Keyword"]) == 'type':
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input1"]) + "' to the keyword manager.")
            locator_type = "xpath"
            if "_css" in str(row["Input2"]).strip().lower():
                locator_type = "css"
            if "_id" in str(row["Input2"]).strip().lower():
                locator_type = "id"
            if str(row["Input3"]).strip().lower() == 'random_notification_id':
                km.ge_type(str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')), locator_type,utils.generate_random_notif_id(),str(row["Input1"]).strip())
            else:
                km.ge_type(str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')), locator_type, row["Input3"],str(row["Input1"]).strip())

        if str(row["Keyword"]) == 'check_element_enabled':
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
            locator_type = "xpath"
            if "_css" in str(row["Input2"]).strip().lower():
                locator_type = "css"
            if "_id" in str(row["Input2"]).strip().lower():
                locator_type = "id"
            km.ge_is_element_enabled(str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')), locator_type,str(row["Input1"]).strip())

        if str(row["Keyword"]) == 'check_element_disabled':
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
            locator_type = "xpath"
            if "_css" in str(row["Input2"]).strip().lower():
                locator_type = "css"
            if "_id" in str(row["Input2"]).strip().lower():
                locator_type = "id"
            km.ge_is_element_disabled(str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')), locator_type,str(row["Input1"]).strip())

        if str(row["Keyword"]) == 'check_element_displayed':
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
            locator_type = "xpath"
            if "_css" in str(row["Input2"]).strip().lower():
                locator_type = "css"
            if "_id" in str(row["Input2"]).strip().lower():
                locator_type = "id"
            km.ge_is_element_displayed(str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')), locator_type,str(row["Input1"]).strip())

        if str(row["Keyword"]) == 'mcnp_choose_date_from_datepicker':
            which_calender = str(row["Input2"]).strip()
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

            km.choose_date_from_date_picker(which_calender=which_calender, date_to_choose=date_to_choose,
                                            locator_type=locator_type,
                                            locator_name=locator_name,
                                            cn_det_ddate_mon_txt_xpath=cn_det_ddate_mon_txt_xpath,
                                            cn_det_ddate_pre_button_xpath=cn_det_ddate_pre_button_xpath,
                                            cn_det_ddate_nxt_button_xpath=cn_det_ddate_nxt_button_xpath,
                                            cn_det_ddate_date_list_xpath=cn_det_ddate_date_list_xpath,
                                            cn_det_edate_mon_txt_xpath=cn_det_edate_mon_txt_xpath,
                                            cn_det_edate_pre_button_xpath=cn_det_edate_pre_button_xpath,
                                            cn_det_edate_nxt_button_xpath=cn_det_edate_nxt_button_xpath,
                                            cn_det_edate_date_list_xpath=cn_det_edate_date_list_xpath)

        if str(row["Keyword"]) == 'verify_displayed_text':
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input1"]) + "' to the keyword manager.")
            locator_type = "xpath"
            if "_css" in str(row["Input2"]).strip().lower():
                locator_type = "css"
            if "_id" in str(row["Input2"]).strip().lower():
                locator_type = "id"
            km.ge_verify_displayed_text(str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')),locator_type, row["Input3"], str(row["Input1"]).strip())

        if str(row["Keyword"]) == 'click':
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input1"]) + "' to the keyword manager.")
            locator_type = "xpath"
            if "_css" in str(row["Input2"]).strip().lower():
                locator_type = "css"
            if "_id" in str(row["Input2"]).strip().lower():
                locator_type = "id"
            km.ge_click(str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')), locator_type,str(row["Input1"]).strip())

        if str(row["Keyword"]) == 'select_file':
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
            locator_type = "xpath"
            if "_css" in str(row["Input2"]).strip().lower():
                locator_type = "css"
            if "_id" in str(row["Input2"]).strip().lower():
                locator_type = "id"
            km.ge_select_file(str(object_repo_reader.get_property(locator_type.upper(), str(row["Input2"]).strip(), fallback='No')), locator_type,str(row["Input3"]).strip())


def start_runner(testscript_file, rlog_queue, rlock, start_props_reader, object_repo_reader, launch_browser=''):
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
    utils = Utils(wafl)

    wafl.info("Starting test script execution.")
    wafl.debug(f"Test script file: {testscript_file}")
    wafl.debug(f"Launch browser parameter: {launch_browser}")

    data_run_in_selenium_grid = str(start_props_reader.get_property('SGrid', 'run_in_selenium_grid', fallback='No')).lower()
    data_run_in_appium_grid = str(start_props_reader.get_property('Appium', 'run_in_appium_grid', fallback='No')).lower()

    if data_run_in_selenium_grid == data_run_in_appium_grid == 'yes':
        wafl.error("Both 'run_in_appium_grid' and 'run_in_selenium_grid' are set to 'Yes' in 'start.properties'. Only one should be set to 'Yes'.")
        raise ValueError("In 'start.properties' file, both 'run_in_appium_grid' and 'run_in_selenium_grid' are set as 'Yes'. Only one should be set as 'Yes'.")

    wafl.debug("Instantiating excel report manager")
    e_report = ExcelReportManager(wafl, rlock)
    
    wafl.debug("Checking if the test script excel file name ends with 'testscript.xlsx'")

    if "testscript.xlsx" in testscript_file:
        wafl.debug("The test script Excel file name ends with 'testscript.xlsx'. Proceeding with execution.")
        df = validate_test_script(testscript_file, wafl, utils)

        retry_count = 1
        wafl.debug("Instantiating the keyword manager.")
        km = KeywordsManager(wafl, retry_count)
        retries = 0
        max_retries = get_max_retries(start_props_reader, rlog_queue)

        while retries <= max_retries:
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


def get_max_retries(start_props_reader, rq):
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
        max_retries = int(start_props_reader.get_property('Misc', 'max_retries', fallback='0'))
    except:
        lgr.error("Invalid value for max_retries in properties file. Defaulting to 0.")
        max_retries = 0
    
    # Enforce the maximum limit of 2
    if max_retries > 2:
        max_retries = 2
    
    return max_retries

def take_recording(process_name: Process, record_name):
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
        logger = LoggerConfig().logger
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

def check_before_start(start_props_reader):
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

    delete_test_results_images_recordings_folders_before_start = str(start_props_reader.get_property('Misc', 'delete_test_results_images_recordings_folders_before_start', fallback='No')).lower()

    logger.debug("Checking if in 'start.properties' file option to delete results and recording folders is set to 'yes'.")

    if delete_test_results_images_recordings_folders_before_start.lower() == 'yes':
        logger.debug("Deleting the test_results and recordings folders.")
        utils.delete_folder_and_contents("images")
        utils.delete_folder_and_contents("recordings")
        utils.delete_folder_and_contents("test_results")

    logger.debug("Deleting the output.xlsx file.")
    utils.delete_file("output.xlsx")
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
        freeze_support()
        lock = Lock()
        log_queue = Queue()

        logger_config = LoggerConfig(log_queue=log_queue)
        listener = logger_config.start_listener()
        logger = logger_config.logger

        utils = Utils(logger)
        prm = PdfReportManager(logger)

        start_props_reader = ConfigReader("start.properties")
        object_repo_reader = ConfigReader("object_repository.properties")

        logger.debug("Execution Started ----------------.")
        logger.debug("Parsing the input arguments.")
        parser = argparse.ArgumentParser()
        parser.add_argument("--start", action="store_true", help="Start the execution.")
        parser.add_argument("--start-parallel", action="store_true", help="Start parallel execution.")
        parser.add_argument("--version", help="Display the Version", action="store_true")
        parser.add_argument("--encrypt-file", help="Encrypts the file", type=str)
        parser.add_argument("--output-file", help="Specify the output file name", type=str)
        parser.add_argument("--help-html", action="store_true", help="Open the default browser to display dynamic help.")
        args = parser.parse_args()

        logger.debug("Counting the number of input arguments.")
        active_args = sum(bool(arg) for arg in [args.start, args.start_parallel, args.version, args.encrypt_file, args.help_html])

        if active_args > 1:
            logger.error("Only one of '--start', --start-parallel, '--version', '--encrypt-file' or '--help-html' can be used at a time.")
            raise ValueError("Only one of '--start', --start-parallel, '--version', '--encrypt-file' or '--help-html' can be used at a time.")

        if args.output_file and not args.encrypt_file:
            logger.error("'--output-file' can only be used with '--encrypt-file'.")
            raise ValueError("'--output-file' can only be used with '--encrypt-file'.")

        if args.help_html:
            html_content = utils.decrypt_file("enc_help_doc.enc")
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

        if args.version:
            logger.info("Version: 3.0")
            print("Version: 3.0")
            sys.exit(0)  # Exit the program successfully after encrypting the file

        if args.start:
            st = time.time()
            check_before_start(start_props_reader)
            run_headless = True if str(start_props_reader.get_property('Browser_Settings', 'Headless', fallback='No')).lower() == 'yes' else False
            run_in_grid =  str(start_props_reader.get_property('SGrid', 'run_in_selenium_grid', fallback='No')).lower()
            run_in_appium =  str(start_props_reader.get_property('Appium', 'run_in_appium_grid', fallback='No')).lower()

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
                            proc1 = Process(target=start_runner,args=(x, log_queue, lock,start_props_reader,object_repo_reader, 'chrome', ))
                            proc1.start()
                            proc2 = None
                            if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                                logger.debug("Starting the execution recording.")
                                proc2 = Process(target=take_recording(proc1, os.path.basename(x).replace("testscript.xlsx", "")))
                                proc2.start()

                            proc1.join()
                            if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                                proc2.join()
                        elif os.path.dirname(x).split(os.sep)[-1].lower() == 'edge':
                            logger.debug("The file " + os.path.basename(x) + " is present in edge folder. Launching the execution of test script on edge browser.")
                            proc1 = Process(target=start_runner, args=(x, log_queue, lock,start_props_reader,object_repo_reader, 'edge',))
                            proc1.start()
                            proc2 = None
                            if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                                logger.debug("Starting the execution recording.")
                                proc2 = Process(target=take_recording(proc1, os.path.basename(x).replace("testscript.xlsx", "")))
                                proc2.start()

                            proc1.join()
                            if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                                proc2.join()
                        elif os.path.dirname(x).split(os.sep)[-1].lower() == 'test_scripts':
                            logger.debug("The file " + os.path.basename(x) + " is present in test_scripts folder. Launching the execution and browser will be choosen from test script.")
                            proc1 = Process(target=start_runner, args=(x,log_queue, lock,start_props_reader,object_repo_reader,))
                            proc1.start()
                            proc2 = None
                            if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                                logger.debug("Starting the execution recording.")
                                proc2 = Process(target=take_recording(proc1, os.path.basename(x).replace("testscript.xlsx", "")))
                                proc2.start()

                            proc1.join()
                            if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                                proc2.join()
            et = time.time()

            elapsed_time = round(et - st)
            logger.info(utils.format_elapsed_time(elapsed_time))
            asyncio.run(prm.generate_test_summary_pdf())

        if args.start_parallel:
            st = time.time()
            check_before_start(start_props_reader)
            run_headless = True if str(start_props_reader.get_property('Browser_Settings', 'Headless', fallback='No')).lower() == 'yes' else False
            run_in_grid =  True if str(start_props_reader.get_property('SGrid', 'run_in_selenium_grid', fallback='No')).lower() == 'yes' else False
            run_in_appium =  True if str(start_props_reader.get_property('Appium', 'run_in_appium_grid', fallback='No')).lower() == 'yes' else False
            number_threads =  int(start_props_reader.get_property('Parallel', 'NoThreads', fallback='5'))

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
                            processes.append(Process(target=start_runner,args=(x,log_queue, lock,start_props_reader,object_repo_reader, 'chrome',)))
                        elif os.path.dirname(x).split(os.sep)[-1].lower() == 'edge':
                            logger.debug("The file " + os.path.basename(x) + " is present in edge folder. Launching the execution of test script on edge browser.")
                            processes.append(Process(target=start_runner,args=(x,log_queue, lock,start_props_reader,object_repo_reader, 'edge',)))
                        elif os.path.dirname(x).split(os.sep)[-1].lower() == 'test_scripts':
                            logger.debug("The file " + os.path.basename(x) + " is present in test_scripts folder. Launching the execution and browser will be choosen from test script.")
                            processes.append(Process(target=start_runner, args=(x,log_queue, lock,start_props_reader,object_repo_reader,)))

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

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
    finally:
        log_queue.put(None)
        listener.stop()
        logger.info("Application ended in main method.")
