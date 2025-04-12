def start_runner(testscript_file, rlog_queue, rlock, start_props_reader, object_repo_reader, launch_browser=''):
    """
    Initializes and executes the test script.

    This function sets up the test execution environment, validates configurations, processes the test script,
    and executes test steps based on predefined keywords. It also generates reports summarizing the test results.

    Args:
        testscript_file (str): The path to the test script Excel file.
        rlog_queue (Queue): A multiprocessing queue for logging.
        rlock (Lock): A multiprocessing lock for thread-safe operations.
        start_props_reader (ConfigReader): Reader for the 'start.properties' configuration file.
        object_repo_reader (ConfigReader): Reader for the 'object_repository.properties' configuration file.
        launch_browser (str, optional): Specifies the browser to launch. Defaults to an empty string.

    Raises:
        ValueError: If invalid configurations or test script data are encountered.
        Exception: If an error occurs during test script execution.
    """
    logger_config = LoggerConfig(log_queue=rlog_queue)
    wafl = logger_config.logger
    utils = Utils(wafl)

    wafl.info("Starting test script execution.")
    wafl.debug(f"Test script file: {testscript_file}")
    wafl.debug(f"Launch browser parameter: {launch_browser}")

    data_run_in_selenium_grid = str(start_props_reader.get_property('SGrid', 'run_in_selenium_grid', fallback='No')).lower()
    data_run_in_appium_grid = str(start_props_reader.get_property('Appium', 'run_in_appium_grid', fallback='No')).lower()

    wafl.debug(f"Run in Selenium Grid: {data_run_in_selenium_grid}")
    wafl.debug(f"Run in Appium Grid: {data_run_in_appium_grid}")

    if data_run_in_selenium_grid == data_run_in_appium_grid == 'yes':
        wafl.error("Both 'run_in_appium_grid' and 'run_in_selenium_grid' are set to 'Yes' in 'start.properties'. Only one should be set to 'Yes'.")
        raise ValueError("In 'start.properties' file, both 'run_in_appium_grid' and 'run_in_selenium_grid' are set as 'Yes'. Only one should be set as 'Yes'.")

    wafl.debug("Instantiating Excel report manager.")
    e_report = ExcelReportManager(wafl, rlock)

    wafl.debug("Validating the test script file format.")