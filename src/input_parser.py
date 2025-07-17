from pathlib import Path

from lark import Lark, Transformer, v_args
from src.logger_setup import logger


# --- Grammar ---
grammar = r"""
    start: action*
    action: simple_action | if_action | include_action
    
    simple_action: "@" NAME (":" params)?
    if_action: "@if:" condition ":" nested_block
    include_action: "@include:" FILENAME
    
    params: single_line_params | params_block
    single_line_params: VALUE (";" VALUE)*
    params_block: "{" VALUE* "}"
    
    nested_block: "{" block_item* "}"
    block_item: /[^{}]+/ | nested_block
    
    condition: VALUE
    
    NAME: /[a-zA-Z_]\w*/
    VALUE: /"[^"]*"/ | /[^;{}\s]+/
    FILENAME: /[^:\n]+/
    
    %import common.NEWLINE
    %import common.WS
    
    %ignore WS
    %ignore /#[^\n]*/
"""

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
        return {'type': 'action', 'name': str(name), 'params': params or []}

    @v_args(inline=True)
    def if_action(self, condition, block_content):
        return {
            'type': 'if',
            'name': 'if',
            'condition': str(condition).strip('"').strip(),
            'params': str(block_content)
        }

    @v_args(inline=True)
    def include_action(self, filename):
        return {'type': 'include', 'name': 'include', 'params': [str(filename).strip()]}

    @v_args(inline=True)
    def params(self, *params):
        return params[0]  # params ist entweder single_line_params oder params_block

    @v_args(inline=True)
    def single_line_params(self, *values):
        return [str(value).strip('"').strip() for value in values if value is not None]

    @v_args(inline=True)
    def nested_block(self, *items):
        # Kombiniere alle block_items zu einem String
        result = ""
        for item in items:
            if hasattr(item, '__iter__') and not isinstance(item, str):
                # Verschachtelter Block - rekursiv zu String
                result += "{" + str(item) + "}"
            else:
                result += str(item)
        return result.strip()

    @v_args(inline=True)
    def block_item(self, content):
        return str(content)

    @v_args(inline=True)
    def params_block(self, *params):
        return [str(param).strip() for param in params if param is not None]

    @v_args(inline=True)
    def condition(self, value):
        return str(value).strip('"').strip()

    def NAME(self, item):
        return str(item)

    def VALUE(self, item):
        return str(item)

    def FILENAME(self, item):
        return str(item)

# --- Parser ---
def parse_config_file(file_path, context=None):
    if context is None:
        context = {
            'visited_files': set(),
            'current_file': file_path,
            'results': []
        }

    if file_path in context['visited_files']:
        print(f"Warnung: Zyklische Einbindung von '{file_path}' erkannt, überspringe.")
        return []

    context['visited_files'].add(file_path)

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        parser = Lark(grammar, start='start')
        tree = parser.parse(text)
        transformer = ActionTransformer()
        result = transformer.transform(tree)
        context['visited_files'].remove(file_path)
        return result

    except FileNotFoundError:
        print(f"Fehler: Datei '{file_path}' nicht gefunden.")
        return []
    except Exception as e:
        print(f"Fehler beim Parsen von '{file_path}': {e}")
        return []

def parse_inputs(inputs: list[str]) -> list[str]:
    """
    Parse the inputs to ensure they are valid URLs or actions.
    You can use multiple lines in a config file
    if the line ends with `{` until a following line starts with `}`,
    these will be combined as one.

    :param inputs: List of input strings.
    :return: List of parsed input strings.
    """

    parsed_inputs = []
    for input_check in inputs:
        if isinstance(input_check, str) and input_check.startswith("config:"):
            config_file = input_check.replace("config:", "")
            logger.info(f"Reading inputs from config file: {config_file}")
            try:
                with open(config_file, "r") as f:
                    basedir = Path(config_file).resolve().parent
                    lines = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith("#")]
                    parsed_inputs.extend(_config_to_actions(lines, basedir))
            except FileNotFoundError:
                logger.error(f"Config file not found: {config_file}")
                continue
        else:
            parsed_inputs.append(input_check)
    return parsed_inputs


def _config_to_actions(inputs: list[str], basedir: Path, processed_files: set[str] = None) -> list[str]:
    """
    Convert the inputs to actions by parsing the config file and including actions from other files.
    This function is used to handle the `@include:` directive in config files.

    :param inputs: List of input strings.
    :param basedir: Base directory to resolve relative paths for included files.
    :param processed_files: Set of already processed files to avoid circular references.
    :return: List of actions as strings.
    """
    if processed_files is None:
        processed_files = set()

    parsed_inputs = []
    combined_line = None
    for line in inputs:
        if not line.strip() or line.startswith("#"):
            continue
        elif combined_line:
            combined_line += " " + line
            if line.startswith("}"):
                parsed_inputs.append(combined_line)
                combined_line = None
        elif line.endswith("{"):
            combined_line = line
        elif line.startswith("@include:"):
            include_file = line.replace("@include:", "").strip()
            logger.info(f"Including actions from file: {include_file} basedir: {basedir}")
            if include_file in processed_files:
                logger.warning(f"Include File {include_file} already processed, skipping to avoid circular reference.")
                continue
            processed_files.add(include_file)
            try:
                include_path = basedir / include_file
                with include_path.open("r") as include_f:
                    basedir = include_path.resolve().parent
                    included_actions = [action.strip() for action in include_f.readlines() if action.strip() and not action.strip().startswith("#")]
                    parsed_inputs.extend(_config_to_actions(included_actions, basedir, processed_files))
            except FileNotFoundError:
                logger.error(f"Include File not found: {include_file}")
        else:
            parsed_inputs.append(line)
    return parsed_inputs
