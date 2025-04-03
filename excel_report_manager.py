import pandas as pd
from tabulate import tabulate

from logger_config import LoggerConfig
from utilities import Utils
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment
import os

class ExcelReportManager:
    def __init__(self):
        self.logger = LoggerConfig().logger
        self.utils = Utils()
        self.all_test_results_list = []

    def add_row(self, test_result):
        if self.utils.check_if_file_exists(os.path.join(".", "output.xlsx")):
            df = pd.read_excel("output.xlsx")
            self.all_test_results_list = df.values.tolist()
            self.all_test_results_list.append(test_result)
            self.export_to_excel()
        else:
            self.all_test_results_list.append(test_result)
            self.export_to_excel()

    def export_to_excel(self):
        # print(self.all_test_results_list)

        df = pd.DataFrame(self.all_test_results_list, columns=['tc_id', 'tc_description', 'Status', 'Browser', 'Executed Date'])
        data_condition = ['Failed', 'Fail', 'FAILED']

        highlighted_rows = df['Status'].isin(data_condition).map({
            True: 'background-color: red',
            False: ''
        })

        styler = df.style.apply(lambda _: highlighted_rows)
        # print(type(styler))
        # print(pd.__version__)
        output_file = 'output.xlsx'
        styler.to_excel(output_file, index=False)
        
        # Auto-adjust column widths and enable wrapping
        workbook = load_workbook(output_file)
        sheet = workbook.active
        max_width = 80  # Set maximum column width

        for column in sheet.columns:
            max_length = 0
            col_letter = get_column_letter(column[0].column)  # Get column letter
            for cell in column:
                try:
                    if cell.value:
                        max_length = min(max(max_length, len(str(cell.value))), max_width)
                        cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)  # Enable text wrapping
                except:
                    pass
            sheet.column_dimensions[col_letter].width = max_length + 2  # Add padding

        workbook.save(output_file)
        
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))

    def is_not_used(self):
        pass
