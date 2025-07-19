from pathlib import Path

from lark import Lark, Transformer, v_args
from src.logger_setup import logger


# --- Grammar ---
grammar = r"""
    %import common.NEWLINE
    %import common.WS

    start: (action | comment)*
    action: if_action | include_action | simple_action
    
    simple_action: "@" NAME (":" params)?
    if_action: "@if:" condition ":" action_block elif_block* else_block?
    elif_block: "@elif:" condition ":" action_block
    else_block: "@else:" action_block

    action_block: "{" (action | comment)* "}"
    include_action: "@include:" filename
    
    params: single_line_params | block_params
    single_line_params: SINGLE_LINE_PARAMS
    block_params: "{" block_content "}"
    block_content: balanced_content*
    balanced_content: BLOCK_TEXT | nested_braces | NEWLINE
    nested_braces: "{" balanced_content* "}"

    condition: CONDITION
    filename: FILENAME
    comment: COMMENT

    NAME: /[a-zA-Z_]\w*/
    BLOCK_TEXT: /[^{}\n]+/
    COMMENT: /#[^\n]*/
    CONDITION: /[^:{}]+/
    FILENAME: /[^\n]+/
    SINGLE_LINE_PARAMS: /[^\n]+/
    
    %ignore WS
"""

action_parser = Lark(grammar, start='start', parser='lalr')

# --- Transformer ---
class ActionTransformer(Transformer):
    @v_args(inline=True)
    def start(self, *items):
        return [item for item in items if item is not None]

    @v_args(inline=True)
    def action(self, action_item):
        return action_item

    @v_args(inline=True)
    def comment(self, comment_text):
        return None  # Ignore comments in the output

    @v_args(inline=True)
    def simple_action(self, name, params=None):
        return {'type': 'action', 'name': str(name), 'params': params or None}

    def if_action(self, items):
        condition = items[0]
        actions = items[1]
        result = {
            'type': 'if',
            'name': 'if',
            'condition': str(condition).strip(),
            'actions': actions or []
        }
        elif_blocks = []
        else_actions = None
        for item in items[2:]:
            if isinstance(item, dict) and 'type' in item:
                if item['type'] == 'elif':
                    elif_blocks.append(item)
                elif item['type'] == 'else':
                    else_actions = item.get('actions', [])
        if elif_blocks:
            result['elif_blocks'] = elif_blocks
        if else_actions:
            result['else_actions'] = else_actions
        return result

    @v_args(inline=True)
    def elif_block(self, condition, actions):
        return {
            'type': 'elif',
            'condition': str(condition).strip(),
            'actions': actions or []
        }

    @v_args(inline=True)
    def else_block(self, actions):
        return {
            'type': 'else',
            'actions': actions or []
        }

    @v_args(inline=True)
    def action_block(self, *actions):
        return [action for action in actions if action is not None]

    @v_args(inline=True)
    def include_action(self, filename):
        filename = str(filename).strip()
        if hasattr(self, '_context') and self._context:
            logger.info(f"Parser: Processing include action for file: {filename}")
            current_file_path = Path(self._context['current_file'])
            basedir = current_file_path.parent
            logger.debug(f"Parser: Base directory for includes: {basedir}")
            include_path = basedir / filename
            included_actions = _parse_config_file(include_path, self._context)
            return included_actions
        return {'type': 'include', 'name': 'include', 'params': [filename]}

    @v_args(inline=True)
    def params(self, param_value):
        return param_value

    @v_args(inline=True)
    def single_line_params(self, value):
        return str(value).strip()

    @v_args(inline=True)
    def block_params(self, content):
        return f"{{{content}}}"

    def block_content(self, items):
        result_parts = []
        for item in items:
            if item is None:
                continue
            if isinstance(item, str):
                result_parts.append(item)
            elif hasattr(item, 'type') and item.type == 'NEWLINE':
                result_parts.append('\n')
            else:
                result_parts.append(str(item))
        return ''.join(result_parts).strip()

    @v_args(inline=True)
    def balanced_content(self, content):
        return content

    @v_args(inline=True)
    def nested_braces(self, *contents):
        result = '{'
        for content in contents:
            if content is not None:
                result += str(content)
        result += '}'
        return result

    @v_args(inline=True)
    def condition(self, value):
        return str(value).strip()

    @v_args(inline=True)
    def filename(self, value):
        return str(value).strip()

    @v_args(inline=True)
    def NAME(self, item):
        return str(item)

    @v_args(inline=True)
    def BLOCK_TEXT(self, item):
        return str(item)

    @v_args(inline=True)
    def COMMENT(self, item):
        return str(item)

    @v_args(inline=True)
    def CONDITION(self, item):
        return str(item)

    @v_args(inline=True)
    def FILENAME(self, item):
        return str(item)

    @v_args(inline=True)
    def SINGLE_LINE_PARAMS(self, item):
        return str(item)

    @v_args(inline=True)
    def NEWLINE(self, item):
        return '\n'

# --- Parser ---
def _parse_config_file(file_path: Path, context: dict | None = None, max_depth: int = 20 ) -> list[dict]:
    """
    Parse a configuration file and return a list of actions.

    :param file_path: Path to the configuration file.
    :param context: Optional context dictionary to track visited files and current file path.
    :param max_depth: Maximum recursion depth.
    :return: List of parsed actions as dictionaries.
    """

    file_path = file_path.resolve()
    if context is None:
        context = {
            'visited_files': set(),
            'current_file': file_path,
            'depth': 0
        }
    else:
        context['current_file'] = file_path
        context['depth'] = context.get('depth', 0) + 1

    if file_path in context['visited_files']:
        logger.warning(f"Parser: File {file_path} already visited. Skipping to avoid circular reference.")
        return []

    if context['depth'] > max_depth:
        logger.error(f"Maximum recursion depth ({max_depth}) exceeded for file: {file_path}")
        return []

    context['visited_files'].add(file_path)

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()


        tree = action_parser.parse(text)
        transformer = ActionTransformer()
        transformer._context = context
        result = transformer.transform(tree)

        # flatten results
        flattened_result = []
        for item in result:
            if isinstance(item, list):
                flattened_result.extend(item)
            else:
                flattened_result.append(item)

        context['visited_files'].remove(file_path)
        return flattened_result


    except FileNotFoundError:
        logger.warning(f"Error loading config file '{file_path}' - not found, will be ignored.")
        return []
    except Exception as e:
        logger.error(f"Error during config parse for '{file_path}': {e}")
        return []

def parse_inputs(inputs: list[str]) -> list[dict]:
    """
    Parse the inputs to ensure they are valid URLs or actions.
    If an input starts with 'config:', it is treated as a path to a configuration file

    the returned list will contain dictionaries that looks like:
    {
        'type': 'url' or 'action' or 'if' or 'include',
        'url': 'http://example.com'     // optional for 'url' type
        'name': 'action_name',          // optional can be omitted for 'url' type
        'params': ['param1', 'param2']  // optional for 'action' type
        'condition': 'condition_value', // for 'if' type
        'actions': [list of actions]    // for 'if' type
        'filename': 'path/to/file.txt'  // for 'include' type
    }

    :param inputs: List of input strings.
    :return: List of parsed inputs to a structured dict.
    """

    parsed_inputs = []
    for input_check in inputs:
        if isinstance(input_check, str) and input_check.startswith("config:"):
            config_file = input_check.replace("config:", "")
            logger.info(f"Reading inputs from config file: {config_file}")
            parsed_inputs.extend(_parse_config_file(Path(config_file)))
        else:
            parsed_inputs.append({ 'type': 'url', 'url': input_check.strip() })
    return parsed_inputs

