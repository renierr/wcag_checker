from lark import Lark, Transformer, v_args
from lark.exceptions import LarkError, VisitError

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
    NUMBER: /-?\d+(\.\d+)?/

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
        if not isinstance(right, (str, list, tuple, dict)):
            raise TypeError(f"Right operand of 'in' must be iterable, got {type(right)}")
        return left in right

    @v_args(inline=True)
    def contains_op(self, left, right):
        if not isinstance(left, (str, list, tuple, dict)):
            raise TypeError(f"Left operand of 'contains' must be iterable, got {type(left)}")
        return right in left

    def true(self, _):
        return True

    def false(self, _):
        return False

    @v_args(inline=True)
    def number(self, n):
        s = str(n)
        return float(s) if '.' in s or s.startswith('-') else int(s)

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
        current = self.context.get(obj)
        if current is None:
            raise NameError(f"Base object '{obj}' not found in context")
        path = str(obj)
        for prop in properties:
            path += f".{prop}"
            if isinstance(current, dict) and prop in current:
                current = current[prop]
            else:
                raise NameError(f"Property '{path}' not found in context")
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
condition_parser = ConditionParser()
