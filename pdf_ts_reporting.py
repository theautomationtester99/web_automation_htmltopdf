from jinja2 import Environment, FileSystemLoader
import base64
from pyppeteer import launch

from utilities import Utils
import os


class PdfTsReporting:
    def __init__(self, logo_path, encrypted_template_file_path, data, document_name):
        self.utils = Utils()
        self.logo_path = logo_path
        self.base64_logo = self._encode_logo()
        self.html_content = self._generate_html(encrypted_template_file_path, data)
        self.head_template = self._create_header_template()
        self.footer_template = self._create_footer_template()
        #self.document_name_pdf = self.utils.get_test_result_folder() + "\\" + document_name + ".pdf"
        self.document_name_pdf = os.path.join(self.utils.get_test_result_folder(), document_name + ".pdf")
    
    def _encode_logo(self):
        with open(self.logo_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _create_header_template(self):
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
        return '''
        <div style='font-size:10px; width:100%; text-align:center;'>
            Page <span class="pageNumber"></span> of <span class="totalPages"></span>
        </div>
        '''

    def _generate_html(self, encrypted_template_file_path, data):
        # Decrypt the file
        decrypted_template = self.utils.decrypt_file(encrypted_template_file_path)

        # Setup Jinja2 environment and render the HTML template
        env = Environment(loader=FileSystemLoader("."))
        template = env.from_string(decrypted_template)
        output = template.render(data=data)

        # Save the populated HTML to a file
        with open("output.html", "w") as f:
            f.write(output)

        # print("HTML file generated successfully!")
        return output
    
    async def generate_pdf(self):
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

        await browser.close()