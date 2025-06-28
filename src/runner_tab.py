from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
from pathlib import Path

from src.config import ProcessingConfig
from src.logger_setup import logger
from src.utils import set_window_size_to_viewport

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

    def run(self, tab_elements: list[WebElement] = None) -> dict:
        """
        Run tabpath script with the given options.

        :param options: dictionary of options.
        """
        command = (
            f"var callback = arguments[arguments.length - 1];"
            f"var elements = arguments[0];"
            "setTimeout(() => {"
            f"runTabpathAnalysis(elements).then(results => callback(results));"
            "});"
        )
        return self.driver.execute_async_script(command, tab_elements)

    def cleanup(self):
        """
        Cleanup the tabpath script.
        """
        self.driver.execute_script("cleanTabpathVisualization();")

def _collect_elements_by_tab_key(driver: WebDriver) -> list[WebElement]:
    """
    Collects all elements that are focusable by the tab key on the current page.
    This function simulates pressing the Tab key to navigate through focusable elements
    and collects them in a list.

    :param driver: The Selenium WebDriver instance.
    :return: A list of WebElement objects that are focusable by the tab key.
    """

    # send tab keys to page to collect all elements focusable by tab key
    logger.info("Sending tab keys to page to collect focusable elements, this may take a while")
    focusable_elements: list[WebElement] = []
    seen_elements = set()  # Track elements by a hash of their properties
    max_tabs = 10000  # Limit the number of tabs to prevent infinite loops
    current_tab_count = 0

    # Reset focus by clicking at (0,0) or sending the page to the top first
    driver.execute_script("window.scrollTo(0, 0);")
    # Send Escape key to clear any potential focus
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()

    first_element_signature = None
    action = ActionChains(driver)
    while current_tab_count < max_tabs:
        # Press the Tab key
        action.send_keys(Keys.TAB).perform()
        current_tab_count += 1

        # Get the currently focused element
        current_element: WebElement = driver.switch_to.active_element

        try:
            # Create a unique signature for this element
            element_signature = (
                current_element.tag_name,
                current_element.location['x'],
                current_element.location['y']
            )

            print(".", end="", flush=True)  # Print dots to indicate progress

            # Store the first element signature to detect cycling
            if first_element_signature is None:
                first_element_signature = element_signature
            elif element_signature == first_element_signature and current_tab_count > 1:
                logger.debug(f"Tab cycle detected after {current_tab_count} tabs")
                break

            # Check if we've already seen this element
            if element_signature not in seen_elements:
                seen_elements.add(element_signature)
                focusable_elements.append(current_element)

        except StaleElementReferenceException:
            logger.debug("Encountered stale element reference")
            continue

    return focusable_elements


def runner_tab(config: ProcessingConfig, driver: WebDriver, results: list,
               screenshots_folder: Path, url_idx: int) -> Path|None:
    global tabpath_checker
    if tabpath_checker is None:
        logger.debug("Setting up tab runner")
        tabpath_checker = TabRunnerScript(driver)

    # send tab keys to page to collect all elements focusable by tab key
    tab_elements = _collect_elements_by_tab_key(driver)
    logger.info(f"Found {len(tab_elements)} tabbable elements on page.")

    logger.debug(f"Inject tab script to url {url_idx}")
    tabpath_checker.inject()

    logger.debug(f"Run tab script for url {url_idx}")
    tabpath_data = tabpath_checker.run(tab_elements=tab_elements)
    if not tabpath_data:
        logger.error("Tab path analysis returned no data. Skipping further processing.")
        return None
    if tabpath_data['success']:
        data = tabpath_data.get('data', tabpath_data)
        results.append(data)
        if 'missed_elements' in data and data['missed_elements']:
            logger.warning(f"Tab path analysis found {len(data['missed_elements'])} missed elements.")
    else:
        error_info = tabpath_data.get('error', {'message': 'Unbekannter Fehler'})
        logger.error(f"Tab-Analyse error: {error_info['message']}")
        logger.debug(f"Error Details: {error_info.get('details', 'No details available')}")
        results.append({'error': error_info['message'], 'status': 'failed'})

    set_window_size_to_viewport(driver)
    full_page_screenshot_path_outline = Path(config.output) / f"{config.mode.value}_{url_idx}_full_page_screenshot_outline.png"
    logger.debug(f"Taking full-page screenshot and saving to: {full_page_screenshot_path_outline}")
    driver.save_screenshot(full_page_screenshot_path_outline.as_posix())
    tabpath_checker.cleanup()

    return full_page_screenshot_path_outline
