import logging

from driver_functions import BrowserDriver
from pdf_report_manager import PdfReportManager
from utilities import Utils
import sys
from datetime import datetime
import asyncio

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.INFO)


class KeywordsManager(BrowserDriver):
    def __init__(self):
        super().__init__()
        self.repo_m = PdfReportManager()
        self.utils = Utils()
        self.chrome_logo_src_b64 = "data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PSIwIDAgMTQgMTQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgeG1sbnM6eGxpbms9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkveGxpbmsiPjxsaW5lYXJHcmFkaWVudCBpZD0iYSIgZ3JhZGllbnRVbml0cz0idXNlclNwYWNlT25Vc2UiIHgxPSIxMjcuNDY5NiIgeDI9IjEyNy40Njk2IiB5MT0iODIuMjU5MjM5IiB5Mj0iMTczLjY2NjQ0Ij48c3RvcCBvZmZzZXQ9IjAiIHN0b3AtY29sb3I9IiM4NmJiZTUiLz48c3RvcCBvZmZzZXQ9IjEiIHN0b3AtY29sb3I9IiMxMDcyYmEiLz48L2xpbmVhckdyYWRpZW50PjxwYXRoIGQ9Im02Ljk4NDc3NjYzIDEuMDAxMDYzMTJzMy41MjQwMDczOS0uMTU4MTQwNTMgNS4zOTIzNTgyNSAzLjM4NDAyMDI2aC01LjY5MjIxNzAzcy0xLjA3NDIzMjczLS4wMzQ2MjI0OC0xLjk5MTg2ODkgMS4yNjg1ODY1MmMtLjI2MzU5ODc1LjU0Njk4ODQ1LS41NDY5NDE2NyAxLjExMDQ0NTk4LS4yMjg5NzYyNyAyLjIyMDg5MTk2LS40NTgwNDYxLS43NzYwMTE1LTIuNDMxNzYxNi00LjIxMjcxNDA5LTIuNDMxNzYxNi00LjIxMjcxNDA5czEuMzkyMTUxMzUtMi41MjA3NTA3NCA0Ljk1MjQxODc3LTIuNjYwNzg0NjV6IiBmaWxsPSIjZWYzZjM2Ii8+PHBhdGggZD0ibTEyLjE5NDI0Mzk1IDkuOTkzMjcwN3MtMS42MjYxMzM4NCAzLjEzMTkzMTE3LTUuNjI2MjkzOTUgMi45NzcwNjU3M2MuNDk0MjU5MzUtLjg1NTA4MTc3IDIuODQ2OTAzOS00LjkyOTM5OTUgMi44NDY5MDM5LTQuOTI5Mzk5NXMuNTY4NDE2OTYtLjkxMjcyMzUyLS4xMDIxMzYzMy0yLjM1OTI0MTUzYy0uMzQxMDc4MjUtLjUwMjQ5Mzg4LS42ODg3MDY3LTEuMDI4MDUzODItMS44MDg5Nzc5OC0xLjMwODE2ODQzLjkwMTIxMzktLjAwODE4Nzc1IDQuODYzNTIzMiAwIDQuODYzNTIzMiAwczEuNDg0MzY4OCAyLjQ2NjM4NDA4LS4xNzMwMTg4NCA1LjYxOTc0Mzc1eiIgZmlsbD0iI2ZjZDkwMCIvPjxwYXRoIGQ9Im0xLjgwMDAxMjkzIDEwLjAxNzk3NDMxcy0xLjg5OTYwNDY3LTIuOTczNzkwNjEuMjM1NTczMjUtNi4zNjEwODU5OGMuNDkyNjIxOC44NTUwODE3OCAyLjg0NTI2NjM0IDQuOTI5Mzk5NSAyLjg0NTI2NjM0IDQuOTI5Mzk5NXMuNTA3NDUzMzIuOTQ4OTgzNTYgMi4wOTQwMDUyNCAxLjA5MDYwODIzYy42MDQ2NzctLjA0NDQ0Nzc4IDEuMjM0MDEwODItLjA4MjM0NTM2IDIuMDM4MDQ3ODItLjkxMTAzOTE5LS40NDMyNjEzNy43ODQyNDYwNC0yLjQzMTg1NTE4IDQuMjExMDc2NTQtMi40MzE4NTUxOCA0LjIxMTA3NjU0cy0yLjg3OTg0MjA0LjA1MjcyOTEtNC43ODEwODQyNi0yLjk1ODk1OTF6IiBmaWxsPSIjNjFiYzViIi8+PHBhdGggZD0ibTYuNTY2MzEyNDUgMTIuOTk5OTk5NDcuODAwNjY4MzMtMy4zNDExNjMyNHMuODc5Nzg1MzgtLjA2OTI0NDk3IDEuNjE3ODk5My0uODc4MTQ3ODNjLS40NTgwNDYxLjgwNTY3NDU1LTIuNDE4NTY3NjMgNC4yMTkzMTEwNy0yLjQxODU2NzYzIDQuMjE5MzExMDd6IiBmaWxsPSIjNWFiMDU1Ii8+PHBhdGggZD0ibTQuMzAyNjEwMjYgNy4wMzc1ODY3MWMwLTEuNDcyODU5MTcgMS4xOTQ0NzU2OC0yLjY2NzMzNDg1IDIuNjY3MzM0ODUtMi42NjczMzQ4NXMyLjY2NzMzNDg1IDEuMTk0NDc1NjggMi42NjczMzQ4NSAyLjY2NzMzNDg0YzAgMS40NzI5MDU5NS0xLjE5NDQ3NTY4IDIuNjY3MzM0ODUtMi42NjczMzQ4NSAyLjY2NzMzNDg1LTEuNDcyODU5MTctLjAwMTYzNzU1LTIuNjY3MzM0ODUtMS4xOTQ0Mjg5LTIuNjY3MzM0ODUtMi42NjczMzQ4NXoiIGZpbGw9IiNmZmYiLz48cGF0aCBkPSJtODAuMDA0IDEyOS4wNTZjMC0yNi4xOTggMjEuMjM0LTQ3LjQ2NyA0Ny40NjgtNDcuNDY3IDI2LjE5OCAwIDQ3LjQ2NyAyMS4yMzQgNDcuNDY3IDQ3LjQ2NyAwIDI2LjE5OS0yMS4yMzMgNDcuNDY4LTQ3LjQ2NyA0Ny40NjgtMjYuMTk5IDAtNDcuNDY4LTIxLjI2OS00Ny40NjgtNDcuNDY4eiIgZmlsbD0idXJsKCNhKSIgdHJhbnNmb3JtPSJtYXRyaXgoLjA0Njc5IDAgMCAuMDQ2NzkgMS4wMDU4OTUgLjk5OTQyNikiLz48cGF0aCBkPSJtMTIuMzY1NTc4NDYgNC4zNzUyMTEzLTMuMjk2NzE1NDYuOTY3MDkwMThzLS40OTc1MzQ0NS0uNzI5ODc5MzgtMS41NjY3NjA5Ni0uOTY3MDkwMThjLjkyNzU1NTA1LS4wMDQ5NTk0NCA0Ljg2MzQ3NjQyIDAgNC44NjM0NzY0MiAweiIgZmlsbD0iI2VhY2EwNSIvPjxwYXRoIGQ9Im00LjM5OTgzMzk0IDcuNzUyNjM0NTdjLS40NjMwMDU1NC0uODAyMzUyNjYtMi4zNjc1MjI4Ni00LjA5MDc4NjgtMi4zNjc1MjI4Ni00LjA5MDc4NjhsMi40NDE2MzM2OSAyLjQxNTI0NTc0cy0uMjUwNDUxNTcuNTE1Njg3ODYtLjE1NjUwMjk5IDEuMjUzNzU1bC4wODIzNDUzNy40MjE3ODYwNnoiIGZpbGw9IiNkZjNhMzIiLz48L3N2Zz4="
        self.edge_logo_src_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAAsTAAALEwEAmpwYAAAJ00lEQVR4nO2YeVBUVxbGL9CPLURTKZOqTNVMKhVTlTEzGkVNNECzQzeLGM3iAopJTKKCGMANEBD3BQXFyJKoGBfQqKAoLtj7AjR0Aw023SBqRJNJjElG0UTpb+r1e8gSehE0Vk15qs4/772+9f3uPdttQp7aU3tqg7YRWq3bm5oLCWNUzbLxVYbrE+Wtv3tIDEauWAeupAFcSZXRUyG590712Rtvq8sax9Yfy3fXFnuQJ23/rr0wdWz1lSYP0U2jl/AmvIQ/giu6Dq7oO3BFF+Et0sFbXA8fsQq+Egn8JGfhLz0Of2kRAmS74F2d1/FWfW7peF32K3+p8DcaDD5jK6995ynogJfwFryEv8FL+DO8hP8BV3QNXNEVcEWt8BY1wUesgY+4Cr4SMfwkp+EvLUGA9AACZQUIlGcjSL4GAcpk40RNhsK9KfOlx6scsB+tvlzsIbwDT8FddAP82gfgMriiFniLG+EjVsNHXAlfiRB+klPwlx5FgOwbBMryECTfgmB5BniKxeArP0eg6uP7Ey6kpT8W7aPUbc+5V/5wxVPwBzwFv8NTcAdewtvwEv6XBbgBL+EP4IraTQDeIgMLUAsfsQK+EgH8JCfhL/0WAbJCBMp2Iki+GcGKNPAUX4Cv/AQhlR8itHo6uE2Lq7hI5Twy8SM1LS+Ol//8i6fgHiwBcEVdAJfgLdLDW6w1AfiK5fCVVMBPWgZ/6SEEyHYjULYDQfKNCFakgKeIA185ByFVHyJMNR3htTPgcyH+Cleb6jZo8SMEWrfxihs/MeItAfwEruh7cEVXWYBmeIsb4COuga9YBj/JOfiZErjYlMCBsu0Ikq9HsCIJPEUM+MpZCK2ahrCa6QhXz0BE/Uz4NSe0EaTaDwrAXXWtwVNwH5YBfukD0NYDQAVfsZStQKVsBfoagfJtCJKvRbBiGXjK+QipjERoNQMwSUMDRGJyYxS4rUnnBiz+Tc2lTEb8QAD6ltAzJoAA6UG2AmUhSL4awYol4Ck/R0jlDBNAeC0NMBMRDZF4tzEK7+pmw+PS6k8eWvwbKv2rE8QdnX0BPCruYtShdrxWoMM/tqvx9201eHmHGsML6jCy6ALeOdvWpwdU9wDoLqFB8iwEy1exFegzhFRO6wUwmQZoisIU3WyEGmLvvNy2y/mhANxrrqs8BZ2s+PsYWXQNw9bI4BBXAhJTAhJbBhJ3CiTuNMiiM4zHnYbdonIMTT+P1wsrwRXVsQDiHgD7ESjLR5B8K1tCE8FXfspUIBUNMAOT6roBpupm4z1DNHwur8y1WfzIxrbRHkJ6xzsx7vhNDE2pAJl/FCT2BMii0yDxFSAJIpDFEpAlMpAlctZlzDP6XXwFXFdUYMwRWY8mdswMwFzzAM0MQFhbbIfNAGNq2oW0+NcLL8Eh5hhI7HFmhxOEIItlIMsqQZbXgCRrQFLqQFLqWa9jntHv6G8Wy2CXKMSIfYJBA3xwcQ4mtG8KsgngbeFv99/YfxV2tPiFJ0HizzPCl1czAlMbQdKaQVa2gGRc7O30M/od/Q397bJq2C2R4V8Hzw4qhN5vnQPfy2nlVsWPUreGjC27CfuFpSBx5Uw4LFWywpv6F23O6W/p3yRr4JCkhMeZ0h5JvNXmJO4C4F9J+NEqwIhTBulz6RJGfKIYZFkVSEoDSLreJtF2SVo4bZJddztYNW9Iufx5t1LVsGeKq+Icc6q/f2GLpMcgZ1sZnaKbhff00Xi/ZQ4mXV541yrA8CLdTVN1SRSZjp+s0IKsbLUuPr0FDnNPwSnpRI25tV32VgonlB9BgOyrB5NosGKpxUY25cIsJg9aojH14idGqwDPb5XfJQkCZudp8Rm2iDeAM/0AqE8P3ba4OGA//NC5292jxDoEK5abHSUma+kwYgEM0ZjSOtc6gFOq2EiWKJiqYku8r7wIzswiUOE74bKufLW19V8uE+Qyw1xOj2FuYe9hTt0jkdkwmqqfjbC2BdZDyG6pFCSpFiS92aaYt59fASpsB6jJ+XDLFQyztv5rQuE/mXH6y/7HaVWPPOgTRoEXl+qtAyQrjWRFo21VJk0PKiIX1KRcUBH5cNtU/rq19d11pcP+fKFJZCvRjO48oMOoriuMGAiPtpUZVgEcVtXcp2Papt2fdxZUWI5JPO0ua0/GWAXQlqQwvaCrEq1hJ9IFbB503wkenII2CvzmBR02XXKoLPVvttZ5zgeFoMK/fADglFwmtrT2CG2xo2fV8Vtdl/pAUyJv6HGp+Zi9lfU+hYiGKExoXTWP2GLO+bUttoWPAVTYNlDhTPjQ7jin+A9La4+tO3PcT3oC/tLDCJDt6c4DeTobRnQ/iGSq0YNTiISnPrmQ2GquB2r229SwElWgQrY9iH+TTy6A8/ryeHNrv1V7rqH7Yr+PHSm6wogup7FMNWJPgV8bZfTQp24iD2PPltaE2QQQJ2EB8roBaJ914D4phkN/a7u3q1zHacrLvBUlnfTFJoC+mZnCiC6nqeAp4k3JzK+cBa/6hMaxujXjyECMk627azWBF5wHFZLd+wS6QimxtNXS+nQyjtYeix5XX3zobfUe8UR1XuPEuuyGCXWbBW81blgzsmXji2Qw5rJPc9Y2gCxTA+sLYEro5cdryZOyIUdUr9qttdyF7RZJQfG3ggrrrkK9fHI+HGNLfnHdK3rM/7aZMefCulqLAMvrweFlggrt7gP9+sz9nc4ZJ3eRAZjL+oK/OSflJgzkt2ToaeUr9hsNnRZnoPAcJg/MhFEvj9zf6ZRyQvLslnM8q8JXFM53/Cz3El2mOeGZ1gc4c+ZWVJttMQ+ij4LD39KrG9vk078xUp8evuMYc/SGY/yRNscvilsd5+/7nore3cGZWmA0fUPPV/ytcFqUs5sMxpx31TdbDCN+JpPM5nJhIB6+kznZ2VntZLD2QrHAzXFn0w2zp/BRCTi8zUxPsCWUrIrPBRW6HdS0rR0kK8uJPApzPaV6yXFn08/9QqTr4RCxg0loE8QgTiJ8Jys+6xZJ3TuEPEobelT9nPNX2rZ+IZK14IRnsxDZTPz20+DM+qQ8JgTpDfhox3WSdfLR7Hx/5npQs9duncH4p3xYpoFDRA44wZuY/hC6jQExDXt5ZoTnMsJDt4MzaRucEvMGl7C22tCTmtHOXze0klV97stpethHFoMTvMGUFxwahD4ROizofkEDmTyHeRZCn1Y2qLn57a6rvh5D/mp75lulL93w7Dfqe/ULu6Vq2EcVg8PbZDoREwwvExzeFtYz4fDuDlDz9lx1Xn34HfLETSBwdjui+txln+acY37jVU6W7o79Or3RLsMA+yVVcIg5ZeTElNyjvjjyq1N8UbPL+pI0kptLPWnZT+2pkf8D+x/JEdtowLOM5wAAAABJRU5ErkJggg=="

    '''
    The below are the keywords that can be used generically for any application under testing.
    '''

    def ge_close(self):
        asyncio.run(self.repo_m.create_report())
        self.close_browser()
    
    def ge_tcid(self, tc_id):
        self.repo_m.page_title = "Test Report"
        self.repo_m.tc_id = tc_id

    def ge_tcdesc(self, tc_desc):
        self.repo_m.test_description = tc_desc

    def ge_step(self, **data):
        self.repo_m.add_report_data(**data)

    def ge_wait_for_seconds(self, how_seconds):
        self.wait_for_some_time(how_seconds)

    def ge_open_browser(self, browser_name):
        try:
            self.launch_browser(browser_name)
            if browser_name.lower() == 'chrome':
                self.repo_m.browser_img_src = self.chrome_logo_src_b64
                self.repo_m.browser_img_alt = browser_name.upper()
                self.repo_m.browser_version = self.ge_browser_version()
            if browser_name.lower() == 'edge':
                self.repo_m.browser_img_src = self.edge_logo_src_b64
                self.repo_m.browser_img_alt = browser_name.upper()
                self.repo_m.browser_version = self.ge_browser_version()
            self.repo_m.add_report_data(sub_step="Open Browser ", sub_step_message="The browser opened successfully", sub_step_status="Pass", image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
        except Exception as e:
            print(e)
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno

            print("Exception type: ", exception_type)
            print("File name: ", filename)
            print("Line number: ", line_number)

            self.repo_m.add_report_data(sub_step="Open Browser " + browser_name, sub_step_message="Error Occured. " + str(e), sub_step_status='Fail', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)

            raise e

    def ge_browser_version(self):
        return self.get_browser_version()

    def ge_is_element_loaded(self, locator, locator_type):
        try:
            return self.is_element_present(locator, locator_type)
        except Exception as e:
            return False
            raise e

    def ge_is_element_enabled(self, locator, locator_type, element_name):
        try:
            is_enabled = self.is_element_enabled(locator, locator_type)
            if is_enabled:
                self.repo_m.add_report_data(sub_step="Check if the element " + element_name+ " is enabled", sub_step_message="The element " + element_name + " is enabled", sub_step_status='Pass', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
            else:
                self.repo_m.add_report_data(sub_step="Check if the element " + element_name+ " is enabled", sub_step_message="The element " + element_name + " is NOT enabled", sub_step_status='Fail', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            self.repo_m.add_report_data(sub_step="Check if the element " + element_name+ " is enabled", sub_step_message="Error Occurred " + str(e), sub_step_status='Fail', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
            raise e

    def ge_is_element_disabled(self, locator, locator_type, element_name):
        try:
            is_disabled = self.is_element_enabled(locator, locator_type)
            if is_disabled is False:
                self.repo_m.add_report_data(sub_step="Check if the element " + element_name+ " is disabled", sub_step_message="The element " + element_name + " is disabled", sub_step_status='Pass', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
            else:
                self.repo_m.add_report_data(sub_step="Check if the element " + element_name+ " is disabled", sub_step_message="The element " + element_name + " is NOT disabled", sub_step_status='Fail', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            self.repo_m.add_report_data(sub_step="Check if the element " + element_name+ " is disabled", sub_step_message="Error Occurred " + str(e), sub_step_status='Fail', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
            raise e

    def ge_is_element_displayed(self, locator, locator_type, element_name):
        try:
            is_displayed = self.is_element_enabled(locator, locator_type)
            if is_displayed:
                self.repo_m.add_report_data(sub_step="Check if the element " + element_name+ " is displayed", sub_step_message="The element " + element_name + " is displayed", sub_step_status='Pass', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
            else:
                self.repo_m.add_report_data(sub_step="Check if the element " + element_name+ " is displayed", sub_step_message="The element " + element_name + " is NOT displayed", sub_step_status='Fail', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            self.repo_m.add_report_data(sub_step="Check if the element " + element_name+ " is displayed", sub_step_message="Error Occurred " + str(e), sub_step_status='Fail', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
            raise e

    def ge_enter_url(self, url):
        try:
            self.open_url(url)
            self.page_has_loaded()
            self.wait_for_some_time(2)
            print("in methond before")
            self.repo_m.add_report_data(sub_step="Enter URL " + str(url), sub_step_message="The URL is entered successfully", sub_step_status='Pass', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
            print("in methond before")
            
        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            self.repo_m.add_report_data(sub_step="Enter URL " + url, sub_step_message="Error Occurred " + str(e), sub_step_status='Fail', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
            raise e

    def ge_type(self, locator, locator_type, text_to_type, element_name):
        len_input = len(text_to_type)
        nbr_spaces = self.utils.count_spaces_in_string(text_to_type)
        percent_spaces = self.utils.is_what_percent_of(nbr_spaces, len_input)
        if percent_spaces > 2:
            report_txt_to_type = text_to_type
        else:
            report_txt_to_type = self.utils.make_string_manageable(
                text_to_type, 25)

        try:
            self.highlight(1, "blue", 2, locator, locator_type)
            self.element_click(locator, locator_type)
            self.send_keys(text_to_type, locator, locator_type)
            self.wait_for_some_time(1)
            self.repo_m.add_report_data(sub_step="Type the text '" + report_txt_to_type + "'in '" + element_name+ "'", sub_step_message="The text should be typed successfully", sub_step_status='Pass', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            self.repo_m.add_report_data(sub_step="Type the text '" + report_txt_to_type + "'in '" + element_name+ "'", sub_step_message="Error Occurred " + str(e), sub_step_status='Fail', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
            raise e

    def ge_verify_displayed_text(self, locator, locator_type, expected_text, element_name):
        try:
            self.wait_for_element(locator, locator_type)
            self.highlight(1, "blue", 2, locator, locator_type)
            actual_text = self.get_text(locator, locator_type, element_name)
            is_matched = (actual_text == expected_text)
            if is_matched:
                self.repo_m.add_report_data(sub_step="Verifying the text '" + expected_text + "'in '" + element_name + "'", sub_step_message="The text is  " + actual_text, sub_step_status='Pass', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
            else:
                self.repo_m.add_report_data(sub_step="Verifying the text '" + expected_text + "'in '" + element_name + "'", sub_step_message="The text is  " + actual_text, sub_step_status='Fail', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            self.repo_m.add_report_data(sub_step="Verifying the text '" + expected_text + "'in '" + element_name + "'", sub_step_message="Error Occurred " + str(e), sub_step_status='Fail', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
            raise e

    def ge_click(self, locator, locator_type, element_name):
        try:
            self.scroll_into_view(locator, locator_type)
            self.highlight(1, "blue", 2, locator, locator_type)
            self.element_click(locator, locator_type)
            self.wait_for_some_time(2)
            self.repo_m.add_report_data(sub_step="Click on the element '" + element_name + "'", sub_step_message="The click is successful", sub_step_status='Pass', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            self.repo_m.add_report_data(sub_step="Click on the element '" + element_name + "'", sub_step_message="Error Occurred " + str(e), sub_step_status='Fail', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
            raise e

    def ge_select_file(self, locator, locator_type, file_paths):
        try:
            self.file_name_to_select(file_paths)
            self.wait_for_element(locator, locator_type)
            self.scroll_into_view(locator, locator_type)
            self.repo_m.add_report_data(sub_step="Upload the file '" + file_paths + "'", sub_step_message="The file is added successfully", sub_step_status='Pass', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            self.repo_m.add_report_data(sub_step="Upload the file '" + file_paths + "'", sub_step_message="Error Occurred " + str(e), sub_step_status='Fail', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
            raise e

    '''
    The below are the keywords that are specific to MCNP application.
    '''

    def choose_date_from_date_picker(self, **kwargs):
        try:
            util_t = Utils()
            which_calender = kwargs.get("which_calender")
            expected_date = kwargs.get("date_to_choose")

            if which_calender == 'cn_det_dd':
                first_date = " ".join(expected_date.split()[0:3])
                first_mon_yr = " ".join(first_date.split()[1:3])
                first_yr = int(first_date.split()[2])
                first_mon = str(first_date.split()[1])
                first_mon_nbr = util_t.get_mtn_number(first_mon)
                first_day = str(first_date.split()[0])

                second_date = " ".join(expected_date.split()[4:7])
                second_mon_yr = " ".join(second_date.split()[1:3])
                second_yr = int(second_date.split()[2])
                second_mon = str(second_date.split()[1])
                second_mon_nbr = util_t.get_mtn_number(second_mon)
                second_day = str(second_date.split()[0])
                while True:
                    displayed_month = self.get_text(kwargs.get('cn_det_ddate_mon_txt_xpath'),
                                                    kwargs.get("locator_type"),
                                                    kwargs.get("locator_name"))
                    disp_yr = int(displayed_month.split()[1])
                    disp_mon = str(displayed_month.split()[0])
                    disp_mon_nbr = util_t.get_mtn_number(disp_mon)
                    if displayed_month == first_mon_yr:
                        break
                    if disp_yr > first_yr:
                        self.element_click(kwargs.get(
                            'cn_det_ddate_pre_button_xpath'), kwargs.get("locator_type"))
                    elif disp_yr < first_yr:
                        self.element_click(kwargs.get(
                            'cn_det_ddate_nxt_button_xpath'), kwargs.get("locator_type"))
                    else:
                        if disp_mon_nbr > first_mon_nbr:
                            self.element_click(kwargs.get('cn_det_ddate_pre_button_xpath'),
                                               kwargs.get("locator_type"))
                        else:
                            self.element_click(kwargs.get('cn_det_ddate_nxt_button_xpath'),
                                               kwargs.get("locator_type"))
                date_element_list = self.get_element_list(kwargs.get('cn_det_ddate_date_list_xpath'),
                                                          kwargs.get("locator_type"))
                for testscript_file in date_element_list:
                    disp_day = self.get_text("", "", testscript_file)
                    disp_day_two_dig = "%02d" % (int(disp_day),)
                    if disp_day_two_dig == first_day:
                        self.element_click("", "", testscript_file)
                        break
                # Second date in date range
                while True:
                    displayed_month = self.get_text(kwargs.get('cn_det_ddate_mon_txt_xpath'),
                                                    kwargs.get("locator_type"),
                                                    kwargs.get("locator_name"))
                    disp_yr = int(displayed_month.split()[1])
                    disp_mon = str(displayed_month.split()[0])
                    disp_mon_nbr = util_t.get_mtn_number(disp_mon)
                    if displayed_month == second_mon_yr:
                        break
                    if disp_yr > second_yr:
                        self.element_click(kwargs.get('cn_det_ddate_pre_button_xpath'),
                                           kwargs.get("locator_type"))
                    elif disp_yr < second_yr:
                        self.element_click(kwargs.get('cn_det_ddate_nxt_button_xpath'),
                                           kwargs.get("locator_type"))
                    else:
                        if disp_mon_nbr > second_mon_nbr:
                            self.element_click(kwargs.get('cn_det_ddate_pre_button_xpath'),
                                               kwargs.get("locator_type"))
                        else:
                            self.element_click(kwargs.get('cn_det_ddate_nxt_button_xpath'),
                                               kwargs.get("locator_type"))
                date_element_list = self.get_element_list(
                    kwargs.get('cn_det_ddate_date_list_xpath'), kwargs.get("locator_type"))
                for testscript_file in date_element_list:
                    disp_day = self.get_text("", "", testscript_file)
                    disp_day_two_dig = "%02d" % (int(disp_day),)
                    if disp_day_two_dig == second_day:
                        self.element_click("", "", testscript_file)
                        break

            if which_calender == 'cn_det_ed':
                mon_yr = " ".join(expected_date.split()[1:3])
                yr = int(expected_date.split()[2])
                mon = str(expected_date.split()[1])
                mon_nbr = util_t.get_mtn_number(mon)
                day = str(expected_date.split()[0])
                while True:
                    displayed_month = self.get_text(kwargs.get('cn_det_edate_mon_txt_xpath'),
                                                    kwargs.get("locator_type"),
                                                    kwargs.get("locator_name"))
                    disp_yr = int(displayed_month.split()[1])
                    disp_mon = str(displayed_month.split()[0])
                    disp_mon_nbr = util_t.get_mtn_number(disp_mon)
                    if displayed_month == mon_yr:
                        break
                    if disp_yr > yr:
                        self.element_click(kwargs.get('cn_det_edate_pre_button_xpath'),
                                           kwargs.get("locator_type"))
                    elif disp_yr < yr:
                        self.element_click(kwargs.get('cn_det_edate_nxt_button_xpath'),
                                           kwargs.get("locator_type"))
                    else:
                        if disp_mon_nbr > mon_nbr:
                            self.element_click(kwargs.get('cn_det_edate_pre_button_xpath'),
                                               kwargs.get("locator_type"))
                        else:
                            self.element_click(kwargs.get('cn_det_edate_nxt_button_xpath'),
                                               kwargs.get("locator_type"))
                date_element_list = self.get_element_list(
                    kwargs.get('cn_det_edate_date_list_xpath'), kwargs.get("locator_type"))
                for testscript_file in date_element_list:
                    disp_day = self.get_text("", "", testscript_file)
                    disp_day_two_dig = "%02d" % (int(disp_day),)
                    if disp_day_two_dig == day:
                        self.element_click("", "", testscript_file)
                        break
            
            self.repo_m.add_report_data(sub_step="Choosing the date '" + expected_date + "'in '" + kwargs.get("locator_name") + "'", sub_step_message="The date is chosen successfully", sub_step_status='Pass', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            self.repo_m.add_report_data(sub_step="Choosing the date '" + expected_date + "'in '" + kwargs.get("locator_name") + "'", sub_step_message="Error Occurred " + str(e), sub_step_status='Fail', image_src=self.take_screenshot(), image_alt = self.repo_m.browser_img_alt)
            raise e

    def login_jnj(self, **kwargs):
        self.ge_click(kwargs.get("uname_locator"), kwargs.get(
            "locator_type"), kwargs.get("uname_element_name"))
        self.ge_type(kwargs.get("uname_locator"), kwargs.get("locator_type"), kwargs.get("uname_data"),
                     kwargs.get("uname_element_name"))
        self.ge_click(kwargs.get("proceed_locator"), kwargs.get(
            "locator_type"), kwargs.get("proceed_element_name"))
        start = datetime.now()
        while True:
            end = datetime.now()
            if int((end - start).total_seconds()) >= 5:
                break
            if self.ge_is_element_loaded(kwargs.get("jnjpwd_locator"), kwargs.get("locator_type")):
                self.ge_click(kwargs.get("jnjpwd_locator"), kwargs.get("locator_type"),
                              kwargs.get("jnjpwd_element_name"))
                self.ge_type(kwargs.get("jnjpwd_locator"), kwargs.get("locator_type"), kwargs.get("pwd_data"),
                             kwargs.get("jnjpwd_element_name"))
                self.ge_click(kwargs.get("signon_locator"), kwargs.get("locator_type"),
                              kwargs.get("signon_element_name"))
                break

    def is_not_used(self):
        pass
