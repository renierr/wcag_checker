from selenium.webdriver.remote.webdriver import WebDriver

from src.action_handler import register_action, parse_param_to_string
from src.config import ProcessingConfig
from src.ignore_violations import add_ignore_violation
from src.logger_setup import logger


@register_action("ignore")
def ignore_action(config: ProcessingConfig, driver: WebDriver, action: dict) -> None:
    """
    Syntax: `@ignore: <violation_id>`

    Add a violation ID to the ignore list.
    You can provide a single violation ID or multiple IDs separated by new lines encapsulated in { ... }.

    examples:
    ```
    @ignore: violation_id_123
    @ignore: {
        violation_id_456
        violation_id_789
        another_violation_id
    }
    ```
    """
    param: str | None = action.get("params", None)
    if not param:
        logger.warning("Param missing, please provide a violation id to add to ignore list.")
        return

    parsed_param = parse_param_to_string(param)
    if ((parsed_param.startswith('"') and parsed_param.endswith('"')) or
            (parsed_param.startswith('{') and parsed_param.endswith('}'))):
        parsed_param = parsed_param[1:-1]

    # Split lines and add them one by one
    for line in parsed_param.splitlines():
        stripped_line = line.strip()
        if stripped_line:
            add_ignore_violation(stripped_line)
    return


