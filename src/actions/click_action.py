from selenium import webdriver

from src.action_handler import register_action
from src.config import Config
from src.logger_setup import logger
from src.utils import wait_page_loaded

@register_action("click")
def click_action(config: Config, driver: webdriver, param: str) -> None:
    """Click on an element."""
    logger.info(f"Clicking on element with selector '{param}'")
    elem = driver.find_element("css selector", param)
    elem.click()
    wait_page_loaded(driver)
