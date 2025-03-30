import asyncio
import re
from multiprocessing import Process, freeze_support
import argparse
import cv2
import numpy as np
import pandas as pd
import pyautogui
from jproperties import Properties
from textwrap3 import wrap
from excel_report_manager import ExcelReportManager
from kewords_manager import KeywordsManager
from pdf_report_manager import PdfReportManager
from utilities import Utils
from sys import exit
import os

utils = Utils()
prm = PdfReportManager()


def start_runner(testscript_file, launch_browser=''):
    '''
    Load the object repository
    '''
    ele_hl_tm = 1
    ele_hl_sz = 2
    ele_hl_cl = 'blue'
    configs = Properties()
    start_properties_configs = Properties()
    with open('start.properties', 'rb') as start_config_file:
        start_properties_configs.load(start_config_file)

    data_run_in_selenium_grid = str(
        start_properties_configs.get('run_in_selenium_grid').data)
    data_run_in_appium_grid = str(
        start_properties_configs.get('run_in_appium_grid').data)

    if data_run_in_selenium_grid.lower() == data_run_in_appium_grid.lower() == 'yes':
        exit(
            "In 'start.properties' file, both 'run_in_appium_grid' and 'run_in_selenium_grid' are set as 'Yes'. Only "
            "1 should be set as 'Yes'")

    with open('object_repository.properties', 'rb') as config_file:
        configs.load(config_file)

    only_delete = str(configs.get("login_uname_textbox_xpath").data)

    valid_keywords_tuple = (
        "tc_id", "tc_desc", "open_browser", "enter_url", "type", "click", "select_file", "verify_displayed_text",
        "mcnp_choose_date_from_datepicker", "wait_for_seconds", "login_jnj", "check_element_enabled",
        "check_element_disabled", "check_element_displayed", "step")
    # all_test_results_list = []
    e_report = ExcelReportManager()

    if "testscript.xlsx" in testscript_file:
        if utils.is_excel_doc(testscript_file):
            # all_steps_list = []
            # step_no = 1
            df = pd.read_excel(testscript_file,
                               dtype={"Keyword": "string", "Input1": "string",
                                      "Input2": "string",
                                      "Input3": "string"})
            check_nan_for_test_steps = df['Keyword'].isnull().values.any()

            if check_nan_for_test_steps:
                exit(
                    "The test steps column in the excel file contains empty values. Please check.")

            df1 = df.replace(np.nan, '', regex=True)
            for index, row in df1.iterrows():
                # print(index)
                if str(row["Keyword"]) not in valid_keywords_tuple:
                    exit("The keyword '" + row[
                        "Keyword"] + "' entered in keyword column in the excel file is invalid. Please"
                        " check.")
                if str(row["Keyword"]) == 'mcnp_choose_date_from_datepicker':
                    which_calender = str(row["Input2"])
                    if which_calender == 'cn_det_ed':
                        utils.check_date_format_validity(str(row["Input3"]))
                    if which_calender == 'cn_det_dd':
                        utils.check_date_range_format_validity(
                            str(row["Input3"]))

                if str(row["Keyword"]) == 'open_browser':
                    browser_given = str(row["Input3"])
                    if launch_browser == '':
                        if browser_given.lower() != 'chrome' and browser_given.lower() != 'edge':
                            exit("The input given for keyword '" +
                                 row["Keyword"] + "' in Input3 column in the excel file is invalid. It should be either 'edge' or 'chrome'. Please check.")

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
                    if not (str(row["Keyword"]) == 'tc_id'):
                        exit("The first keyword must be 'tc_id'")
                if index == 1:
                    if not (str(row["Keyword"]) == 'tc_desc'):
                        exit("The second keyword must be 'tc_desc'")
                if index == 2:
                    if not (str(row["Keyword"]) == 'step'):
                        exit("The third keyword must be 'step'")
                if index == 3:
                    if not (str(row["Keyword"]) == 'open_browser'):
                        exit("The fourth keyword must be 'open_browser'")
                if index == 4:
                    if not (str(row["Keyword"]) == 'enter_url'):
                        exit("The fifth keyword must be 'enter_url'")

            km = KeywordsManager()
            # tca_id = ''
            # tca_desc = ''
            # tca_browser_name = ''
            # tca_browser_version = ''
            # tca_date_executed = utils.get_date_string()
            # tca_overall_status = 'Passed'
            # repo_m = PdfReportManager()
            for index, row in df1.iterrows():
                print(str(row["Keyword"]))

                if str(row["Keyword"]) == 'tc_id':
                    km.ge_tcid(str(row["Input3"]))

                if str(row["Keyword"]) == 'tc_desc':
                    km.ge_tcdesc(str(row["Input3"]))

                if str(row["Keyword"]) == 'step':
                    km.ge_step(step=str(row["Input1"]), result=str(row["Input2"]))

                if str(row["Keyword"]) == 'wait_for_seconds':
                    # sd.wait_for_some_time(int(row["Input3"]))
                    km.ge_wait_for_seconds(int(row["Input3"]))

                if str(row["Keyword"]) == 'open_browser':
                    try:
                        if launch_browser == '':
                            km.ge_open_browser(str(row["Input3"]))
                        else:
                            km.ge_open_browser(str(launch_browser))
                    except Exception as e:
                        print(e)
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
                        print(e)
                        break

                if str(row["Keyword"]) == 'enter_url':
                    try:
                        print("before url")
                        km.ge_enter_url(str(row["Input3"]))
                        print("inside url")
                    except Exception as e:
                        print(e)
                        break

                if str(row["Keyword"]) == 'type':
                    try:
                        if row["Input3"].lower() == 'random_notification_id':
                            km.ge_type(str(configs.get(row["Input2"]).data), "xpath",
                                       utils.generate_random_notif_id(),
                                       str(row["Input1"]))
                        else:
                            km.ge_type(str(configs.get(row["Input2"]).data), "xpath", row["Input3"],
                                       str(row["Input1"]))
                    except Exception as e:
                        print(e)
                        break

                if str(row["Keyword"]) == 'check_element_enabled':
                    try:
                        km.ge_is_element_enabled(str(configs.get(row["Input2"]).data), "xpath",
                                                 row["Input3"])
                    except Exception as e:
                        print(e)
                        break

                if str(row["Keyword"]) == 'check_element_disabled':
                    try:
                        km.ge_is_element_disabled(str(configs.get(row["Input2"]).data), "xpath",
                                                  row["Input3"])
                    except Exception as e:
                        print(e)
                        break

                if str(row["Keyword"]) == 'check_element_displayed':
                    try:
                        km.ge_is_element_displayed(str(configs.get(row["Input2"]).data), "xpath",
                                                   row["Input3"])
                    except Exception as e:
                        print(e)
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
                        print(e)
                        break

                if str(row["Keyword"]) == 'verify_displayed_text':
                    try:
                        km.ge_verify_displayed_text(
                            str(configs.get(row["Input2"]).data),
                            "xpath", row["Input3"], str(row["Input1"]))
                    except Exception as e:
                        print(e)
                        break

                if str(row["Keyword"]) == 'click':
                    try:
                        km.ge_click(str(configs.get(row["Input2"]).data), "xpath",
                                    str(row["Input1"]))
                    except Exception as e:
                        print(e)
                        break

                if str(row["Keyword"]) == 'select_file':
                    try:
                        km.ge_select_file(str(configs.get(row["Input2"]).data), "xpath",
                                          str(row["Input3"]))
                    except Exception as e:
                        print(e)
                        break

            # test_result = [km.repo_m.tc_id, "\n".join(wrap(km.repo_m.test_description, width=110)),
            #                km.repo_m.overall_status_text,
            #                km.repo_m.browser_img_alt + " " + km.repo_m.browser_version, km.repo_m.executed_date]
            test_result = [km.repo_m.tc_id, km.repo_m.test_description,km.repo_m.overall_status_text, km.repo_m.browser_img_alt + " " + km.repo_m.browser_version, km.repo_m.executed_date]
            e_report.add_row(test_result)

            km.ge_close()


