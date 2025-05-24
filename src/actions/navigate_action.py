from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

from src.action_handler import register_action
from src.logger_setup import logger
from src.utils import call_url


@register_action("scroll")
def scroll_action(config, driver, param):
    """
    Syntax: `@scroll <direction>` or `@scroll <selector>`

    Scrolls the page in a specific direction (top, bottom, left, right) or
    to a specific element identified by a CSS selector `<selector>`.
    ```
    @scroll: bottom
    @scroll: #footer
    ```
    """
    if param in ["top", "bottom", "left", "right"]:
        scroll_script = {
            "top": "window.scrollTo(0, 0);",
            "bottom": "window.scrollTo(0, document.body.scrollHeight);",
            "left": "window.scrollBy(-window.innerWidth, 0);",
            "right": "window.scrollBy(window.innerWidth, 0);"
        }
        driver.execute_script(scroll_script[param])
    else:
        try:
            elem = driver.find_element(By.CSS_SELECTOR, param)
            driver.execute_script("arguments[0].scrollIntoView();", elem)
        except NoSuchElementException:
            logger.warning(f"No element found for scrolling with selector: {param}")
            return


@register_action("navigate")
def navigate_action(config, driver, param):
    """
    Syntax: `@navigate <url>`

    Navigates to the specified `<url>`.
    ```
    @navigate: https://example.com
    @navigate: /servlet/BrowseUser
    ```
    """
    if not param:
        logger.warning("No URL provided for navigation action.")
        return
    call_url(driver, param)


@register_action("hover")
def hover_action(config, driver, param):
    """
    Syntax: `@hover <selector>`

    Hovers over the element identified by the CSS selector `<selector>`.
    ```
    @hover: #menu-item
    ```
    """
    if not param:
        logger.warning("No selector provided for hover action.")
        return
    try:
        element = driver.find_element(By.CSS_SELECTOR, param)
        driver.ActionChains(driver).move_to_element(element).perform()
    except NoSuchElementException:
        logger.warning(f"No element found for hover action with selector: {param}")
        return

@register_action("back")
def back_action(config, driver, param):
    """
    Syntax: `@back`

    Navigates back to the previous page in the browser history.
    ```
    @back
    ```
    """
    driver.back()

@register_action("refresh")
def refresh_action(config, driver, param):
    """
    Syntax: `@refresh`

    Refreshes the current page.
    ```
    @refresh
    ```
    """
    driver.refresh()

