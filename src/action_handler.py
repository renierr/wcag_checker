from selenium import webdriver

from src.config import Config
from src.logger_setup import logger

class ActionRegistry:
    """Registry to manage browser actions."""
    def __init__(self):
        self._actions = {}

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

