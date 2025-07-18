from lark import Lark, Transformer, v_args
from lark.exceptions import LarkError, VisitError
from selenium.webdriver.remote.webdriver import WebDriver

from src.action_handler import register_action
from src.config import ProcessingConfig

# Grammar for condition parsing
CONDITION_GRAMMAR = r"""
    ?start: or_expr

    ?or_expr: and_expr
            | or_expr "or" and_expr   -> or_op

    ?and_expr: not_expr
             | and_expr "and" not_expr -> and_op

    ?not_expr: "not" not_expr          -> not_op
             | comparison

    ?comparison: atom
               | atom "==" atom        -> eq
               | atom "!=" atom        -> ne
               | atom "<" atom         -> lt
               | atom ">" atom         -> gt
               | atom "<=" atom        -> le
               | atom ">=" atom        -> ge
               | atom "in" atom        -> in_op
               | atom "contains" atom  -> contains_op

    ?atom: property_access 
         | "true"                      -> true
         | "false"                     -> false
         | NUMBER                      -> number
         | ESCAPED_STRING              -> string
         | IDENTIFIER                  -> identifier
         | "(" or_expr ")"

    property_access: IDENTIFIER ("." IDENTIFIER)+
    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
    NUMBER: /\d+(\.\d+)?/

    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
"""


class ConditionTransformer(Transformer):
    """Transform parsed condition tree into boolean result."""

    def __init__(self, context: dict = None):
        super().__init__()
        self.context = context or {}

    @v_args(inline=True)
    def or_op(self, left, right):
        return left or right

    @v_args(inline=True)
    def and_op(self, left, right):
        return left and right

    @v_args(inline=True)
    def not_op(self, expr):
        return not expr

    @v_args(inline=True)
    def eq(self, left, right):
        return left == right

    @v_args(inline=True)
    def ne(self, left, right):
        return left != right

    @v_args(inline=True)
    def lt(self, left, right):
        return left < right

    @v_args(inline=True)
    def gt(self, left, right):
        return left > right

    @v_args(inline=True)
    def le(self, left, right):
        return left <= right

    @v_args(inline=True)
    def ge(self, left, right):
        return left >= right

    @v_args(inline=True)
    def in_op(self, left, right):
        return left in right

    @v_args(inline=True)
    def contains_op(self, left, right):
        return right in left

    def true(self, _):
        return True

    def false(self, _):
        return False

    @v_args(inline=True)
    def number(self, n):
        return float(n) if '.' in str(n) else int(n)

    @v_args(inline=True)
    def string(self, s):
        return s[1:-1]  # Remove quotes

    @v_args(inline=True)
    def identifier(self, name):
        if str(name) not in self.context:
            raise NameError(f"Undefined identifier: {name}")
        return self.context[str(name)]

    def property_access(self, items):
        """Handle dot notation property access"""
        obj = items[0]
        properties = items[1:]

        # Navigate through the nested properties
        current = self.context.get(obj, {})
        for prop in properties:
            if isinstance(current, dict) and prop in current:
                current = current[prop]
            else:
                raise NameError(f"Property '{prop}' not found in context")

        return current


class ConditionParser:
    """Parser for condition expressions using Lark."""

    def __init__(self):
        self.parser = Lark(CONDITION_GRAMMAR, parser='lalr')

    def evaluate(self, condition: str, context: dict = None) -> bool:
        """
        Evaluate a condition string with optional context variables.

        Args:
            condition: The condition string to evaluate
            context: Dictionary of variables available in the condition

        Returns:
            Boolean result of the condition evaluation
        """
        try:
            tree = self.parser.parse(condition)
            transformer = ConditionTransformer(context)
            result = transformer.transform(tree)
            return bool(result)
        except VisitError as e:
            # Check if it's wrapping a NameError (undefined identifier)
            if isinstance(e.orig_exc, NameError):
                raise e.orig_exc
            raise ValueError(f"Invalid condition syntax: {e}")
        except LarkError as e:
            raise ValueError(f"Invalid condition syntax: {e}")
        except NameError as e:
            raise
        except Exception as e:
            raise ValueError(f"Error evaluating condition '{condition}': {e}")


# Global condition parser instance
_condition_parser = ConditionParser()


@register_action("if")
def if_action(config: ProcessingConfig, driver: WebDriver, action: dict, context: dict) -> list | None:
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
    return _condition_parser.evaluate(condition, context)