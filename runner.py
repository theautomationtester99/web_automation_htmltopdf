import asyncio
import re
from multiprocessing import Process, Queue, freeze_support, Lock
import argparse
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


def start_runner(testscript_file, rlog_queue, rlock, launch_browser=''):
    """
    Start Runner

    This function initializes the test execution environment, validates configurations, processes a test
    script, and executes test steps based on defined keywords. It performs the following steps:

    1. Loads the 'start.properties' and 'object_repository.properties' configuration files.
    2. Validates that only one of 'run_in_selenium_grid' or 'run_in_appium_grid' is set to 'Yes'.
    3. Ensures the test script Excel file:
        - Is correctly formatted.
        - Ends with 'testscript.xlsx'.
        - Has non-empty values in the 'Keyword' column.
    4. Verifies that the first few rows in the test script contain specific keywords in a defined order:
        - Row 0: 'tc_id'
        - Row 1: 'tc_desc'
        - Row 2: 'step'
        - Row 3: 'open_browser'
        - Row 4: 'enter_url'.
    5. Processes the test script data, validating and executing each step based on predefined keywords:
        - Keywords include 'tc_id', 'tc_desc', 'step', 'wait_for_seconds', 'open_browser', 'login_jnj',
        'enter_url', 'type', 'check_element_enabled', 'check_element_disabled', 'check_element_displayed',
        'mcnp_choose_date_from_datepicker', 'verify_displayed_text', 'click', and 'select_file'.
        - Passes relevant parameters to the 'KeywordsManager' for execution.
    6. Collects test results and updates the summary report in Excel.
    7. Generates a PDF report summarizing the test results.

    Args:
        testscript_file (str): The path to the test script Excel file.
        launch_browser (str, optional): Specifies the browser to launch, defaults to an empty string.

    Raises:
        SystemExit: If invalid configurations or invalid test script data are encountered.
        Exception: If an error occurs during test script execution.

    """
    logger_config = LoggerConfig(log_queue=rlog_queue)
    wafl = logger_config.logger
    utils = Utils(wafl)
    '''
    Load the object repository
    '''
    ele_hl_tm = 1
    ele_hl_sz = 2
    ele_hl_cl = 'blue'
    wafl.debug("Loading 'start.properties' file")
    configs = Properties()
    start_properties_configs = Properties()
    with open('start.properties', 'rb') as start_config_file:
        wafl.debug("Loading 'start.properties' file")
        start_properties_configs.load(start_config_file)

    wafl.debug("Loading 'start.properties' is successful")

    data_run_in_selenium_grid = str(
        start_properties_configs.get('run_in_selenium_grid').data)
    data_run_in_appium_grid = str(
        start_properties_configs.get('run_in_appium_grid').data)

    if data_run_in_selenium_grid.lower() == data_run_in_appium_grid.lower() == 'yes':
        exit("In 'start.properties' file, both 'run_in_appium_grid' and 'run_in_selenium_grid' are set as 'Yes'. Only 1 should be set as 'Yes'")

    wafl.debug("Loading 'object_repository.properties' file")

    with open('object_repository.properties', 'rb') as config_file:
        configs.load(config_file)

    wafl.debug("Loading 'object_repository.properties' is successful.")

    only_delete = str(configs.get("login_uname_textbox_xpath").data)

    valid_keywords_tuple = ("tc_id", "tc_desc", "open_browser", "enter_url", "type", "click", "select_file", "verify_displayed_text","mcnp_choose_date_from_datepicker", "wait_for_seconds", "login_jnj", "check_element_enabled","check_element_disabled", "check_element_displayed", "step")
    # all_test_results_list = []
    wafl.debug("Instantiating excel report manager")
    e_report = ExcelReportManager(wafl, rlock)

    wafl.debug("Checking if the test script excel file name ends with 'testscript.xlsx'")

    if "testscript.xlsx" in testscript_file:
        wafl.debug("Test script excel file name ends with 'testscript.xlsx'. Proceeding execution.")
        wafl.debug("Checking if the test script excel file is in correct excel format")
        if utils.is_excel_doc(testscript_file):
            wafl.debug("Test script excel file is in correct excel format. Proceeding execution.")
            # all_steps_list = []
            # step_no = 1
            wafl.debug("Reading the test script excel file into pandas dataframe.")
            df = pd.read_excel(testscript_file,dtype={"Keyword": "string", "Input1": "string","Input2": "string","Input3": "string"})
            wafl.debug("Checking if the 'Keyword' column of test script excel file does not contain empty values.")
            check_nan_for_test_steps = df['Keyword'].isnull().values.any()

            if check_nan_for_test_steps:
                wafl.error("The 'Keyword' column in the excel file contains empty values. Please check.")
                exit("The 'Keyword' column in the excel file contains empty values. Please check.")

            wafl.debug("Replacing all empty values in pandas data frame as ''.")
            df1 = df.replace(np.nan, '', regex=True)
            wafl.debug("Looping through the data frame to check the validity of its content.")
            for index, row in df1.iterrows():
                wafl.debug("Reading Row Number " + str(index))
                # print(index)
                wafl.debug("Checking if the keyword in row number " + str(index) + " of 'Keyword' column '" +str(row["Keyword"]) + "' is a valid keyword.")
                if str(row["Keyword"]) not in valid_keywords_tuple:
                    wafl.error("The keyword in row number " + str(index) + " of 'Keyword' column '" +str(row["Keyword"]) + "' is invalid.")
                    exit("The keyword '" + row["Keyword"] + "' entered in keyword column in the excel file is invalid. Please check.")
                wafl.debug("The keyword in row number " + str(index) + " of 'Keyword' column '" +str(row["Keyword"]) + "' is a valid keyword.")

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
                            exit("The input given for keyword '" + str(row["Keyword"]) + "' in Input3 column in the excel file is invalid. It should be either 'edge' or 'chrome'. Please check.")

                if str(row["Keyword"]) == 'login_jnj':
                    element_name_data = str(row["Input1"])
                    element_locator_data = str(row["Input2"])
                    login_uname_pwd_data = str(row["Input3"])

                    element_name_data_lst = element_name_data.split(";")
                    element_locator_data_lst = element_locator_data.split(";")
                    login_uname_pwd_data_lst = login_uname_pwd_data.split(";")

                    if len(list(filter(None, login_uname_pwd_data_lst))) != 2:
                        exit("The data entered in the Input3 Column for the keyword '" + row[
                            "Keyword"] + "' is '" + login_uname_pwd_data + "'. It is not correct. It should be 2 "
                            "datas "
                            "separated by a ';'. For example "
                            "UserName;Password")
                    if len(list(filter(None, element_name_data_lst))) != 4:
                        exit("The data entered in the Input1 Column for the keyword '" + row[
                            "Keyword"] + "' is '" + element_name_data + "'. It is not correct. It should be 4 datas "
                            "separated by a ';'. For example "
                            "Name1;Name2;Name3;Name4")
                    if len(list(filter(None, element_locator_data_lst))) != 4:
                        exit("The data entered in the Input2 Column for the keyword '" + row[
                            "Keyword"] + "' is '" + element_locator_data + "'. It is not correct. It should be 4 "
                            "datas "
                            "separated by a ';'. For example "
                            "locator1;locator1;locator1;locator1")

                if index == 0:
                    wafl.debug("Checking if a first keyword in the test script excel file is 'tc_id'.")
                    if not (str(row["Keyword"]) == 'tc_id'):
                        wafl.error("The first keyword must be 'tc_id'")
                        exit("The first keyword must be 'tc_id'")
                    else:
                        fn = os.path.basename(testscript_file)
                        prefix = fn.split('_')[0]
                        if not (str(prefix).lower() == str(row["Input3"]).lower()):
                            wafl.error("The 'tc_id' in the script file is not matching with the tc id mentioned in the file name " + testscript_file)
                            exit("The 'tc_id' in the script file is not matching with the tc id mentioned in the file name " + testscript_file)
                        
                if index == 1:
                    wafl.debug("Checking if a second keyword in the test script excel file is 'tc_desc'.")
                    if not (str(row["Keyword"]) == 'tc_desc'):
                        wafl.error("The second keyword must be 'tc_desc'")
                        exit("The second keyword must be 'tc_desc'")
                if index == 2:
                    wafl.debug("Checking if a third keyword in the test script excel file is 'step'.")
                    if not (str(row["Keyword"]) == 'step'):
                        wafl.error("The third keyword must be 'step'")
                        exit("The third keyword must be 'step'")
                if index == 3:
                    wafl.debug("Checking if a fourth keyword in the test script excel file is 'open_browser'.")
                    if not (str(row["Keyword"]) == 'open_browser'):
                        wafl.error("The fourth keyword must be 'open_browser'")
                        exit("The fourth keyword must be 'open_browser'")
                if index == 4:
                    wafl.debug("Checking if a fifth keyword in the test script excel file is 'enter_url'.")
                    if not (str(row["Keyword"]) == 'enter_url'):
                        wafl.error("The fifth keyword must be 'enter_url'")
                        exit("The fifth keyword must be 'enter_url'")

            wafl.debug("Instantiating the keyword manager.")

            km = KeywordsManager(wafl)
            # tca_id = ''
            # tca_desc = ''
            # tca_browser_name = ''
            # tca_browser_version = ''
            # tca_date_executed = utils.get_date_string()
            # tca_overall_status = 'Passed'
            # repo_m = PdfReportManager()
            wafl.debug("Looping through the data frame to execute the test script.")
            for index, row in df1.iterrows():
                wafl.debug("Reading Row Number " + str(index))

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
                    # sd.wait_for_some_time(int(row["Input3"]))
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
                        login_jnj_locator_data = str(
                            row["Input2"])
                        login_jnj_uname_pwd_data = str(row["Input3"])

                        login_jnj_name_data_lst = login_jnj_name_data.split(
                            ";")
                        login_jnj_locator_data_lst = login_jnj_locator_data.split(
                            ";")
                        login_jnj_uname_pwd_data_lst = login_jnj_uname_pwd_data.split(
                            ";")
                        # login_jnj_name_locator_dict = dict(zip(login_jnj_name_data_lst, login_jnj_locator_data_lst))
                        login_jnj_dict = {'locator_type': 'xpath', 'uname_data': login_jnj_uname_pwd_data_lst[0],
                                          'pwd_data': login_jnj_uname_pwd_data_lst[1]}
                        for i in range(len(login_jnj_name_data_lst)):
                            if i == 0:
                                login_jnj_dict['uname_element_name'] = login_jnj_name_data_lst[i]
                                login_jnj_dict['uname_locator'] = str(
                                    configs.get(login_jnj_locator_data_lst[i]).data)
                            if i == 1:
                                login_jnj_dict['proceed_element_name'] = login_jnj_name_data_lst[i]
                                login_jnj_dict['proceed_locator'] = str(
                                    configs.get(login_jnj_locator_data_lst[i]).data)
                            if i == 2:
                                login_jnj_dict['jnjpwd_element_name'] = login_jnj_name_data_lst[i]
                                login_jnj_dict['jnjpwd_locator'] = str(
                                    configs.get(login_jnj_locator_data_lst[i]).data)
                            if i == 3:
                                login_jnj_dict['signon_element_name'] = login_jnj_name_data_lst[i]
                                login_jnj_dict['signon_locator'] = str(
                                    configs.get(login_jnj_locator_data_lst[i]).data)
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
                        if row["Input3"].lower() == 'random_notification_id':
                            km.ge_type(str(configs.get(row["Input2"]).data), "xpath",utils.generate_random_notif_id(),str(row["Input1"]))
                        else:
                            km.ge_type(str(configs.get(row["Input2"]).data), "xpath", row["Input3"],str(row["Input1"]))
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

                if str(row["Keyword"]) == 'check_element_enabled':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                    try:
                        km.ge_is_element_enabled(str(configs.get(row["Input2"]).data), "xpath",row["Input3"])
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

                if str(row["Keyword"]) == 'check_element_disabled':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                    try:
                        km.ge_is_element_disabled(str(configs.get(row["Input2"]).data), "xpath",row["Input3"])
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

                if str(row["Keyword"]) == 'check_element_displayed':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                    try:
                        km.ge_is_element_displayed(str(configs.get(row["Input2"]).data), "xpath",row["Input3"])
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

                if str(row["Keyword"]) == 'mcnp_choose_date_from_datepicker':
                    try:
                        which_calender = str(row["Input2"])
                        date_to_choose = str(row["Input3"])
                        locator_type = "xpath"
                        locator_name = str(row["Input1"])
                        cn_det_ddate_mon_txt_xpath = str(
                            configs.get('cn_det_ddate_mon_txt_xpath').data)
                        cn_det_ddate_pre_button_xpath = str(
                            configs.get('cn_det_ddate_pre_button_xpath').data)
                        cn_det_ddate_nxt_button_xpath = str(
                            configs.get('cn_det_ddate_nxt_button_xpath').data)
                        cn_det_ddate_date_list_xpath = str(
                            configs.get('cn_det_ddate_date_list_xpath').data)
                        cn_det_edate_mon_txt_xpath = str(
                            configs.get('cn_det_edate_mon_txt_xpath').data)
                        cn_det_edate_pre_button_xpath = str(
                            configs.get('cn_det_edate_pre_button_xpath').data)
                        cn_det_edate_nxt_button_xpath = str(
                            configs.get('cn_det_edate_nxt_button_xpath').data)
                        cn_det_edate_date_list_xpath = str(
                            configs.get('cn_det_edate_date_list_xpath').data)

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
                    try:
                        km.ge_verify_displayed_text(str(configs.get(row["Input2"]).data),"xpath", row["Input3"], str(row["Input1"]))
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

                if str(row["Keyword"]) == 'click':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input1"]) + "' to the keyword manager.")
                    try:
                        km.ge_click(str(configs.get(row["Input2"]).data), "xpath",str(row["Input1"]))
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

                if str(row["Keyword"]) == 'select_file':
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input2"]) + "' to the keyword manager.")
                    wafl.debug("Passing the keyword '" + str(row["Keyword"]) + "' and input '" +  str(row["Input3"]) + "' to the keyword manager.")
                    try:
                        km.ge_select_file(str(configs.get(row["Input2"]).data), "xpath",str(row["Input3"]))
                    except Exception as e:
                        wafl.error("An error occurred: %s", e, exc_info=True)
                        break

            # test_result = [km.repo_m.tc_id, "\n".join(wrap(km.repo_m.test_description, width=110)),
            #                km.repo_m.overall_status_text,
            #                km.repo_m.browser_img_alt + " " + km.repo_m.browser_version, km.repo_m.executed_date]
            wafl.debug("Gathering test summary results.")
            test_result = [km.repo_m.tc_id, km.repo_m.test_description,km.repo_m.overall_status_text, km.repo_m.os_img_alt + " " + km.repo_m.browser_img_alt + " " + km.repo_m.browser_version, km.repo_m.executed_date]
            wafl.debug("Adding row to test summary results excel file.")
            e_report.add_row(test_result)

            wafl.debug("Closing the test and creating the test result pdf file.")

            km.ge_close()


