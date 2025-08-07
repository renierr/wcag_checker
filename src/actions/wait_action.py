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
    Syntax: `@wait` or `@wait: <seconds>[s|m]` or  `@wait: [!]<selector>`

    Waits for the specified number of seconds before the next step if param starts with a digit.
    If no parameter is given, it waits for page loaded.

    all other text is treated as a selector and waits until the element is present.
    If the selector starts with `!` it will wait for the element to be absent instead.

    The timeout for waiting for an element is 10 seconds by default.

    Examples:
    ```
    @wait
    @wait: !#my-element-id-absent
    @wait: 5
    @wait: 2m
    @wait: #myid
    ```
    """
    try:
        param: str | None = action.get("params", None)
        timeout = 10

        if not param:
            logger.info("No wait time specified, waiting for page to load")
            wait_page_loaded(driver)
            return

        if param.startswith("!"):
            # If the parameter starts with '!', wait for the element to be absent
            param = param[1:]
            logger.info(f"Waiting for element with ID '{param}' to not exist (timeout: {timeout} seconds)")
            WebDriverWait(driver, timeout).until(EC.staleness_of(driver.find_element(By.CSS_SELECTOR, param)))
            return

        if not param[0].isdigit():
            logger.info(f"Waiting for element with ID '{param}' to exist (timeout: {timeout} seconds)")
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, param)))
            return

        wait_time = 0
        if param.endswith("s"):
            wait_time = int(param[:-1])  # Interpret as seconds
        elif param.endswith("m"):
            wait_time = int(param[:-1]) * 60  # Interpret as minutes
        elif param.isdigit():
            wait_time = int(param)  # Default to seconds if no suffix

        if wait_time > 0:
            logger.info(f"Waiting for {wait_time} seconds")
            time.sleep(wait_time)
    except ValueError:
        logger.error(f"Invalid wait time: {param}. Must be an integer or have a valid suffix (s/m).")
