from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from src.action_handler import register_action, parse_param_to_key_value
from src.config import ProcessingConfig
from src.logger_setup import logger
from src.utils import wait_page_loaded

special_chars = {
    "<CR>": "\r",
    "<LF>": "\n",
    "<TAB>": "\t",
    "<ESC>": Keys.ESCAPE,
    "<BACKSPACE>": Keys.BACKSPACE,
    "<DELETE>": Keys.DELETE,
    "<ENTER>": Keys.ENTER,
    "<SHIFT>": Keys.SHIFT,
    "<CTRL>": Keys.CONTROL,
    "<ALT>": Keys.ALT,
    "<F1>": Keys.F1,
    "<F2>": Keys.F2,
    "<F3>": Keys.F3,
    "<F4>": Keys.F4,
    "<F5>": Keys.F5,
    "<F6>": Keys.F6,
    "<F7>": Keys.F7,
    "<F8>": Keys.F8,
    "<F9>": Keys.F9,
    "<F10>": Keys.F10,
    "<F11>": Keys.F11,
    "<F12>": Keys.F12,
    "<ARROW_UP>": Keys.ARROW_UP,
    "<ARROW_DOWN>": Keys.ARROW_DOWN,
    "<ARROW_LEFT>": Keys.ARROW_LEFT,
    "<ARROW_RIGHT>": Keys.ARROW_RIGHT,
    "<HOME>": Keys.HOME,
    "<END>": Keys.END,
    "<PAGE_UP>": Keys.PAGE_UP,
    "<PAGE_DOWN>": Keys.PAGE_DOWN,
    "<META>": Keys.META,
    "<COMMAND>": Keys.COMMAND,
    "<INSERT>": Keys.INSERT,
    "<SPACE>": Keys.SPACE,
    "<PLUS>": Keys.ADD,
}
special_keys_doc = ", ".join([f"`{key}`" for key in special_chars.keys()])

@register_action("input")
def input_action(config: ProcessingConfig, driver: webdriver, param: str) -> None:
    """
    Syntax: `@input <selector>=<text>`

    Types the given `<text>` into the input field identified by `<selector>`.

    You can use special keys via placeholders: {special_keys_doc}

    ```
    @input #username-field=My input text<LF>
    ```
    """
    if not param or "=" not in param:
        logger.warning("Invalid parameter for input action. Expected format: 'selector=value'.")
        return

    selector, text = parse_param_to_key_value(param)
    logger.debug(f"Inputting text '{text}' into element with selector '{selector}'")

    try:
        elem = driver.find_element(By.CSS_SELECTOR, selector)
        for placeholder, char in special_chars.items():
            text = text.replace(placeholder, char)
        elem.send_keys(text)
        wait_page_loaded(driver)
    except NoSuchElementException:
        logger.warning(f"Element with selector '{selector}' is not displayed.")
        return

input_action.__doc__ = input_action.__doc__.format(special_keys_doc=special_keys_doc)

@register_action("clear")
def clear_action(config: ProcessingConfig, driver: webdriver, param: str) -> None:
    """
    Syntax: `@clear <selector>`

    Clears the input field identified by the CSS selector `<selector>`.
    ```
    @clear: #input-field
    ```
    """
    if not param:
        logger.warning("no selector provided for clear action.")
        return
    try:
        element = driver.find_element(By.CSS_SELECTOR, param)
        element.clear()
    except NoSuchElementException:
        logger.warning(f"No element found for clear action with selector: {param}")
        return

@register_action("select")
def select_action(config: ProcessingConfig, driver: webdriver, param: str) -> None:
    """
    Syntax: `@select <selector>=<value>`

    Selects an option from a dropdown or select element identified by the CSS selector `<selector>`.
    You can specify the option value to select.
    ```
    @select: #dropdown-menu=option_value
    ```
    """
    if not param or "=" not in param:
        logger.warning("Invalid parameter for select action. Expected format: 'selector=value'.")
        return
    selector, value = parse_param_to_key_value(param)
    logger.debug(f"Selecting value '{value}' in element with selector '{selector}'")
    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)
        Select(element).select_by_value(value)
    except NoSuchElementException:
        logger.warning(f"No element found for select action with selector: {selector}")
        return

@register_action("send_keys")
def send_keys_action(config: ProcessingConfig, driver: webdriver, param: str | None) -> None:
    """
    Syntax: `@send_keys <selector>=<keys>`

    Sends keys to the element identified by the CSS selector `<selector>`.

    You can use special keys via placeholders:
    {special_keys_doc}
    ```
    @send_keys: #element-id=Hello World<CR>
    ```
    """
    if not param or "=" not in param:
        logger.warning("Invalid parameter for send_keys action. Expected format: 'selector=keys'.")
        return

    selector, keys = parse_param_to_key_value(param)
    logger.debug(f"Sending keys '{keys}' to element with selector '{selector}'")

    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)
        for placeholder, char in special_chars.items():
            keys = keys.replace(placeholder, char)
        element.send_keys(keys)
    except NoSuchElementException:
        logger.warning(f"No element found for send_keys action with selector: {selector}")
        return
send_keys_action.__doc__ = send_keys_action.__doc__.format(special_keys_doc=special_keys_doc)

@register_action("send_key_combination")
def send_key_combination(config: ProcessingConfig, driver: webdriver, param: str | None) -> None:
    """
    Syntax: `@send_key_combination <selector>=<key_combination>` or `@send_key_combination <key_combination>`

    Sends a key combination to the element identified by the CSS selector `<selector>`.
    Or if no selector is provided, it sends the key combination to the active element.

    The key combination should be a string of keys separated by '+'.

    You can use special keys via placeholders:
    {special_keys_doc}

    ```
    @send_key_combination: #element-id=<CTRL>+<SHIFT>+x
    @send_key_combination: <CTRL>+a
    ```
    """
    if not param:
        logger.warning("Invalid parameter for send_key_combination action.")
        return

    selector, key_combination = parse_param_to_key_value(param)
    logger.debug(f"Sending key combination '{key_combination}' to element with selector '{selector}'")

    try:
        keys = key_combination.split('+')
        action_chain = ActionChains(driver)
        if selector:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            action_chain.click(element)

        # Press and hold special keys
        for key in keys:
            action_chain.key_down(special_chars.get(key, key))

        # Release all keys
        for key in keys:
            action_chain.key_down(special_chars.get(key, key))

        action_chain.perform()
    except NoSuchElementException:
        logger.warning(f"No element found for send_key_combination action with selector: {selector}")
        return
send_key_combination.__doc__ = send_key_combination.__doc__.format(special_keys_doc=special_keys_doc)


@register_action("submit")
def submit_action(config: ProcessingConfig, driver: webdriver, param: str | None) -> None:
    """
    Syntax: `@submit <selector>`

    Submits the form identified by the CSS selector `<selector>`.
    ```
    @submit: #form-id
    ```
    """
    if not param:
        logger.warning("No selector provided for submit action.")
        return

    try:
        element = driver.find_element(By.CSS_SELECTOR, param)
        element.submit()
    except NoSuchElementException:
        logger.warning(f"No element found for submit action with selector: {param}")
        return
