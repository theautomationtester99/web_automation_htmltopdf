import filecmp
import os
import platform
import sys
from logger_config import LoggerConfig
import numpy as np
import cv2
import pyautogui
from datetime import datetime
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import shutil
from io import BytesIO
import base64
from cryptography.fernet import Fernet
import pandas as pd


class Utils:
    def __init__(self):
        self.logger = LoggerConfig().logger
        self.date_str = self.get_date_string()
        # self.images_folder = os.path.abspath("images\\" + self.date_str)
        # self.recordings_folder = os.path.abspath("recordings\\" + self.date_str)
        # self.test_results_folder = os.path.abspath("test_results\\" + self.date_str)
        # # self.create_image_and_test_results_folders()        
        self.images_folder = os.path.abspath(os.path.join("images", self.date_str))
        self.recordings_folder = os.path.abspath(os.path.join("recordings", self.date_str))
        self.test_results_folder = os.path.abspath(os.path.join("test_results", self.date_str))

    def get_test_result_folder(self):
        return self.test_results_folder

    def get_test_recordings_folder(self):
        return self.recordings_folder

    def delete_file(self, file_path):
        self.is_not_used()
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            self.logger.debug("File does not exists")

    def delete_folder_and_contents(self, folder_path):
        self.is_not_used()
        try:
            shutil.rmtree(folder_path)
            self.logger.debug('Folder and its content removed')  # Folder and its content removed
        except:
            self.logger.debug('Folder not deleted')

    def generate_random_notif_id(self):
        self.is_not_used()
        logged_user_name = self.get_logged_in_user_name()
        date_time_string = self.get_datetime_string()
        date_string = self.get_date_string()
        user_name_length = len(logged_user_name)
        if user_name_length >= 10:
            logged_user_name = logged_user_name[:9]
            random_id = logged_user_name + "_" + date_string[:5] + date_time_string[-5:]
        else:
            random_id = logged_user_name + "_" + date_string[:5] + date_time_string[-(14 - user_name_length):]
        return random_id

    def get_logged_in_user_name(self):
        self.is_not_used()
        return os.getlogin()

    def make_string_manageable(self, input_str, length):
        self.is_not_used()
        return ' '.join(input_str[i:i + length] for i in range(0, len(input_str), length))

    def is_what_percent_of(self, num_a, num_b):
        self.is_not_used()
        try:
            return int((num_a / num_b) * 100)
        except ZeroDivisionError:
            return 0

    def count_spaces_in_string(self, input_string):
        self.is_not_used()
        return input_string.count(" ")

    def create_image_and_test_results_folders(self):
        # Check whether the specified path exists or not
        is_exist = os.path.exists(self.images_folder)
        if not is_exist:
            # Create a new directory because it does not exist
            os.makedirs(self.images_folder)
        is_exist_re = os.path.exists(self.recordings_folder)
        if not is_exist_re:
            # Create a new directory because it does not exist
            os.makedirs(self.recordings_folder)
        is_exist_tr = os.path.exists(self.test_results_folder)
        if not is_exist_tr:
            # Create a new directory because it does not exist
            os.makedirs(self.test_results_folder)

    def get_resource_path(self, relative_path):
        self.is_not_used()
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    def get_datetime_string(self):
        self.is_not_used()
        now = datetime.now()
        date_time = now.strftime("%d%b%Y_%I%M%S%f")
        # self.logger.debug("date and time:", date_time)
        return date_time

    def get_date_string(self):
        self.is_not_used()
        now = datetime.now()
        date_time = now.strftime("%d%b%Y")
        # self.logger.debug("date and time:", date_time)
        return date_time

    def take_page_screenshot_full(self, image_name_start):
        date_time_str = self.get_datetime_string()
        image_name = image_name_start + "_" + date_time_str
        full_img_path = self.images_folder + "\\" + image_name + ".png"
        # take screenshot using pyautogui
        image = pyautogui.screenshot()

        # since the pyautogui takes as a
        # PIL(pillow) and in RGB we need to
        # convert it to numpy array and BGR
        # so we can write it to the disk
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        cv2.imwrite(full_img_path, image)
        # self.logger.debug(os.path.abspath(full_img_path))
        return full_img_path

    def take_screenshot_full(self, image_name_start):
        date_time_str = self.get_datetime_string()
        image_name = image_name_start + "_" + date_time_str
        full_img_path = self.images_folder + "\\" + image_name + ".png"
        # take screenshot using pyautogui
        image = pyautogui.screenshot()

        # since the pyautogui takes as a
        # PIL(pillow) and in RGB we need to
        # convert it to numpy array and BGR
        # so we can write it to the disk
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        cv2.imwrite(full_img_path, image)
        # self.logger.debug(os.path.abspath(full_img_path))
        return full_img_path
    
    def take_screenshot_full_src_tag(self):
        # Take a screenshot using pyautogui
        screenshot = pyautogui.screenshot()

        # Convert the screenshot to a bytes buffer in PNG format
        buffered = BytesIO()
        screenshot.save(buffered, format="PNG")
        
        # Encode the bytes buffer to a base64 string
        base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # Return the base64 image code
        return f"data:image/png;base64,{base64_image}"

    def add_date_time_watermark_to_image(self, file_name_path, text):
        self.is_not_used()
        image = Image.open(file_name_path)
        font = ImageFont.truetype("arial.ttf", 36)
        width, height = image.size
        draw = ImageDraw.Draw(image)
        text_width = draw.textlength(text, font)

        # calculate the x,y coordinates of the text
        margin = 20
        x = width - text_width - margin
        y = height - margin

        # add Watermark
        # (0,0,0)-black color text
        draw.text((x, y), text, fill=(0, 0, 0), font=font, anchor='ms')
        image.save(file_name_path)

    def is_not_used(self):
        pass

    def get_absolute_file_paths_in_dir(self, directory):
        self.is_not_used()
        for dir_path, _, filenames in os.walk(directory):
            for f in filenames:
                yield os.path.abspath(os.path.join(dir_path, f))

    def get_list_str_paths_of_all_sub_directories(self, folder):
        str_lst = []
        self.is_not_used()
        absolute_path = os.path.abspath(folder)
        str_lst.append(absolute_path)
        for file in os.listdir(absolute_path):
            d = os.path.join(absolute_path, file)
            if os.path.isdir(d):
                str_lst.append(d)
        return str_lst

    def check_if_two_folder_contain_same_files(self, folder1, folder2):
        self.is_not_used()
        result = filecmp.dircmp(folder1, folder2)
        a = result.common
        if not a:
            return False
        else:
            return True

    def is_excel_doc(self, input_file):
        self.is_not_used()
        excel_signatures = [
            ('xlsx', b'\x50\x4B\x05\x06', 2, -22, 4),
            ('xls', b'\x09\x08\x10\x00\x00\x06\x05\x00', 0, 512, 8),  # Saved from Excel
            ('xls', b'\x09\x08\x10\x00\x00\x06\x05\x00', 0, 1536, 8),  # Saved from LibreOffice Calc
            ('xls', b'\x09\x08\x10\x00\x00\x06\x05\x00', 0, 2048, 8)  # Saved from Excel then saved from Calc
        ]

        for sigType, sig, whence, offset, size in excel_signatures:
            with open(input_file, 'rb') as f:
                f.seek(offset, whence)
                file_bytes = f.read(size)

                if file_bytes == sig:
                    return True

        return False

    def get_mtn_number(self, x):
        months = {
            'January': 1,
            'February': 2,
            'March': 3,
            'April': 4,
            'May': 5,
            'June': 6,
            'July': 7,
            'August': 8,
            'September': 9,
            'October': 10,
            'November': 11,
            'December': 12
        }
        self.is_not_used()
        try:
            ez = months[x]
            self.logger.debug(ez)
            return ez
        except:
            raise ValueError('Not a month')

    def check_if_file_exists(self, path):
        self.is_not_used()
        does_file_exists = os.path.isfile(path)
        return does_file_exists

    # utils = Utils()
    # self.logger.debug(utils.take_screenshot_full('tc001'))

    # date_str = get_date_string()
    # create_image_folder(os.path.abspath("images\\" + date_str))
    # take_screenshot_full("images\\" + date_str, "tc001")
    def check_date_format_validity(self, entered_date):
        self.is_not_used()
        dts = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15",
               "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
               "31"]
        mts = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
               "October", "November", "December"]
        yrs = ["2019", "2020", "2021", "2022", "2023", "2024", "2025"]
        input_date = entered_date
        # checking validity of input date as DD MMMM YYYY
        input_date_split_list = input_date.split()
        if len(input_date_split_list) != 3:
            exit("Check the date entered for the keyword 'choose_date_from_datepicker'. It should be like "
                 "the example 01 December 2022")
        if len(input_date_split_list[0]) != 2:
            exit("Check the date entered for the keyword 'choose_date_from_datepicker'. It should be like "
                 "the example 01 December 2022")
        if len(input_date_split_list[2]) != 4:
            exit("Check the date entered for the keyword 'choose_date_from_datepicker'. It should be like "
                 "the example 01 December 2022")
        if input_date_split_list[0] not in dts:
            exit("Check the date entered for the keyword 'choose_date_from_datepicker'. It should be like "
                 "the example 01 December 2022")
        if input_date_split_list[1] not in mts:
            exit("Check the date entered for the keyword 'choose_date_from_datepicker'. It should be like "
                 "the example 01 December 2022")
        if input_date_split_list[2] not in yrs:
            exit("Check the date entered for the keyword 'choose_date_from_datepicker'. The year should "
                 "be between 2019 and 2025")

    def check_date_range_format_validity(self, entered_date):
        self.is_not_used()
        dts = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15",
               "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
               "31"]
        mts = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
               "October", "November", "December"]
        yrs = ["2019", "2020", "2021", "2022", "2023", "2024", "2025"]
        input_date = entered_date
        # checking validity of input date as DD MMMM YYYY
        input_date_split_list = input_date.split()
        if len(input_date_split_list) != 7:
            exit("Check the date entered for the keyword 'choose_date_from_datepicker'. It should be like "
                 "the example '01 December 2022 - 02 December 2022'")

        first_date = " ".join(input_date.split()[0:3])
        self.check_date_format_validity(first_date)

        first_date_yr = int(first_date.split()[2])
        first_date_mon = self.get_mtn_number(first_date.split()[1])
        first_date_day = int(first_date.split()[0])

        second_date = " ".join(input_date.split()[4:7])
        self.check_date_format_validity(second_date)

        second_date_yr = int(second_date.split()[2])
        second_date_mon = self.get_mtn_number(second_date.split()[1])
        second_date_day = int(second_date.split()[0])

        if first_date_yr > second_date_yr:
            exit("Check the date entered for the keyword 'choose_date_from_datepicker'. It should be like "
                 "the example '01 December 2022 - 02 December 2022' and the first date must be prior to the second date")
        elif first_date_yr == second_date_yr:
            if first_date_mon > second_date_mon:
                exit("Check the date entered for the keyword 'choose_date_from_datepicker'. It should be like "
                     "the example '01 December 2022 - 02 December 2022' and the first date must be prior to the second date")
            elif first_date_mon == second_date_mon:
                if first_date_day > second_date_day:
                    exit("Check the date entered for the keyword 'choose_date_from_datepicker'. It should be like "
                         "the example '01 December 2022 - 02 December 2022' and the first date must be prior to the "
                         "second date")

    def encrypt_file(self, file_path, output_file, encryption_key="DC3HN3PdUb5z_MyYbitSyVnPU_E_WOfZkUsYR8bWKzY="):
        # Read the file content
        with open(file_path, "r") as f:
            file_content = f.read()

        # Encrypt the file content
        fernet = Fernet(encryption_key)
        encrypted_content = fernet.encrypt(file_content.encode())

        # Save the encrypted content to a new file
        with open(output_file, "wb") as f:
            f.write(encrypted_content)

        # self.logger.debug("File encrypted successfully!")
        # return encrypted_content

    def decrypt_file(self, encrypted_file_path, decryption_key="DC3HN3PdUb5z_MyYbitSyVnPU_E_WOfZkUsYR8bWKzY="):
        # Read the encrypted file content
        with open(encrypted_file_path, "rb") as f:
            encrypted_content = f.read()

        # Decrypt the file content
        fernet = Fernet(decryption_key)
        decrypted_content = fernet.decrypt(encrypted_content).decode()

        return decrypted_content
    
    def detect_os(self):
        os_name = platform.system()
        if os_name == "Linux":
            return "Linux"
        elif os_name == "Windows":
            return "Windows"
        else:
            return f"Operating System detected: {os_name}"