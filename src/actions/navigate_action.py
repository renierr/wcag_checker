from src.action_handler import register_action
from src.logger_setup import logger
from src.utils import call_url


@register_action("scroll")
def scroll_action(config, driver, param):
    if param in ["up", "down", "left", "right"]:
        scroll_script = {
            "up": "window.scrollBy(0, -window.innerHeight);",
            "down": "window.scrollBy(0, window.innerHeight);",
            "left": "window.scrollBy(-window.innerWidth, 0);",
            "right": "window.scrollBy(window.innerWidth, 0);"
        }
        driver.execute_script(scroll_script[param])
    else:
        driver.execute_script("document.querySelector(arguments[0]).scrollIntoView();", param)


@register_action("navigate")
def navigate_action(config, driver, param):
    if not param:
        logger.warning("No URL provided for navigation action.")
        return
    call_url(driver, param)


@register_action("hover")
def hover_action(config, driver, param):
    if not param:
        logger.warning("No selector provided for hover action.")
        return
    element = driver.find_element_by_css_selector(param)
    driver.ActionChains(driver).move_to_element(element).perform()

@register_action("back")
def back_action(config, driver, param):
    driver.back()

@register_action("refresh")
def refresh_action(config, driver, param):
    driver.refresh()

