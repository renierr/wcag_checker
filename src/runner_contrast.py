from pathlib import Path
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from src.config import ReportLevel, ProcessingConfig
from src.contrast import check_contrast
from src.css import inject_outline_css
from src.logger_setup import logger
from src.utils import define_get_path_script, get_csspath, set_window_size_to_viewport


def runner_contrast(config: ProcessingConfig, driver: WebDriver, results: list, screenshots_folder: Path, url_idx: int) -> Path | None:
    """
    This function checks the contrast of elements on a webpage using Selenium.

    :param config: Configuration object containing settings.
    :param driver: Selenium WebDriver instance.
    :param results: List to store results.
    :param screenshots_folder: Path to the folder where screenshots will be saved.
    :param url_idx: Index of the URL being processed.
    :return: Path to the full-page screenshot with outlines of elements.
    """

    # find visible elements on page
    if config.context:
        context = driver.find_elements(By.CSS_SELECTOR, config.context)
        if context:
            elements = []
            for element in context:
                elements += [element for element in element.find_elements(By.CSS_SELECTOR, config.selector) if element.is_displayed()]
        else:
            logger.warning(f"No context found for selector {config.context}. Using all visible elements.")
            elements = [element for element in driver.find_elements(By.CSS_SELECTOR, config.selector) if element.is_displayed()]
    else:
        elements = [element for element in driver.find_elements(By.CSS_SELECTOR, config.selector) if element.is_displayed()]
    define_get_path_script(driver)  # will later be used in JavaScript for element XPath
    missed_contrast_elements = []
    logger.info(f"Found {len(elements)} elements on page.")
    for index, element in enumerate(elements):
        try:
            element_path = get_csspath(driver, element)
            if element.size['width'] == 0 or element.size['height'] == 0:
                results.append({
                    "element_index": index,
                    "element_path": element_path,
                    "element_text": element.text,
                    "error": f"Skipping element {index} due to 0 width or height."
                })
                continue

            screenshot_path = screenshots_folder / f"{config.mode.value}_{url_idx}_link_{index}.png"
            if not check_contrast(driver, config, index, element, screenshot_path, results, element_path=element_path):
                missed_contrast_elements.append(element)
        except Exception as e:
            error_message = str(e).splitlines()[0]
            logger.error(f"Error on element {index}: {error_message}")
            results.append({
                "element_index": index,
                "error": error_message
            })
            if config.debug:
                raise e
    # last screenshot with outline of elements
    full_page_screenshot_path_outline = outline_elements_for_screenshot(config, driver, elements,
                                                                        missed_contrast_elements, url_idx)
    return full_page_screenshot_path_outline


def outline_elements_for_screenshot(config: ProcessingConfig, driver: WebDriver, elements: list[WebElement],
                                    missed_contrast_elements: list, url_idx: int) -> Path:
    set_window_size_to_viewport(driver)
    inject_outline_css(driver)
    full_page_screenshot_path_outline = Path(config.output) / f"{config.mode.value}_{url_idx}_full_page_screenshot_outline.png"
    logger.debug(f"Taking full-page screenshot with outlines and saving to: {full_page_screenshot_path_outline}")
    # language=JS
    script = """
        arguments[0].classList.add('contrat_checker--outline');
        
        // Create a label with the index number
        const label = document.createElement('div');
        label.textContent = arguments[1];
        label.className = 'contrat_checker--label';
        label.style.left = (arguments[0].getBoundingClientRect().left + window.scrollX) + 'px';
        label.style.top = (arguments[0].getBoundingClientRect().top + window.scrollY - 20) + 'px';
        document.body.appendChild(label);
    """

    for index, element in enumerate(elements):
        try:
            if element.size['width'] == 0 or element.size['height'] == 0:
                logger.debug(f"Element {index} has 0 width or height. Skipping outline.")
                continue

            missed_element_present = (elements == missed_contrast_elements) or any(element == missed for missed in missed_contrast_elements)
            report_invalid_only = config.report_level == ReportLevel.INVALID
            if report_invalid_only and not missed_element_present:
                logger.debug(f"Element {index} is not in missed_contrast_elements and invalid_only mode is set. Skipping outline.")
                continue

            output_label = f"⚠️{index}" if missed_element_present else f"✓{index}"
            driver.execute_script(script, element, output_label)
        except Exception:
            pass
    driver.save_screenshot(full_page_screenshot_path_outline)

    # clear outlines and labels
    # language=JS
    cleanup_script = """
        document.querySelectorAll('.contrat_checker--outline').forEach(el => el.classList.remove('contrat_checker--outline'));
        document.querySelectorAll('.contrat_checker--label').forEach(label => label.remove());
    """
    driver.execute_script(cleanup_script)

    return full_page_screenshot_path_outline