def take_recording(process_name: Process, record_name):
    try:
        # time.sleep(30)
        # display screen resolution, get it using pyautogui itself
        logger = LoggerConfig().logger
        logger.debug("Gathering screen size for recording.")

        SCREEN_SIZE = tuple(pyautogui.size())
        # define the codec
        # fourcc = cv2.VideoWriter_fourcc(*"XVID")
        fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        # frames per second
        logger.debug("Setting FPS for recording.")

        fps = 60.0
        # create the video write object
        # out = cv2.VideoWriter(utils.get_test_recordings_folder() + "\\" + record_name +utils.get_datetime_string() + ".mp4", fourcc,fps, (SCREEN_SIZE))
        # Construct the path in a platform-independent way
        logger.debug("Gathering the output path and file name for recording.")

        output_path = os.path.join(utils.get_test_recordings_folder(), f"{record_name}_{utils.get_datetime_string()}.mp4")

        # Create the VideoWriter object
        out = cv2.VideoWriter(output_path, fourcc, fps, SCREEN_SIZE)
        # the time you want to record in seconds
        record_seconds = 10

        logger.debug("Starting recording.")

        while True:
            # print(process_name.is_alive())
            # make a screenshot
            img = pyautogui.screenshot()
            # convert these pixels to a proper numpy array to work with OpenCV
            frame = np.array(img)
            # convert colors from BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # write the frame
            out.write(frame)
            # show the frame
            # cv2.imshow("screenshot", frame)
            # if the user clicks q, it exits
            if not process_name.is_alive():
                break
        # make sure everything is closed when exited
        cv2.destroyAllWindows()
        out.release()
        logger.debug("Finished recording.")
    except Exception as e:
        logger.error("An error occurred: %s", e, exc_info=True)
        pass

