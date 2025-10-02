from selenium.webdriver.remote.webdriver import WebDriver

from src.action_handler import register_action
from src.config import ProcessingConfig

@register_action("iframe")
def iframe_action(config: ProcessingConfig, driver: WebDriver, action: dict, context: dict) -> list | None:
    """
    Syntax: `@iframe <condition> { <actions> }`

    Conditional action that executes a block of actions for a specific iframe.
    The condition is a string that select the iframe (CSS selector).

    The actions are a list of actions to be executed if the condition is true.

    More complete example:
    ```
    @if "#my_iframe" {
        @analyse_axe: {"context": "#dashboard"}
    }
    ```

    """

    action_type = action.get('type')
    if not action_type or action_type != 'iframe':
        raise ValueError("Action must be a dictionary of type 'iframe' to be processed by iframe_action.")
    if 'actions' not in action:
        raise ValueError("Action must contain 'actions' key with a list of actions to be processed.")
    if not isinstance(action['actions'], list):
        raise ValueError("Action 'actions' must be a list of actions to be processed.")
    if 'condition' not in action:
        raise ValueError("Action must contain 'condition' key with a string condition to be processed.")
    if not isinstance(action['condition'], str):
        raise ValueError("Action 'condition' must be a string to be processed.")

    condition = action.get('condition', '')
    actions = action.get('actions', [])

    return actions


