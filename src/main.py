import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
import json
import logging
import time
import importlib
import pkgutil

from rich.console import Console
from rich.markdown import Markdown
from selenium import webdriver
import selenium.common.exceptions

from src.logger_setup import logger
from src.arg_parse import argument_parser
from src.utils import get_embedded_file_path, call_url, get_full_base_url, filter_args_for_dataclass
from src.report import generate_markdown_report, generate_html_report, build_markdown
from src.youtrack import report_to_youtrack_as_issue, YouTrackAPI
from src.config import Config, AxeConfig, ContrastConfig, ConfigEncoder, Mode, ReportLevel
from src.action_handler import action_registry, print_action_documentation
from src.actions.analyse_action import analyse_action
import src.actions

# dynamically load all actions from the actions module
def load_all_actions():
    for _, module_name, _ in pkgutil.iter_modules(src.actions.__path__):
        importlib.import_module(f"src.actions.{module_name}")


def info_logs_of_config(config: Config) -> None:
    """
    Log the configuration details.
    :param config: Config object containing all arguments.
    """
    logger.info(f"Running in mode: {config.mode.value}")
    logger.info(f"Browser: {config.browser}")
    logger.info(f"Base folder for output: {config.output}")
    logger.info(f"Inputs to check ({len(config.inputs)}): {config.inputs}")

    if config.mode == Mode.CONTRAST:
        logger.info(f"Using selector: {config.selector}")
        logger.info(f"Contrast ratio threshold: {config.contrast_threshold}")
        logger.info("Reporting only invalid elements (do not meet WCAG requirements): " + ("Yes" if config.report_level == ReportLevel.INVALID else "No"))
        logger.info(f"Color source: {config.color_source}")
        logger.info(f"Image processing options - Canny-edge detection: {config.use_canny_edge_detection}, Antialias: {config.use_antialias}")
        if config.alternate_color_suggestion:
            logger.info("Using alternate RGB color suggestion algorithm.")
        else:
            logger.info("Using default HSL color spectrum for suggestions.")

    if config.mode == Mode.AXE:
        logger.info(f"Axe rules to check: {config.axe_rules if config.axe_rules else 'default'}")


def handle_action(config: Config, driver: webdriver, action_str: str) -> dict | None:
    """Delegates action handling to the ActionRegistry."""
    return action_registry.execute(config, driver, action_str)


