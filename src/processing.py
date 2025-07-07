import json
import sys
import time
from pathlib import Path

import selenium.common
from selenium.webdriver.remote.webdriver import WebDriver

from src.action_handler import action_registry
from src.actions.analyse_action import analyse_action
from src.browser_console_log_handler import handle_browser_console_log, get_browser_console_log
from src.config import Config, ProcessingConfig, ConfigEncoder, ReportLevel, Runner
from src.logger_setup import logger
from src.report import build_markdown, generate_markdown_report, generate_html_report
from src.utils import call_url, get_full_base_url


def check_run(config: ProcessingConfig) -> None:
    """
    Main function to process the config and inputs.
    This function initializes the Selenium WebDriver, processes the inputs,
    and generates reports based on the configuration.

    :param config: Config object base class can be instances of sub classes.
    """
    info_logs_of_config(config)

    # create folders
    Path(config.output).mkdir(parents=True, exist_ok=True)

    screenshots_folder = Path(config.output) / "screenshots"
    screenshots_folder.mkdir(parents=True, exist_ok=True)

    json_data = {}
    if isinstance(config, ProcessingConfig):
        if config.simulate:
            logger.info(f"Simulating with file: {config.simulate}")
            with open(config.simulate, "r") as f:
                json_data = json.load(f)
        else:
            # if inputs contain a string with prefix "config:" thread it as a file and read the lines as inputs to append
            expanded_inputs = parse_inputs(config.inputs)
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
            if config.browser_visible:
                #options.add_argument("--auto-open-devtools-for-tabs")
                pass
            else:
                options.add_argument("--headless")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-extensions")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.enable_bidi = True
            if config.browser == "edge":
                driver = selenium.webdriver.Edge(options=options)
            else:
                driver = selenium.webdriver.Chrome(options=options)

            logger.debug(f"Selenium WebDriver Initialized")
            driver.script.add_console_message_handler(handle_browser_console_log)
            try:
                # first go to login url if defined
                if config.login:
                    logger.info(f"Perform Login with URL: {config.login}")
                    call_url(driver, config.login)

                base_url = get_full_base_url(driver)
                logger.debug(f"Extracted Base URL: {base_url}")

                url_data = []
                last_action = None
                for url_idx, input in enumerate(expanded_inputs):
                    url_idx += 1
                    logger.info(f"[{url_idx}/{inputs_len}] Processing Input or Action: {input}")
                    entry = None
                    results = []

                    try:
                        # detect actions starting with @
                        if isinstance(input, str) and input.startswith("@"):
                            entry = handle_action(config, driver, input)
                            if entry:
                                if last_action:
                                    entry["last_action"] = last_action
                                entry["action"] = input
                                url_data.append(entry)
                            last_action = input
                            continue

                        # normal url navigation
                        call_url(driver, input)
                        entry = analyse_action(config, driver, None)
                        entry["url"] = input  # ensure the URL is set in the entry
                        last_action = "direct url analyse for: " + input

                    except Exception as e:
                        error_message = str(e).splitlines()[0]
                        logger.error(f"Error processing Input or Action {input}: {error_message}")
                        results.append({
                            "url": input,
                            "error": error_message
                        })
                        if config.debug:
                            raise e

                    if entry:
                        url_data.append(entry)


                json_data.update({
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "base_url": base_url,
                    "total_inputs": len(url_data),
                    "inputs": url_data,
                    "browser_console_log": get_browser_console_log(),
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
                if config.browser_leave_open and config.browser_visible:
                    logger.warning("Leave Browser open by user request - close it yourself or things happen.")
                else:
                    driver.quit()

    reporting(config, json_data)
    logger.info("Finished.")
    if config.browser_leave_open and config.browser_visible:
        logger.warning("The browser has been left open - remember to close it later to close the tool.")


def info_logs_of_config(config: ProcessingConfig) -> None:
    """
    Log the configuration details.
    :param config: Config object containing all arguments.
    """
    logger.info(f"Running in mode: {config.mode.value}")
    logger.info(f"Browser: {config.browser}")
    logger.info(f"Browser visible: {'Yes' if config.browser_visible else 'No'}")
    logger.info(f"Base folder for output: {config.output}")
    logger.info(f"Login URL: {config.login if config.login else 'None'}")
    logger.info(f"Resolution: {config.resolution_width}x{config.resolution_height}")
    logger.info(f"JSON output enabled: {'Yes' if config.json else 'No'}")
    logger.info(f"Markdown report enabled: {'Yes' if config.markdown else 'No'}")
    logger.info(f"HTML report enabled: {'Yes' if config.html else 'No'}")
    logger.info(f"Simulate with file: {config.simulate if config.simulate else 'None'}")
    logger.info(f"Inputs to check ({len(config.inputs)}): {config.inputs}")

    if config.runner == Runner.CONTRAST:
        logger.info(f"Using selector: {config.selector}")
        logger.info(f"Contrast ratio threshold: {config.contrast_threshold}")
        logger.info("Reporting only invalid elements (do not meet WCAG requirements): " + ("Yes" if config.report_level == ReportLevel.INVALID else "No"))
        logger.info(f"Color source: {config.color_source}")
        logger.info(f"Image processing options - Canny-edge detection: {config.use_canny_edge_detection}, Antialias: {config.use_antialias}")
        if config.alternate_color_suggestion:
            logger.info("Using alternate RGB color suggestion algorithm.")
        else:
            logger.info("Using default HSL color spectrum for suggestions.")

    if config.runner == Runner.AXE:
        logger.info(f"Axe rules to check: {config.axe_rules if config.axe_rules else 'default'}")

    if config.runner == Runner.TAB:
        logger.info(f"Missing TAB check: {config.missing_tab_check}")


def handle_action(config: ProcessingConfig, driver: WebDriver, action_str: str) -> dict | None:
    """Delegates action handling to the ActionRegistry."""
    return action_registry.execute(config, driver, action_str)


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
            with open(config_file, "r") as f:
                lines = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith("#")]
                combined_line = None
                for line in lines:
                    if combined_line:
                        combined_line += " " + line
                        if line.startswith("}"):
                            parsed_inputs.append(combined_line)
                            combined_line = None
                    elif line.endswith("{"):
                        combined_line = line
                    else:
                        parsed_inputs.append(line)
        else:
            parsed_inputs.append(input_check)
    return parsed_inputs


def reporting(config: Config, json_data: dict) -> None:
    """
    Generate reports based on the configuration and JSON data.
    :param config: Config object containing all arguments.
    :param json_data: JSON data containing the report details.
    """

    if not json_data:
        logger.warning("No data to report. Exiting.")
        return
    if isinstance(config, ProcessingConfig) and (config.markdown or config.html):
        logger.info("Building Markdown report data...")
        markdown_report_data = build_markdown(config, json_data)

        if config.markdown:
            logger.info("Generating Markdown report...")
            generate_markdown_report(config, json_data, markdown_data=markdown_report_data)
        if config.html:
            logger.info("Generating HTML report...")
            generate_html_report(config, json_data, markdown_data=markdown_report_data)
