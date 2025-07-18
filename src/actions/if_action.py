from selenium.webdriver.remote.webdriver import WebDriver

from src.action_handler import register_action
from src.config import ProcessingConfig


@register_action("if")
def if_action(config: ProcessingConfig, driver: WebDriver, action: dict) -> None:
    """
    Syntax: `@if: <condition> : { <actions> }`

    optional syntax in addition to the if action (can not be used alone, only with if):

    `@elif: <condition> : { <actions> }`

    `@else: { <actions> }`

    Conditional action that executes a block of actions based on a condition.
    The condition is a string that can be evaluated to determine if the actions should be executed.

    The actions are a list of actions to be executed if the condition is true.

    Optional elif and else blocks can be used to handle additional conditions or default actions.

    More complete example:
    ```
    @if: "my_condition" : {
        @navigate: "/dashboard"
        @analyse_axe: {"context": "#dashboard"}
    }
    @elif: "another_condition" : {
        @navigate: "/settings"
        @wait: 2
    }
    @else: {
        @navigate: "/home"
        @analyse
    }
    ```

    """
    pass

