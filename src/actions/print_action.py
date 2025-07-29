from selenium.webdriver.remote.webdriver import WebDriver

from src.action_handler import register_action, parse_param_to_string
from src.config import ProcessingConfig
from src.logger_setup import logger


@register_action("print")
def print_action(config: ProcessingConfig, driver: WebDriver, action: dict) -> None:
    """
    Syntax: `@print: <output_to_stdout>`

    Print a message to the standard output (stdout).
    This action is useful for debugging or logging purposes.
    """

    param: str | None = action.get("params", None)
    if not param:
        logger.warning("Param missing, please provide a message to print.")
        return

    parsed_param = parse_param_to_string(param)
    if ((parsed_param.startswith('"') and parsed_param.endswith('"')) or
        (parsed_param.startswith('{') and parsed_param.endswith('}'))):
        parsed_param = parsed_param[1:-1]
    print(parsed_param)
    return

