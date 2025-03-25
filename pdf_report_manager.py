import logging

from reporting import PdfReporting
from utilities import Utils

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.INFO)


class PdfReportManager:
    def __init__(self):
        self.utils = Utils()
        self.tca_id = ''
        self.tca_desc = ''
        self.tca_browser_name = ''
        self.tca_browser_version = ''
        self.tca_date_executed = self.utils.get_date_string()
        self.tca_overall_status = 'Passed'
        self.all_steps_list = []
        self.step_no = 1

    def add_step_data(self, step_data, expected_result, actual_result, step_status, step_screenshot):
        step_list = [self.step_no, step_data, expected_result, actual_result, step_status, step_screenshot]
        self.all_steps_list.append(step_list)
        self.step_no = self.step_no + 1

    def create_report(self):
        pdf = PdfReporting(
            self.tca_id + "_test_results_" + self.tca_browser_name + "_" + self.tca_overall_status + "_" + self.utils.get_datetime_string())
        pdf.add_heading(self.tca_id, 1)
        pdf.add_paragraph(self.tca_desc, 11, False)
        para = pdf.add_paragraph("Executed On: ", 11, True)
        pdf.add_paragraph_run(para, self.tca_date_executed, 11)
        para = pdf.add_paragraph("Web Browser Used: ", 11, True)
        pdf.add_paragraph_run(para, self.tca_browser_name + " " + self.tca_browser_version, 11)
        para = pdf.add_paragraph("Overall Status: ", 11, True)
        pdf.add_paragraph_run(para, self.tca_overall_status, 11)
        # print(all_steps_list)
        pdf.add_table(self.all_steps_list)
        pdf.add_footer()
        pdf.add_header("Test Results")
        pdf.save_file()
        pdf.convert_to_pdf()

    def is_not_used(self):
        pass
