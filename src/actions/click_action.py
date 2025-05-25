from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

from src.action_handler import register_action
from src.config import Config
from src.logger_setup import logger
from src.utils import wait_page_loaded

@register_action("click")
def click_action(config: Config, driver: webdriver, param: str) -> None:
    """
    Syntax: `@click <selector>`

    Clicks the element identified by the CSS selector `<selector>`.
    ```
    @click: #submit-button
    ```
    """
    if not param:
        logger.warning("No selector provided for click action.")
        return
    try:
        elem = driver.find_element(By.CSS_SELECTOR, param)
        elem.click()
        wait_page_loaded(driver)
    except NoSuchElementException as e:
        logger.warning(f"No element found for click action with selector: {param}")
        return
