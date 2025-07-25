from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from src.action_handler import register_action, parse_param_to_key_value
from src.config import ProcessingConfig
from src.logger_setup import logger


@register_action("error")
def error_action(config: ProcessingConfig, driver: WebDriver, action: dict, context: dict) -> dict | None:
    """
    Syntax: `@error: [<selector>=]<message>`

    Output an error message to the result (will generate a Page with the text as error in the final report).
    If a selector is provided, the error will only be done if the selector is present or if the selector starts with the character '!' not present.
    Without a selector, the error will always be generated.

    ```
    @error: #should_be_there = "My error message if the element is found"
    @error: !#should_not_be_there = "My error message if the element is not found"
    @error: {
      Multiline messages
      are also possible
    }
    @error: #what = {
        even with a selector
    }
    ```
    """
    param: str | None = action.get("params", None)
    if not param:
        logger.error("No message provided to generate an error.")
        return

    selector, message = parse_param_to_key_value(param)
    output_error = True
    if selector:
        not_present = False
        # If the selector starts with '!', we check for its absence
        if selector.startswith("!"):
            selector = selector[1:]
            not_present = True

        element_present = driver.find_elements(By.CSS_SELECTOR, selector)
        output_error = (not_present and not element_present) or (not not_present and element_present)

    if output_error:
        logger.info(f"Error condition met: Element '{selector}', generate an error message to result.")
        # sanitize the message a bit
        message = message.strip()
        if not message:
            message = "An error action was executed, but no message was provided."
        if message.startswith('"') and message.endswith('"'):
            message = message[1:-1]
        if message.startswith('{') and message.endswith('}'):
            message = message[1:-1]
        return {
            "url": driver.current_url,
            "title": "Manual Error: " + driver.title,
            "type": "error",
            "action": "Manual error triggered",
            "failed": True,
            "error": message
        }
    else:
        logger.debug(f"Error condition not met: Element '{selector}', no error will be generated.")
    return None


