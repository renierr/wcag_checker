from dataclasses import fields
from pathlib import Path

from selenium import webdriver

from src.action_handler import register_action, parse_param_to_json
from src.config import Config, Mode, AxeConfig, ContrastConfig, ProcessingConfig
from src.logger_setup import logger
from src.mode_axe import axe_mode_setup, axe_mode
from src.mode_own import own_mode_contrast
from src.utils import reset_window_size, call_url, set_window_size_to_viewport

url_idx = 0
axe = None

@register_action("analyze")
@register_action("analyse")
def analyse_action(config: Config, driver: webdriver, param: str|None) -> dict | None:
    """
    Syntax: `@analyse` or `@analyse "My page Title"` or `@analyse <url>`

    Triggers an analysis of the current page (e.g., WCAG or contrast check).
    ```
    @analyse
    ```
    Optionally, you can pass a parameter.

    Where text in brackets `"My page Title"` is used as the title in the report.

    Or a Url that first will be navigated to before the analysis is performed, e.g., `/my_sub_page/index.html`.
    """
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
        "config": config.__dict__,
        "results": results,
        "title": page_title if 'page_title' in locals() else None,
    }
    if full_page_screenshot_path:
        entry["screenshot"] = full_page_screenshot_path.as_posix()
    if full_page_screenshot_path_outline:
        entry["screenshot_outline"] = full_page_screenshot_path_outline.as_posix()
    return entry

@register_action("analyse_axe")
def analyse_axe_action(config: Config, driver: webdriver, param: str|None) -> dict | None:
    """
    Syntax: `@analyse_axe: <config>`

    Triggers an analysis of the current page using Axe.
    The `<config>` parameter can be a JSON string with Axe options,
    or it can be omitted to use the default Axe configuration if provided on startup.
    ```
    @analyse_axe: {axe_rules: ["wcag2aa"]}
    ```
    """

    axe_options = parse_param_to_json(param)
    if not isinstance(config, AxeConfig) and not axe_options:
        logger.error("No Axe configuration provided for @analyse_axe action.")
        return None

    # build new config object with options set
    base_fields = {field.name for field in fields(ProcessingConfig) if field.init}
    axe_config = ContrastConfig(
        **{key: value for key, value in vars(config).items() if key in base_fields},
        **axe_options
    ) if axe_options else config
    axe_config.mode = Mode.AXE
    # analyse the page with the given axe config
    analyse_action(axe_config, driver, None)



@register_action("analyse_contrast")
def analyse_contrast_action(config: Config, driver: webdriver, param: str|None) -> dict | None:
    """
    Syntax: `@analyse_contrast: <config>`

    Triggers an analysis of the current page using Contrast.
    The `<config>` parameter can be a JSON string with Contrast options,
    or it can be omitted to use the default Contrast configuration if provided on startup.
    ```
    @analyse_contrast: {contrast_threshold: 4.5, selector: "a, button:not([disabled])"}
    ```
    """

    contrast_options = parse_param_to_json(param)
    if not isinstance(config, ContrastConfig) and not contrast_options:
        logger.error("No Contrast configuration provided for @analyse_contrast action.")
        return None

    # build new config object with options set
    base_fields = {field.name for field in fields(ProcessingConfig) if field.init}
    contrast_config = ContrastConfig(
        **{key: value for key, value in vars(config).items() if key in base_fields},
        **contrast_options
    ) if contrast_options else config
    contrast_config.mode = Mode.CONTRAST

    # analyse the page with the given axe config
    return analyse_action(contrast_config, driver, None)

