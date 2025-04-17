import filecmp
import getpass
import os
from pathlib import Path
import platform
import re
import sys
import PyPDF2
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


class Utils:
    """
    A utility class that provides helper methods for logging, folder management, file operations,
    and string manipulation.

    Attributes:
        logger (Logger): Logger instance for logging messages and events.
        date_str (str): Current date string used for folder naming.
        images_folder (str): Path to the images folder.
        recordings_folder (str): Path to the recordings folder.
        test_results_folder (str): Path to the test results folder.
    """
    _instance = None  # Class-level attribute to store the single instance

    def __new__(cls, *args, **kwargs):
        """
        Ensures only one instance of the class is created.
        """
        if not cls._instance:
            cls._instance = super(Utils, cls).__new__(cls)
        return cls._instance

    def __init__(self, logger):
        """
        Initializes the Utils class by setting up logger and folder paths for images,
        recordings, and test results.
        """
        self.logger = logger
        self.date_str = self.get_date_string()
        self.date_time_str = self.get_datetime_string()
        # self.images_folder = os.path.abspath("images\\" + self.date_str)
        # self.recordings_folder = os.path.abspath("recordings\\" + self.date_str)
        # self.test_results_folder = os.path.abspath("test_results\\" + self.date_str)
        # # self.create_image_and_test_results_folders()
        self.images_folder = os.path.abspath(os.path.join("images", self.date_str))
        self.recordings_folder = os.path.abspath(os.path.join("recordings", self.date_str))
        self.test_results_folder = os.path.abspath(os.path.join("test_results", self.date_str))

    def get_test_result_folder(self):
        """
        Gets the path to the test results folder.

        Returns:
            str: The absolute path to the test results folder.
        """
        return self.test_results_folder
    
    def merge_pdfs_in_parts(self):
        folder_path = self.get_test_result_folder()
        output_base = os.path.join(folder_path, "consolidated")
        output_file_base = os.path.join(output_base, "Test_Results_" + self.get_datetime_string())
        os.makedirs(os.path.dirname(output_file_base), exist_ok=True)

        pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
        test_summary = [f for f in pdf_files if f.startswith('Test_Summary_Results')]
        
        grouped_pdfs = {}
        for pdf in pdf_files:
            match = re.match(r'(QS\d+)_test_results', pdf, re.IGNORECASE)
            if match:
                prefix = match.group(1).upper()
                grouped_pdfs.setdefault(prefix, []).append(pdf)

        merge_order = test_summary + sum([grouped_pdfs[key] for key in sorted(grouped_pdfs.keys())], [])

        part_number = 1
        current_output_path = f"{output_file_base}_part{part_number}.pdf"
        pdf_writer = PyPDF2.PdfMerger()

        current_size = 0
        max_size = 100 * 1024 * 1024  # 100MB threshold

        for pdf_file in merge_order:
            pdf_writer.append(os.path.join(folder_path, pdf_file))
            
            current_size += os.path.getsize(os.path.join(folder_path, pdf_file))

            if current_size >= max_size:
                with open(current_output_path, "wb") as output_pdf:
                    pdf_writer.write(output_pdf)

                part_number += 1
                current_size = 0
                current_output_path = f"{output_file_base}_part{part_number}.pdf"
                pdf_writer = PyPDF2.PdfMerger()  # Properly reset PdfMerger

        # Save the last part
        if pdf_writer.pages:
            with open(current_output_path, "wb") as output_pdf:
                pdf_writer.write(output_pdf)

        self.logger.info(f"Merged PDFs saved in parts under: {output_base}")

    
    def get_test_recordings_folder(self):
        """
        Gets the path to the recordings folder.

        Returns:
            str: The absolute path to the recordings folder.
        """
        return self.recordings_folder

    def delete_file(self, file_path):
        """
        Deletes a file at the specified path if it exists.

        Args:
            file_path (str): The path to the file to be deleted.

        Logs:
            Debug: If the file does not exist.
        """
        self.is_not_used()
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            self.logger.debug("File does not exists")

    def delete_folder_and_contents(self, folder_path):
        """
        Deletes a folder and its contents at the specified path.

        Args:
            folder_path (str): The path to the folder to be deleted.

        Logs:
            Debug: If the folder and its contents are successfully removed or if the folder could
            not be deleted.
        """
        self.is_not_used()
        try:
            shutil.rmtree(folder_path)
            self.logger.debug('Folder and its content removed')  # Folder and its content removed
        except:
            self.logger.debug('Folder not deleted')

    def generate_random_notif_id(self):
        """
        Generates a random notification ID using the logged-in user's name,
        the current date, and the current timestamp.

        Returns:
            str: A randomly generated notification ID.
        """
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
        """
        Gets the name of the currently logged-in user.

        Returns:
            str: The name of the logged-in user.
        """
        # return os.getlogin()
        return getpass.getuser()

    def make_string_manageable(self, input_str, length):
        """
        Splits a string into manageable chunks of the specified length.

        Args:
            input_str (str): The string to be split.
            length (int): The desired length of each chunk.

        Returns:
            str: A string with chunks separated by spaces.
        """
        self.is_not_used()
        return ' '.join(input_str[i:i + length] for i in range(0, len(input_str), length))

    def is_what_percent_of(self, num_a, num_b):
        """
        Calculates what percentage `num_a` is of `num_b`.

        Args:
            num_a (int): The numerator.
            num_b (int): The denominator.

        Returns:
            int: The percentage value, or 0 if division by zero occurs.
        """
        self.is_not_used()
        try:
            return int((num_a / num_b) * 100)
        except ZeroDivisionError:
            return 0

    def count_spaces_in_string(self, input_string):
        """
        Counts the number of spaces in a given string.

        Args:
            input_string (str): The string in which spaces are to be counted.

        Returns:
            int: The number of spaces in the string.
        """
        self.is_not_used()
        return input_string.count(" ")

    def create_image_and_test_results_folders(self):
        """
        Creates directories for storing images, recordings, and test results
        if they do not already exist.

        Checks if the specified paths exist and creates new directories if necessary.

        Attributes Used:
            images_folder (str): Path to the images folder.
            recordings_folder (str): Path to the recordings folder.
            test_results_folder (str): Path to the test results folder.
        """
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
        """
        Gets the absolute path to a resource, supporting PyInstaller builds.

        Args:
            relative_path (str): The relative path to the resource.

        Returns:
            str: The absolute path to the resource.
        """
        self.is_not_used()
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    def get_datetime_string(self):
        """
        Generates a formatted string representing the current date and time.

        Format:
            DayMonthYear_HourMinuteSecondMicrosecond (e.g., 04Apr2025_014238123456)

        Returns:
            str: The formatted date and time string.
        """
        self.is_not_used()
        now = datetime.now()
        date_time = now.strftime("%d%b%Y_%I%M%S%f")
        # self.logger.debug("date and time:", date_time)
        return date_time

    def get_date_string(self):
        """
        Generates a formatted string representing the current date.

        Format:
            DayMonthYear (e.g., 04Apr2025)

        Returns:
            str: The formatted date string.
        """
        self.is_not_used()
        now = datetime.now()
        date_time = now.strftime("%d%b%Y")
        # self.logger.debug("date and time:", date_time)
        return date_time

    def take_page_screenshot_full(self, image_name_start):
        """
        Takes a full-page screenshot and saves it as a PNG file.

        Args:
            image_name_start (str): The prefix for the screenshot's file name.

        Returns:
            str: The absolute path to the saved screenshot file.
        """
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
        """
        Takes a screenshot of the full screen and saves it as a PNG file.

        Args:
            image_name_start (str): The prefix for the screenshot's file name.

        Returns:
            str: The absolute path to the saved screenshot file.
        """
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

    # def take_screenshot_full_src_tag(self):
    #     """
    #     Takes a screenshot of the full screen and returns it as a base64-encoded string
    #     in PNG format.

    #     Returns:
    #         str: The base64-encoded string representing the screenshot in PNG format.
    #     """
    #     # Take a screenshot using pyautogui
    #     screenshot = pyautogui.screenshot()

    #     # Convert the screenshot to a bytes buffer in PNG format
    #     buffered = BytesIO()
    #     screenshot.save(buffered, format="PNG")

    #     # Encode the bytes buffer to a base64 string
    #     base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

    #     # Return the base64 image code
    #     return f"data:image/png;base64,{base64_image}"

    def take_screenshot_full_src_tag(self, file_name: str):
        """
        Takes a screenshot of the full screen, saves it under the appropriate folder structure,
        and returns it as a base64-encoded string in PNG format.

        Args:
            file_name (str): The string used to create folder structure and name the saved image file.

        Returns:
            str: The base64-encoded string representing the screenshot in PNG format.
        """
        # Split the file_name to create the folder structure
        parts = file_name.split("_")
        if len(parts) < 3:
            raise ValueError("Invalid file_name format. Expected format: 'tc1_chrome_001'")

        # Define the base directory and folder structure
        base_dir = self.images_folder
        folder_1 = parts[0]  # e.g., 'tc1'
        folder_2 = parts[1]  # e.g., 'chrome'
        image_name = f"{file_name}.png"  # e.g., 'tc1_chrome_001.png'

        # Create the folders if they don't exist
        folder_path = os.path.join(base_dir, folder_1, folder_2)
        os.makedirs(folder_path, exist_ok=True)

        # Define the full file path
        file_path = os.path.join(folder_path, image_name)

        # Take a screenshot using pyautogui
        screenshot = pyautogui.screenshot()

        # Save the screenshot as a PNG file
        screenshot.save(file_path, format="PNG")

        # Convert the screenshot to a bytes buffer in PNG format
        buffered = BytesIO()
        screenshot.save(buffered, format="PNG")

        # Encode the bytes buffer to a base64 string
        base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # Return the base64 image code
        return f"data:image/png;base64,{base64_image}"

    def add_date_time_watermark_to_image(self, file_name_path, text):
        """
        Adds a date and time watermark to the bottom-right corner of an image.

        Args:
            file_name_path (str): The path to the image file to which the watermark will be added.
            text (str): The text to use as the watermark.

        Details:
            - The watermark is rendered in black color with a font size of 36.
            - It is positioned with a margin of 20 pixels from the right and bottom edges.
        """
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
        """
        Generates absolute file paths for all files within a directory, including its subdirectories.

        Args:
            directory (str): The path to the directory.

        Yields:
            str: Absolute file paths of the files within the directory and its subdirectories.
        """
        self.is_not_used()
        for dir_path, _, filenames in os.walk(directory):
            for f in filenames:
                yield os.path.abspath(os.path.join(dir_path, f))

    def get_list_abs_paths_of_dir_and_sub_dir(self, folder):
        """
        Retrieves a list of absolute paths for all subdirectories within a given folder.

        Args:
            folder (str): The path to the folder.

        Returns:
            list: A list containing the absolute path of the folder and its subdirectories.
        """
        str_lst = []
        self.is_not_used()
        absolute_path = os.path.abspath(folder)
        str_lst.append(absolute_path)
        for file in os.listdir(absolute_path):
            d = os.path.join(absolute_path, file)
            if os.path.isdir(d):
                str_lst.append(d)
        return str_lst
    
    def extract_first_x_chars(self, input_string, x):
        """
        Extracts the first x characters from the given string.

        Args:
            input_string (str): The string to extract characters from.
            x (int): The number of characters to extract.

        Returns:
            str: The first x characters of the input string.
        """
        if not isinstance(input_string, str):
            raise ValueError("Input must be a string.")
        if not isinstance(x, int) or x < 0:
            raise ValueError("The number of characters to extract must be a non-negative integer.")
        
        return input_string[:x]

    def get_abs_path_folder_matching_string_within_folder(self, root_folder_path, search_folder_name: str) -> str:
        """
        Processes the test_scripts folder to identify subfolders like 'chrome', 'edge', or 'test_scripts'.

        Args:
            folder_name (str): The name of the folder to process (e.g., 'chrome', 'edge', 'test_scripts').
            utils (Utils): Utility class instance for file operations.

        Returns:
            str: The path to the folder if found, otherwise an empty string.
        """
        for folder_path in self.get_list_abs_paths_of_dir_and_sub_dir(root_folder_path):
            if Path(folder_path).name.lower() == search_folder_name.lower():
                return folder_path
        return ''

    def check_if_two_folder_contain_same_files(self, folder1, folder2):
        """
        Compares two folders to check if they contain the same files.

        Args:
            folder1 (str): Path to the first folder.
            folder2 (str): Path to the second folder.

        Returns:
            bool: True if the folders contain common files, False otherwise.
        """
        self.is_not_used()
        result = filecmp.dircmp(folder1, folder2)
        a = result.common
        if not a:
            return False
        else:
            return True

    def is_excel_doc(self, input_file):
        """
        Determines if a given file is an Excel document by analyzing its file signature.

        Args:
            input_file (str): Path to the file to be checked.

        Returns:
            bool: True if the file matches known Excel file signatures, False otherwise.
        """
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
        """
        Retrieves the numerical representation of a given month name.

        Args:
            x (str): Name of the month (e.g., 'January').

        Returns:
            int: Numerical representation of the month (1 for January, 2 for February, etc.).

        Raises:
            ValueError: If the input is not a valid month name.
        """
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
        """
        Checks if a file exists at the specified path.

        Args:
            path (str): Path to the file.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        self.is_not_used()
        does_file_exists = os.path.isfile(path)
        return does_file_exists

    # utils = Utils()
    # self.logger.debug(utils.take_screenshot_full('tc001'))

    # date_str = get_date_string()
    # create_image_folder(os.path.abspath("images\\" + date_str))
    # take_screenshot_full("images\\" + date_str, "tc001")
    def check_date_format_validity(self, entered_date):
        """
        Validates the format of the entered date as 'DD MMMM YYYY'.

        Args:
            entered_date (str): The date to validate, in the format 'DD MMMM YYYY'.

        Exits:
            If the date format is invalid or if the date components do not match
            the expected range of valid days, months, or years.

        Note:
            The valid years range from 2019 to 2025.
        """
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
        """
        Validates the format of a date range as 'DD MMMM YYYY - DD MMMM YYYY'.

        Args:
            entered_date (str): The date range to validate, in the format
                                'DD MMMM YYYY - DD MMMM YYYY'.

        Exits:
            If the date range format is invalid, or if the first date is not
            prior to the second date.

        Note:
            The valid years range from 2019 to 2025.
        """
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
        """
        Encrypts a file's content and saves the encrypted content to a new file.

        Args:
            file_path (str): Path to the file to be encrypted.
            output_file (str): Path to save the encrypted file.
            encryption_key (str): Encryption key to use for encryption (default provided).

        Details:
            Uses the Fernet symmetric encryption to secure the file content.
        """
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
        """
        Decrypts the content of an encrypted file.

        Args:
            encrypted_file_path (str): Path to the encrypted file.
            decryption_key (str): Key used to decrypt the file content (default provided).

        Returns:
            str: The decrypted content as a string.
        """
        # Read the encrypted file content
        with open(encrypted_file_path, "rb") as f:
            encrypted_content = f.read()

        # Decrypt the file content
        fernet = Fernet(decryption_key)
        decrypted_content = fernet.decrypt(encrypted_content).decode()

        return decrypted_content

    def detect_os(self):
        """
        Detects the operating system on which the script is running.

        Returns:
            str: The name of the operating system ('Linux', 'Windows', or others).
        """
        os_name = platform.system()
        if os_name == "Linux":
            return "Linux"
        elif os_name == "Windows":
            return "Windows"
        else:
            return f"Operating System detected: {os_name}"

    def format_number_zeropad_4char(self, number):
        """
        Converts an integer to a zero-padded string with a length of 4 characters.

        Args:
            number (int): The integer to be formatted.

        Returns:
            str: A string representation of the integer with leading zeros,
                ensuring a total length of 4 characters.

        Example:
            format_number(1) -> "0001"
            format_number(123) -> "0123"
        """
        return f"{number:04}"

    def format_elapsed_time(self, elapsed_time):
        milliseconds = int((elapsed_time - int(elapsed_time)) * 1000)
        seconds = int(elapsed_time) % 60
        minutes = (int(elapsed_time) // 60) % 60
        hours = int(elapsed_time) // 3600

        return f"{hours}hrs:{minutes}min:{seconds}sec:{milliseconds}ms"