from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from pathlib import Path
import re

from src.config import ProcessingConfig
from src.logger_setup import logger
from src.runner_contrast import outline_elements_for_screenshot
from src.utils import take_element_screenshot

axe = None
class Axe:
    """
    Axe class to handle accessibility checks using the Axe library.
    """

    def __init__(self, driver: WebDriver):
        self.driver = driver

        try:
            axe_file = Path(__file__).parent / "axe-core" / "axe.min.js"
            logger.debug(f"Loading Axe script from {axe_file}")
            if not axe_file.exists():
                raise FileNotFoundError("Axe script not found in the expected location.")
            # Load the Axe script from the package
            with axe_file.open("r", encoding="utf-8") as f:
                self.script_data = f.read()

            # Extract Axe version using regex.
            version_pattern = re.compile(r'\! axe v([\d.]+)')
            match = version_pattern.search(self.script_data)
            if match:
                version = match.group(1)
                logger.info(f"Using Axe version: {version}")
            else:
                logger.warning("Axe version not found in the script.")
        except FileNotFoundError:
            logger.error("Axe script not found. Ensure the axe-core directory is present in the src folder.")
            raise

    def inject(self):
        """
        Inject the Axe script into the current page.
        """
        self.driver.execute_script(self.script_data)

    def run(self, context: object = None, options: dict = None) -> dict:
        """
        Run Axe accessibility checks with the given options.

        :param context: which page part(s) to analyze and/or what to exclude.
        :param options: dictionary of Axe options.
        """
        args = ""

        if context:
            args += f"'{context}'"
            if options is not None:
                args += ","

        if options is not None:
            args += f"{options}"
        logger.debug(f"Running Axe with args: {args}")
        command = (
            f"var callback = arguments[arguments.length - 1];"
            "setTimeout(() => {"
            f"axe.run({args}).then(results => callback(results));"
            "});"
        )
        return self.driver.execute_async_script(command)

def runner_axe(config: ProcessingConfig, driver: WebDriver, results: list,
               screenshots_folder: Path, url_idx: int) -> Path|None:
    global axe
    if axe is None:
        logger.debug("Setting up axe")
        axe = Axe(driver)

    logger.debug(f"Inject axe to url {url_idx}")
    axe.inject()

    logger.debug(f"Run axe for url {url_idx}")
    options = {
        "resultTypes": ["violations", "incomplete"]
    }

    if config.axe_rules:
        rules = [rule.strip() for rule in config.axe_rules.split(",")]
        logger.debug(f"Setting axe rules: {rules}")
        options["runOnly"] = dict(type="tag", values=rules)  # type: ignore
    axe_data = axe.run(context=config.context, options=options)

    # extract violation elements
    elements: list[WebElement] = []
    elm_idx = 0
    violations = axe_data.get("violations", [])
    for violation in violations:
        for node in violation.get("nodes", []):
            element = node.get("target", [])
            if element:
                element_path = element[0]
                screenshot_path = screenshots_folder / f"{config.mode.value}_{url_idx}_link_{elm_idx}.png"
                dat = {
                    "index": elm_idx,
                    "path": element_path,
                    "screenshot": screenshot_path.as_posix()
                }
                node["element_info"] = dat
                elm_idx += 1
                # find an element and take a screenshot
                try:
                    element = driver.find_element(By.CSS_SELECTOR, element_path)
                    if element.size['width'] == 0 or element.size['height'] == 0:
                        logger.debug(f"Element {elm_idx} has 0 width or height. Skipping screenshot.")
                        continue
                    elif element.is_displayed():
                        elements.append(element)
                        take_element_screenshot(driver, element, elm_idx, screenshot_path)
                        element.screenshot(dat["screenshot"])
                    else:
                        logger.debug(f"Element {elm_idx} is not displayed. Skipping screenshot.")
                        node["element_info"]["screenshot"] = None
                except Exception as e:
                    logger.error(f"Error taking screenshot of element {elm_idx}: {e}")
                    dat["error"] = str(e)

    results.append(axe_data)
    logger.info(f"Found {len(elements)} violating elements on page.")
    full_page_screenshot_path_outline = outline_elements_for_screenshot(config, driver, elements,
                                                                        elements, url_idx)
    return full_page_screenshot_path_outline
