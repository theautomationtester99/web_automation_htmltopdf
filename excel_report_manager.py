import logging

import pandas as pd
from tabulate import tabulate

from utilities import Utils

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.WARN)


class ExcelReportManager:
    def __init__(self):
        self.utils = Utils()
        self.all_test_results_list = []

    def add_row(self, test_result):
        if self.utils.check_if_file_exists(".\\output.xlsx"):
            df = pd.read_excel("output.xlsx")
            self.all_test_results_list = df.values.tolist()
            self.all_test_results_list.append(test_result)
            self.export_to_excel()
        else:
            self.all_test_results_list.append(test_result)
            self.export_to_excel()

    def export_to_excel(self):
        # print(self.all_test_results_list)

        df = pd.DataFrame(self.all_test_results_list, columns=['tc_id', 'tc_description', 'Status', 'Browser'])
        data_condition = ['Failed', 'Fail']

        highlighted_rows = df['Status'].isin(data_condition).map({
            True: 'background-color: red',
            False: ''
        })

        styler = df.style.apply(lambda _: highlighted_rows)
        # print(type(styler))
        # print(pd.__version__)
        styler.to_excel('output.xlsx', index=False)
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))

    def is_not_used(self):
        pass
