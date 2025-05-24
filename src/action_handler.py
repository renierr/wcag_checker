from collections import defaultdict
from rich.markdown import Markdown
from rich.table import Table
from rich.console import Console
from selenium import webdriver

from src.config import Config
from src.logger_setup import logger

class ActionRegistry:
    """Registry to manage browser actions."""
    def __init__(self):
        self._actions = {}

    def get_registered_actions(self):
        return self._actions

    def register(self, name, func):
        """Register a new action."""
        if name in self._actions:
            raise ValueError(f"Action '{name}' is already registered.")
        self._actions[name] = func

    def execute(self, config: Config, driver: webdriver, action_str: str) -> dict | None:
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
                return self._actions[action](config, driver, param)
            else:
                logger.warning(f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Error executing action '{action_str}': {e}")


# create action registry
action_registry = ActionRegistry()

# Decorator for auto-registration
def register_action(name):
    def decorator(func):
        action_registry.register(name, func)
        return func
    return decorator

def print_action_documentation():
    console = Console(width=100)

    console.print("\nThe following actions are registered and can be used", style="bold green")
    console.print("Hint: Actions start with an [bold cyan]@[/bold cyan] sign and can have parameters delimited with [bold cyan]:[/bold cyan] \n", style="dim")

    table = Table(title="Registered Actions", show_lines=True)
    table.add_column("Action", style="bold cyan")
    table.add_column("Description", style="dim")

    actions_by_func = defaultdict(list)

    for action, func in action_registry.get_registered_actions().items():
        actions_by_func[func].append(action)

    for func, actions in actions_by_func.items():
        doc = func.__doc__ or "No description available"
        markdown_doc = Markdown(doc.strip())
        table.add_row(", ".join(actions), markdown_doc)

    console.print(table)
