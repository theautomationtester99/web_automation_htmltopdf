from jinja2 import Environment, FileSystemLoader
import base64
from pyppeteer import launch

from utilities import Utils
import os


class PdfTsReporting:
    """
    A class to generate a PDF Test Summary Report with a custom header, footer, and content
    dynamically populated from a provided template and data.

    Attributes:
        logger (logging.Logger): Logger instance for debugging and logging information.
        utils (Utils): Utility instance for performing various helper functions.
        logo_path (str): Path to the logo image file.
        base64_logo (str): Base64 encoded string representation of the logo image.
        html_content (str): Generated HTML content of the test report populated with data.
        head_template (str): HTML template string for the header of the PDF.
        footer_template (str): HTML template string for the footer of the PDF.
        document_name_pdf (str): Full path where the generated PDF document will be saved.
    """
    def __init__(self, logger, logo_path, encrypted_template_file_path, data, document_name):
        """
        Initializes the PdfTsReporting class by configuring logger, encoding logo, and generating templates.

        Args:
            logo_path (str): File path to the logo image.
            encrypted_template_file_path (str): File path to the encrypted HTML template file.
            data (dict): Data to populate the HTML template.
            document_name (str): Desired name of the output PDF document.
        """
        self.logger = logger
        self.utils = Utils(self.logger)
        self.logo_path = logo_path
        self.base64_logo = self._encode_logo()
        self.html_content = self._generate_html(encrypted_template_file_path, data)
        self.head_template = self._create_header_template()
        self.footer_template = self._create_footer_template()
        #self.document_name_pdf = self.utils.get_test_result_folder() + "\\" + document_name + ".pdf"
        self.document_name_pdf = os.path.join(self.utils.get_test_result_folder(), document_name + ".pdf")

    def _encode_logo(self):
        """
        Encodes the provided logo image to a Base64 string format for embedding in HTML.

        Returns:
            str: Base64 encoded string of the logo image.
        """
        self.logger.debug("Encoding the logo png file")
        with open(self.logo_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _create_header_template(self):
        """
        Creates an HTML header template containing the report title and logo.

        Returns:
            str: HTML string for the header template.
        """
        self.logger.debug("Creating the test summary report PDF header template")
        return f'''
        <div style="display: flex; width: 100%; height: auto; justify-content: space-between; align-items: center; border-bottom: 2px solid #413a97;">
            <div style="flex: 0;margin-left: 5px;">
                <img id="logo" src="data:image/png;base64,{self.base64_logo}" alt="Logo" style="max-height: 99px;object-fit: contain;">
            </div>
            <div id="tcid" style="flex: 0;font-size:20px;white-space: nowrap;margin-right: 20px;">
                <h1>Test Summary Report</h1>
            </div>
        </div>
        '''

    def _create_footer_template(self):
        """
        Creates an HTML footer template containing page numbering information.

        Returns:
            str: HTML string for the footer template.
        """
        self.logger.debug("Creating the test summary report PDF footer template")
        return '''
        <div style='font-size:10px; width:100%; text-align:center;'>
            Page <span class="pageNumber"></span> of <span class="totalPages"></span>
        </div>
        '''

    def _generate_html(self, encrypted_template_file_path, data):
        """
        Decrypts the provided HTML template file, populates it with the provided data, and generates the HTML.

        Args:
            encrypted_template_file_path (str): Path to the encrypted HTML template file.
            data (dict): Data to populate the HTML template.

        Returns:
            str: The generated HTML content populated with the data.
        """
        self.logger.debug("Decrypting the test summary report PDF template")
        # Decrypt the file
        decrypted_template = self.utils.decrypt_file(encrypted_template_file_path)

        # Setup Jinja2 environment and render the HTML template
        env = Environment(loader=FileSystemLoader("."))
        template = env.from_string(decrypted_template)
        output = template.render(data=data)

        self.logger.debug("Generated the test summary report PDF template with appropriate data")

        # Save the populated HTML to a file
        # with open("output.html", "w") as f:
        #     f.write(output)

        # print("HTML file generated successfully!")
        return output

    async def generate_pdf(self):
        """
        Generates the PDF report from the populated HTML content using a headless browser.

        Saves the generated PDF to the specified location.

        Returns:
            None
        """
        self.logger.debug("Starting creation of test dummary PDF report from template with populated data")
        #browser = await launch({"headless": True})
        browser = await launch(options={'args': ['--no-sandbox'], 'headless': True})
        # print(await browser.version())
        page = await browser.newPage()

        await page.setContent(self.html_content)

        await page.pdf({
            "path": self.document_name_pdf,
            "format": "Letter",
            "printBackground": True,
            "landscape": True,
            "margin": {
                "top": 125,
                "bottom": 25,
                "left": 25,
                "right": 25
            },
            "displayHeaderFooter": True,
            "headerTemplate": self.head_template,
            "footerTemplate": self.footer_template,
        })

        self.logger.debug("Completed creation of test summary PDF report from template with populated data")

        await browser.close()