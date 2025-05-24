from pathlib import Path
from src.action_handler import register_action
from src.logger_setup import logger

@register_action("screenshot")
def screenshot_action(config, driver, param):
    """
    Syntax: `@screenshot <filename>`

    Takes a screenshot of the current page and saves it with the specified `<filename>`.
    ```
    @screenshot: my_screenshot.png
    ```
    """
    if not param:
        logger.warning("No data to take a screenshot for action @screenshot.")
        return
    if not param.endswith(".png"):
        param += ".png"
    screenshot = Path(config.output) / "screenshots" / param
    logger.debug(f"Taking screenshot and saving to {screenshot}")
    driver.save_screenshot(screenshot.as_posix())
