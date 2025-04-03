import pandas as pd

from pdf_reporting import PdfReporting
from pdf_ts_reporting import PdfTsReporting
from utilities import Utils
import os
from logger_config import LoggerConfig


class PdfReportManager:
    def __init__(self):
        self.logger = LoggerConfig().logger
        self.utils = Utils()
        self.tc_id = ''
        self.all_steps_list = []
        self.step_no = 0
        self.sub_step_no = 0
        self.row_span = 0
        self.report_data = {}
        self.table_data = {}

        self.page_title = "",
        self.test_description = ""
        self.browser_img_src = ""
        self.browser_img_alt = ""
        self.os_img_src = ""
        self.os_img_alt = ""
        self.browser_version = ""
        self.executed_date = self.utils.get_date_string()
        self.overall_status_text = "PASSED"

    def add_report_data(self, **data):
        if "step" in data:
            self.logger.debug('Step is captured to be added to PDF report.')
            self.step_no += 1
            self.row_span = 1
            if str(self.step_no) not in self.table_data:
                self.table_data[str(self.step_no)] = {}
            self.table_data[str(self.step_no)]["sno"] = str(self.step_no)
            self.table_data[str(self.step_no)]["rowspan"] = str(self.row_span)
            self.table_data[str(self.step_no)]["step"] = data["step"]
            self.table_data[str(self.step_no)]["result"] = data["result"]
            self.table_data[str(self.step_no)]["overall_step_status"] = "Pass"
            self.sub_step_no = 0
        else:
            self.logger.debug('Sub Step is captured to be added to PDF report.')
            self.sub_step_no += 1
            self.row_span += 1
            self.table_data[str(self.step_no)]["rowspan"] = str(self.row_span)
            if "sub_steps" not in self.table_data[str(self.step_no)]:
                self.table_data[str(self.step_no)]["sub_steps"] = {}
            
            if str(self.sub_step_no) not in self.table_data[str(self.step_no)]["sub_steps"]:
                self.table_data[str(self.step_no)]["sub_steps"][str(self.sub_step_no)] = {}
            
            self.table_data[str(self.step_no)]["sub_steps"][str(self.sub_step_no)]["sub_step"] = data["sub_step"]
            self.table_data[str(self.step_no)]["sub_steps"][str(self.sub_step_no)]["sub_step_message"] = data["sub_step_message"]
            if "image_src" in data:
                self.table_data[str(self.step_no)]["sub_steps"][str(self.sub_step_no)]["image_src"] = data["image_src"]
                self.table_data[str(self.step_no)]["sub_steps"][str(self.sub_step_no)]["image_alt"] = data["image_alt"]
            self.table_data[str(self.step_no)]["sub_steps"][str(self.sub_step_no)]["sub_step_status"] = data["sub_step_status"]
            self.table_data[str(self.step_no)]["overall_step_status"] = data["sub_step_status"]
            if str(data["sub_step_status"]).lower() == "fail":
                self.overall_status_text = "FAILED"

    # def add_step_data(self, step_data, expected_result, actual_result, step_status, step_screenshot):
    #     step_list = [self.step_no, step_data, expected_result, actual_result, step_status, step_screenshot]
    #     self.all_steps_list.append(step_list)
    #     self.step_no = self.step_no + 1

    async def create_report(self):
        self.logger.debug('Finalizing the data to be added to PDF report.')
        self.report_data["page_title"] = self.page_title
        self.report_data["test_description"] = self.test_description
        self.report_data["browser_img_src"] = self.browser_img_src
        self.report_data["browser_img_alt"] = self.browser_img_alt
        self.report_data["os_img_src"] = self.os_img_src
        self.report_data["os_img_alt"] = self.os_img_alt
        self.report_data["browser_version"] = self.browser_version
        self.report_data["executed_date"] = self.executed_date
        self.report_data["overall_status_text"] = self.overall_status_text
        self.report_data["table_data"] = self.table_data
        pdf = PdfReporting("logo.png", "encrypted_file.jinja2", self.report_data, self.tc_id, self.tc_id + "_test_results_" + self.browser_img_alt + "_" + self.overall_status_text + "_" + self.utils.get_datetime_string())
        
        await pdf.generate_pdf()
        
    async def generate_test_summary_pdf(self):
        self.logger.debug('Checking if output.xlsx file exists before creating the test summary PDF report.')
        if self.utils.check_if_file_exists(os.path.join(".", "output.xlsx")):
            self.logger.debug('Output.xlsx exists and starting to create test summary PDF report.')
            df = pd.read_excel("output.xlsx")
            table_data = df.to_dict(orient='records')
            
            ts_pdf = PdfTsReporting("logo.png", "encrypted_ts_file.jinja2", table_data, "Test_Summary_Results_" + self.utils.get_datetime_string())
            await ts_pdf.generate_pdf()

    def is_not_used(self):
        pass
