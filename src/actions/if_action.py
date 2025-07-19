from selenium.webdriver.remote.webdriver import WebDriver

from src.action_handler import register_action
from src.condition_parser import condition_parser
from src.config import ProcessingConfig

@register_action("if")
def if_action(config: ProcessingConfig, driver: WebDriver, action: dict, context: dict) -> list | None:
    """
    Syntax: `@if: <condition> { <actions> }`

    optional syntax in addition to the if action (can not be used alone, only with if):

    `@elif: <condition> { <actions> }`

    `@else: { <actions> }`

    Conditional action that executes a block of actions based on a condition.
    The condition is a string that can be evaluated to determine if the actions should be executed.

    The actions are a list of actions to be executed if the condition is true.

    Optional elif and else blocks can be used to handle additional conditions or default actions.

    More complete example:
    ```
    @if: "my_condition" {
        @navigate: "/dashboard"
        @analyse_axe: {"context": "#dashboard"}
    }
    @elif: "another_condition" {
        @navigate: "/settings"
        @wait: 2
    }
    @else: {
        @navigate: "/home"
        @analyse
    }
    ```

    """

    action_type = action.get('type')
    if not action_type or action_type != 'if':
        raise ValueError("Action must be a dictionary of type 'if' to be processed by if_action.")
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
    elif_blocks = action.get('elif_blocks', [])
    else_actions = action.get('else_actions', [])

    # Process the condition and build the action results
    action_results = []
    if _eval_condition(condition, context):
        for act in actions:
            action_results.append(act)
    else:
        for elif_block in elif_blocks:
            elif_condition = elif_block.get('condition', '')
            elif_actions = elif_block.get('actions', [])
            if _eval_condition(elif_condition, context):
                for act in elif_actions:
                    action_results.append(act)
                return
        if else_actions:
            for act in else_actions:
                action_results.append(act)
    return action_results if action_results else None


def _eval_condition(condition: str, context: dict = None) -> bool:
    """
    Evaluate a condition string with optional context variables.
    This function uses the global condition parser to evaluate the condition.

    @:param condition: The condition string to evaluate
    @:param context: Dictionary of variables available in the condition
    @:return: Boolean result of the condition evaluation

    """
    return condition_parser.evaluate(condition, context)
