from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from src.action_handler import register_action
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
    if not param or "=" not in param:
        logger.warning("Invalid parameter for input action. Expected format: 'selector=value'.")
        return

    selector, text = param.split("=", 1)
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
    if not param or "=" not in param:
        logger.warning("Invalid parameter for select action. Expected format: 'selector=value'.")
        return
    selector, value = param.split("=", 1)
    logger.debug(f"Selecting value '{value}' in element with selector '{selector}'")
    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)
        Select(element).select_by_visible_text(value)
    except NoSuchElementException:
        logger.warning(f"No element found for select action with selector: {selector}")
        return
