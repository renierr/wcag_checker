from pathlib import Path

from selenium import webdriver

from src.action_handler import register_action
from src.config import Config, Mode
from src.logger_setup import logger
from src.mode_axe import axe_mode_setup, axe_mode
from src.mode_own import own_mode_contrast
from src.utils import reset_window_size, call_url, set_window_size_to_viewport

url_idx = 0
axe = None

@register_action("analyze")
@register_action("analyse")
def analyse_action(config: Config, driver: webdriver, param: str|None) -> dict | None:
    """Analyse the page using a specific action."""
    global url_idx
    global axe
    if config.mode == Mode.AXE and not axe:
        axe = axe_mode_setup(config, driver)

    url_idx += 1
    logger.info(f"[{url_idx}] Analysing page '{param if param else 'current'}'")
    results = []
    screenshots_folder = Path(config.output) / "screenshots"

    if param:
        # analyse param is considered a new url to change to except it begins with " or ' then it is the page title
        if param.startswith('"') and param.endswith('"') or param.startswith("'") and param.endswith("'"):
            # remove the quotes
            param = param[1:-1]
            logger.info(f"Page title: {param}")
            page_title = param
        else:
            reset_window_size(driver, width=config.resolution_width, height=config.resolution_height)
            call_url(driver, param)
            set_window_size_to_viewport(driver)
            page_title = driver.title
    else:
        # if no param is given, we assume the current page is the one to analyse
        page_title = driver.title


    # take full-pagescreenshot
    full_page_screenshot_path = Path(config.output) / f"{config.mode.value}_{url_idx}_full_page_screenshot.png"
    logger.debug(f"Taking full-page screenshot and saving to: {full_page_screenshot_path}")
    driver.save_screenshot(full_page_screenshot_path)

    # select mode to run the check
    if config.mode == Mode.AXE:
        full_page_screenshot_path_outline = axe_mode(axe, config, driver,
                                                     results, screenshots_folder, url_idx)
    else:
        full_page_screenshot_path_outline = own_mode_contrast(config, driver,
                                                              results, screenshots_folder, url_idx)
    # save results
    entry = {
        "url": param,
        "index": url_idx,
        "results": results,
        "title": page_title if 'page_title' in locals() else None,
    }
    if full_page_screenshot_path:
        entry["screenshot"] = full_page_screenshot_path.as_posix()
    if full_page_screenshot_path_outline:
        entry["screenshot_outline"] = full_page_screenshot_path_outline.as_posix()
    return entry