def take_recording(process_name: Process, record_name):
    try:
        # time.sleep(30)
        # display screen resolution, get it using pyautogui itself
        SCREEN_SIZE = tuple(pyautogui.size())
        # define the codec
        # fourcc = cv2.VideoWriter_fourcc(*"XVID")
        fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        # frames per second
        fps = 60.0
        # create the video write object
        out = cv2.VideoWriter(
            utils.get_test_recordings_folder() + "\\" + record_name +
            utils.get_datetime_string() + ".mp4", fourcc,
            fps, (SCREEN_SIZE))
        # the time you want to record in seconds
        record_seconds = 10

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
    except:
        pass


if __name__ == '__main__':
    freeze_support()
    parser = argparse.ArgumentParser()
    parser.add_argument("start", type=str, nargs='?',
                        help="start the execution")
    parser.add_argument(
        "--version", help="Display the Version", action="store_true")
    parser.add_argument("--encrypt-file", help="Encrypts the file", type=str)
    parser.add_argument("--output-file", help="Specify the output file name", type=str)
    args = parser.parse_args()
    # Count how many arguments are provided
    active_args = sum(bool(arg) for arg in [args.start, args.version, args.encrypt_file])

    if active_args > 1:
        exit("Error: Only one of 'start', '--version', or '--encrypt-file' can be used at a time.")
    
    if args.output_file and not args.encrypt_file:
        exit("Error: '--output-file' can only be used with '--encrypt-file'.")
        
    if args.encrypt_file:
        if not os.path.isfile(args.encrypt_file):
            exit("Error: The provided input is not a valid file.")
        else:
            output_file = args.output_file or "default_encrypted_file"
            utils.encrypt_file(str(args.encrypt_file), str(output_file))
            print(f"Encrypting file {args.encrypt_file} to {output_file}")
            exit("file encrypted")
    if args.version and args.start is None:
        exit("Version: 3.0")
    if args.start is not None and args.start.lower() == 'start' and args.version is False:
        start_configs = Properties()
        with open('start.properties', 'rb') as config_file:
            start_configs.load(config_file)
        run_in_grid = str(start_configs.get('run_in_selenium_grid').data)
        run_in_appium = str(start_configs.get('run_in_appium_grid').data)
        delete_test_results_images_recordings_folders_before_start = str(
            start_configs.get('delete_test_results_images_recordings_folders_before_start').data)
        if delete_test_results_images_recordings_folders_before_start.lower() == 'yes':
            utils.delete_folder_and_contents("images")
            utils.delete_folder_and_contents("recordings")
            utils.delete_folder_and_contents("test_results")
        utils.delete_file("output.xlsx")
        utils.create_image_and_test_results_folders()

        '''
        Below code checks if there are duplicate test script excel file in '.\\test_scripts' folder and '.\\test_scripts\\chrome'
        Below code checks if there are duplicate test script excel file in '.\\test_scripts' folder and '.\\test_scripts\\edge'
        '''
        root_folder = ''
        chrome_folder = ''
        edge_folder = ''
        for folder_path in utils.get_list_str_paths_of_all_sub_directories(".\\test_scripts"):
            if folder_path.split('\\')[-1].lower() == 'test_scripts':
                root_folder = folder_path
            if folder_path.split('\\')[-1].lower() == 'chrome':
                chrome_folder = folder_path
            if folder_path.split('\\')[-1].lower() == 'edge':
                edge_folder = folder_path

        if utils.check_if_two_folder_contain_same_files(root_folder, chrome_folder):
            exit(
                "The 'test_scripts' folder and 'chrome' folder contains same test script excel files. Make the files "
                "unique per folder.")
        if utils.check_if_two_folder_contain_same_files(root_folder, edge_folder):
            exit(
                "The 'test_scripts' folder and 'edge' folder contains same test script excel files. Make the files "
                "unique per folder.")
        '''
        End
        '''
        for x in utils.get_absolute_file_paths_in_dir(".\\test_scripts"):
            if "testscript.xlsx" in x:
                p = re.compile('ts', re.I)
                if p.match(x.split('\\')[-1]):
                    if x.split('\\')[-2].lower() == 'chrome':
                        proc1 = Process(target=start_runner,
                                        args=(x, 'chrome',))
                        proc1.start()
                        # time.sleep(5)
                        proc2 = None
                        if run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                            proc2 = Process(target=take_recording(
                                proc1, x.split("\\")[-1].replace("testscript.xlsx", "")))

                            # print(proc1.is_alive())
                            proc2.start()

                        proc1.join()
                        if run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                            proc2.join()
                    elif x.split('\\')[-2].lower() == 'edge':
                        proc1 = Process(target=start_runner, args=(x, 'edge',))
                        proc1.start()
                        # time.sleep(5)
                        proc2 = None
                        if run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                            proc2 = Process(target=take_recording(
                                proc1, x.split("\\")[-1].replace("testscript.xlsx", "")))

                            # print(proc1.is_alive())
                            proc2.start()

                        proc1.join()
                        if run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                            proc2.join()
                    elif x.split('\\')[-2].lower() == 'test_scripts':
                        proc1 = Process(target=start_runner, args=(x,))
                        proc1.start()
                        # time.sleep(5)
                        proc2 = None
                        if run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                            proc2 = Process(target=take_recording(
                                proc1, x.split("\\")[-1].replace("testscript.xlsx", "")))

                            # print(proc1.is_alive())
                            proc2.start()

                        proc1.join()
                        if run_in_grid.lower() != 'yes' and run_in_appium.lower() != 'yes':
                            proc2.join()
                            
        asyncio.run(prm.generate_test_summary_pdf())
        
    else:
        exit("The syntax for running is 'runner.exe start' or to check the version use 'runner.exe --version'")
# print("thread finished...exiting")
