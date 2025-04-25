# import argparse
#
# parser = argparse.ArgumentParser(description="Just an example",
#                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter)
# parser.add_argument("-a", "--archive", action="store_true", help="archive mode")
# parser.add_argument("-v", "--verbose", action="store_true", help="increase verbosity")
# parser.add_argument("-B", "--block-size", help="checksum blocksize")
# parser.add_argument("--ignore-existing", action="store_true", help="skip files that exist")
# parser.add_argument("--exclude", help="files to exclude")
# parser.add_argument("src", help="Source location")
# parser.add_argument("dest", help="Destination location")
# args = parser.parse_args()
# config = vars(args)
# # print(config)
# from utilities import Utils


# def generate_random_notif_id():
#     utils = Utils()
#     logged_user_name = 'utils.get_logged_in_user_name()'
#     date_time_string = utils.get_datetime_string()
#     date_string = utils.get_date_string()
#     user_name_length = len(logged_user_name)
#     if user_name_length >= 10:
#         logged_user_name = logged_user_name[:9]
#         random_id = logged_user_name + "_" + date_string[:5] + date_time_string[-5:]
#     else:
#         random_id = logged_user_name + "_" + date_string[:5] + date_time_string[-(14 - user_name_length):]
#     return random_id

# # print(generate_random_notif_id())

# # import required module
# import os
# from cryptography.fernet import Fernet
# import platform
# # key generation
# # key = Fernet.generate_key()
# # print(f"Generated Key: {key.decode()}")
# from config import start_properties

# print(f"Screenshot strategy: {start_properties.SCREENSHOT_STRATEGY}")
# print(f"Log Level: {start_properties.LOG_LEVEL}")
# print(f"Selenium Grid URL: {start_properties.GRID_URL}")
# print(f"Appium Grid URL: {start_properties.APPIUM_URL}")
# print(f"Delete test results: {start_properties.DELETE_TEST_RESULTS}") 

# key="DC3HN3PdUb5z_MyYbitSyVnPU_E_WOfZkUsYR8bWKzY="
# input = "my deep dark secret"

# f = Fernet(key)

# token = f.encrypt(input.encode())

# print(token)

# dec = f.decrypt("gAAAAABn4lHdfMxWfYLUF9HdSM245-iHNUvatXxllwgSB-hHyZWA2OLTPM0gva0dYAKQG-0ELa0OuHHBICYsNr2h0q7rmRfjTYUiQa35pM5NXqgZD1t7jNw=")
# print(dec.decode("utf-8"))

# # Initialize a dictionary
# my_dict = {'1': 'Alice', 'age': 25}

# a=1
# b=2
# print(my_dict[str(a)])
# my_dict[str(b)] = {"sno": "test"}
# my_dict[str(b)] = {"sno1": "test1"}

# print(my_dict)

# # Add a new key-value pair
# my_dict['city'] = {'cest': "tes"}

# my_dict['name'] = 'Test'
# print(my_dict)

# my_dict['city']['cest'] = 'tlsor'
# print(my_dict)

# from utilities import Utils

# utils = Utils()

# utils.encrypt_file("jinja2_template.html")


# def detect_os():
#     os_name = platform.system()
#     if os_name == "Linux":
#         return "This system is running Linux."
#     elif os_name == "Windows":
#         return "This system is running Windows."
#     else:
#         return f"Operating System detected: {os_name}"

# print(detect_os())

# class a:
#     def __init__(self):
#         self.a = 1

#     def my_function(self, x):
#         print(f"Received value: {x}")

#     # Example of passing and incrementing in a single line
#     def another(self):
#         self.my_function(self.a := self.a + 1)

# run_headless = True
# run_in_grid =  True
# if not run_headless and not run_in_grid:
#     exit("Parallel execution can only be run in headless mode.")
# else:
#     print("running")

# processes = [1]

# for batch_start in range(0, len(processes), 5):
#     batch = processes[batch_start:batch_start + 5]
#     print(batch)



# def get_logged_in_user_name():
#         """
#         Gets the name of the currently logged-in user.

#         Returns:
#             str: The name of the logged-in user.
#         """
#         return os.getlogin()

# print(get_logged_in_user_name())


# import smtplib
# import os
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.application import MIMEApplication

# def send_email_with_attachment(sender_email, sender_password, recipient_emails, subject_prefix, folder_path):
#     """
#     Sends individual emails with attachments from a specified folder using a Gmail account,
#     ensuring that duplicate email addresses only receive one email. If the recipient list is empty
#     or contains only blank spaces, no emails will be sent.

#     Parameters:
#     sender_email (str): Your Gmail email address.
#     sender_password (str): Your Gmail app password.
#     recipient_emails (list): List of recipient email addresses (duplicates and empty values will be removed).
#     subject_prefix (str): The prefix for the email subject (e.g., "Report").
#     folder_path (str): Path to the folder containing files to send.

#     Returns:
#     None
#     """

#     smtp_server = "smtp.gmail.com"
#     smtp_port = 587  # Gmail SMTP port

#     # Remove duplicate emails and filter out empty strings or whitespace-only entries
#     unique_recipients = list({email.strip() for email in recipient_emails if email.strip()})

#     # Check if recipient list is empty
#     if not unique_recipients:
#         print("Recipient email list is empty or contains only blank entries. No emails sent.")
#         return

#     # Get list of files in the folder
#     files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

#     if not files:
#         print("No files found in the folder.")
#         return
    
