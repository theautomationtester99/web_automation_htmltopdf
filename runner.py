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
from jproperties import Properties
from excel_report_manager import ExcelReportManager
from keywords_manager import KeywordsManager
from pdf_report_manager import PdfReportManager
from utilities import Utils
from sys import exit
import os
from pathlib import Path
from logger_config import LoggerConfig
from constants import VALID_KEYWORDS


def start_runner(testscript_file, rlog_queue, rlock, start_props_reader, object_repo_reader, launch_browser=''):
    """
    Initializes and executes the test script.

    This function sets up the test execution environment, validates configurations, processes the test script,
    and executes test steps based on predefined keywords. It also generates reports summarizing the test results.

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

    data_run_in_selenium_grid = str(start_props_reader.get_property('SGrid', 'run_in_selenium_grid', fallback='No')).lower()
    data_run_in_appium_grid = str(start_props_reader.get_property('Appium', 'run_in_appium_grid', fallback='No')).lower()

    if data_run_in_selenium_grid == data_run_in_appium_grid == 'yes':
        wafl.error("Both 'run_in_appium_grid' and 'run_in_selenium_grid' are set to 'Yes' in 'start.properties'. Only one should be set to 'Yes'.")
        raise ValueError("In 'start.properties' file, both 'run_in_appium_grid' and 'run_in_selenium_grid' are set as 'Yes'. Only one should be set as 'Yes'.")

    wafl.debug("Instantiating excel report manager")
    e_report = ExcelReportManager(wafl, rlock)

    wafl.debug("Checking if the test script excel file name ends with 'testscript.xlsx'")

    if "testscript.xlsx" in testscript_file:
        wafl.debug("Test script excel file name ends with 'testscript.xlsx'. Proceeding execution.")
        wafl.debug("Checking if the test script excel file is in correct excel format")
        if utils.is_excel_doc(testscript_file):
            wafl.debug("Test script excel file is in correct excel format. Proceeding execution.")
            wafl.debug("Reading the test script excel file into pandas dataframe.")
            df = pd.read_excel(testscript_file, dtype={"Keyword": "string", "Input1": "string", "Input2": "string", "Input3": "string"})
            wafl.debug("Checking if the 'Keyword' column of test script excel file does not contain empty values.")
            check_nan_for_test_steps = df['Keyword'].isnull().values.any()

            if check_nan_for_test_steps:
                wafl.error("The 'Keyword' column in the excel file contains empty values. Please check.")
                raise ValueError("The 'Keyword' column in the excel file contains empty values. Please check.")

            wafl.debug("Replacing all empty values in pandas data frame as ''.")
            df1 = df.replace(np.nan, '', regex=True)
            wafl.debug("Looping through the data frame to check the validity of its content.")
            for index, row in df1.iterrows():
                wafl.debug("Reading Row Number " + str(index))
                wafl.debug("Checking if the keyword in row number " + str(index) + " of 'Keyword' column '" + str(row["Keyword"]) + "' is a valid keyword.")
                if str(row["Keyword"]) not in VALID_KEYWORDS:
                    wafl.error("The keyword in row number " + str(index) + " of 'Keyword' column '" + str(row["Keyword"]) + "' is invalid.")
                    raise ValueError(f"The keyword '{row['Keyword']}' entered in keyword column in the excel file is invalid. Please check.")
                wafl.debug("The keyword in row number " + str(index) + " of 'Keyword' column '" + str(row["Keyword"]) + "' is a valid keyword.")

                if str(row["Keyword"]) == 'mcnp_choose_date_from_datepicker':
                    which_calender = str(row["Input2"])
                    if which_calender == 'cn_det_ed':
                        utils.check_date_format_validity(str(row["Input3"]))
                    if which_calender == 'cn_det_dd':
                        utils.check_date_range_format_validity(
                            str(row["Input3"]))

                if str(row["Keyword"]) == 'open_browser':
                    browser_given = str(row["Input3"])
                    wafl.debug("Checking if a valid browser name is given.")
                    if launch_browser == '':
                        if browser_given.lower() != 'chrome' and browser_given.lower() != 'edge':
                            wafl.error("The input given for keyword '" + str(row["Keyword"]) + "' in Input3 column in the excel file is invalid. It should be either 'edge' or 'chrome'.")
                            raise ValueError("The input given for keyword '" + str(row["Keyword"]) + "' in Input3 column in the excel file is invalid. It should be either 'edge' or 'chrome'. Please check.")

                if str(row["Keyword"]) == 'login_jnj':
                    element_name_data = str(row["Input1"])
                    element_locator_data = str(row["Input2"])
                    login_uname_pwd_data = str(row["Input3"])

                    element_name_data_lst = element_name_data.split(";")
                    element_locator_data_lst = element_locator_data.split(";")
                    login_uname_pwd_data_lst = login_uname_pwd_data.split(";")

                    if len(list(filter(None, login_uname_pwd_data_lst))) != 2:
                        raise ValueError("The data entered in the Input3 Column for the keyword '" + row[
                            "Keyword"] + "' is '" + login_uname_pwd_data + "'. It is not correct. It should be 2 "
                            "datas "
                            "separated by a ';'. For example "
                            "UserName;Password")
                    if len(list(filter(None, element_name_data_lst))) != 4:
                        raise ValueError("The data entered in the Input1 Column for the keyword '" + row[
                            "Keyword"] + "' is '" + element_name_data + "'. It is not correct. It should be 4 datas "
                            "separated by a ';'. For example "
                            "Name1;Name2;Name3;Name4")
                    if len(list(filter(None, element_locator_data_lst))) != 4:
                        raise ValueError("The data entered in the Input2 Column for the keyword '" + row[
                            "Keyword"] + "' is '" + element_locator_data + "'. It is not correct. It should be 4 "
                            "datas "
                            "separated by a ';'. For example "
                            "locator1;locator1;locator1;locator1")
                
                if str(row["Keyword"]) == 'drag_drop':
                    dd_element_name_data = str(row["Input1"])
                    dd_element_locator_data = str(row["Input2"])

                    dd_element_name_data_lst = dd_element_name_data.split(";")
                    dd_element_locator_data_lst = dd_element_locator_data.split(";")
                    
                    if len(list(filter(None, dd_element_name_data_lst))) != 2:
                        raise ValueError("The data entered in the Input1 Column for the keyword '" + row[
                            "Keyword"] + "' is '" + dd_element_name_data + "'. It is not correct. It should be 2 element names "
                            "separated by a ';'. For example "
                            "element1;elementName2")
                    if len(list(filter(None, dd_element_locator_data_lst))) != 2:
                        raise ValueError("The data entered in the Input2 Column for the keyword '" + row[
                            "Keyword"] + "' is '" + dd_element_locator_data + "'. It is not correct. It should be 2 "
                            "datas "
                            "separated by a ';'. For example "
                            "locator1;locator2")

                if index == 0:
                    wafl.debug("Checking if a first keyword in the test script excel file is 'tc_id'.")
                    if not (str(row["Keyword"]) == 'tc_id'):
                        wafl.error("The first keyword must be 'tc_id'")
                        raise ValueError("The first keyword must be 'tc_id'")
                    else:
                        fn = os.path.basename(testscript_file)
                        prefix = fn.split('_')[0]
                        if not (str(prefix).lower() == str(row["Input3"]).lower()):
                            wafl.error("The 'tc_id' in the script file is not matching with the tc id mentioned in the file name " + testscript_file)
                            raise ValueError("The 'tc_id' in the script file is not matching with the tc id mentioned in the file name " + testscript_file)

                if index == 1:
                    wafl.debug("Checking if a second keyword in the test script excel file is 'tc_desc'.")
                    if not (str(row["Keyword"]) == 'tc_desc'):
                        wafl.error("The second keyword must be 'tc_desc'")
                        raise ValueError("The second keyword must be 'tc_desc'")
                if index == 2:
                    wafl.debug("Checking if a third keyword in the test script excel file is 'step'.")
                    if not (str(row["Keyword"]) == 'step'):
                        wafl.error("The third keyword must be 'step'")
                        raise ValueError("The third keyword must be 'step'")
                if index == 3:
                    wafl.debug("Checking if a fourth keyword in the test script excel file is 'open_browser'.")
                    if not (str(row["Keyword"]) == 'open_browser'):
                        wafl.error("The fourth keyword must be 'open_browser'")
                        raise ValueError("The fourth keyword must be 'open_browser'")
                if index == 4:
                    wafl.debug("Checking if a fifth keyword in the test script excel file is 'enter_url'.")
                    if not (str(row["Keyword"]) == 'enter_url'):
                        wafl.error("The fifth keyword must be 'enter_url'")
                        raise ValueError("The fifth keyword must be 'enter_url'")

            wafl.debug("Instantiating the keyword manager.")

            km = KeywordsManager(wafl)
            wafl.debug("Looping through the data frame to execute the test script.")
            for index, row in df1.iterrows():
                wafl.debug("Reading Row Number " + str(index))
                
                if str(row["Keyword"]) == 'hover_mouse':
                    locator_type = "xpath"
                    if "_css" in str(row["Input2"]).lower():
                        locator_type = "css"
                    if "_id" in str(row["Input2"]).lower():
                        locator_type = "id"
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    km.ge_mouse_hover(str(object_repo_reader.get_property(locator_type.upper(), row["Input2"], fallback='No')), locator_type,str(row["Input1"]))
                
                if str(row["Keyword"]) == 'drag_drop':
                    locator_type_s = "xpath"
                    locator_type_d = "xpath"
                    
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    dd_ele_name_data = str(row["Input1"])
                    dd_ele_locator_data = str(row["Input2"])

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
                    if "_css" in str(row["Input2"]).lower():
                        locator_type = "css"
                    if "_id" in str(row["Input2"]).lower():
                        locator_type = "id"
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    km.ge_is_chk_radio_element_not_selected(str(object_repo_reader.get_property(locator_type.upper(), row["Input2"], fallback='No')), locator_type,str(row["Input1"]))
                
                if str(row["Keyword"]) == 'check_radio_chk_selected':
                    locator_type = "xpath"
                    if "_css" in str(row["Input2"]).lower():
                        locator_type = "css"
                    if "_id" in str(row["Input2"]).lower():
                        locator_type = "id"
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    km.ge_is_chk_radio_element_selected(str(object_repo_reader.get_property(locator_type.upper(), row["Input2"], fallback='No')), locator_type,str(row["Input1"]))
                
                if str(row["Keyword"]) == 'switch_to_default_content':
                    km.ge_switch_to_default_content()
                    
                if str(row["Keyword"]) == 'switch_to_iframe':
                    locator_type = "xpath"
                    if "_css" in str(row["Input2"]).lower():
                        locator_type = "css"
                    if "_id" in str(row["Input2"]).lower():
                        locator_type = "id"
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                    km.ge_switch_to_iframe(str(object_repo_reader.get_property(locator_type.upper(), row["Input2"], fallback='No')), locator_type,str(row["Input1"]))

                if str(row["Keyword"]) == 'tc_id':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                    km.ge_tcid(str(row["Input3"]))

                if str(row["Keyword"]) == 'tc_desc':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                    km.ge_tcdesc(str(row["Input3"]))

                if str(row["Keyword"]) == 'step':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input1"]) + "' to the keyword manager.")
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    km.ge_step(step=str(row["Input1"]), result=str(row["Input2"]))

                if str(row["Keyword"]) == 'wait_for_seconds':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                    km.ge_wait_for_seconds(int(row["Input3"]))

                if str(row["Keyword"]) == 'open_browser':
                    wafl.debug("Checking if 'launch_browser' paramater is empty.")
                    try:
                        if launch_browser == '':
                            wafl.debug("The 'launch_browser' paramater is empty. Taking this paramater from test script excel file.")
                            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                            km.ge_open_browser(str(row["Input3"]))
                        else:
                            wafl.debug("The 'launch_browser' paramater is available. Using it.")
                            wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(launch_browser) + "' to the keyword manager.")
                            km.ge_open_browser(str(launch_browser))
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

                if str(row["Keyword"]) == 'login_jnj':
                    try:
                        login_jnj_name_data = str(row["Input1"])
                        login_jnj_locator_data = str(row["Input2"])
                        login_jnj_uname_pwd_data = str(row["Input3"])

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

                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

                if str(row["Keyword"]) == 'enter_url':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                    try:
                        km.ge_enter_url(str(row["Input3"]))
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

                if str(row["Keyword"]) == 'type':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input1"]) + "' to the keyword manager.")
                    try:
                        locator_type = "xpath"
                        if "_css" in str(row["Input2"]).lower():
                            locator_type = "css"
                        if "_id" in str(row["Input2"]).lower():
                            locator_type = "id"
                        if row["Input3"].lower() == 'random_notification_id':
                            km.ge_type(str(object_repo_reader.get_property(locator_type.upper(), row["Input2"], fallback='No')), locator_type,utils.generate_random_notif_id(),str(row["Input1"]))
                        else:
                            km.ge_type(str(object_repo_reader.get_property(locator_type.upper(), row["Input2"], fallback='No')), locator_type, row["Input3"],str(row["Input1"]))
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

                if str(row["Keyword"]) == 'check_element_enabled':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                    locator_type = "xpath"
                    if "_css" in str(row["Input2"]).lower():
                        locator_type = "css"
                    if "_id" in str(row["Input2"]).lower():
                        locator_type = "id"
                    try:
                        km.ge_is_element_enabled(str(object_repo_reader.get_property(locator_type.upper(), row["Input2"], fallback='No')), locator_type,row["Input3"])
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

                if str(row["Keyword"]) == 'check_element_disabled':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                    locator_type = "xpath"
                    if "_css" in str(row["Input2"]).lower():
                        locator_type = "css"
                    if "_id" in str(row["Input2"]).lower():
                        locator_type = "id"
                    try:
                        km.ge_is_element_disabled(str(object_repo_reader.get_property(locator_type.upper(), row["Input2"], fallback='No')), locator_type,row["Input3"])
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

                if str(row["Keyword"]) == 'check_element_displayed':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                    locator_type = "xpath"
                    if "_css" in str(row["Input2"]).lower():
                        locator_type = "css"
                    if "_id" in str(row["Input2"]).lower():
                        locator_type = "id"
                    try:
                        km.ge_is_element_displayed(str(object_repo_reader.get_property(locator_type.upper(), row["Input2"], fallback='No')), locator_type,row["Input3"])
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

                if str(row["Keyword"]) == 'mcnp_choose_date_from_datepicker':
                    try:
                        which_calender = str(row["Input2"])
                        date_to_choose = str(row["Input3"])
                        locator_type = "xpath"
                        locator_name = str(row["Input1"])
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
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

                if str(row["Keyword"]) == 'verify_displayed_text':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input1"]) + "' to the keyword manager.")
                    locator_type = "xpath"
                    if "_css" in str(row["Input2"]).lower():
                        locator_type = "css"
                    if "_id" in str(row["Input2"]).lower():
                        locator_type = "id"
                    try:
                        km.ge_verify_displayed_text(str(object_repo_reader.get_property(locator_type.upper(), row["Input2"], fallback='No')),locator_type, row["Input3"], str(row["Input1"]))
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

                if str(row["Keyword"]) == 'click':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input1"]) + "' to the keyword manager.")
                    locator_type = "xpath"
                    if "_css" in str(row["Input2"]).lower():
                        locator_type = "css"
                    if "_id" in str(row["Input2"]).lower():
                        locator_type = "id"
                    try:
                        km.ge_click(str(object_repo_reader.get_property(locator_type.upper(), row["Input2"], fallback='No')), locator_type,str(row["Input1"]))
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

                if str(row["Keyword"]) == 'select_file':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                    locator_type = "xpath"
                    if "_css" in str(row["Input2"]).lower():
                        locator_type = "css"
                    if "_id" in str(row["Input2"]).lower():
                        locator_type = "id"
                    try:
                        km.ge_select_file(str(object_repo_reader.get_property(locator_type.upper(), row["Input2"], fallback='No')), locator_type,str(row["Input3"]))
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

            wafl.debug("Gathering test summary results.")
            logged_user_name = str(utils.get_logged_in_user_name())
            test_result = [km.repo_m.tc_id, km.repo_m.test_description,km.repo_m.overall_status_text, km.repo_m.os_img_alt + " " + km.repo_m.browser_img_alt + " " + km.repo_m.browser_version + " ( User: " + logged_user_name + " )", km.repo_m.executed_date]
            wafl.debug("Adding row to test summary results excel file.")
            e_report.add_row(test_result)

            wafl.debug("Closing the test and creating the test result pdf file.")

            km.ge_close()


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

    if utils.check_if_two_folder_contain_same_files(root_folder, chrome_folder):
        logger.error("The 'test_scripts' folder and 'chrome' folder contains same test script excel files. Make the files unique per folder.")
        raise ValueError("The 'test_scripts' folder and 'chrome' folder contains same test script excel files. Make the files unique per folder.")

    logger.debug("Checking if test_scripts folder and edge folder contains the same files.")

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
