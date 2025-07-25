from dataclasses import fields
from pathlib import Path

from selenium.webdriver.remote.webdriver import WebDriver

from src.action_handler import register_action, parse_param_to_dict
from src.config import ProcessingConfig, Runner
from src.logger_setup import logger
from src.runner_axe import runner_axe
from src.runner_contrast import runner_contrast
from src.runner_tab import runner_tab
from src.utils import take_fullpage_screenshot, count_violations

runner_function_map = {
    Runner.AXE: runner_axe,
    Runner.CONTRAST: runner_contrast,
    Runner.TAB: runner_tab,
}

input_idx = 0
tabpath_checker = None

@register_action("analyze")
@register_action("analyse")
def analyse_action(config: ProcessingConfig, driver: WebDriver, action: dict) -> dict | None:
    """
    Syntax: `@analyse` or `@analyse: "My page Title"`

    Triggers an analysis of the current page (e.g., WCAG or contrast check).
    With the default runner and configuration set on startup.
    ```
    @analyse
    ```
    Optionally, you can pass a parameter.

    Where text in brackets `"My page Title"` is used as the page title in the report.

    """
    global input_idx

    param: str | None = action.get("params", None)
    input_idx += 1
    results = []
    screenshots_folder = Path(config.output) / "screenshots"

    if param:
        # analyse param is considered a context css selector, except it begins with " or ' then it is the page title
        if param.startswith('"') and param.endswith('"') or param.startswith("'") and param.endswith("'"):
            # remove the quotes
            param = param[1:-1]
            logger.debug(f"Using manual Page title: {param}")
            page_title = param
        else:
            page_title = driver.title
    else:
        # if no param is given, we assume the current page is the one to analyse
        page_title = driver.title

    logger.info(f"[{input_idx}] Analysing page '{page_title}' with runner '{config.runner.value}'")

    # take full-pagescreenshot
    full_page_screenshot_path = Path(config.output) / f"{config.mode.value}_{input_idx}_full_page_screenshot.png"
    logger.debug(f"Taking full-page screenshot and saving to: {full_page_screenshot_path}")
    take_fullpage_screenshot(driver, full_page_screenshot_path)

    # select runner to run the check
    runner_function = runner_function_map.get(config.runner)
    if runner_function is None:
        raise ValueError(f"Invalid runner: {config.runner}")
    full_page_screenshot_path_outline = runner_function(config, driver, results, screenshots_folder, input_idx)

    # check for violations
    violations = count_violations(results)
    logger.info(f"Analyse found {violations} Violations on page '{page_title}'")

    # save results
    browser_width, browser_height = driver.get_window_size().values()
    entry = {
        "url": driver.current_url,
        "index": input_idx,
        "config": config.__dict__,
        "results": results,
        "title": page_title if 'page_title' in locals() else None,
        "browser_width": browser_width,
        "browser_height": browser_height,
        "violations": violations,
        "failed": violations > 0,
    }
    if full_page_screenshot_path:
        entry["screenshot"] = full_page_screenshot_path.as_posix()
    if full_page_screenshot_path_outline:
        entry["screenshot_outline"] = full_page_screenshot_path_outline.as_posix()
    return entry


def _analyse_runner(runner: Runner, config: ProcessingConfig, driver: WebDriver, action: dict) -> dict | None:
    """
    Internal function to handle the different analysis action runners.
    This is used to avoid code duplication in the `analyse_action` function.
    """
    param: str | None = action.get("params", None)
    check_options = parse_param_to_dict(param)
    if check_options is None:
        check_options = {}

    # build new config object with options set
    base_fields = {field.name for field in fields(ProcessingConfig) if field.init}
    check_config = ProcessingConfig(
        **{key: value for key, value in vars(config).items() if key in base_fields and key not in check_options},
        **{key: value for key, value in check_options.items() if key in base_fields}
    )
    check_config.runner = runner
    # analyse the page with the given axe config
    return analyse_action(check_config, driver, action)


@register_action("analyse_axe")
def analyse_axe_action(config: ProcessingConfig, driver: WebDriver, action: dict) -> dict | None:
    """
    Syntax: `@analyse_axe: <config>`

    Triggers an analysis of the current page using Axe.
    The `<config>` parameter can be a JSON string with Axe options,
    or it can be omitted to use the default Axe configuration if provided on startup.
    ```
    @analyse_axe: {"context": "#myelement", "axe_rules": ["wcag2aa"]}
    ```
    """
    return _analyse_runner(Runner.AXE, config, driver, action)


@register_action("analyse_contrast")
def analyse_contrast_action(config: ProcessingConfig, driver: WebDriver, action: dict) -> dict | None:
    """
    Syntax: `@analyse_contrast: <config>`

    Triggers an analysis of the current page using Contrast.
    The `<config>` parameter can be a JSON string with Contrast options,
    or it can be omitted to use the default Contrast configuration if provided on startup.
    ```
    @analyse_contrast: {"contrast_threshold": "4.5", "selector": "a, button:not([disabled])"}
    @analyse_axe: {}
    ```
    """
    return _analyse_runner(Runner.CONTRAST, config, driver, action)

@register_action("analyse_tab")
def analyse_tab_action(config: ProcessingConfig, driver: WebDriver, action: dict) -> dict | None:
    """
    Syntax: `@analyse_tab: <config>`

    Triggers an analysis of the current page using the tab runner.
    The `<config>` parameter can be a JSON string with options,
    or it can be omitted to use the defaults.
    ```
    @analyse_tab
    ```
    """
    return _analyse_runner(Runner.TAB, config, driver, action)

