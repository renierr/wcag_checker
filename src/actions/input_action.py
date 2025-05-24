from selenium import webdriver
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

    elem = driver.find_element("css selector", selector)
    if not elem.is_displayed():
        logger.warning(f"Element with selector '{selector}' is not displayed.")
        return
    for placeholder, char in special_chars.items():
        text = text.replace(placeholder, char)
    elem.send_keys(text)
    wait_page_loaded(driver)

@register_action("clear")
def clear_action(config, driver, param):
    if not param:
        logger.warning("no selector provided for clear action.")
        return
    element = driver.find_element_by_css_selector(param)
    element.clear()

@register_action("select")
def select_action(config, driver, param):
    if not param or "=" not in param:
        logger.warning("Invalid parameter for select action. Expected format: 'selector=value'.")
        return
    selector, value = param.split("=", 1)
    logger.debug(f"Selecting value '{value}' in element with selector '{selector}'")
    element = driver.find_element_by_css_selector(selector)
    Select(element).select_by_visible_text(value)
