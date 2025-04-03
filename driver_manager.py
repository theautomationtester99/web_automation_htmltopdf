import os
import time

import pyautogui as pag
from appium import webdriver as appium_wd
from appium.options.android import UiAutomator2Options
from jproperties import Properties
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.edge.options import Options as EdgeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager


class DriverManager:
    """
    This class is for instantiating web driver instances.
    """

    def __init__(self):
        os.environ['WDM_SSL_VERIFY'] = '0'
        start_configs = Properties()
        with open('start.properties', 'rb') as config_file:
            start_configs.load(config_file)
        self.run_in_selenium_grid = str(
            start_configs.get('run_in_selenium_grid').data)
        self.grid_url = str(start_configs.get('grid_url').data)
        self.run_in_appium_grid = str(
            start_configs.get('run_in_appium_grid').data)
        self.appium_url = str(start_configs.get('appium_url').data)

    def launch_browser(self, browser_name):
        if self.run_in_selenium_grid.lower() == 'yes':
            if browser_name.lower() == "chrome":
                prefs = {"credentials_enable_service": False,
                         "profile.password_manager_enabled": False}
                options = Options()
                options.add_experimental_option(
                    "useAutomationExtension", False)
                options.add_experimental_option(
                    "excludeSwitches", ["enable-automation"])
                options.add_experimental_option("prefs", prefs)
                self.driver = webdriver.Remote(
                    command_executor=self.grid_url, options=options)
                self.driver.maximize_window()
                # self.driver = webdriver.Chrome(ChromeDriverManager().install())
            if browser_name.lower() == "edge":
                prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False,
                         "browser.show_hub_apps_tower": False, "browser.show_hub_apps_tower_pinned": False}
                edge_options = EdgeOptions()
                edge_options.add_experimental_option(
                    "useAutomationExtension", False)
                edge_options.add_experimental_option(
                    "excludeSwitches", ["enable-automation"])
                edge_options.add_experimental_option("prefs", prefs)
                # edge_options.add_argument("-inprivate")
                edge_options.add_argument("--disable-extensions")
                self.driver = webdriver.Remote(
                    command_executor=self.grid_url, options=edge_options)
                self.driver.maximize_window()
                pag.press('esc')

                # self.driver = webdriver.Edge(EdgeChromiumDriverManager().install())
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
                prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False,
                         "browser.show_hub_apps_tower": False, "browser.show_hub_apps_tower_pinned": False}
                edge_options = EdgeOptions()
                edge_options.add_experimental_option(
                    "useAutomationExtension", False)
                edge_options.add_experimental_option(
                    "excludeSwitches", ["enable-automation"])
                edge_options.add_experimental_option("prefs", prefs)
                # edge_options.add_argument("-inprivate")
                edge_options.add_argument("--disable-extensions")
                self.driver = webdriver.Remote(
                    command_executor=self.grid_url, options=edge_options)
                self.driver.maximize_window()
                pag.press('esc')

                # self.driver = webdriver.Edge(EdgeChromiumDriverManager().install())
        else:
            if browser_name.lower() == "chrome":
                prefs = {"credentials_enable_service": False,
                         "profile.password_manager_enabled": False}
                options = Options()
                options.add_experimental_option(
                    "useAutomationExtension", False)
                options.add_experimental_option(
                    "excludeSwitches", ["enable-automation"])
                options.add_experimental_option("prefs", prefs)
                options.add_argument("--no-sandbox")
                self.driver = webdriver.Chrome(options=options, service=ChromeService(ChromeDriverManager(
                ).install()))
                # self.driver = webdriver.Chrome(options=options)
                self.driver.maximize_window()
                # self.driver = webdriver.Chrome(ChromeDriverManager().install())
            if browser_name.lower() == "edge":
                prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False,
                         "browse.show_hub_apps_tower": False, "browser.show_hub_apps_tower_pinned": False}
                edge_options = EdgeOptions()
                edge_options.add_experimental_option(
                    "useAutomationExtension", False)
                edge_options.add_experimental_option(
                    "excludeSwitches", ["enable-automation"])
                edge_options.add_experimental_option("prefs", prefs)
                # edge_options.add_argument("--inprivate")
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
                self.driver = webdriver.Edge(options=edge_options,
                                             service=EdgeService(EdgeChromiumDriverManager().install()))
                # self.driver = webdriver.Edge(options=edge_options)
                self.driver.maximize_window()
                # self.driver = webdriver.Edge(EdgeChromiumDriverManager().install())
                time.sleep(10)
                pag.press('esc')
            if browser_name.lower() == "firefox":
                self.driver = webdriver.Firefox()
                self.driver.maximize_window()
