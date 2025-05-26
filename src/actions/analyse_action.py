from dataclasses import fields
from pathlib import Path

from selenium import webdriver

from src.action_handler import register_action, parse_param_to_json
from src.config import ProcessingConfig, Runner
from src.logger_setup import logger
from src.mode_axe import axe_mode_setup, axe_mode
from src.mode_own import own_mode_contrast
from src.utils import reset_window_size, call_url, set_window_size_to_viewport

url_idx = 0
axe = None

@register_action("analyze")
@register_action("analyse")
def analyse_action(config: ProcessingConfig, driver: webdriver, param: str|None) -> dict | None:
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
    if config.runner == Runner.AXE and not axe:
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

    # select runner to run the check
    if config.runner == Runner.AXE:
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


def _analyse_runner(runner: Runner, config: ProcessingConfig, driver: webdriver, param: str | None) -> dict | None:
    """
    Internal function to handle the different analysis action runners.
    This is used to avoid code duplication in the `analyse_action` function.
    """
    check_options = parse_param_to_json(param)
    check_param = None
    if check_options is None:
        check_param = param
        check_options = {}

    # build new config object with options set
    base_fields = {field.name for field in fields(ProcessingConfig) if field.init}
    check_config = ProcessingConfig(
        **{key: value for key, value in vars(config).items() if key in base_fields},
        **check_options
    )
    check_config.runner = runner
    # analyse the page with the given axe config
    return analyse_action(check_config, driver, check_param)


@register_action("analyse_axe")
def analyse_axe_action(config: ProcessingConfig, driver: webdriver, param: str|None) -> dict | None:
    """
    Syntax: `@analyse_axe: <config>`

    Triggers an analysis of the current page using Axe.
    The `<config>` parameter can be a JSON string with Axe options,
    or it can be omitted to use the default Axe configuration if provided on startup.
    ```
    @analyse_axe: {axe_rules: ["wcag2aa"]}
    ```
    """
    return _analyse_runner(Runner.AXE, config, driver, param)


@register_action("analyse_contrast")
def analyse_contrast_action(config: ProcessingConfig, driver: webdriver, param: str|None) -> dict | None:
    """
    Syntax: `@analyse_contrast: <config>`

    Triggers an analysis of the current page using Contrast.
    The `<config>` parameter can be a JSON string with Contrast options,
    or it can be omitted to use the default Contrast configuration if provided on startup.
    ```
    @analyse_contrast: {contrast_threshold: 4.5, selector: "a, button:not([disabled])"}
    @analyse_axe: {}
    ```
    """
    return _analyse_runner(Runner.CONTRAST, config, driver, param)

