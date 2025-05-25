from selenium import webdriver

from src.action_handler import register_action
from src.config import Config
from src.logger_setup import logger

@register_action("var")
def var_action(config: Config, driver: webdriver, param: str | None, context: dict) -> None:
    """
    Syntax: `@var <name>=<value>`

    Sets a variable in the context dictionary with the specified name and value.
    ```
    @var: my_variable=my_value
    @var: another_variable=123
    ```
    If the parameter is not in the correct format, a warning is logged.
    This action is useful for storing values that can be used later in the script.
    """

    if not param or "=" not in param:
        logger.warning("Invalid parameter for var action. Expected format: 'name=value'.")
        return

    name, value = param.split('=', 1)
    value = value.strip()
    name = name.strip()
    logger.debug(f"Setting variable: {name}={value}")
    # Store the variable in the context dictionary
    context[name] = value
