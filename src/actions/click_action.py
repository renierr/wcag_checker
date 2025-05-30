from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

from src.action_handler import register_action
from src.config import ProcessingConfig
from src.logger_setup import logger
from src.utils import wait_page_loaded

@register_action("click")
def click_action(config: ProcessingConfig, driver: WebDriver, param: str | None) -> None:
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

@register_action("click_double")
def click_double_action(config: ProcessingConfig, driver: WebDriver, param: str | None) -> None:
    """
    Syntax: `@click_double <selector>`

    Double-Clicks the element identified by the CSS selector `<selector>`.
    ```
    @click_double: #double-click-item
    ```
    """
    if not param:
        logger.warning("No selector provided for click_double action.")
        return
    try:
        elem = driver.find_element(By.CSS_SELECTOR, param)
        ActionChains(driver).double_click(elem).perform()
    except NoSuchElementException as e:
        logger.warning(f"No element found for click_double action with selector: {param}")
        return


@register_action("click_context")
def click_context_action(config: ProcessingConfig, driver: WebDriver, param: str | None) -> None:
    """
    Syntax: `@click_context <selector>`

    Right Click (context) the element identified by the CSS selector `<selector>`.
    ```
    @click_context: #context-menu-item
    ```
    """
    if not param:
        logger.warning("No selector provided for click_context action.")
        return
    try:
        elem = driver.find_element(By.CSS_SELECTOR, param)
        ActionChains(driver).context_click(elem).perform()
    except NoSuchElementException as e:
        logger.warning(f"No element found for click_context action with selector: {param}")
        return
