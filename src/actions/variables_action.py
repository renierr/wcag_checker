from selenium.webdriver.remote.webdriver import WebDriver

from src.action_handler import register_action, parse_param_to_key_value
from src.config import ProcessingConfig
from src.logger_setup import logger
from src.utils import setting_var


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
    setting_var(context, name, value)


@register_action("var_default")
def var_default_action(config: ProcessingConfig, driver: WebDriver, action: dict, context: dict) -> None:
    """
    Syntax: `@var_default: <name>=<value>`

    Sets a variable in the context only if it doesn't exist yet.
    Useful for defining default values for variables.

    ```
    @var_default: my_variable=default_value
    ```
    """
    param: str | None = action.get("params", None)
    if not param or "=" not in param:
        logger.warning("Invalid parameter for var_default action. Expected format: 'name=value'.")
        return

    name, value = parse_param_to_key_value(param)
    if setting_var(context, name, value, override=False):
        logger.debug(f"Setting default variable: {name}={value}")
    else:
        logger.debug(f"Variable '{name}' already exists. Not overriding with default value: {value}")
