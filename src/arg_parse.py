import argparse
import textwrap
from rich.markdown import Markdown
from rich_argparse import RawTextRichHelpFormatter
from gettext import gettext as _
from argparse import SUPPRESS, OPTIONAL, ZERO_OR_MORE

from src.config import Config, AxeConfig, ContrastConfig, ColorSource, ConfigEncoder, Mode, ReportLevel

class CustomArgparseFormatter(RawTextRichHelpFormatter):

    def _get_help_string(self, action):
        help = action.help or ''
        if '%(default)' not in help:
            if action.default is not SUPPRESS:
                defaulting_nargs = [OPTIONAL, ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    help += _('\n[argparse.prog](default: %(default)s)[/]')
        return help


def argument_parser() -> argparse.ArgumentParser:
    description = textwrap.dedent("""\
    WCAG Checker
    ============

    This tool checks the WCAG rules or contrast ratio of elements on a webpage and generates reports.    
    It has a Axe mode to use Axe WCAG checker on the provided pages (see mode option)

    It uses Selenium WebDriver to interact with the webpage (a Chrome Browser is needed).

    The report can be generated in JSON, Markdown and HTML format.

    Select a mode to run the Tool with, call option --help after mode to see specific options for them.    
    Be aware that global options are defined before the mode.
    """)

    parser = argparse.ArgumentParser(
        description=Markdown(description, style="argparse.text"),
        formatter_class=CustomArgparseFormatter
    )
    parser.add_argument("--browser", "-b", type=str, choices=["chrome", "edge"], default="chrome",
                        help="Select Browser for Selenium webdriver (chrome or edge).")
    parser.add_argument("--browser_visible", "-bv", action="store_true",
                        help="Make the remote controlled browser visible - keep in mind that this prevent resolution to be set correctly use it only for debugging.")
    parser.add_argument("--output", "-o", type=str,
                        help="The base folder for output files.", nargs="?", default="output")
    parser.add_argument("--debug", "-d", action="store_true",
                        help="Enable debug mode for detailed output.")
    parser.add_argument("--readme", "-r", action="store_true",
                        help="Show README markdown in terminal.")
    parser.add_argument(
        "--version", "-v", action="version", version="[argparse.prog]%(prog)s[/] version [i]1.0.0[/]"
    )

    parent_processing_parser = argparse.ArgumentParser(add_help=False)
    parent_processing_parser.add_argument("--login", "-l", type=str,
                                          help="The URL to login to page - called before processing", nargs="?", default="")
    parent_processing_parser.add_argument("--inputs", "-i", type=str,
                                          help=textwrap.dedent("""\
                            The Inputs to check.
                            You can pass a file by prefix the path to file with 'config:'
                            """).strip(),
                                          nargs="*", default="")
    parent_processing_parser.add_argument("--json", action=argparse.BooleanOptionalAction,
                                          help="Enable or disable JSON output.", default=True)
    parent_processing_parser.add_argument("--markdown", action=argparse.BooleanOptionalAction,
                                          help="Enable or disable Markdown Report output.", default=True)
    parent_processing_parser.add_argument("--html", action=argparse.BooleanOptionalAction,
                                          help="Enable or disable HTML Report output.", default=True)
    parent_processing_parser.add_argument("--simulate", "-s", type=str,
                                          help="Simulate checking; use JSON as base to generate reports (no website calls)")
    parent_processing_parser.add_argument("--resolution", "-r", type=str,
                                          help="Set the Resolution the remote controlled Browser will default to. Format <width>x<height>", default="1920x1080")

    subparsers = parser.add_subparsers(dest="mode", required=False,
                                       help="Mode of the Tool")

    # Subparser for mode 'actions'
    actions_parser = subparsers.add_parser(Mode.ACTIONS.value,
                                           help="Show all registered actions and their documentation.",
                                           formatter_class=CustomArgparseFormatter)
    # Subparser for mode 'axe'
    axe_parser = subparsers.add_parser(Mode.AXE.value,
                                       parents=[parent_processing_parser],
                                       help="Use Axe-Mode.",
                                       formatter_class=CustomArgparseFormatter)
    axe_parser.add_argument("--axe_rules", type=str,
                            default="wcag22aa",
                            help=textwrap.dedent("""\
                                Define axe rules (comma separated) that should be checked. set empty to use all axe rules.
                                see: https://github.com/dequelabs/axe-core/blob/develop/doc/API.md#axe-core-tags for rule names
                                example: --axe_rules "wcag2aa, wcag21aa, wcag22aa"
                                """).strip())

    # Subparser for mode 'contrast'
    contrast_parser = subparsers.add_parser(Mode.CONTRAST.value,
                                            parents=[parent_processing_parser],
                                            help="Use Contrast-Mode.",
                                            formatter_class=CustomArgparseFormatter)
    contrast_parser.add_argument("--contrast_threshold", type=float,
                                 help="The minimum contrast ratio to meet WCAG requirements.", nargs="?", default=4.5)
    contrast_parser.add_argument("--use_canny_edge_detection", action="store_true",
                                 help="Apply and use Canny edge detection on processed images.")
    contrast_parser.add_argument("--use_antialias", action="store_true",
                                 help="Apply and use antialias on processed images.")
    contrast_parser.add_argument("--selector", type=str,
                                 help="CSS selector to find elements on the page.", nargs="?", default="a, button:not([disabled])")
    contrast_parser.add_argument("--color_source", type=ColorSource,
                                 help="The source to extract the colors from to check.",
                                 choices=list(ColorSource), nargs="?", default=ColorSource.ELEMENT)
    contrast_parser.add_argument("--alternate_color_suggestion", action="store_true",
                                 help="Use alternative color suggestion algorithm (RGB color basis and computation heavy) - default is HSL color spectrum.")
    contrast_parser.add_argument("--report_level", type=ReportLevel,
                                 help="The level of which to report.",
                                 choices=list(ReportLevel), nargs="?", default=ReportLevel.INVALID)
    return parser