def main(config: Config, youtrack: YouTrackAPI = None) -> None:
    """
    Main function to check a contrast ratio of elements on a webpage.

    :param config: Config object containing all arguments.
    :param youtrack: YouTrackAPI object for reporting issues.
    """
    info_logs_of_config(config)

    # create folders
    Path(config.output).mkdir(parents=True, exist_ok=True)

    screenshots_folder = Path(config.output) / "screenshots"
    screenshots_folder.mkdir(parents=True, exist_ok=True)

    json_data = {}
    if config.simulate:
        logger.info(f"Simulating with file: {config.simulate}")
        with open(config.simulate, "r") as f:
            json_data = json.load(f)
    else:
        # if inputs contain a string with prefix "config:" thread it as a file and read the lines as inputs to append
        expanded_inputs = []
        for input_check in config.inputs:
            if isinstance(input_check, str) and input_check.startswith("config:"):
                config_file = input_check.replace("config:", "")
                logger.info(f"Reading inputs from config file: {config_file}")
                with open(config_file, "r") as f:
                    file_inputs = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith("#")]
                    expanded_inputs.extend(file_inputs)
            else:
                expanded_inputs.append(input_check)
        inputs_len = len(expanded_inputs)
        if inputs_len == 0:
            logger.error("No Inputs provided to check. Please provide at least one input or a config file")
            sys.exit(1)

        logger.info("Starting Selenium WebDriver")
        if config.browser == "edge":
            from selenium.webdriver.edge.options import Options
            options = Options()
        else:
            from selenium.webdriver.chrome.options import Options
            options = Options()
        if not config.browser_visible:
            options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        if config.browser == "edge":
            driver = webdriver.Edge(options=options)
        else:
            driver = webdriver.Chrome(options=options)
        try:
            # first go to login url if defined
            if config.login:
                logger.info(f"Perform Login with URL: {config.login}")
                call_url(driver, config.login)

            base_url = get_full_base_url(driver)
            logger.debug(f"Extracted Base URL: {base_url}")

            url_data = []
            for url_idx, url in enumerate(expanded_inputs):
                url_idx += 1
                logger.info(f"[{url_idx}/{inputs_len}] Processing Input or Action: {url}")
                entry = None
                results = []

                try:
                    # detect actions starting with @
                    if isinstance(url, str) and url.startswith("@"):
                        entry = handle_action(config, driver, url)
                        if entry:
                            url_data.append(entry)
                        continue

                    # normal url will get analysed directly
                    entry = analyse_action(config, driver, url)

                except Exception as e:
                    error_message = str(e).splitlines()[0]
                    logger.error(f"Error processing Input or Action {url}: {error_message}")
                    results.append({
                        "url": url,
                        "error": error_message
                    })
                    if config.debug:
                        raise e

                if entry:
                    url_data.append(entry)


            json_data.update({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "base_url": base_url,
                "config": config.__dict__,
                "total_inputs": len(url_data),
                "inputs": url_data,
            })

            if config.json:
                results_file = Path(config.output) / f"{config.mode.value}_results.json"
                with results_file.open("w", encoding="utf-8") as json_file:
                    json.dump(json_data, json_file, indent=4, ensure_ascii=False, cls=ConfigEncoder)

        except selenium.common.exceptions.WebDriverException as e:
            logger.error(f"WebDriverException occurred: {e.msg}")
            logger.error(f"Screen: {e.screen}")
            logger.warning("Please check if the URL is correct and the server is running. \
            You can use the --debug flag to enable debug mode. \
            Please check the arguments passed to the script. \
            Use --help to see all available arguments.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e
        finally:
            # close bowser
            driver.quit()

    reporting(config, json_data, youtrack)
    logger.info("Finished checking contrast ratio.")


def reporting(config: Config, json_data: dict, youtrack: YouTrackAPI) -> None:
    """
    Generate reports based on the configuration and JSON data.
    :param config: Config object containing all arguments.
    :param json_data: JSON data containing the report details.
    :param youtrack: YouTrackAPI object for reporting issues.
    """

    if not json_data:
        logger.warning("No data to report. Exiting.")
        return
    if config.markdown or config.html or config.youtrack:
        logger.info("Building Markdown report data...")
        markdown_report_data = build_markdown(config, json_data)

        if config.markdown:
            logger.info("Generating Markdown report...")
            generate_markdown_report(config, json_data, markdown_data=markdown_report_data)
        if config.html:
            logger.info("Generating HTML report...")
            generate_html_report(config, json_data, markdown_data=markdown_report_data)
        if config.youtrack:
            logger.info("Generating YouTrack issues...")
            report_to_youtrack_as_issue(config, youtrack, json_data, markdown_data=markdown_report_data)


def show_readme(file_path: str):
    """
    Zeigt den Inhalt der README.md-Datei im Terminal an.

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


if __name__ == "__main__":

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

    if args.youtrack:
        if not args.youtrack_api_key:
            parser.error("--youtrack_api_key is required when --youtrack is enabled.")
        if not args.youtrack_url:
            parser.error("--youtrack_url is required when --youtrack is enabled.")
        if not args.youtrack_project:
            parser.error("--youtrack_project is required when --youtrack is enabled.")

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled.")

    # convert to dict to create dataclass instances
    args_dict = vars(args)
    args_dict["mode"] = Mode(args_dict["mode"])
    args_dict["resolution"] = tuple(map(int, args_dict["resolution"].split("x")))

    if args.mode == Mode.AXE:
        filtered_args = filter_args_for_dataclass(AxeConfig, args_dict)
        arg_config = AxeConfig(**filtered_args)
    elif args.mode == Mode.CONTRAST:
        filtered_args = filter_args_for_dataclass(ContrastConfig, args_dict)
        arg_config = ContrastConfig(**filtered_args)
    else:
        filtered_args = filter_args_for_dataclass(Config, args_dict)
        arg_config = Config(**filtered_args)

    if args.youtrack:
        youtrack_api = YouTrackAPI(args.youtrack_api_key, args.youtrack_url, args.youtrack_project)
    else:
        youtrack_api = None

    main(arg_config, youtrack_api)

