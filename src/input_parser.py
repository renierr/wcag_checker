from pathlib import Path

from lark import Lark, Transformer, v_args
from src.logger_setup import logger


# --- Grammar ---
grammar = r"""
    %import common.NEWLINE
    %import common.WS

    start: action*
    action: if_action | include_action | simple_action
    
    simple_action: "@" NAME (":" params)?
    if_action: "@if:" condition ":" action_block
    action_block: "{" action* "}"
    include_action: "@include:" filename
    
    params: single_line_params | params_block
    single_line_params: VALUE
    params_block: "{" block_content "}"
    block_content: balanced_content*
    balanced_content: BLOCK_TEXT | nested_braces | NEWLINE
    nested_braces: "{" balanced_content* "}"

    condition: VALUE
    filename: FILENAME
    
    NAME: /[a-zA-Z_]\w*/
    VALUE: /"[^"]*"/ | /(?:[^;{}\s$]|\$\{[^}]*\})+/
    FILENAME: /[^\n]+/
    BLOCK_TEXT: /[^{}\n]+/
    
    %ignore WS
    %ignore /#[^\n]*/
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
    def simple_action(self, name, params=None):
        return {'type': 'action', 'name': str(name), 'params': params or None}

    @v_args(inline=True)
    def if_action(self, condition, actions):
        return {
            'type': 'if',
            'name': 'if',
            'condition': str(condition).strip('"').strip(),
            'actions': actions or []
        }

    @v_args(inline=True)
    def action_block(self, *actions):
        return [action for action in actions if action is not None]

    @v_args(inline=True)
    def include_action(self, filename):
        filename = str(filename).strip()

        # use context from _parse_config_file
        if hasattr(self, '_context') and self._context:
            logger.info(f"Parser: Processing include action for file: {filename}")
            current_file_path = Path(self._context['current_file'])
            basedir = current_file_path.parent
            logger.debug(f"Parser: Base directory for includes: {basedir}")
            include_path = basedir / filename
            included_actions = _parse_config_file(include_path, self._context)
            return included_actions
        else:
            # Fallback to normal action syntax
            return {'type': 'include', 'name': 'include', 'params': [filename]}

    @v_args(inline=True)
    def params(self, param_value):
        return param_value

    @v_args(inline=True)
    def single_line_params(self, value):
        return str(value).strip('"').strip()

    @v_args(inline=True)
    def params_block(self, content):
        return content

    def block_content(self, items):
        result_parts = []
        for item in items:
            if item is not None:
                if hasattr(item, 'type') and item.type == 'NEWLINE':
                    result_parts.append('\n')
                elif hasattr(item, 'value'):
                    result_parts.append(str(item.value))
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
        return str(value).strip('"').strip()

    def filename(self, items):
        """Transform filename rule to extract the actual path string"""
        return items[0]  # Return the first (and only) item which should be the path string

    def NAME(self, item):
        return str(item)

    def VALUE(self, item):
        return str(item)

    def FILENAME(self, item):
        return str(item)

    def BLOCK_TEXT(self, item):
        return str(item)

# --- Parser ---
def _parse_config_file(file_path: Path, context=None):
    file_path = file_path.resolve()
    if context is None:
        context = {
            'visited_files': set(),
            'current_file': file_path,
        }
    else:
        context['current_file'] = file_path

    if file_path in context['visited_files']:
        logger.warning(f"Parser: File {file_path} already visited. Skipping to avoid circular reference.")
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

