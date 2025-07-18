import time

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.action_handler import register_action
from src.config import ProcessingConfig
from src.logger_setup import logger
from src.utils import wait_page_loaded

@register_action("wait")
def wait_action(config: ProcessingConfig, driver: WebDriver, action: dict) -> None:
    """
    Syntax: `@wait: <seconds>` or `@wait: loaded` or `@wait: <selector>`

    Waits for the specified number of seconds before the next step.

    or `loaded` waits until the page is fully loaded.

    or all other text is treated as a selector and waits until the element is present.
    ```
    @wait: loaded
    ```
    """
    try:
        param: str | None = action.get("params", None)
        if not param:
            logger.warning("No wait time or selector provided for wait action.")
            return

        param = param.strip()
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
