import os
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

from src.action_handler import register_action, parse_param_to_key_value
from src.config import ProcessingConfig
from src.logger_setup import logger

@register_action("upload")
def upload_action(config: ProcessingConfig, driver: webdriver, param: str | None) -> None:
    """
    Syntax: `@upload <selector>=<file_path>`

    Uploads a file to the input field identified by the CSS selector `<selector>`.
    ```
    @upload: #input-button=/path/to/file.txt
    ```
    """
    key, val = parse_param_to_key_value(param)

    if not key or not val:
        logger.warning("Invalid parameter for upload action. Expected format: 'selector=file_path'.")
        return
    logger.debug(f"Uploading file '{val}' to element with selector '{key}'")
    try:
        element = driver.find_element(By.CSS_SELECTOR, key)
        # check if element is input type file
        if element.get_attribute("type") != "file":
            logger.warning(f"Element with selector '{key}' is not an input type file.")
            return
        absolute_path = os.path.abspath(val)
        logger.debug(f"Uploading file from path: {absolute_path}")
        element.send_keys(absolute_path)
    except NoSuchElementException:
        logger.warning(f"No element found for upload action with selector: {key}")
        return
    except Exception as e:
        logger.error(f"Error during file upload: {e}")


