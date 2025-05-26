from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium_axe_python import Axe
from pathlib import Path

from src.config import ProcessingConfig
from src.logger_setup import logger
from src.runner_contrast import outline_elements_for_screenshot


def axe_mode_setup(config: ProcessingConfig, driver: webdriver) -> Axe:
    """
    Setup Axe
    :param config: Configuration object containing settings.
    :param driver: Selenium WebDriver instance.
    """
    logger.debug("Setting up axe")
    axe = Axe(driver)
    return axe

def runner_axe(axe: Axe, config: ProcessingConfig, driver: webdriver, results: list,
               screenshots_folder: Path, url_idx: int) -> Path|None:
    if axe is None:
        logger.error("Axe is not initialized. Please call axe_mode_setup first.")
        return None

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
    axe_data = axe.run(options=options)

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
                        element.screenshot(dat["screenshot"])
                        logger.debug(f"Element Screenshot saved to {dat['screenshot']}")
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
