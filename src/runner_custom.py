from selenium.webdriver.remote.webdriver import WebDriver
from pathlib import Path

from src.config import ProcessingConfig
from src.logger_setup import logger
from src.utils import set_window_size_to_viewport

custom_checker = None
class CustomRunnerScript:
    """
    Tab class to handle tab path visualisation.
    """

    def __init__(self, driver: WebDriver):
        self.driver = driver

        #FIXME implement logic to load custom script
        try:
            tab_file = Path(__file__).parent / "js" / "custom-runner.js"
            logger.debug(f"Loading Tab script from {tab_file}")
            if not tab_file.exists():
                raise FileNotFoundError("Custom script not found in the expected location.")
            with tab_file.open("r", encoding="utf-8") as f:
                self.script_data = f.read()
        except FileNotFoundError:
            logger.error("Custom script not found. Ensure the js directory with script is present in the src folder.")
            raise

    def inject(self):
        """
        Inject the Tab script into the current page.
        """
        self.driver.execute_script(self.script_data)

    def run(self) -> dict:
        """
        Run custom script with the given options.

        :param options: dictionary of options.
        """
        command = (
            f"var callback = arguments[arguments.length - 1];"
            "setTimeout(() => {"
            f"runCustom().then(results => callback(results));"
            "});"
        )
        return self.driver.execute_async_script(command)


def runner_custom(config: ProcessingConfig, driver: WebDriver, results: list,
               screenshots_folder: Path, url_idx: int) -> Path|None:
    global custom_checker
    if custom_checker is None:
        logger.debug("Setting up the custom runner")
        custom_checker = CustomRunnerScript(driver)

    logger.debug(f"Inject custom script to url {url_idx}")
    custom_checker.inject()

    logger.debug(f"Run tab script for url {url_idx}")
    custom_data = custom_checker.run()
    if not custom_data:
        logger.error("no custom data. Skipping further processing.")
        return None

    if custom_data['success']:
        data = custom_data.get('data', custom_data)
        results.append(data)
    else:
        error_info = custom_data.get('error', {'message': 'Unbekannter Fehler'})
        logger.error(f"Custom-Analyse error: {error_info['message']}")
        logger.debug(f"Error Details: {error_info.get('details', 'No details available')}")
        results.append({'error': error_info['message'], 'status': 'failed'})

    set_window_size_to_viewport(driver)
    full_page_screenshot_path_outline = Path(config.output) / f"{config.mode.value}_{url_idx}_full_page_screenshot_outline.png"
    logger.debug(f"Taking full-page screenshot and saving to: {full_page_screenshot_path_outline}")
    driver.save_screenshot(full_page_screenshot_path_outline.as_posix())

    return full_page_screenshot_path_outline
