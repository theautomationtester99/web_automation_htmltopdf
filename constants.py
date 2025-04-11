"""
constants.py

This module defines constants used throughout the web automation framework. 
These constants include valid keywords for test case execution and other 
framework-specific configurations.

Constants:
    VALID_KEYWORDS (tuple): A tuple of valid keywords that can be used in 
                            test case definitions for various operations 
                            such as opening a browser, entering a URL, 
                            interacting with elements, and more.
"""

VALID_KEYWORDS = ("tc_id", "tc_desc", "open_browser", "enter_url", "type", "click", "select_file", "verify_displayed_text","mcnp_choose_date_from_datepicker",  "wait_for_seconds","login_jnj", "check_element_enabled", "check_element_disabled","check_element_displayed", "step", "switch_to_iframe", "switch_to_default_content")