import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.action_handler import register_action
from src.config import Config
from src.logger_setup import logger
from src.utils import wait_page_loaded

@register_action("wait")
def wait_action(config: Config, driver: webdriver, param: str) -> None:
    """Wait for a specific time or until a page is loaded."""
    try:
        if param.endswith("s"):
            wait_time = int(param[:-1])  # Interpret as seconds
        elif param.endswith("m"):
            wait_time = int(param[:-1]) * 60  # Interpret as minutes
        elif param.isdigit():
            wait_time = int(param)  # Default to seconds if no suffix
        else:
            # If param is not a number, assume it's an ID to wait for, if the id is 'loaded'
            # then use our own page loaded function
            if param == "loaded":
                logger.info("Waiting for page to load")
                wait_page_loaded(driver)
                return
            timeout = 10
            logger.info(f"Waiting for element with ID '{param}' to exist (timeout: {timeout} seconds)")
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, param)))
            return

        if wait_time > 0:
            logger.info(f"Waiting for {wait_time} seconds")
            time.sleep(wait_time)
    except ValueError:
        logger.error(f"Invalid wait time: {param}. Must be an integer or have a valid suffix (s/m).")
