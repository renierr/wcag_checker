import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import importlib
import pkgutil

from rich.console import Console
from rich.markdown import Markdown

from src.logger_setup import logger
from src.arg_parse import argument_parser
from src.utils import get_embedded_file_path, filter_args_for_dataclass
from src.config import Config, AxeConfig, ContrastConfig, Mode, ProcessingConfig
from src.action_handler import print_action_documentation
from src.actions.analyse_action import analyse_action
from src.processing import check_run
import src.actions

# dynamically load all actions from the actions module
def load_all_actions():
    for _, module_name, _ in pkgutil.iter_modules(src.actions.__path__):
        importlib.import_module(f"src.actions.{module_name}")


def show_readme(file_path: str):
    """
    Shows the content of the README.md file in the terminal.

    :param file_path: Pfad zur README.md-Datei
    """
    console = Console(width=100)
    try:
        readme_path = get_embedded_file_path(file_path)
        with open(readme_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # remove [[_TOC_]] because it is not supported in the terminal
            content = content.replace("[[_TOC_]]", "")
            markdown = Markdown(content)
            console.print(markdown)
    except FileNotFoundError:
        console.print(f"[bold red]Fehler:[/bold red] Datei '{file_path}' nicht gefunden.")
    except Exception as e:
        console.print(f"[bold red]Fehler:[/bold red] {e}")

def main():
    parser = argument_parser()
    args = parser.parse_args()

    # if no arguments passed show readme
    if args.readme:
        show_readme("README.md")
        print("\nTool help can be called with option --help:")
        sys.exit(0)

    if args.mode is None:
        parser.print_help()
        sys.exit(0)

    load_all_actions()
    if args.mode == Mode.ACTIONS.value:
        print_action_documentation()
        sys.exit(0)

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled.")

    # convert to dict to create dataclass instances
    args_dict = vars(args)
    args_dict["mode"] = Mode(args_dict["mode"])
    args_dict["resolution"] = tuple(map(int, args_dict["resolution"].split("x")))

    if args.mode == Mode.CHECK:
        filtered_args = filter_args_for_dataclass(ProcessingConfig, args_dict)
        arg_config = ProcessingConfig(**filtered_args)
        check_run(arg_config)


if __name__ == "__main__":
    main()