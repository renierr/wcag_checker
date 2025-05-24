from selenium import webdriver

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
    """Input text into a field."""
    selector, text = param.split("=", 1)
    logger.info(f"Inputting text '{text}' into element with selector '{selector}'")

    elem = driver.find_element("css selector", selector)
    if not elem.is_displayed():
        logger.warning(f"Element with selector '{selector}' is not displayed.")
        return
    for placeholder, char in special_chars.items():
        text = text.replace(placeholder, char)
    elem.send_keys(text)
    wait_page_loaded(driver)
