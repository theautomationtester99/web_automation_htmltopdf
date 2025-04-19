import os

# Load environment variables
DELETE_TEST_RESULTS = os.getenv("DELETE_TEST_RESULTS_IMAGES_RECORDINGS_FOLDERS_BEFORE_START", "yes")
SCREENSHOT_STRATEGY = os.getenv("SCREENSHOT_STRATEGY", "never")
HIGHLIGHT_ELEMENTS = os.getenv("HIGHLIGHT_ELEMENTS", "no")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "0"))
UPLOAD_TEST_RESULTS = os.getenv("UPLOAD_TEST_RESULTS", "no")
SEND_TEST_RESULTS_EMAIL = os.getenv("SEND_TEST_RESULTS_EMAIL", "no")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "theautomationtester99@gmail.com")
SENDER_EMAIL_PASSWORD = os.getenv("SENDER_EMAIL_PASSWORD", "gAAAAABoAjriMu91TSpf6VycE89O8wv2gpUMx4MkmxAtvFn-Auz4g5RhnPUZJ13FRHkvoM_JnpWau3GoHgcumOmp14Aecg7AKKVORICG87IPFKFX4I6r2xY=")
RECIPIENT_EMAILS = os.getenv("RECIPIENT_EMAILS", "theautomationtester@hotmail.com,theautomationtester99@gmail.com")

RUN_IN_SELENIUM_GRID = os.getenv("RUN_IN_SELENIUM_GRID", "no")
GRID_URL = os.getenv("GRID_URL", "http://localhost:30805/wd/hub")
RUN_IN_APPIUM_GRID = os.getenv("RUN_IN_APPIUM_GRID", "no")
APPIUM_URL = os.getenv("APPIUM_URL", "http://192.168.1.8:4723/wd/hub")

LOG_LEVEL = os.getenv("LOG_LEVEL", "debug")

INPRIVATE = os.getenv("INPRIVATE", "yes")
HEADLESS = os.getenv("HEADLESS", "yes")

NO_THREADS = int(os.getenv("NO_THREADS", "4"))
