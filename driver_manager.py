import os

import pyautogui as pag
from appium import webdriver as appium_wd
from appium.options.android import UiAutomator2Options
import requests
from config_reader import ConfigReader
from jproperties import Properties
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.edge.options import Options as EdgeOptions


class DriverManager:
    """
    This class is responsible for managing and instantiating web driver instances. It provides configurations
    for browser settings, including private browsing, headless mode, and grid setup. It also reads configurations
    from a properties file for initializing browser behavior.

    Attributes:
        logger (Logger): Logger instance for logging messages.
        config_reader (ConfigReader): An instance of ConfigReader to read configuration properties.
        is_inprivate (bool): A boolean value indicating whether the browser should run in private mode.
        is_headless (bool): A boolean value indicating whether the browser should run in headless mode.
        run_in_selenium_grid (str): A string indicating whether to run in the Selenium grid.
        grid_url (str): The URL for the Selenium grid.
        run_in_appium_grid (str): A string indicating whether to run in the Appium grid.
        appium_url (str): The URL for the Appium grid.
        driver (WebDriver): The WebDriver instance for the launched browser.
    """

    def __init__(self, logger):
        """
        Initializes a new instance of the DriverManager class. Sets up the required browser configurations by
        reading properties from the 'start.properties' file.

        - Sets the environment variable 'WDM_SSL_VERIFY' to '0' to bypass SSL verification.
        - Reads and parses the configuration properties from the 'start.properties' file.
        - Initializes browser settings like private mode, headless mode, and grid configurations.

        Args:
            logger (Logger): Logger instance for logging messages.

        Attributes initialized:
            - config_reader: Reads configuration properties.
            - is_inprivate: Determines if the browser runs in private mode.
            - is_headless: Determines if the browser runs in headless mode.
            - run_in_selenium_grid: Retrieves Selenium grid execution preference.
            - grid_url: Retrieves the Selenium grid URL.
            - run_in_appium_grid: Retrieves Appium grid execution preference.
            - appium_url: Retrieves the Appium grid URL.
        """
        self.logger = logger
        os.environ['WDM_SSL_VERIFY'] = '0'
        self.config_reader = ConfigReader("start.properties")
        self.is_inprivate = self._is_browser_in_private()
        self.is_headless = self._is_browser_headless()
        self.is_running_grid = self._is_running_grid()
        start_configs = Properties()
        with open('start.properties', 'rb') as config_file:
            start_configs.load(config_file)
        self.run_in_selenium_grid = str(
            start_configs.get('run_in_selenium_grid').data)
        self.grid_url = str(start_configs.get('grid_url').data)
        self.run_in_appium_grid = str(
            start_configs.get('run_in_appium_grid').data)
        self.appium_url = str(start_configs.get('appium_url').data)
        self.grid_os_info = ""

    def _is_browser_in_private(self):
        """
        Retrieves the browser's private mode setting from the configuration file.

        Returns:
            bool: True if the browser is configured to run in private mode, False otherwise.
        """
        is_in_private = self.config_reader.get_property('Browser_Settings', 'InPrivate', fallback='No').upper()
        return str(is_in_private.lower())=="yes"

    def _is_browser_headless(self):
        """
        Retrieves the browser's headless mode setting from the configuration file.

        Returns:
            bool: True if the browser is configured to run in headless mode, False otherwise.
        """
        is_headless = self.config_reader.get_property('Browser_Settings', 'Headless', fallback='No').upper()
        return str(is_headless.lower()) == "yes"
    
    def _is_running_grid(self):
        """
        Retrieves the browser's headless mode setting from the configuration file.

        Returns:
            bool: True if the browser is configured to run in headless mode, False otherwise.
        """
        is_running_grid = self.config_reader.get_property('SGrid', 'run_in_selenium_grid', fallback='No').upper()
        return str(is_running_grid.lower()) == "yes"

    def launch_browser(self, browser_name):
        """
        Launches a web browser based on the provided browser name and configuration settings.
        This method supports execution in Selenium Grid, Appium Grid, or a local environment.

        Args:
            browser_name (str): The name of the browser to launch. Supported options include "chrome", "edge", and "firefox".

        Functionality:
            - If running in Selenium Grid:
                - Configures and launches the specified browser (Chrome or Edge) using Selenium Remote WebDriver.
                - Applies browser-specific options, such as disabling automation extensions and customizing preferences.
            - If running in Appium Grid:
                - Configures and launches the specified mobile browser (Chrome) using Appium Remote WebDriver.
                - Loads necessary capabilities for Android devices, such as device name, platform name, and automation framework.
            - If running locally:
                - Configures and launches the specified browser (Chrome, Edge, or Firefox) using WebDriverManager.
                - Applies browser-specific options, such as incognito mode, headless mode, and customized preferences.

        Attributes Used:
            - run_in_selenium_grid: Determines if execution should occur in Selenium Grid.
            - grid_url: URL for the Selenium Grid.
            - run_in_appium_grid: Determines if execution should occur in Appium Grid.
            - appium_url: URL for the Appium Grid.
            - is_inprivate: Specifies if the browser should run in private mode.
            - is_headless: Specifies if the browser should run in headless mode.

        Notes:
            - Firefox browser currently only supports local execution without additional configurations.
            - This method applies extensive browser options for Edge to optimize browser performance and behavior.

        Raises:
            ValueError: If the provided browser_name is not supported.

        Example:
            >>> driver_manager = DriverManager(logger)
            >>> driver_manager.launch_browser("chrome")
        """
        if self.run_in_selenium_grid.lower() == 'yes':
            if browser_name.lower() == "chrome":
                prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False}
                options = Options()
                options.add_experimental_option("useAutomationExtension", False)
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option("prefs", prefs)
                if self.is_inprivate:
                    options.add_argument("--incognito")
                if self.is_headless:
                    options.add_argument("--headless")
                self.driver = webdriver.Remote(command_executor=self.grid_url, options=options)
                self.driver.maximize_window()
                # self.driver = webdriver.Chrome(ChromeDriverManager().install())
                # Query the Selenium Grid API for node status
                try:
                    response = requests.get(f"{self.grid_url}/status")
                    response.raise_for_status()
                    grid_status = response.json()
                    # self.logger.info(f"Full Grid Status Response: {grid_status}")  # Log the full response

                    nodes = grid_status.get("value", {}).get("nodes", [])
                    for node in nodes:
                        os_info = node.get("osInfo", {}).get("name", "Unknown OS")
                        self.grid_os_info = os_info
                        os_version = node.get("osInfo", {}).get("version", "Unknown Version")
                        os_arch = node.get("osInfo", {}).get("arch", "Unknown Architecture")
                        self.logger.info(f"Node OS: {os_info}, Version: {os_version}, Architecture: {os_arch}")
                except requests.RequestException as e:
                    self.logger.error(f"Failed to fetch Selenium Grid status: {e}")
            if browser_name.lower() == "edge":
                prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False, "browser.show_hub_apps_tower": False, "browser.show_hub_apps_tower_pinned": False}
                edge_options = EdgeOptions()
                edge_options.add_experimental_option("useAutomationExtension", False)
                edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                edge_options.add_experimental_option("prefs", prefs)
                if self.is_inprivate:
                    edge_options.add_argument("--incognito")
                if self.is_headless:
                    edge_options.add_argument("--headless")
                # edge_options.add_argument("-inprivate")
                edge_options.add_argument("--disable-extensions")
                self.driver = webdriver.Remote(command_executor=self.grid_url, options=edge_options)
                self.driver.maximize_window()
                pag.press('esc')

                # self.driver = webdriver.Edge(EdgeChromiumDriverManager().install())
                # Query the Selenium Grid API for node status
                try:
                    response = requests.get(f"{self.grid_url}/status")
                    response.raise_for_status()
                    grid_status = response.json()
                    # self.logger.info(f"Full Grid Status Response: {grid_status}")  # Log the full response
                    # Extract OS information from the nodes
                    nodes = grid_status.get("value", {}).get("nodes", [])
                    for node in nodes:
                        os_info = node.get("osInfo", {}).get("name", "Unknown OS")
                        self.grid_os_info = os_info
                        os_version = node.get("osInfo", {}).get("version", "Unknown Version")
                        os_arch = node.get("osInfo", {}).get("arch", "Unknown Architecture")
                        self.logger.info(f"Node OS: {os_info}, Version: {os_version}, Architecture: {os_arch}")
                except requests.RequestException as e:
                    self.logger.error(f"Failed to fetch Selenium Grid status: {e}")
        elif self.run_in_appium_grid.lower() == 'yes':
            if browser_name.lower() == "chrome":
                print('inside loop')
                capabilities = {
                    # 'deviceName': 'Nexus9T',
                    'deviceName': 'Nexus_9_API_34',
                    'platformName': 'Android',
                    'browserName': 'Chrome',
                    'automationName': 'UiAutomator2',
                    # 'systemPort': '10000',
                    # 'chromeDriverPort': '11000',
                    'udid': 'emulator-5554'
                }
                capabilities_options = UiAutomator2Options().load_capabilities(capabilities)

                self.driver = appium_wd.Remote(self.appium_url, options=capabilities_options)
                # self.driver.maximize_window()
                # self.driver = webdriver.Chrome(ChromeDriverManager().install())
            if browser_name.lower() == "edge":
                prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False, "browser.show_hub_apps_tower": False, "browser.show_hub_apps_tower_pinned": False}
                edge_options = EdgeOptions()
                edge_options.add_experimental_option("useAutomationExtension", False)
                edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                edge_options.add_experimental_option("prefs", prefs)
                # edge_options.add_argument("-inprivate")
                edge_options.add_argument("--disable-extensions")
                self.driver = webdriver.Remote(command_executor=self.grid_url, options=edge_options)
                self.driver.maximize_window()
                pag.press('esc')

                # self.driver = webdriver.Edge(EdgeChromiumDriverManager().install())
        else:
            if browser_name.lower() == "chrome":
                prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False}
                options = Options()
                options.add_experimental_option("useAutomationExtension", False)
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option("prefs", prefs)
                if self.is_inprivate:
                    options.add_argument("--incognito")
                if self.is_headless:
                    options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                self.driver = webdriver.Chrome(options=options)
                # self.driver = webdriver.Chrome(options=options, service=ChromeService(ChromeDriverManager().install()))
                # self.driver = webdriver.Chrome(options=options)
                self.driver.maximize_window()
                # self.driver = webdriver.Chrome(ChromeDriverManager().install())
            if browser_name.lower() == "edge":
                prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False, "browse.show_hub_apps_tower": False, "browser.show_hub_apps_tower_pinned": False}
                edge_options = EdgeOptions()
                edge_options.add_experimental_option("useAutomationExtension", False)
                edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                edge_options.add_experimental_option("prefs", prefs)
                if self.is_inprivate:
                    edge_options.add_argument("--inprivate")
                if self.is_headless:
                    edge_options.add_argument("--headless")
                edge_options.add_argument("--disable-extensions")
                edge_options.add_argument("--disable-gpu")
                edge_options.add_argument("--disable-field-trial-config")
                edge_options.add_argument("--disable-background-networking")
                edge_options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
                edge_options.add_argument("--disable-background-timer-throttling")
                edge_options.add_argument("--disable-backgrounding-occluded-windows")
                edge_options.add_argument("--disable-back-forward-cache")
                edge_options.add_argument("--disable-breakpad")
                edge_options.add_argument("--disable-client-side-phishing-detection")
                edge_options.add_argument("--disable-component-extensions-with-background-pages")
                edge_options.add_argument("--disable-component-update")
                edge_options.add_argument("--no-default-browser-check")
                edge_options.add_argument("--disable-default-apps")
                edge_options.add_argument("--disable-dev-shm-usage")
                edge_options.add_argument("--disable-extensions")
                edge_options.add_argument(
                    "--disable-features=ImprovedCookieControls,LazyFrameLoading,GlobalMediaControls,"
                    "DestroyProfileOnBrowserClose,MediaRouter,DialMediaRouteProvider,AcceptCHFrame,"
                    "AutoExpandDetailsElement,CertificateTransparencyComponentUpdater,"
                    "AvoidUnnecessaryBeforeUnloadCheckSync,Translate")
                edge_options.add_argument("--allow-pre-commit-input")
                edge_options.add_argument("--disable-hang-monitor")
                edge_options.add_argument("--disable-ipc-flooding-protection")
                edge_options.add_argument("--disable-popup-blocking")
                edge_options.add_argument("--disable-prompt-on-repost")
                edge_options.add_argument("--disable-renderer-backgrounding")
                edge_options.add_argument("--disable-sync")
                edge_options.add_argument("--force-color-profile=srgb")
                edge_options.add_argument("--metrics-recording-only")
                edge_options.add_argument("--no-first-run")
                # edge_options.add_argument("--enable-automation")
                edge_options.add_argument("--password-store=basic")
                edge_options.add_argument("--use-mock-keychain")
                edge_options.add_argument("--no-service-autorun")
                edge_options.add_argument("--export-tagged-pdf")
                edge_options.add_argument("--no-sandbox")
                # edge_options.add_argument("--user-data-dir=new_profile_dir")
                # self.driver = webdriver.Edge(options=edge_options, service=EdgeService(EdgeChromiumDriverManager().install()))
                self.driver = webdriver.Edge(options=edge_options)
                self.driver.maximize_window()
                # self.driver = webdriver.Edge(EdgeChromiumDriverManager().install())
                # time.sleep(5)
                # pag.press('esc')
            if browser_name.lower() == "firefox":
                self.driver = webdriver.Firefox()
                self.driver.maximize_window()
