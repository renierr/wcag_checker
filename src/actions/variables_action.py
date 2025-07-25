from selenium.webdriver.remote.webdriver import WebDriver

from src.action_handler import register_action, parse_param_to_key_value
from src.config import ProcessingConfig
from src.logger_setup import logger

@register_action("var")
def var_action(config: ProcessingConfig, driver: WebDriver, action: dict, context: dict) -> None:
    """
    Syntax: `@var: <name>=<value>`

    Sets a variable in the context dictionary with the specified name and value.
    In appropriate actions you can use these variables with the syntax `${name}`.

    ```
    @var: my_variable=my_value
    @var: another_variable=123
    ```
    If the parameter is not in the correct format, a warning is logged.
    This action is useful for storing values that can be used later in the script.
    """

    param: str | None = action.get("params", None)
    if not param or "=" not in param:
        logger.warning("Invalid parameter for var action. Expected format: 'name=value'.")
        return

    name, value = parse_param_to_key_value(param)
    logger.debug(f"Setting variable: {name}={value}")

    # Handle nested variable names
    keys = name.split(".")
    current = context
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value
