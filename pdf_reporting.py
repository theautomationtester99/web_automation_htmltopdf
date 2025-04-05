from utilities import Utils
from jinja2 import Environment, FileSystemLoader
import os
import base64
from pyppeteer import launch


class PdfReporting:
    """
    A class to generate PDF reports based on HTML templates.

    This class provides functionality to create PDF reports with custom headers,
    footers, and content, using provided templates and data. It supports features
    such as logo encoding, HTML generation, and PDF creation with adjustable configurations.

    Attributes:
        logger (Logger): Logger instance for logging messages and debugging information.
        utils (Utils): Utility instance for handling file-related operations.
        tc_id (str): Test case identifier to display in the header.
        logo_path (str): Path to the logo image file used in the header.
        base64_logo (str): Base64 encoded representation of the logo image.
        html_content (str): Populated HTML content generated from the template and data.
        head_template (str): HTML template for the PDF report header.
        footer_template (str): HTML template for the PDF report footer.
        document_name_pdf (str): Full path of the PDF file to be created.

    Methods:
        _encode_logo(): Encodes the logo image to a Base64 string for embedding in the header template.
        _create_header_template(): Generates an HTML header template for the PDF report.
        _create_footer_template(): Generates an HTML footer template for the PDF report.
        _generate_html(encrypted_template_file_path, data): Decrypts the template file, populates it with data, and generates HTML content.
        generate_pdf(): Asynchronously creates a PDF from the generated HTML content, header, and footer templates.
    """
    def __init__(self, logger, logo_path, encrypted_template_file_path, data, tc_id, document_name):
        """
        Initializes the PdfReporting class with provided attributes.

        Args:
            logo_path (str): Path to the logo image file.
            encrypted_template_file_path (str): Path to the encrypted template file.
            data (dict): Data for populating the template.
            tc_id (str): Test case identifier.
            document_name (str): Name of the PDF document to be created.
        """
        self.logger = logger
        self.utils = Utils(self.logger)
        self.tc_id = tc_id
        self.logo_path = logo_path
        self.base64_logo = self._encode_logo()
        self.html_content = self._generate_html(encrypted_template_file_path, data)
        self.head_template = self._create_header_template()
        self.footer_template = self._create_footer_template()
        # self.document_name_pdf = self.utils.get_test_result_folder() + "\\" + document_name + ".pdf"

        self.document_name_pdf = os.path.join(self.utils.get_test_result_folder(), document_name + ".pdf")


    def _encode_logo(self):
        """
        Encodes the logo image to a Base64 string for embedding in the header template.

        Returns:
            str: Base64 encoded representation of the logo image.
        """
        self.logger.debug("Encoding the logo png file")
        with open(self.logo_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _create_header_template(self):
        """
        Generates an HTML header template for the PDF report.

        Returns:
            str: HTML content for the report's header.
        """
        self.logger.debug("Creating the PDF report header template")
        return f'''
        <div style="display: flex; width: 100%; height: auto; justify-content: space-between; align-items: center; border-bottom: 2px solid #413a97;">
            <div style="flex: 0;margin-left: 5px;">
                <img id="logo" src="data:image/png;base64,{self.base64_logo}" alt="Logo" style="max-height: 60px;object-fit: contain;">
            </div>
            <div id="tcid" style="flex: 0;font-size:10px;white-space: nowrap;margin-right: 20px;">
                <h1>{self.tc_id}</h1>
            </div>
        </div>
        '''

    def _create_footer_template(self):
        """
        Generates an HTML footer template for the PDF report.

        Returns:
            str: HTML content for the report's footer.
        """
        self.logger.debug("Creating the PDF report footer template")
        return '''
        <div style='font-size:10px; width:100%; text-align:center;'>
            Page <span class="pageNumber"></span> of <span class="totalPages"></span>
        </div>
        '''

    def _generate_html(self, encrypted_template_file_path, data):
        """
        Decrypts the template file, populates it with data, and generates HTML content.

        Args:
            encrypted_template_file_path (str): Path to the encrypted template file.
            data (dict): Data for populating the template.

        Returns:
            str: HTML content populated with data.
        """
        self.logger.debug("Decrypting the PDF report template")
        # Decrypt the file
        decrypted_template = self.utils.decrypt_file(encrypted_template_file_path)

        # Setup Jinja2 environment and render the HTML template
        env = Environment(loader=FileSystemLoader("."))
        template = env.from_string(decrypted_template)
        output = template.render(data)

        self.logger.debug("Generated the PDF report template with appropriate data")

        # Save the populated HTML to a file
        with open("output.html", "w") as f:
            f.write(output)

        # print("HTML file generated successfully!")
        return output

    async def generate_pdf(self):
        """
        Asynchronously creates a PDF from the generated HTML content, header, and footer templates.

        Returns:
            None
        """
        self.logger.debug("Starting creation of PDF report from template with populated data")
        # browser = await launch({"headless": True})
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
                "top": 85,
                "bottom": 25,
                "left": 25,
                "right": 25
            },
            "displayHeaderFooter": True,
            "headerTemplate": self.head_template,
            "footerTemplate": self.footer_template,
        })

        self.logger.debug("Completed creation of PDF report from template with populated data")

        await browser.close()