def check_before_start():
    logger.debug("Loading 'start.properties' file.")

    runner_config_reader = ConfigReader("start.properties")
    delete_test_results_images_recordings_folders_before_start =  str(runner_config_reader.get_property('Misc', 'delete_test_results_images_recordings_folders_before_start', fallback='No')).lower()

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

    '''
    Below code checks if there are duplicate test script excel file in '.\\test_scripts' folder and '.\\test_scripts\\chrome'
    Below code checks if there are duplicate test script excel file in '.\\test_scripts' folder and '.\\test_scripts\\edge'
    '''
    logger.debug("Starting analysis of the contents of the test_scripts folders.")

    root_folder = ''
    chrome_folder = ''
    edge_folder = ''
    generic_path = os.path.join(".", "test_scripts")
    for folder_path in utils.get_list_str_paths_of_all_sub_directories(generic_path):
        if Path(folder_path).name.lower() == 'test_scripts':
            root_folder = folder_path
        if Path(folder_path).name.lower() == 'chrome':
            chrome_folder = folder_path
        if Path(folder_path).name.lower() == 'edge':
            edge_folder = folder_path

    logger.debug("Checking if test_scripts folder and chrome folder contains the same files.")

    if utils.check_if_two_folder_contain_same_files(root_folder, chrome_folder):
        logger.error("The 'test_scripts' folder and 'chrome' folder contains same test script excel files. Make the files unique per folder.")
        exit("The 'test_scripts' folder and 'chrome' folder contains same test script excel files. Make the files unique per folder.")

    logger.debug("Checking if test_scripts folder and edge folder contains the same files.")

    if utils.check_if_two_folder_contain_same_files(root_folder, edge_folder):
        logger.error("The 'test_scripts' folder and 'edge' folder contains same test script excel files. Make the files unique per folder.")
        exit("The 'test_scripts' folder and 'edge' folder contains same test script excel files. Make the files unique per folder.")
    '''
    End
    '''

