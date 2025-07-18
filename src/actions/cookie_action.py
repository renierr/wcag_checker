from selenium.webdriver.remote.webdriver import WebDriver

from src.action_handler import register_action, parse_param_to_json, parse_param_to_key_value
from src.config import ProcessingConfig
from src.logger_setup import logger

@register_action("cookie")
def cookie_action(config: ProcessingConfig, driver: WebDriver, action: dict) -> None:
    """
    Syntax: `@cookie <name>=<value>` or `@cookie {"name": "<name>", "value": "<value>"}`

    Sets a cookie in the browser with the specified name and value.
    ```
    @cookie: my_cookie=my_value
    @cookie: {"name": "my_cookie", "value": "my_value"}
    ```
    If no parameter is provided, a warning is logged.
    If the parameter is not in the correct format, a warning is logged.
    """

    param: str | None = action.get("params", None)
    if not param:
        logger.warning("No cookie name and value provided.")
        return

    json_param = parse_param_to_json(param)
    if json_param:
        logger.debug(f"Setting cookie from JSON: {json_param}")
        # Set the cookie in the browser
        driver.add_cookie(json_param)
    else:
        if '=' not in param:
            logger.warning("Invalid cookie format. Use <name>=<value>.")
            return

        name, value = parse_param_to_key_value(param)
        logger.debug(f"Setting cookie: {name}={value}")
        # Set the cookie in the browser
        driver.add_cookie({"name": name, "value": value})
