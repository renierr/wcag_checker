from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from pathlib import Path

from src.config import ProcessingConfig
from src.logger_setup import logger

tabpath_checker = None
class TabRunnerScript:
    """
    Tab class to handle tab path visualisation.
    """

    def __init__(self, driver: WebDriver):
        self.driver = driver

        try:
            tab_file = Path(__file__).parent / "js" / "tabpath-runner.js"
            logger.debug(f"Loading Tab script from {tab_file}")
            if not tab_file.exists():
                raise FileNotFoundError("Tab script not found in the expected location.")
            # Load the Tab script from the package
            with tab_file.open("r", encoding="utf-8") as f:
                self.script_data = f.read()
        except FileNotFoundError:
            logger.error("Tabpath script not found. Ensure the js directory with script is present in the src folder.")
            raise

    def inject(self):
        """
        Inject the Tab script into the current page.
        """
        self.driver.execute_script(self.script_data)

    def run(self, options: dict = None) -> dict:
        """
        Run tabpath script with the given options.

        :param options: dictionary of options.
        """
        command = (
            f"var callback = arguments[arguments.length - 1];"
            "setTimeout(() => {"
            f"runTabpathAnalysis().then(results => callback(results));"
            "});"
        )
        return self.driver.execute_async_script(command)

def runner_tab(config: ProcessingConfig, driver: WebDriver, results: list,
               screenshots_folder: Path, url_idx: int) -> Path|None:
    global tabpath_checker
    if tabpath_checker is None:
        logger.debug("Setting up tab runner")
        tabpath_checker = TabRunnerScript(driver)

    logger.debug(f"Inject tab script to url {url_idx}")
    tabpath_checker.inject()

    logger.debug(f"Run tab script for url {url_idx}")
    options = { }
    driver.set_script_timeout(7200)
    tabpath_data = tabpath_checker.run(options=options)

    # extract some info
    elements: list[WebElement] = []
    elm_idx = 0

    results.append(tabpath_data)
    #logger.info(f"Found {len(tabpath_data)} tabbings on page.")
    # take full-pagescreenshot
    full_page_screenshot_path_outline = Path(config.output) / f"{config.mode.value}_{url_idx}_full_page_screenshot_outline.png"
    logger.debug(f"Taking full-page screenshot and saving to: {full_page_screenshot_path_outline}")
    driver.save_screenshot(full_page_screenshot_path_outline)

    # TODO cleanup the tabpath data

    return full_page_screenshot_path_outline