if __name__ == '__main__':
    """
    This script performs various operations based on the command-line arguments provided by the user. It serves as a command-line tool with the following features:

    Features:
    ---------
    1. Accepts command-line arguments to start execution, display version information, or encrypt a specified file.
    2. Enforces rules to ensure proper usage of the arguments. For example:
    - Only one argument among 'start', '--version', or '--encrypt-file' can be used at a time.
    - '--output-file' can only be used in conjunction with '--encrypt-file'.
    3. Handles the encryption of files while checking the validity of input files and specifying an output file name.
    4. Displays version information ('Version: 3.0') if the '--version' argument is used.
    5. When 'start' is chosen:
    - Loads configurations from 'start.properties'.
    - Deletes specified directories/files and creates folders for storing test results and recordings.
    - Validates the contents of the 'test_scripts' folder and checks for duplicate files in 'chrome' and 'edge' subdirectories.
    6. Identifies files named 'testscript.xlsx' in the 'test_scripts', 'chrome', or 'edge' folders:
    - Validates if the file name starts with 'ts' (case insensitive).
    - Executes test scripts based on the browser specified by the folder name ('chrome', 'edge', or dynamic selection from 'test_scripts').
    - Utilizes multi-process handling for execution and recording, if applicable.
    7. Generates a test summary PDF after completing the execution.
    8. Process 'testscript.xlsx' files in specified folders ('chrome', 'edge', or 'test_scripts'): The script dynamically handles execution based on folder type and file naming conventions.
    9. This script uses comprehensive logging to track progress and errors throughout its execution.

    How to Use:
    -----------
    - Run the script with the desired arguments:
    * `start`: Begin execution and process configurations defined in 'start.properties'.
    * `--version`: Display version information.
    * `--encrypt-file`: Encrypt a specified file. Use '--output-file' to specify the name of the output file (optional).
    - Ensure valid usage and adherence to rules for argument combinations.

    Dependencies:
    -------------
    - argparse: For command-line argument parsing.
    - os, Path, and utils modules: To handle file and folder operations.
    - LoggerConfig: For logging actions and events during execution.
    - ConfigReader and Properties classes: To read and process configurations from 'start.properties'.
    - re: For regular expression matching.

    Examples:
    ---------
    - Start the execution:
    python runner.py start
    - Display version information:
    python runner.py --version
    - Encrypt a file and specify an output file name:
    python runner.py --encrypt-file input.txt --output-file encrypted.txt
    -
    """
    freeze_support()
    lock = Lock()
    # Create a shared log queue
    log_queue = Queue()

    # Initialize logger config and start the listener
    logger_config = LoggerConfig(log_queue=log_queue)
    listener = logger_config.start_listener()
    logger = logger_config.logger
    
    utils = Utils(logger)
    prm = PdfReportManager(logger)
    
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
    # Count how many arguments are provided
    active_args = sum(bool(arg) for arg in [args.start, args.start_parallel, args.version, args.encrypt_file, args.help_html])

    if active_args > 1:
        logger.error("Only one of '--start', --start-parallel, '--version', '--encrypt-file' or '--help-html' can be used at a time.")
        exit("Only one of '--start', --start-parallel, '--version', '--encrypt-file' or '--help-html' can be used at a time.")

    if args.output_file and not args.encrypt_file:
        logger.error("'--output-file' can only be used with '--encrypt-file'.")
        exit("Error: '--output-file' can only be used with '--encrypt-file'.")
        
    if args.help_html:
        html_content = utils.decrypt_file("enc_help_doc.enc")
        # Create a temporary file without deleting it afterward
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as temp_file:
            temp_file.write(html_content)
            temp_file.flush()
            temp_file_path = temp_file.name

        # Open the temporary file in the default browser
        webbrowser.open(f"file://{temp_file_path}")
        logger.debug(f"Temporary file created at: {temp_file_path}")
        logger.debug("Please close the browser manually when you're done.")

    if args.encrypt_file:
        logger.debug("Started encrypting file " + args.encrypt_file + ".")
        if not os.path.isfile(args.encrypt_file):
            logger.error("The provided input is not a valid file.")
            exit("Error: The provided input is not a valid file.")
        else:
            output_file = args.output_file or "default_encrypted_file"
            utils.encrypt_file(str(args.encrypt_file), str(output_file))
            logger.debug(f"Finished encrypting file {args.encrypt_file} to {output_file}")
            exit()
    
    if args.version and not(args.start):
        logger.debug("Version: 3.0")
        exit("Version: 3.0")
    
    if args.start and args.version is False:
        st = time.time()
        check_before_start()
        logger.debug("Loading 'start.properties' file.")

        runner_config_reader = ConfigReader("start.properties")
        run_headless = True if str(runner_config_reader.get_property('Browser_Settings', 'Headless', fallback='No')).lower() == 'yes' else False
        run_in_grid =  str(runner_config_reader.get_property('SGrid', 'run_in_selenium_grid', fallback='No')).lower()
        run_in_appium =  str(runner_config_reader.get_property('Appium', 'run_in_appium_grid', fallback='No')).lower()

        logger.debug("Gathering all files present in the test_scripts folder.")
        
        generic_path = os.path.join(".", "test_scripts")

        for x in utils.get_absolute_file_paths_in_dir(generic_path):
            logger.debug("Getting the file path " + x + ".")
            logger.debug("Checking if the file path contains 'testscript.xlsx' in the end.")

            if "testscript.xlsx" in x:
                logger.debug("The file path " + x + " contains 'testscript.xlsx' in the end.")
                logger.debug("Checking if the file name starts with 'ts' (case insensitive).")

                p = re.compile('^ts', re.I)
                if p.match(os.path.basename(x)):
                    logger.debug("The file name " + os.path.basename(x) + " starts with 'ts' (case insensitive).")
                    logger.debug("Checking if the file " + os.path.basename(x) + " is present in chrome or edge folder.")
                    if os.path.dirname(x).split(os.sep)[-1].lower() == 'chrome':
                        logger.debug("The file " + os.path.basename(x) + " is present in chrome folder. Launching the execution of test script on chrome browser.")
                        proc1 = Process(target=start_runner,args=(x, log_queue, lock, 'chrome', ))
                        proc1.start()
                        # time.sleep(5)
                        proc2 = None
                        if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                            logger.debug("Starting the execution recording.")

                            # proc2 = Process(target=take_recording(proc1, x.split("\\")[-1].replace("testscript.xlsx", "")))
                            proc2 = Process(target=take_recording(proc1, os.path.basename(x).replace("testscript.xlsx", "")))

                            # print(proc1.is_alive())
                            proc2.start()

                        proc1.join()
                        if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                            proc2.join()
                    elif os.path.dirname(x).split(os.sep)[-1].lower() == 'edge':
                        logger.debug("The file " + os.path.basename(x) + " is present in edge folder. Launching the execution of test script on edge browser.")
                        proc1 = Process(target=start_runner, args=(x, log_queue, lock, 'edge',))
                        proc1.start()
                        # time.sleep(5)
                        proc2 = None
                        if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                            logger.debug("Starting the execution recording.")
                            # proc2 = Process(target=take_recording(proc1, x.split("\\")[-1].replace("testscript.xlsx", "")))
                            proc2 = Process(target=take_recording(proc1, os.path.basename(x).replace("testscript.xlsx", "")))

                            # print(proc1.is_alive())
                            proc2.start()

                        proc1.join()
                        if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                            proc2.join()
                    elif os.path.dirname(x).split(os.sep)[-1].lower() == 'test_scripts':
                        logger.debug("The file " + os.path.basename(x) + " is present in test_scripts folder. Launching the execution and browser will be choosen from test script.")
                        proc1 = Process(target=start_runner, args=(x,log_queue, lock,))
                        proc1.start()
                        # time.sleep(5)
                        proc2 = None
                        if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                            logger.debug("Starting the execution recording.")
                            #proc2 = Process(target=take_recording(proc1, x.split("\\")[-1].replace("testscript.xlsx", "")))
                            proc2 = Process(target=take_recording(proc1, os.path.basename(x).replace("testscript.xlsx", "")))

                            # print(proc1.is_alive())
                            proc2.start()

                        proc1.join()
                        if not run_headless and run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                            proc2.join()
        et = time.time()

        # get the execution time
        elapsed_time = round(et - st)
        logger.info(utils.format_elapsed_time(elapsed_time))
        


        asyncio.run(prm.generate_test_summary_pdf())
    
    if args.start_parallel and args.version is False:
        st = time.time()
        check_before_start()
        logger.debug("Loading 'start.properties' file.")

        runner_config_reader = ConfigReader("start.properties")
        run_headless = True if str(runner_config_reader.get_property('Browser_Settings', 'Headless', fallback='No')).lower() == 'yes' else False
        run_in_grid =  True if str(runner_config_reader.get_property('SGrid', 'run_in_selenium_grid', fallback='No')).lower() == 'yes' else False
        run_in_appium =  True if str(runner_config_reader.get_property('Appium', 'run_in_appium_grid', fallback='No')).lower() == 'yes' else False
        number_threads =  int(runner_config_reader.get_property('Parallel', 'NoThreads', fallback='5'))
        
        if number_threads > 5:
            exit("number of threads cannot be more than 5")
        
        if not run_headless and not run_in_grid:
            logger.error("Parallel execution can only be run in headless mode.")
            exit("Parallel execution can only be run in headless mode.")

        logger.debug("Gathering all files present in the test_scripts folder.")
        
        generic_path = os.path.join(".", "test_scripts")        

        processes = []

        for x in utils.get_absolute_file_paths_in_dir(generic_path):
            logger.debug("Getting the file path " + x + ".")
            logger.debug("Checking if the file path contains 'testscript.xlsx' in the end.")

            if "testscript.xlsx" in x:
                logger.debug("The file path " + x + " contains 'testscript.xlsx' in the end.")
                logger.debug("Checking if the file name starts with 'ts' (case insensitive).")

                p = re.compile(r'^ts[a-zA-Z0-9]*_testscript\.xlsx$', re.I)
                if p.match(os.path.basename(x)):
                    logger.debug("The file name " + os.path.basename(x) + " starts with 'ts' (case insensitive).")
                    logger.debug("Checking if the file " + os.path.basename(x) + " is present in chrome or edge folder.")
                    if os.path.dirname(x).split(os.sep)[-1].lower() == 'chrome':
                        logger.debug("The file " + os.path.basename(x) + " is present in chrome folder. Launching the execution of test script on chrome browser.")
                        processes.append(Process(target=start_runner,args=(x,log_queue, lock, 'chrome',)))
                    elif os.path.dirname(x).split(os.sep)[-1].lower() == 'edge':
                        logger.debug("The file " + os.path.basename(x) + " is present in edge folder. Launching the execution of test script on edge browser.")
                        processes.append(Process(target=start_runner,args=(x,log_queue, lock, 'edge',)))
                    elif os.path.dirname(x).split(os.sep)[-1].lower() == 'test_scripts':
                        logger.debug("The file " + os.path.basename(x) + " is present in test_scripts folder. Launching the execution and browser will be choosen from test script.")
                        processes.append(Process(target=start_runner, args=(x,log_queue, lock,)))
        
        # Start processes in batches of 5
        for batch_start in range(0, len(processes), 5):
            batch = processes[batch_start:batch_start + 5]  # Create batches of 5 processes

            for process in batch:
                process.start()

            # Wait for all processes in the batch to complete
            for process in batch:
                process.join()

        et = time.time()

        # get the execution time
        elapsed_time = round(et - st)
        logger.info(utils.format_elapsed_time(elapsed_time))
        
        asyncio.run(prm.generate_test_summary_pdf())
    
    log_queue.put(None)  # Signal to stop the listener
    listener.stop()
    logger.info("Application ended in main method.")

    # else:
    #     logger.error("The syntax for running is 'runner.exe --start' or to check the version use 'runner.exe --version'")
    #     exit("The syntax for running is 'runner.exe --start' or to check the version use 'runner.exe --version'")
# print("thread finished...exiting")
