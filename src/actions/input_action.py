from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from src.action_handler import register_action, parse_param_to_key_value
from src.config import Config
from src.logger_setup import logger
from src.utils import wait_page_loaded

special_chars = {
    "<CR>": "\r",
    "<LF>": "\n",
    "<TAB>": "\t"
}

@register_action("input")
def input_action(config: Config, driver: webdriver, param: str) -> None:
    """
    Syntax: `@input <selector>=<text>`

    Types the given `<text>` into the input field identified by `<selector>`.
    ```
    @input #username-field=My input text<LF>
    ```
    You can use special characters `<LF>` for new lines or `<TAB>` for tabs.
    """
    if not param or "=" not in param:
        logger.warning("Invalid parameter for input action. Expected format: 'selector=value'.")
        return

    selector, text = parse_param_to_key_value(param)
    logger.debug(f"Inputting text '{text}' into element with selector '{selector}'")

    try:
        elem = driver.find_element(By.CSS_SELECTOR, selector)
        for placeholder, char in special_chars.items():
            text = text.replace(placeholder, char)
        elem.send_keys(text)
        wait_page_loaded(driver)
    except NoSuchElementException:
        logger.warning(f"Element with selector '{selector}' is not displayed.")
        return

@register_action("clear")
def clear_action(config, driver, param):
    """
    Syntax: `@clear <selector>`

    Clears the input field identified by the CSS selector `<selector>`.
    ```
    @clear: #input-field
    ```
    """
    if not param:
        logger.warning("no selector provided for clear action.")
        return
    try:
        element = driver.find_element(By.CSS_SELECTOR, param)
        element.clear()
    except NoSuchElementException:
        logger.warning(f"No element found for clear action with selector: {param}")
        return

@register_action("select")
def select_action(config, driver, param):
    """
    Syntax: `@select <selector>=<value>`

    Selects an option from a dropdown or select element identified by the CSS selector `<selector>`.
    You can specify the option value to select.
    ```
    @select: #dropdown-menu=option_value
    ```
    """
    if not param or "=" not in param:
        logger.warning("Invalid parameter for select action. Expected format: 'selector=value'.")
        return
    selector, value = parse_param_to_key_value(param)
    logger.debug(f"Selecting value '{value}' in element with selector '{selector}'")
    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)
        Select(element).select_by_value(value)
    except NoSuchElementException:
        logger.warning(f"No element found for select action with selector: {selector}")
        return
