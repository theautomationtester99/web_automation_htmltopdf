import base64
import calendar
import filecmp
import getpass
import glob
import json
import os
import platform
import re
import shutil
import smtplib
import socket
import sys
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ftplib import FTP
from io import BytesIO
from pathlib import Path
import cv2
import numpy as np
import psutil
import pyautogui
import PyPDF2
from cryptography.fernet import Fernet
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from PIL import Image, ImageDraw, ImageFont
from config import start_properties
from constants import SCOPES, SERVICE_ACCOUNT_FILE


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
        if not hasattr(self, "_initialized"):
            self._initialized = True  # Prevents re-initialization
            self.logger = logger
            self.date_str = self.get_date_string()
            self.date_time_str = self.get_datetime_string()
            self.time_str = self.get_time_string()
            self.hostname = self.sanitize_string(self.get_hostname())
            # self.images_folder = os.path.abspath("images\\" + self.date_str)
            # self.recordings_folder = os.path.abspath("recordings\\" + self.date_str)
            # self.test_results_folder = os.path.abspath("test_results\\" + self.date_str)
            # # self.create_image_and_test_results_folders()
            # self.images_folder = os.path.abspath(os.path.join("images", self.date_str))
            # self.recordings_folder = os.path.abspath(os.path.join("recordings", self.date_str))
            if getattr(sys, 'frozen', False):  # Check if running as a frozen executable
                script_dir = os.path.dirname(sys.executable)  # Use the directory of the executable
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))  # Normal script behavior

            generic_path = os.path.join(script_dir, "test_results")
            self.test_results_folder = os.path.abspath(os.path.join(generic_path, self.hostname, self.date_str, self.time_str))
            self.recordings_folder = os.path.abspath(os.path.join(self.test_results_folder, "recordings"))
            self.images_folder = os.path.abspath(os.path.join(self.test_results_folder, "images"))

    def get_test_result_folder(self):
        """
        Gets the path to the test results folder.

        Returns:
            str: The absolute path to the test results folder.
        """
        return self.test_results_folder

    def stop_driver_processes(self):
        driver_names = ["msedgedriver", "chromedriver","msedgedriver.exe", "chromedriver.exe", "chromerunnerprocess", "edgerunnerprocess", "recordingprocess", "chrome", "msedge", "firefox", "geckodriver", "chromerunnerprocess.exe", "edgerunnerprocess.exe", "recordingprocess.exe"]

        for process in psutil.process_iter(attrs=["pid", "name"]):
            try:
                process_name = process.info["name"].lower()
                self.logger.warning(f"Process name: {process_name}")
                # Skip if the process is 'msedgewebview'
                if "msedgewebview" in process_name:
                    self.logger.info(f"Skipping {process_name} (PID: {process.info['pid']})")
                    continue
                if any(driver in process_name for driver in driver_names):
                    self.logger.info(f"Terminating {process_name} (PID: {process.info['pid']})")
                    psutil.Process(process.info["pid"]).terminate()
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                self.logger.warning(f"Process already terminated: {process.info.get('name', 'Unknown')} (PID: {process.info.get('pid', 'Unknown')})")
            except psutil.AccessDenied:
                self.logger.error(f"Access denied for process: {process.info.get('name', 'Unknown')} (PID: {process.info.get('pid', 'Unknown')})")
            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")

    # FTP upload related methods
    ##################################################################################

    def connect_to_ftp(self, host, port, username, password):
        """Connect to FTP server and return the FTP object."""
        ftp = FTP()
        ftp.connect(host, port)
        ftp.login(username, password)
        self.logger.info(f"Connected to FTP server: {host}:{port}")
        return ftp

    def ensure_remote_dir_exists(self, ftp, remote_dir):
        """Ensure the remote directory exists, create it if necessary."""
        self.logger.info(f"Ensuring remote directory exists: {remote_dir}")
        try:
            ftp.cwd(remote_dir)
            self.logger.info(f"Changed to remote directory: {remote_dir}")
        except Exception:
            # ftp.mkd(remote_dir)
            parts = remote_dir.split('/')
            current_path = ""
            for part in parts:
                if part:  # Skip empty parts (e.g., leading '/')
                    current_path += f"/{part}"
                    try:
                        ftp.cwd(current_path)  # Check if the directory exists
                    except Exception:
                        ftp.mkd(current_path)
            self.logger.info(f"Created remote directory: {remote_dir}")
            ftp.cwd(remote_dir)
            self.logger.info(f"Changed to remote directory: {remote_dir}")

    def upload_file(self, ftp, local_file, remote_file):
        """Upload a single file to the FTP server if it doesn't already exist."""
        try:
            ftp.size(remote_file)  # Check if the file exists
            self.logger.warn(f"File exists, skipping: {remote_file}")
        except Exception:
            with open(local_file, 'rb') as file:
                ftp.storbinary(f"STOR {remote_file}", file)
                self.logger.info(f"Uploaded file: {remote_file}")

    def upload_directory(self, ftp, local_dir, remote_dir):
        """Upload all files and subdirectories from a local directory."""
        self.logger.warning(f"Uploading directory: {local_dir} to {remote_dir}")
        self.ensure_remote_dir_exists(ftp, remote_dir)  # Ensure the root remote directory exists
        for item in os.listdir(local_dir):
            self.logger.warning(f"Processing item: {item}")
            local_path = os.path.join(local_dir, item)
            remote_path = f"{remote_dir}/{item}"
            # remote_path = os.path.join(remote_dir, item)
            if os.path.isdir(local_path):
                # Handle subdirectories
                # try:
                #     self.logger.info(f"Checking remote folder: {item}")
                #     ftp.cwd(item)  # Check if the remote folder exists
                # except Exception as e:
                #     self.logger.info(f"Creating remote folder: {item}")
                #     ftp.mkd(item)  # Create the folder if it doesn't exist
                # ftp.cwd(item)  # Navigate into the folder
                self.upload_directory(ftp, local_path, remote_path)
                ftp.cwd("..")  # Navigate back to parent folder
            else:
                # Handle files
                self.upload_file(ftp, local_path, item)

    def upload_folder_to_ftp(self):
        """Main function to upload a folder to the FTP server."""
        try:
            # local_folder=self.get_test_result_folder()
            do_ftp_upload = True if start_properties.FTP_UPLOAD.lower() == "yes" else False
            if not do_ftp_upload:
                self.logger.warning("FTP upload is disabled.")
                return
            local_folder = os.path.abspath(os.path.join(self.test_results_folder, "..", "..", ".."))
            remote_folder=start_properties.FTP_USER_HOME
            host = start_properties.FTP_HOST
            port = 21
            username = start_properties.FTP_USER
            password = start_properties.FTP_PASSWORD
            ftp = self.connect_to_ftp(host, port, username, password)  # Connect to the FTP server
            self.upload_directory(ftp, local_folder, remote_folder)  # Upload the folder
            ftp.quit()
            self.logger.warning("Connection closed.")
        except Exception as e:
            self.logger.error(f"Error: {e}")

    ###########################################

    def merge_pdfs_in_parts(self):
        folder_path = self.get_test_result_folder()
        output_base = os.path.join(folder_path, "consolidated")
        output_file_base = os.path.join(output_base, "Test_Results_" + self.get_datetime_string())
        os.makedirs(os.path.dirname(output_file_base), exist_ok=True)

        pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
        test_summary = [f for f in pdf_files if f.startswith('Test_Summary_Results')]

        self.logger.info(pdf_files)

        grouped_pdfs = {}
        for pdf in pdf_files:
            self.logger.info(f"Processing PDF: {pdf}")
            match = re.match(r'(QS\d+)_', pdf, re.IGNORECASE)
            if match:
                prefix = match.group(1).upper()
                grouped_pdfs.setdefault(prefix, []).append(pdf)

        merge_order = test_summary + sum([grouped_pdfs[key] for key in sorted(grouped_pdfs.keys())], [])

        self.logger.info(f"Merge order: {merge_order}")

        total_size = sum(os.path.getsize(os.path.join(folder_path, pdf_file)) for pdf_file in merge_order)

        max_size = 100 * 1024 * 1024  # 100MB threshold

        if total_size <= max_size:
            self.logger.info("All PDFs are within the size limit. Merging into a single file.")
            pdf_writer = PyPDF2.PdfMerger()
            for pdf_file in merge_order:
                pdf_writer.append(os.path.join(folder_path, pdf_file))
            with open(output_file_base + ".pdf", "wb") as output_pdf:
                pdf_writer.write(output_pdf)
            self.logger.info(f"Merged PDF saved at: {output_file_base}.pdf")
        else:
            part_number = 1
            current_output_path = f"{output_file_base}_part{part_number}.pdf"
            pdf_writer = PyPDF2.PdfMerger()

            current_size = 0

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
        now = datetime.now(timezone.utc)
        date_time = now.strftime("%d%b%Y_%Ih%Mm%Ss%f")
        # self.logger.debug("date and time:", date_time)
        return date_time

    def get_time_string(self):
        """
        Generates a formatted string representing the current date and time.

        Format:
            DayMonthYear_HourMinuteSecondMicrosecond (e.g., 04Apr2025_014238123456)

        Returns:
            str: The formatted date and time string.
        """
        self.is_not_used()
        now = datetime.now(timezone.utc)
        time_str = now.strftime("%Hh%Mm%Ss")
        # self.logger.debug("date and time:", date_time)
        return time_str

    def get_date_string(self):
        """
        Generates a formatted string representing the current date.

        Format:
            DayMonthYear (e.g., 04Apr2025)

        Returns:
            str: The formatted date string.
        """
        self.is_not_used()
        now = datetime.now(timezone.utc)
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

    def authenticate_service_account(self):
        base_dir = Path(sys.argv[0]).parent.resolve()
        service_account_info = json.loads(self.decrypt_file(base_dir/"resources"/"enc_service_account.json.file"))
        creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
        drive_service = build("drive", "v3", credentials=creds)
        return drive_service

    # Authenticate using the service account
    def authenticate_service_account_file(self):
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        drive_service = build("drive", "v3", credentials=creds)
        return drive_service

    def get_existing_root_folder_id(self, folder_name, drive_service):
        """Check if a folder with the given name exists and return its ID."""
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        results = drive_service.files().list(q=query, fields="files(id, webViewLink)").execute()
        folders = results.get("files", [])

        if folders:
            folder_id = folders[0]["id"]
            folder_link = folders[0]["webViewLink"]
            self.logger.info(f"Existing folder '{folder_name}' found: {folder_link}")
            return folder_id, folder_link
        else:
            return None, None

    def create_folder(self, folder_name, drive_service):
        """Create a new folder in Google Drive."""
        folder_metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}
        folder = drive_service.files().create(body=folder_metadata, fields="id, webViewLink").execute()
        folder_id = folder.get("id")
        folder_link = folder.get("webViewLink")
        print(f"New folder '{folder_name}' created: {folder_link}")
        return folder_id, folder_link

    def get_existing_folder_id(sef, folder_name, parent_folder_id, drive_service):
        """Check if a folder already exists in Google Drive."""
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and '{parent_folder_id}' in parents and trashed=false"
        response = drive_service.files().list(q=query, fields="files(id)").execute()
        folders = response.get("files", [])
        return folders[0]["id"] if folders else None

    def get_existing_file_id(self, file_name, parent_folder_id, drive_service):
        """Check if a file already exists in Google Drive."""
        query = f"name='{file_name}' and '{parent_folder_id}' in parents and trashed=false"
        response = drive_service.files().list(q=query, fields="files(id)").execute()
        files = response.get("files", [])
        return files[0]["id"] if files else None

    # def upload_folder_to_drive(self, parent_folder_id, folder_path, drive_service):
    #     """Recursively upload a folder and its contents to Google Drive, avoiding duplicates."""
    #     folder_name = os.path.basename(folder_path)

    #     # Check if folder exists, if not, create it
    #     drive_folder_id = self.get_existing_folder_id(folder_name, parent_folder_id, drive_service)
    #     if not drive_folder_id:
    #         folder_metadata = {
    #             "name": folder_name,
    #             "mimeType": "application/vnd.google-apps.folder",
    #             "parents": [parent_folder_id]
    #         }
    #         folder = drive_service.files().create(body=folder_metadata, fields="id").execute()
    #         drive_folder_id = folder.get("id")
    #         self.logger.info(f"Created folder '{folder_name}' in Drive (ID: {drive_folder_id})")
    #     else:
    #         self.logger.warning(f"Folder '{folder_name}' already exists in Drive (ID: {drive_folder_id})")

    #     # Iterate over items in the local folder
    #     for item_name in os.listdir(folder_path):
    #         item_path = os.path.join(folder_path, item_name)

    #         if os.path.isdir(item_path):
    #             # Recursively upload subfolders
    #             self.upload_folder_to_drive(drive_folder_id, item_path, drive_service)
    #         else:
    #             # Check if file exists before uploading
    #             if not self.get_existing_file_id(item_name, drive_folder_id, drive_service):
    #                 file_metadata = {
    #                     "name": item_name,
    #                     "parents": [drive_folder_id]
    #                 }
    #                 media = MediaFileUpload(item_path, mimetype="application/octet-stream")
    #                 drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    #                 self.logger.info(f"Uploaded file '{item_name}' to Drive in folder '{folder_name}'")
    #             else:
    #                 self.logger.warning(f"File '{item_name}' already exists in folder '{folder_name}', skipping upload.")

    #     self.logger.info(f"Files from '{folder_path}' uploaded successfully!")

    def upload_folder_to_drive(self, parent_folder_id, folder_path, drive_service):
        """Recursively upload a folder and its contents to Google Drive, avoiding duplicates."""
        folder_name = os.path.basename(folder_path)

        # Check if folder exists, if not, create it
        drive_folder_id = self.get_existing_folder_id(folder_name, parent_folder_id, drive_service)
        if not drive_folder_id:
            folder_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_folder_id]
            }
            folder = drive_service.files().create(body=folder_metadata, fields="id").execute()
            drive_folder_id = folder.get("id")
            self.logger.info(f"Created folder '{folder_name}' in Drive (ID: {drive_folder_id})")
        else:
            self.logger.warning(f"Folder '{folder_name}' already exists in Drive (ID: {drive_folder_id})")

        # Get a list of existing files in the folder
        existing_files = {file["name"]: file["id"] for file in self.list_files_in_folder(drive_folder_id, drive_service)}

        # Iterate over items in the local folder
        for item_name in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item_name)

            if os.path.isdir(item_path):
                # Recursively upload subfolders
                self.upload_folder_to_drive(drive_folder_id, item_path, drive_service)
            else:
                # Check if file exists before uploading
                if item_name not in existing_files:
                    file_metadata = {
                        "name": item_name,
                        "parents": [drive_folder_id]
                    }
                    media = MediaFileUpload(item_path, mimetype="application/octet-stream")
                    drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
                    self.logger.info(f"Uploaded file '{item_name}' to Drive in folder '{folder_name}'")
                else:
                    self.logger.warning(f"File '{item_name}' already exists in folder '{folder_name}', skipping upload.")

        self.logger.info(f"Files from '{folder_path}' uploaded successfully!")

    def list_files_in_folder(self, folder_id, drive_service):
        """Retrieve a list of files in a Google Drive folder."""
        query = f"'{folder_id}' in parents and trashed = false"
        response = drive_service.files().list(q=query, fields="files(id, name)").execute()
        return response.get("files", [])

    def delete_folder_from_drive(self, folder_id, drive_service):
        """Delete all files and subfolders inside a Google Drive folder."""
        query = f"'{folder_id}' in parents and trashed = false"
        response = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = response.get("files", [])

        if not files:
            self.logger.info(f"No files found in folder (ID: {folder_id}).")
            return

        for file in files:
            try:
                drive_service.files().delete(fileId=file["id"]).execute()
                self.logger.info(f"Deleted '{file['name']}' from Drive.")
            except Exception as e:
                self.logger.error(f"Failed to delete '{file['name']}': {e}")

        self.logger.info(f"All contents from folder (ID: {folder_id}) deleted successfully!")

    def grant_access_to_folder_and_contents(self, folder_id, user_emails, drive_service):
        """Remove existing permissions (except for specified users) and grant new access to a list of users for a folder and its contents."""

        # Convert user_emails to a set for quick lookup
        user_emails_set = set(user_emails)

        # Fetch existing permissions for the folder
        existing_permissions = drive_service.permissions().list(fileId=folder_id).execute()
        for permission in existing_permissions.get('permissions', []):
            if permission['role'] != 'owner':
                drive_service.permissions().delete(fileId=folder_id, permissionId=permission['id']).execute()
                self.logger.info(f"Removed permission {permission['id']} from folder {folder_id}")

        # List all files and subfolders within the folder
        results = drive_service.files().list(q=f"'{folder_id}' in parents").execute()
        files = results.get('files', [])

        for file in files:
            # Fetch existing permissions for each file
            existing_file_permissions = drive_service.permissions().list(fileId=file['id']).execute()
            for permission in existing_file_permissions.get('permissions', []):
                if permission['role'] != 'owner' and 'emailAddress' in permission:
                    if permission['emailAddress'] not in user_emails_set:  # Only remove if not in user_emails
                        drive_service.permissions().delete(fileId=file['id'], permissionId=permission['id']).execute()
                        self.logger.info(f"Removed permission {permission['id']} from {file['name']} ({file['id']})")

        # Grant new access to all users
        for user_email in user_emails:
            if not self.is_valid_gmail(user_email):
                self.logger.warning(f"The email address {user_email} is not a gmail address. Skipping granding access to google drive.")
                continue
            new_permission = {
                "type": "user",
                "role": "reader",  # Change to 'writer' for edit access
                "emailAddress": user_email
            }

            # Grant access to the folder
            drive_service.permissions().create(fileId=folder_id, body=new_permission).execute()
            self.logger.info(f"Access granted to {user_email} for folder {folder_id}")

            # Grant access to each file and subfolder
            for file in files:
                drive_service.permissions().create(fileId=file['id'], body=new_permission).execute()
                self.logger.info(f"Access granted to {user_email} for {file['name']} ({file['id']})")


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

    def sanitize_string(self, input_str: str) -> str:
        # Replace all non-alphanumeric and non-underscore characters with '_'
        return re.sub(r'[^a-zA-Z0-9_]', '_', input_str)

    def get_hostname(self) -> str:
        """Returns the hostname of the system."""
        if start_properties.RUN_IN_SELENIUM_GRID.lower() == "yes":
            return "selenium_grid"
        else:
            return socket.gethostname()

    def upload_test_results_to_drive(self, recipient_email):
        folder_name = "TestResults"

        if getattr(sys, 'frozen', False):  # Check if running as a frozen executable
            script_dir = os.path.dirname(sys.executable)  # Use the directory of the executable
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))  # Normal script behavior

        generic_path = os.path.join(script_dir, "test_results")

        folder_path = generic_path
        # recipient_email = ["theautomationtester99@gmail.com"]

        drive_service = self.authenticate_service_account()
        folder_id, folder_link = self.get_existing_root_folder_id(folder_name, drive_service)
        if not folder_id:
            folder_id, folder_link = self.create_folder(folder_name, drive_service)

        self.upload_folder_to_drive(folder_id, folder_path, drive_service)
        # self.logger.info(folder_id, folder_link)
        self.grant_access_to_folder_and_contents(folder_id, recipient_email, drive_service)
        return folder_link

    def delete_test_results_from_drive(self):
        folder_name = "TestResults"
        drive_service = self.authenticate_service_account()
        folder_id, folder_link = self.get_existing_root_folder_id(folder_name, drive_service)
        if not folder_id:
            return

        self.delete_folder_from_drive(folder_id, drive_service)

    def zip_folder(self, folder_path, zip_name):
        """Compress a folder into a ZIP file."""
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), folder_path))
        self.logger.info(f"ZIP file created: {zip_name}")

    def split_zip(self, zip_path, part_size=15*1024*1024):
        """Split ZIP into 15MB chunks."""
        with open(zip_path, 'rb') as zip_file:
            index = 1
            while chunk := zip_file.read(part_size):
                part_filename = f"{zip_path}.part{index}"
                with open(part_filename, 'wb') as part:
                    part.write(chunk)
                index += 1
        self.logger.info(f"Split completed: {index - 1} parts created.")
        return glob.glob(f"{zip_path}.part*")  # Return list of split parts

    def send_email_with_attachment(self):
        """
        Sends individual emails with attachments from a specified folder using a Gmail account,
        ensuring that duplicate email addresses only receive one email. If the recipient list is empty
        or contains only blank spaces, no emails will be sent.

        Parameters:
        sender_email (str): Your Gmail email address.
        sender_password (str): Your Gmail app password.
        recipient_emails (list): List of recipient email addresses (duplicates and empty values will be removed).
        subject_prefix (str): The prefix for the email subject (e.g., "Report").
        folder_path (str): Path to the folder containing files to send.

        Returns:
        None
        """
        send_test_results_email = True if str(start_properties.SEND_TEST_RESULTS_EMAIL).lower() == 'yes' else False
        upload_test_results_to_drive = True if str(start_properties.UPLOAD_TEST_RESULTS).lower() == 'yes' else False

        if send_test_results_email:
            sender_email =  str(start_properties.SENDER_EMAIL).lower()
            sender_password = self.decrypt_string(str(start_properties.SENDER_EMAIL_PASSWORD))
            recipient_emails = str(start_properties.RECIPIENT_EMAILS).lower().split(",")
            zip_folder_path = os.path.join(self.get_test_result_folder(), "recordings")
            folder_path = os.path.join(self.get_test_result_folder(), "consolidated")
            subject_prefix = "Test Results"
            zip_subject_prefix = "Recordings"

            smtp_server = "smtp.gmail.com"
            smtp_port = 587  # Gmail SMTP port

            # Remove duplicate emails and filter out empty strings or whitespace-only entries
            unique_recipients = list({email.strip() for email in recipient_emails if email.strip() and self.is_valid_email(email)})

            # Check if recipient list is empty
            if not unique_recipients:
                self.logger.warning(f"Recipient email list is empty {recipient_emails}, contains only blank entries, or has invalid email addresses. No emails sent.")
                return

            if not self.is_valid_email(sender_email):
                self.logger.warning(f"Invalid sender email address {sender_email}. No emails sent.")
                return

            if not self.is_valid_gmail(sender_email):
                self.logger.warning(f"Sender email address {sender_email} should only a gmail account. No emails sent.")
                return

            # Get list of files in the folder
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

            if not files:
                self.logger.warning("No files found in the folder.")
                return

            total_files = len(files)

            for recipient_email in unique_recipients:
                for idx, file_name in enumerate(files, start=1):
                    # Determine email subject
                    subject = subject_prefix if total_files == 1 else f"{subject_prefix} - Part {idx}/{total_files}"

                    # Create email message
                    msg = MIMEMultipart()
                    msg["From"] = sender_email
                    msg["To"] = recipient_email
                    msg["Subject"] = subject

                    if upload_test_results_to_drive and self.is_valid_gmail(recipient_email):
                        fldr_link = self.upload_test_results_to_drive(recipient_emails)
                        body = f"Hello,\n\nPlease find attached test results summary: {file_name}\n\n Below is the link to the full test results folder uploaded to google drive:\n\n {fldr_link} \n\nBest regards."
                    else:
                        body = f"Hello,\n\nPlease find attached test results summary: {file_name}\n\nBest regards."
                    msg.attach(MIMEText(body, "plain"))

                    # Attach the file
                    file_path = os.path.join(folder_path, file_name)
                    try:
                        with open(file_path, "rb") as attachment:
                            part = MIMEApplication(attachment.read(), Name=file_name)
                            part["Content-Disposition"] = f'attachment; filename="{file_name}"'
                            msg.attach(part)
                    except Exception as e:
                        self.logger.error(f"Could not attach file {file_name}: {e}")
                        continue

                    try:
                        # Connect to Gmail SMTP server
                        server = smtplib.SMTP(smtp_server, smtp_port)
                        server.starttls()  # Secure connection
                        server.login(sender_email, sender_password)  # Use your app password

                        # Send email
                        server.sendmail(sender_email, recipient_email, msg.as_string())
                        server.quit()

                        self.logger.info(f"Email sent successfully to {recipient_email} with attachment: {file_name}")
                    except Exception as e:
                        self.logger.error(f"Error sending email to {recipient_email} for {file_name}: {e}")

            # **Check if recordings folder contains at least one file**
            if not any(os.path.isfile(os.path.join(zip_folder_path, f)) for f in os.listdir(zip_folder_path)):
                self.logger.warning(f"No files found in 'recordings' folder. Zipping and sending email skipped.")
                return

            zip_name = os.path.join(self.get_test_result_folder(), "recordings.zip")
            self.zip_folder(zip_folder_path, zip_name)  # Using defined function

            # **Call existing function to split the ZIP into 15MB parts**
            split_files = self.split_zip(zip_name)  # Using defined function
            self.logger.info(f"Split ZIP into {len(split_files)} parts.")

            # **Preserving your email logic, now sending split files**
            total_zip_files = len(split_files)  # Update file count to reflect split ZIP files

            for recipient_email in unique_recipients:
                for idx, file_path in enumerate(split_files, start=1):
                    zip_subject = zip_subject_prefix if total_zip_files == 1 else f"{subject_prefix} - Part {idx}/{total_zip_files}"

                    msg = MIMEMultipart()
                    msg["From"] = sender_email
                    msg["To"] = recipient_email
                    msg["Subject"] = zip_subject

                    body_single = f"Hello,\n\nAttached is recordings zip.\n\nBest regards."
                    body = body_single if total_zip_files == 1 else f"Hello,\n\nPlease find attached recordings zip - Part {idx}/{total_zip_files}\n\nBest regards."

                    msg.attach(MIMEText(body, "plain"))

                    try:
                        with open(file_path, "rb") as attachment:
                            part = MIMEApplication(attachment.read(), Name=os.path.basename(file_path))
                            part["Content-Disposition"] = f'attachment; filename="{os.path.basename(file_path)}"'
                            msg.attach(part)
                    except Exception as e:
                        self.logger.error(f"Could not attach file {os.path.basename(file_path)}: {e}")
                        continue

                    try:
                        server = smtplib.SMTP(smtp_server, smtp_port)
                        server.starttls()
                        server.login(sender_email, sender_password)
                        server.sendmail(sender_email, recipient_email, msg.as_string())
                        server.quit()
                        self.logger.info(f"Email sent successfully to {recipient_email} with attachment: {os.path.basename(file_path)}")
                    except Exception as e:
                        self.logger.error(f"Error sending email to {recipient_email} for {os.path.basename(file_path)}: {e}")

            # **Delete ZIP files after emails are sent**
            zip_files = [zip_name] + split_files  # Includes main ZIP and all split parts
            for file in zip_files:
                try:
                    os.remove(file)
                    self.logger.info(f"Deleted file: {file}")
                except Exception as e:
                    self.logger.error(f"Error deleting {file}: {e}")

    def is_not_used(self):
        pass

    def is_valid_email(self,email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email)

    def is_valid_gmail(self, email):
        return re.match(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", email) is not None

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
    def is_date_format_valid(self, entered_date):
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
        dts = [f"{day:02}" for day in range(1, 32)]
        mts = list(calendar.month_name)[1:]  # Exclude the first element (empty string)
        current_year = datetime.now().year
        yrs = [str(year) for year in range(1900, current_year + 1)]
        
        # Used a try-except block to handle cases where entered_date.split() doesn’t return three components.
        try:
            self.logger.warning("validating date")
            day, month, year = entered_date.split()
            self.logger.warning(day)
            datetime.strptime(entered_date, '%d %B %Y')
            if not (day in dts and month in mts and year in yrs):
                self.logger.warning(entered_date)
                return False
            else:
                return True
        except ValueError as e:
            self.logger.error(e)
            return False

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
        self.is_date_format_valid(first_date)

        first_date_yr = int(first_date.split()[2])
        first_date_mon = self.get_mtn_number(first_date.split()[1])
        first_date_day = int(first_date.split()[0])

        second_date = " ".join(input_date.split()[4:7])
        self.is_date_format_valid(second_date)

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

    def encrypt_string(self, input_string, encryption_key="DC3HN3PdUb5z_MyYbitSyVnPU_E_WOfZkUsYR8bWKzY="):
        """
        Encrypts a given string using Fernet encryption.

        Args:
            input_string (str): The string to be encrypted.
            encryption_key (str): Encryption key to use for encryption (default provided).

        Returns:
            str: Encrypted string in bytes format.
        """
        # Create a Fernet cipher using the encryption key
        f = Fernet(encryption_key)

        # Encrypt the input string
        encrypted_string = f.encrypt(input_string.encode())

        return encrypted_string

    def decrypt_string(self, encrypted_string, encryption_key="DC3HN3PdUb5z_MyYbitSyVnPU_E_WOfZkUsYR8bWKzY="):
        """
        Decrypts an encrypted string using Fernet encryption.

        Args:
            encrypted_string (bytes): The encrypted string in bytes format.
            encryption_key (str): Encryption key used for encryption.

        Returns:
            str: Decrypted original string.
        """
        # Create a Fernet cipher using the encryption key
        fernet = Fernet(encryption_key)

        # Decrypt the encrypted string
        decrypted_string = fernet.decrypt(encrypted_string).decode()

        return decrypted_string

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