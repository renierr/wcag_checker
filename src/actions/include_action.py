from selenium.webdriver.remote.webdriver import WebDriver

from src.action_handler import register_action
from src.config import ProcessingConfig


@register_action("include")
def include_action(config: ProcessingConfig, driver: WebDriver, param: str | None = None) -> None:
    """
    Syntax: `@include: <filename>`

    Fake noop action for including other files in the processing.

    This action does not perform any operation, the parsing is done elsewhere,
    we need this to avoid leftover and provide documentation.
    """
    pass

