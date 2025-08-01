from selenium.webdriver.remote.webdriver import WebDriver

from src.action_handler import register_action, parse_param_to_string, parse_param_to_key_value
from src.config import ProcessingConfig
from src.logger_setup import logger
from src.utils import trim_string_to_length


@register_action("script")
def script_action(config: ProcessingConfig, driver: WebDriver, action: dict, context: dict) -> None:
    """
    Syntax: `@script: [<var>=]<script>`

    Execute a script on the current page.
    If a variable name is provided, the result of the script will be stored in the context dictionary under that name.
    If no variable name is provided, the script will be executed without storing the result.
    The script can be a single line or multiple lines of JavaScript code, multiline has to start and end with { }.

    To return a value from the script, use the `return` statement.

    ```
    @script: console.log("Hello, world!");
    @script: {
      document.title = "New Title";
      console.log("Title changed to:", document.title);
    }
    @script: myDocTitle=return document.title
    ```
    """
    param: str | None = action.get("params", None)
    if not param:
        logger.error("No script provided to execute.")
        return

    try:
        var_name = action.get("var", None)
        logger.debug(f"Executing script: {trim_string_to_length(param, 70)}")
        result = driver.execute_script(param)
        if result is not None and var_name:
            context[var_name] = result
            logger.debug(f"Script result stored in context: {var_name} = {trim_string_to_length(result, 20)}")
    except Exception as e:
        logger.error(f"Error executing script: {e}")

# language=JS
log_script = """console.log(arguments[0]);"""

@register_action("log")
def log_action(config: ProcessingConfig, driver: WebDriver, action: dict) -> None:
    """
    Syntax: `@log: "<message>"`

    Log a message to the browser console.
    Use " to treat the message as a string.
    Anything else will be treated as code passed to the console log.

    Context variables can be used in the message by using the syntax `${variable_name}`.

    ```
    @log: "This is a log message."
    @log: "The value of my variable is: ${my_variable}"
    @log: document.title
    ```
    """
    param: str | None = action.get("params", None)
    if not param:
        logger.error("@log action: No message provided to log.")
        return

    try:
        parsed_param = parse_param_to_string(param)
        if parsed_param.startswith('"') and parsed_param.endswith('"'):
            # remove the quotes from the string
            parsed_param = parsed_param[1:-1]
            driver.execute_script(log_script, parsed_param)
        else:
            # If the message is not a string, we assume it's code to be executed
            driver.execute_script(log_script.replace("arguments[0]", parsed_param))
    except Exception as e:
        logger.error(f"Error logging message: {e}")

