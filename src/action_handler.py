import json
from collections import defaultdict
from rich.markdown import Markdown
from rich.table import Table
from rich.console import Console
from selenium.webdriver.remote.webdriver import WebDriver


from src.config import ProcessingConfig
from src.logger_setup import logger

action_context = {}

class ActionRegistry:
    """
    Registry to manage browser actions.

    use the decorator `@register_action("action_name")` to register a new action.

    Actions should be defined as functions that accept `config`, `driver`, and an optional `param` argument.
    The `param` argument can be a string or None, depending on the action's requirements.
    Actions can also accept a `context` dictionary if needed, which can be used to share state between actions.

    Action return values can be a dictionary or None, depending on the action's purpose.
    Returned dictionaries will be used as a result for the current processed action.

    example declaration of an action:
    @register_action("my_action")
    def my_action(config: Config, driver: webdriver, param: str | None = None, context: dict = action_context) -> dict | None:
        pass
    """
    def __init__(self):
        self._actions = {}

    def get_registered_actions(self):
        return self._actions

    def register(self, name, func):
        """Register a new action."""
        if name in self._actions:
            raise ValueError(f"Action '{name}' is already registered.")
        self._actions[name] = func

    def execute(self, config: ProcessingConfig, driver: WebDriver, action_str: str) -> dict | None:
        """Execute a registered action."""
        if not action_str.startswith("@"):
            logger.warning(f"Invalid action format: {action_str}")
            return None

        try:
            action_body = action_str[1:]
            if ":" in action_body:
                action, param = action_body.split(":", 1)
                param = param.strip()
            else:
                action, param = action_body, None

            if action in self._actions:
                action_func = self._actions[action]
                if "context" in action_func.__code__.co_varnames:
                    return action_func(config, driver, param, action_context)
                else:
                    return action_func(config, driver, param)
            else:
                logger.warning(f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Error executing action '{action_str}': {e}")
        return None


# create action registry
action_registry = ActionRegistry()

# Decorator for auto-registration
def register_action(name):
    def decorator(func):
        action_registry.register(name, func)
        return func
    return decorator

def print_action_documentation():
    console = Console()

    console.print("\nThe following actions are registered and can be used", style="bold green")
    console.print("Hint: Actions start with an [bold cyan]@[/bold cyan] sign and can have parameters delimited with [bold cyan]:[/bold cyan] \n", style="dim")

    table = Table(title="Registered Actions", show_lines=True)
    table.add_column("Action", style="bold cyan")
    table.add_column("Description", style="dim")

    actions_by_func = defaultdict(list)

    for action, func in action_registry.get_registered_actions().items():
        actions_by_func[func].append(action)

    for func, actions in sorted(
        {func: sorted(actions) for func, actions in actions_by_func.items()}.items(),
        key=lambda item: item[1][0] if item[1] else ""
    ):
        doc = func.__doc__ or "No description available"
        markdown_doc = Markdown(doc.strip())
        table.add_row(", ".join(actions), markdown_doc)

    console.print(table)

def parse_param_to_string(param: str | None) -> str | None:
    """
    Parse a parameter string to a string. Allow multiline via the {...} syntax.
    Use action_context to replace any variables with syntax ${...}.

    If the string is empty or None, return None.
    Otherwise, return the string with variables replaced.
    """
    if not param:
        return None
    try:
        # multiline strings can be enclosed in {...}
        if param.startswith('{') and param.endswith('}'):
            param = param[1:-1].strip()
        # Replace any variables in the string with their values from action_context
        for var_name, var_value in action_context.items():
            param = param.replace(f"${{{var_name}}}", str(var_value))
        return param.strip()
    except Exception as e:
        logger.error(f"Error parsing string parameter: {e}")
        return None


def parse_param_to_json(param: str | None) -> dict | None:
    """
    Parse a parameter string to a JSON object.
    Use action_context to replace any variables with syntax ${...}.

    If the string is empty or None, return None.
    If the string starts with '{' or '[', parse it as JSON.
    Otherwise, return None.
    """
    if not param:
        return None
    try:
        if param.startswith('{') or param.startswith('['):
            # Replace any variables in the JSON string with their values from action_context
            for var_name, var_value in action_context.items():
                param = param.replace(f"${{{var_name}}}", str(var_value))
            return json.loads(param)
        else:
            return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error: {e}")
        return None

def parse_param_to_key_value(param: str | None) -> tuple[str | None, str | None]:
    """
    Parse a parameter string to a key-value tuple.
    Use action_context to replace any variables with syntax ${...}.

    If the string is empty or None, return None.
    If the string contains '=', split it into key and value.
    Otherwise, return None.
    """
    if not param:
        return None, None
    if '=' not in param:
        return None, param
    try:
        key, value = param.split('=', 1)
        # Replace any variables in the value with their values from action_context
        for var_name, var_value in action_context.items():
            key = key.replace(f"${{{var_name}}}", str(var_value))
            value = value.replace(f"${{{var_name}}}", str(var_value))
        return key.strip(), value.strip()
    except ValueError as e:
        logger.error(f"Error parsing key-value pair: {e}")
        return None, None
