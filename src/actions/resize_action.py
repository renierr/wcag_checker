from src.action_handler import register_action
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
def resize_action(config, driver, param):
    """Resize the browser window."""
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
