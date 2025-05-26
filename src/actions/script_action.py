import time

from selenium import webdriver

from src.action_handler import register_action, parse_param_to_string
from src.config import ProcessingConfig
from src.logger_setup import logger

@register_action("script")
def script_action(config: ProcessingConfig, driver: webdriver, param: str | None) -> None:
    """
    Syntax: `@script: <script>`

    Execute a script on the current page.
    ```
    @script: console.log("Hello, world!");
    @script: document.title = "New Title";
    ```
    """
    if not param:
        logger.error("No script provided to execute.")
        return

    try:
        parsed_param = parse_param_to_string(param)
        logger.debug(f"Executing script: {parsed_param[:40]}{'...' if len(parsed_param) > 40 else ''}")
        driver.execute_script(parsed_param)
    except Exception as e:
        logger.error(f"Error executing script: {e}")