#     total_files = len(files)
    
#     for recipient_email in unique_recipients:
#         for idx, file_name in enumerate(files, start=1):
#             # Determine email subject
#             subject = subject_prefix if total_files == 1 else f"{subject_prefix} - Part {idx}"

#             # Create email message
#             msg = MIMEMultipart()
#             msg["From"] = sender_email
#             msg["To"] = recipient_email
#             msg["Subject"] = subject

#             body = f"Hello,\n\nPlease find attached file: {file_name}\n\nBest regards."
#             msg.attach(MIMEText(body, "plain"))

#             # Attach the file
#             file_path = os.path.join(folder_path, file_name)
#             try:
#                 with open(file_path, "rb") as attachment:
#                     part = MIMEApplication(attachment.read(), Name=file_name)
#                     part["Content-Disposition"] = f'attachment; filename="{file_name}"'
#                     msg.attach(part)
#             except Exception as e:
#                 print(f"Could not attach file {file_name}: {e}")
#                 continue

#             try:
#                 # Connect to Gmail SMTP server
#                 server = smtplib.SMTP(smtp_server, smtp_port)
#                 server.starttls()  # Secure connection
#                 server.login(sender_email, sender_password)  # Use your app password

#                 # Send email
#                 server.sendmail(sender_email, recipient_email, msg.as_string())
#                 server.quit()

#                 print(f"Email sent successfully to {recipient_email} with attachment: {file_name}")
#             except Exception as e:
#                 print(f"Error sending email to {recipient_email} for {file_name}: {e}")

# # Example usage
# # send_email_with_attachment("your_email@gmail.com", "your_password", ["recipient1@example.com", " ", "recipient2@example.com", ""], "Report", "path/to/folder")

# send_email_with_attachment(
#     sender_email="theautomationtester99@gmail.com",
#     sender_password="eaab htxy kwjw ixew",
#     recipient_emails=[" "],
#     subject_prefix="Test Report",
#     folder_path="test_results\\18Apr2025\\consolidated"
# )


# import re

# def is_valid_email(email):
#     return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# def send_email_with_attachment(self, sender_email, sender_password, recipient_emails, start_props_reader):
#     """
#     Sends individual emails with attachments from a specified folder using a Gmail account,
#     ensuring that duplicate email addresses only receive one email. If the recipient list is empty
#     or contains only blank spaces, no emails will be sent.

#     Parameters:
#     sender_email (str): Your Gmail email address.
#     sender_password (str): Your Gmail app password.
#     recipient_emails (list): List of recipient email addresses (duplicates and empty values will be removed).
#     subject_prefix (str): The prefix for the email subject (e.g., "Report").
#     folder_path (str): Path to the folder containing files to send.

#     Returns:
#     None
#     """
#     sender_email =  str(start_props_reader.get_property('Misc', 'sender_email', fallback='No')).lower()
#     sender_password = str(start_props_reader.get_property('Misc', 'sender_password', fallback='No')).lower()
#     recipient_emails = str(start_props_reader.get_property('Misc', 'recipient_emails', fallback='No')).lower().split(";")
#     folder_path = os.path.join(self.get_test_result_folder(), "consolidated")
#     subject_prefix = "Test Results"
    
#     smtp_server = "smtp.gmail.com"
#     smtp_port = 587  # Gmail SMTP port

#     # Remove duplicate emails, filter out empty strings or whitespace-only entries, and validate emails
#     unique_recipients = list({email.strip() for email in recipient_emails if email.strip() and is_valid_email(email)})

#     # Validate sender email
#     if not is_valid_email(sender_email):
#         print("Invalid sender email address. No emails sent.")
#         return

#     # Check if recipient list is empty
#     if not unique_recipients:
#         print("Recipient email list is empty, contains only blank entries, or has invalid email addresses. No emails sent.")
#         return

#     # Get list of files in the folder
#     files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

#     if not files:
#         print("No files found in the folder.")
#         return
    
#     total_files = len(files)
    
#     for recipient_email in unique_recipients:
#         for idx, file_name in enumerate(files, start=1):
#             # Determine email subject
#             subject = subject_prefix if total_files == 1 else f"{subject_prefix} - Part {idx}"

#             # Create email message
#             msg = MIMEMultipart()
#             msg["From"] = sender_email
#             msg["To"] = recipient_email
#             msg["Subject"] = subject

#             body = f"Hello,\n\nPlease find attached file: {file_name}\n\nBest regards."
#             msg.attach(MIMEText(body, "plain"))

#             # Attach the file
#             file_path = os.path.join(folder_path, file_name)
#             try:
#                 with open(file_path, "rb") as attachment:
#                     part = MIMEApplication(attachment.read(), Name=file_name)
#                     part["Content-Disposition"] = f'attachment; filename="{file_name}"'
#                     msg.attach(part)
#             except Exception as e:
#                 print(f"Could not attach file {file_name}: {e}")
#                 continue

#             try:
#                 # Connect to Gmail SMTP server
#                 server = smtplib.SMTP(smtp_server, smtp_port)
#                 server.starttls()  # Secure connection
#                 server.login(sender_email, sender_password)  # Use your app password

#                 # Send email
#                 server.sendmail(sender_email, recipient_email, msg.as_string())
#                 server.quit()

#                 print(f"Email sent successfully to {recipient_email} with attachment: {file_name}")
#             except Exception as e:
#                 print(f"Error sending email to {recipient_email} for {file_name}: {e}")
