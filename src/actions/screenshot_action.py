from src.action_handler import register_action
from src.logger_setup import logger

@register_action("screenshot")
def screenshot_action(config, driver, param):
    if not param:
        logger.warning("No data to take a screenshot for action @screenshot.")
        return
    driver.save_screenshot(param)
