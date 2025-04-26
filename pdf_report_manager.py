import os
import sys
from pathlib import Path
import pandas as pd
from pdf_reporting import PdfReporting
from pdf_ts_reporting import PdfTsReporting
from utilities import Utils


class PdfReportManager:
    """
    A class to manage the creation of detailed PDF reports and test summary reports.
    Handles the organization and structure of step-by-step and sub-step reporting data,
    which is then used to generate visually structured PDF documents.
    """
    def __init__(self, logger):
        """
        Initializes the PdfReportManager with essential components and placeholders.

        Attributes:
            logger: An instance of LoggerConfig used for logging messages.
            utils: Utility instance providing date and file handling methods.
            tc_id: Test case identifier initialized as an empty string.
            all_steps_list: A list to store all step-related data.
            step_no: Counter for the current step number.
            sub_step_no: Counter for the current sub-step number.
            row_span: Tracks the row span of steps in the report table.
            report_data: Dictionary to store data for the final report generation.
            table_data: Dictionary to store step-by-step and sub-step data.
            page_title: Placeholder for the title of the report page.
            test_description: Placeholder for the description of the test.
            browser_img_src, browser_img_alt: Placeholders for browser image source and alt text.
            os_img_src, os_img_alt: Placeholders for OS image source and alt text.
            browser_version: Placeholder for the browser version information.
            executed_date: Stores the date when the test was executed.
            overall_status_text: Text to indicate the overall status of the test, defaults to "PASSED".
        """
        self.logger = logger
        self.utils = Utils(self.logger)
        self.tc_id = ''
        self.all_steps_list = []
        self.step_no = 0
        self.sub_step_no = 0
        self.row_span = 0
        self.report_data = {}
        self.table_data = {}
        self.current_retry = 1
        self.page_title = "",
        self.test_description = ""
        self.browser_img_src = ""
        self.browser_img_alt = ""
        self.os_img_src = ""
        self.os_img_alt = ""
        self.running_on_host_name = ""
        self.browser_version = ""
        self.grid_img_src = ""
        self.executed_date = self.utils.get_date_string()
        self.overall_status_text = "PASSED"

    def add_report_data(self, **data):
        """
        Adds data for a test step or a sub-step into the report structure.

        Args:
            **data: Arbitrary keyword arguments containing details of a step or sub-step.
                For a step:
                    - step (str): Description of the step.
                    - result (str): Result of the step (e.g., "Pass" or "Fail").
                For a sub-step:
                    - sub_step (str): Description of the sub-step.
                    - sub_step_message (str): Additional details about the sub-step.
                    - image_src (str, optional): Source path of an image related to the sub-step.
                    - image_alt (str, optional): Alt text for the sub-step image.
                    - sub_step_status (str): Status of the sub-step (e.g., "Pass" or "Fail").

        Updates the overall status to "FAILED" if any sub-step has a status of "Fail".
        """
        retry_key = f"retry_{self.current_retry}"  # Group data by retry attempt

        if retry_key not in self.table_data:
            self.table_data[retry_key] = {}  # Initialize retry group if not present
            self.step_no = 0
            self.overall_status_text = "PASSED"
            self.table_data[retry_key]["rstatus"] = "Pass"

        if "step" in data:
            self.logger.debug('Step is captured to be added to PDF report.')
            self.step_no += 1
            self.row_span = 1
            if str(self.step_no) not in self.table_data[retry_key]:
                self.table_data[retry_key][str(self.step_no)] = {}
            self.table_data[retry_key][str(self.step_no)]["sno"] = str(self.step_no)
            self.table_data[retry_key][str(self.step_no)]["rowspan"] = str(self.row_span)
            self.table_data[retry_key][str(self.step_no)]["step"] = data["step"]
            self.table_data[retry_key][str(self.step_no)]["result"] = data["result"]
            self.table_data[retry_key][str(self.step_no)]["overall_step_status"] = "Pass"
            self.sub_step_no = 0
        else:
            self.logger.debug('Sub Step is captured to be added to PDF report.')
            self.sub_step_no += 1
            self.row_span += 1
            self.table_data[retry_key][str(self.step_no)]["rowspan"] = str(self.row_span)
            if "sub_steps" not in self.table_data[retry_key][str(self.step_no)]:
                self.table_data[retry_key][str(self.step_no)]["sub_steps"] = {}

            if str(self.sub_step_no) not in self.table_data[retry_key][str(self.step_no)]["sub_steps"]:
                self.table_data[retry_key][str(self.step_no)]["sub_steps"][str(self.sub_step_no)] = {}

            self.table_data[retry_key][str(self.step_no)]["sub_steps"][str(self.sub_step_no)]["sub_step"] = data["sub_step"]
            self.table_data[retry_key][str(self.step_no)]["sub_steps"][str(self.sub_step_no)]["sub_step_message"] = data["sub_step_message"]
            if "image_src" in data:
                self.table_data[retry_key][str(self.step_no)]["sub_steps"][str(self.sub_step_no)]["image_src"] = data["image_src"]
                self.table_data[retry_key][str(self.step_no)]["sub_steps"][str(self.sub_step_no)]["image_alt"] = data["image_alt"]
            self.table_data[retry_key][str(self.step_no)]["sub_steps"][str(self.sub_step_no)]["sub_step_status"] = data["sub_step_status"]
            self.table_data[retry_key][str(self.step_no)]["overall_step_status"] = data["sub_step_status"]
            if str(data["sub_step_status"]).lower() == "fail":
                self.overall_status_text = "FAILED"
                self.table_data[retry_key]["rstatus"] = "Fail"
                self.table_data[retry_key]["rerror"]=self.utils.extract_first_x_chars(data["sub_step_message"], 350)

    async def create_report(self):
        """
        Finalizes the gathered report data and generates a PDF report.

        This method uses the PdfReporting class to create the report by populating a template
        with test-specific information. The report includes:
            - Page title, test description, browser and OS details.
            - Executed date, overall test status, and a detailed step-by-step breakdown.

        The generated PDF is saved with a name containing the test case ID, browser details,
        and the execution timestamp.
        """
        base_dir = Path(sys.argv[0]).parent.resolve()

        self.logger.debug('Finalizing the data to be added to PDF report.')
        self.report_data["page_title"] = self.page_title
        self.report_data["test_description"] = self.test_description
        self.report_data["browser_img_src"] = self.browser_img_src
        self.report_data["browser_img_alt"] = self.browser_img_alt
        self.report_data["os_img_src"] = self.os_img_src
        self.report_data["os_img_alt"] = self.os_img_alt
        if self.grid_img_src != "":
            self.report_data["grid_img_src"] = self.grid_img_src
        self.report_data["grid_img_alt"] = self.grid_img_src
        self.report_data["browser_version"] = self.browser_version
        self.report_data["executed_date"] = self.executed_date
        self.report_data["overall_status_text"] = self.overall_status_text
        self.report_data["table_data"] = self.table_data
        pdf = PdfReporting(self.logger, base_dir/"resources"/"logo.png", base_dir/"resources"/"encrypted_file.jinja2", self.report_data, self.tc_id + "-" + self.running_on_host_name + "-" + self.browser_img_alt + "-" + self.os_img_alt, self.tc_id + "_" + self.browser_img_alt + "_" + self.overall_status_text + "_" + self.utils.get_date_string())

        await pdf.generate_pdf()

    async def generate_test_summary_pdf(self):
        """
        Generates a summary PDF report based on the contents of 'output.xlsx' file.

        This method checks if the 'output.xlsx' file exists in the current directory.
        If the file is found:
            - The data is read into a Pandas DataFrame and converted to a table-friendly format.
            - PdfTsReporting class is used to create a test summary report with this data.

        The generated summary report includes the test case results and is saved with a
        timestamped filename.
        """
        base_dir = Path(sys.argv[0]).parent.resolve()
        tr_folder = self.utils.get_test_result_folder()

        self.logger.debug('Checking if output.xlsx file exists before creating the test summary PDF report.')
        if self.utils.check_if_file_exists(os.path.join(tr_folder, "output.xlsx")):
            self.logger.debug('Output.xlsx exists and starting to create test summary PDF report.')
            df = pd.read_excel(os.path.join(tr_folder, "output.xlsx"))
            table_data = df.to_dict(orient='records')

            ts_pdf = PdfTsReporting(self.logger, base_dir/"resources"/"logo.png", base_dir/"resources"/"encrypted_ts_file.jinja2", table_data, "Test_Summary_Results_" + self.utils.get_date_string())
            await ts_pdf.generate_pdf()

    def is_not_used(self):
        pass
