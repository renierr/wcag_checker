from selenium import webdriver

from src.action_handler import register_action
from src.config import ProcessingConfig
from src.logger_setup import logger
from src.utils import set_window_size_to_viewport

PREDEFINED_RESOLUTIONS = {
    "mobile": (375, 667),
    "mobile_landscape": (667, 375),
    "tablet": (768, 1024),
    "tablet_landscape": (1024, 768),
    "desktop": (1920, 1080),
}

@register_action("resize")
def resize_action(config: ProcessingConfig, driver: webdriver, param: str | None) -> None:
    """
    Syntax: `@resize <size | predefined | full>`

    Resizes the browser window to a specific size or view.
    - `size`: Specify a width and height (e.g., `@resize: 1024x768`).
    - `predefined`: Use a predefined size like `mobile`, `tablet`, or `desktop` (e.g., `@resize: mobile`).
    - `full`: Resizes to full inner width and height, so that all content will be visible (e.g., `@resize: full`).
    ```
    @resize: 1024x768
    @resize: mobile
    @resize: full
    ```
    """
    try:
        if not param or param in ["full"]:
            set_window_size_to_viewport(driver)
            return
        elif param in PREDEFINED_RESOLUTIONS:
            width, height = PREDEFINED_RESOLUTIONS[param]
            driver.set_window_size(width, height)
            logger.debug(f"Resized browser window to predefined {param} size: {width}x{height}.")
        else:
            width, height = map(int, param.split('x'))
            driver.set_window_size(width, height)
            logger.debug(f"Resized browser window to {width}x{height}.")
    except ValueError as e:
        logger.error(f"Invalid size format for resize action: {param}. Expected format is 'widthxheight' or named 'view | full'. Error: {e}")
    except Exception as e:
        logger.error(f"Error resizing browser window: {e}")
