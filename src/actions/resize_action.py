from selenium.webdriver.remote.webdriver import WebDriver

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
def resize_action(config: ProcessingConfig, driver: WebDriver, action: dict) -> None:
    """
    Syntax: `@resize: <size | predefined | full>`

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
        param: str | None = action.get("params", None)
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

@register_action("zoom")
def zoom_action(config: ProcessingConfig, driver: WebDriver, action: dict) -> None:
    """
    Syntax: `@zoom: <factor>`

    Zooms the browser window to a specific factor.
    - `factor`: Specify a zoom factor (e.g., `@zoom: 1.5` for 150% zoom) or percentage with % char at the end.
    ```
    @zoom: 1.5
    ```
    """
    param : str | None = action.get("params", None)
    if not param:
        logger.error("Zoom action requires a zoom factor parameter.")
        return

    try:
        if param.endswith('%'):
            factor = float(param[:-1]) / 100.0
        else:
            factor = float(action.get("params", 1.0))

        driver.execute_script(f"document.body.style.zoom = '{factor}';")
        logger.debug(f"Zoomed browser window to {factor * 100}%.")
    except ValueError as e:
        logger.error(f"Invalid zoom factor: {param}. Expected a number. Error: {e}")
    except Exception as e:
        logger.error(f"Error zooming browser window: {e}")

