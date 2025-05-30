from pathlib import Path
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By

from src.action_handler import register_action, parse_param_to_key_value
from src.config import ProcessingConfig
from src.logger_setup import logger

@register_action("screenshot")
def screenshot_action(config: ProcessingConfig, driver: WebDriver, param: str | None = None) -> None:
    """
    Syntax: `@screenshot <filename>=<selector>`

    Takes a screenshot of the current page and saves it with the specified `<filename>`.
    If optional `<selector>` is provided, it will take a screenshot of that specific element.
    This is done by separating the filename and selector with an equals sign (`=`).
    ```
    @screenshot: my_screenshot.png
    @screenshot: my_screenshot.png=#header
    ```
    """
    if not param:
        logger.warning("No data to take a screenshot for action @screenshot.")
        return

    parts = parse_param_to_key_value(param)
    filename = parts[0]
    selector = parts[1] if len(parts) > 1 else None

    if not param.endswith(".png"):
        param += ".png"

    screenshot_path = Path(config.output) / "screenshots" / filename
    logger.debug(f"Taking screenshot for '{selector if selector else 'all'}' and saving to {screenshot_path}")

    if selector:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            element.screenshot(screenshot_path.as_posix())
        except Exception as e:
            logger.error(f"Failed to take screenshot of element '{selector}': {e}")
    else:
        driver.save_screenshot(screenshot_path.as_posix())

