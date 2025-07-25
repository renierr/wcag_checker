import sys
import base64

from dataclasses import fields
from urllib.parse import urlparse
from pathlib import Path
from selenium.webdriver.support.wait import WebDriverWait
from src.logger_setup import logger

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver

def get_element_colors(driver: WebDriver, element: WebElement) -> tuple:
    """
    Determines the foreground and background colors of an element using JavaScript.

    :param driver: The Selenium WebDriver instance.
    :param element: The WebElement for which to get the colors.
    :return: A tuple containing the foreground and background colors as RGB tuples.
    """

    # language=JS
    script = """
    function parentWithOpacity(el) {
        while (el) {
            const style = window.getComputedStyle(el);
            const opacity = parseFloat(style.getPropertyValue("opacity"));
            if (opacity < 1) {
                return opacity;
            }
            el = el.parentElement;
        }
        return 1;
    }
    function blendColors(baseColor, overlayColor, alpha) {
        return [
            Math.round((1 - alpha) * baseColor[0] + alpha * overlayColor[0]),
            Math.round((1 - alpha) * baseColor[1] + alpha * overlayColor[1]),
            Math.round((1 - alpha) * baseColor[2] + alpha * overlayColor[2])
        ];
    }
    function getComputedColor(el, property, bg_color) {
        let baseColor = [255, 255, 255];
        while (el) {
            const style = window.getComputedStyle(el);
            const color = style.getPropertyValue(property);
            let opacity = 1;
            if (bg_color) {
                opacity = parentWithOpacity(el) || 1;
            }
            if (color.startsWith("rgba")) {
                const match = color.match(/rgba\\((\\d+), (\\d+), (\\d+), ([0-9.]+)\\)/);
                if (match) {
                    const r = parseInt(match[1]);
                    const g = parseInt(match[2]);
                    const b = parseInt(match[3]);
                    const alpha = parseFloat(match[4]) * opacity;
                    if (alpha === 1) {
                        return [r, g, b];
                    } else if (alpha > 0) {
                        baseColor = blendColors(baseColor, [r, g, b], alpha);
                    }
                }
            } else if (color !== "transparent") {
                const match = color.match(/rgb\\((\\d+), (\\d+), (\\d+)/);
                if (match) {
                    const r = parseInt(match[1]);
                    const g = parseInt(match[2]);
                    const b = parseInt(match[3]);
                    if (opacity < 1) {
                        return blendColors(bg_color, [r, g, b], opacity);
                    } else {
                        return [r, g, b];
                    }
                }
            }
            el = el.parentElement;
        }
        return null;
    }
    const backgroundColor = getComputedColor(arguments[0], "background-color", undefined);
    const foregroundColor = getComputedColor(arguments[0], "color", backgroundColor);
    return [foregroundColor, backgroundColor];
    """
    colors = driver.execute_script(script, element)
    return tuple(colors)

def log_colored_char(color1: tuple[int, int, int], color2: tuple[int, int, int], char:str = "⬤"):
    """
    create a colored character with the given colors (ANSI).

    :param color1: color1 tuple (r,g,b)
    :param color2: color2 tuple (r,g,b)
    :param char: character to log (default: "⬤")
    """
    fg_color = f"\033[38;2;{color1[0]};{color1[1]};{color1[2]}m"
    bg_color = f"\033[38;2;{color2[0]};{color2[1]};{color2[2]}m"
    hex_color1 = f"#{color1[0]:02x}{color1[1]:02x}{color1[2]:02x}"
    hex_color2 = f"#{color2[0]:02x}{color2[1]:02x}{color2[2]:02x}"
    reset_color = "\033[38;2;128;128;128m"  # grey as default
    log_message = f"\n\t{reset_color}⤷ Colors checked fg: {fg_color}{char}{reset_color} {hex_color1} | bg: {bg_color}{char}{reset_color} {hex_color2}"
    return log_message

def define_get_path_script(driver: WebDriver) -> None:
    """
    Defines the JavaScript function getXPath in the browser context, if it does not already exist."

    :param driver: Selenium WebDriver instance.
    """

    # language=JS
    script = """
    if (typeof getXPath !== 'function') {
        window.getXPath = function(el) {
            if (el.id !== '') {
                return 'id("' + el.id + '")';
            }
            if (el === document.body) {
                return '/html/body';
            }
            let ix = 0;
            const siblings = el.parentNode.childNodes;
            for (let i = 0; i < siblings.length; i++) {
                const sibling = siblings[i];
                if (sibling === el) {
                    return getXPath(el.parentNode) + '/' + el.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                }
                if (sibling.nodeType === 1 && sibling.tagName === el.tagName) {
                    ix++;
                }
            }
        };
    }
    if (typeof getCSSPath !== 'function') { 
        window.getCSSPath = function(element) {
            if (!(element instanceof Element)) return '';
            const path = [];
            while (element && element.nodeType === Node.ELEMENT_NODE) {
                let selector = element.nodeName.toLowerCase();
                if (element.id) {
                    selector = `#${element.id}`;
                    path.unshift(selector);
                    break;
                } else {
                    let sib = element, nth = 1;
                    while (sib.previousElementSibling) {
                        sib = sib.previousElementSibling;
                        if (sib.nodeName.toLowerCase() === selector) nth++;
                    }
                    if (nth !== 1) selector += `:nth-child(${nth})`;
                }
                path.unshift(selector);
                element = element.parentNode;
            }
            return path.join(' > ');
        };
    }
    """
    driver.execute_script(script)


def get_xpath(driver: WebDriver, element: WebElement) -> str:
    """
    Determines the full XPath of a WebElement using JavaScript.

    :param driver: Selenium WebDriver instance.
    :param element: The WebElement for which to get the XPath.
    :return: The XPath of the WebElement as a string.
    """
    return driver.execute_script("return getXPath(arguments[0]);", element)

def get_csspath(driver: WebDriver, element: WebElement) -> str:
    """
    Determines the full CSS Path of a WebElement using JavaScript.

    :param driver: Selenium WebDriver instance.
    :param element: The WebElement for which to get the XPath.
    :return: The CSS Path of the WebElement as a string.
    """
    return driver.execute_script("return getCSSPath(arguments[0]);", element)

# language=JS
script_viewport_size = """
function getMaxDimensions() {
    // Calculate maximum absolute bottom from all elements
    const allElements = document.querySelectorAll('*');
    let maxBottom = 0;
    allElements.forEach(element => {
        const rect = element.getBoundingClientRect();
        const absoluteBottom = rect.bottom + window.scrollY;
        maxBottom = Math.max(maxBottom, absoluteBottom);
    });
    
    // Get body dimensions
    const bodyWidth = document.body.scrollWidth;
    const bodyHeight = document.body.scrollHeight;
    
    return {
    scrollWidth: bodyWidth,
    // Use the maximum of body height or calculated maximum element bottom
    scrollHeight: Math.max(maxBottom, bodyHeight),
    browserUIWidth: window.outerWidth - window.innerWidth,
    browserUIHeight: window.outerHeight - window.innerHeight
    };
}

// Reset scroll position and return dimensions
window.scrollTo(0, 0);
return getMaxDimensions();
"""

def set_window_size_to_viewport(driver: WebDriver) -> None:
    """
    Set the browser window size to match the viewport dimensions.
    This is necessary to capture the full page screenshot correctly.

    :param driver: The Selenium WebDriver instance.
    """
    dimensions = driver.execute_script(script_viewport_size)
    scroll_width = dimensions["scrollWidth"]
    scroll_height = dimensions["scrollHeight"]
    browser_ui_height = dimensions["browserUIHeight"]
    browser_ui_width = dimensions["browserUIWidth"]
    scroll_width += browser_ui_width  # Adjust for browser UI width
    scroll_height += browser_ui_height  # Adjust for browser UI height
    driver.set_window_size(scroll_width, scroll_height)
    logger.debug(f"Browser window set to viewport size: {scroll_width}x{scroll_height} (including UI: {browser_ui_width}x{browser_ui_height})")

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def create_color_span(color: str) -> str:
    return f"<span class='color-point' style='color: {color};'>⬤</span> {color} "


def relative_luminance(color: tuple[int, int, int]) -> float:
    """
    Calculate the relative luminance of a color.
    The formula is based on the WCAG 2.0 guidelines.

    The formula is:
    L = 0.2126 * R + 0.7152 * G + 0.0722 * B
    where R, G, and B are the normalized RGB values (0-1).

    The RGB values are normalized to the range 0-1 by dividing by 255.
    The gamma correction is applied to the RGB values before calculating the luminance.
    The gamma correction is defined as:
    R = R / 12.92 if R <= 0.04045 else ((R + 0.055) / 1.055) ** 2.4
    G = G / 12.92 if G <= 0.04045 else ((G + 0.055) / 1.055) ** 2.4
    B = B / 12.92 if B <= 0.04045 else ((B + 0.055) / 1.055) ** 2.4

    The relative luminance is then calculated using the formula above.

    :param color: The color as an RGB tuple (R, G, B).
    :return: The relative luminance of the color.
    """
    r, g, b = [c / 255.0 for c in color]  # normalization to 0-1 for calculation
    r, g, b = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(l1: float, l2: float) -> float:
    """
    Calculate the contrast ratio between two luminance values.
    :param l1: luminance of the first color
    :param l2: luminance of the second color
    :return: contrast ratio
    """
    l1, l2 = max(l1, l2), min(l1, l2)
    return (l1 + 0.05) / (l2 + 0.05)

def get_embedded_file_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / filename
    return filename

def take_element_screenshot(driver: WebDriver, element: WebElement, index: int, screenshot_path: Path) -> None:
    """
    Take a screenshot of a specific WebElement and save it to the specified path.
    :param driver: Selenium WebDriver instance.
    :param element: The WebElement to take a screenshot of.
    :param index: Index of the element for log output.
    :param screenshot_path: Path where the screenshot will be saved.
    """
    logger.debug(f"[Element {index}] Take screenshot of element")
    driver.execute_script("arguments[0].scrollIntoView({ behavior: 'instant'});", element)
    element.screenshot(str(screenshot_path))
    logger.debug(f"[Element {index}] Screenshot saved to: {screenshot_path}")


def get_full_base_url(driver: WebDriver) -> str:
    parsed_url = urlparse(driver.current_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url

def call_url(driver: WebDriver, url: str) -> None:
    """
    Call a URL in the browser.
    Wait until the page is fully loaded before proceeding.
    This is done by checking the document's ready state (timeout 10 seconds).

    :param driver: Selenium WebDriver instance.
    :param url: The URL to call.
    """
    logger.debug(f"Goto URL: {url}")
    if not url.startswith("http"):
        # if the url is a relative path, append it to the base url
        base_url = get_full_base_url(driver)
        if not url.startswith("/"):
            url = "/" + url
        url = f"{base_url}{url}"
    driver.get(url)
    wait_page_loaded(driver)

def wait_page_loaded(driver: WebDriver) -> None:
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script(
            "return document.readyState === 'complete' && "
            "window.performance.getEntriesByType('resource').filter(r => r.responseEnd === 0).length === 0"
        )
    )

def filter_args_for_dataclass(cls, args_dict):
    cls_fields = {f.name for f in fields(cls)}
    return {key: value for key, value in args_dict.items() if key in cls_fields}

def trim_string_to_length(s: str, length: int) -> str:
    """
    Trim a string to a specified length, adding an ellipsis if it exceeds the length.

    :param s: The string to trim.
    :param length: The maximum length of the string.
    :return: The trimmed string.
    """
    if len(s) > length:
        return s[:length - 3] + "..."
    return s

def take_fullpage_screenshot(driver: WebDriver, screenshot_path: Path) -> None:
    """
    Take a full-page screenshot of the current page and save it to the specified path.

    :param driver: Selenium WebDriver instance.
    :param screenshot_path: Path where the full-page screenshot will be saved.
    """
    # Ensure the current window is active.
    driver.switch_to.window(driver.current_window_handle)

    #scroll to the top of the page
    driver.execute_script("window.scrollTo(0, 0);")

    # Capture screenshot from the surface (full page)
    screenshot_data = driver.execute_cdp_cmd("Page.captureScreenshot", {
        "captureBeyondViewport": True,
    })

    # Save the screenshot to the full_page_screenshot_path
    with open(screenshot_path, "wb") as file:
        file.write(base64.b64decode(screenshot_data["data"]))


def count_violations(results):
    violations_count = 0

    for result in results:
        # tab runner
        if isinstance(result, dict) and 'tabbed_elements' in result:
            violations_count += len(result.get('missed_elements', []))
        # axe runner
        elif 'violations' in result:
            for violation in result.get('violations', []):
                violations_count += len(violation.get('nodes', []))
        # contrast runner
        else:
            return len(results)

    return violations_count

def resolve_var(context: dict, text: str) -> str:
    """
    Replace variables in the text with their values from the context dictionary.
    Supports nested variables using dot-separated keys.

    :param context: Dictionary containing variable values.
    :param text: String with variables in the format ${<varname>}.
    :return: Resolved string with variables replaced.
    """
    def get_nested_value(d, keys):
        """Retrieve a nested value from a dictionary using a list of keys."""
        for key in keys:
            d = d.get(key, None)
            if d is None:
                return None
        return d

    resolved_vars = set()
    try:
        while "${" in text and "}" in text:
            start = text.index("${") + 2
            end = text.index("}", start)
            var_name = text[start:end]

            if var_name in resolved_vars:
                break

            keys = var_name.split(".")
            value = get_nested_value(context, keys)
            resolved_vars.add(var_name)
            text = text.replace(f"${{{var_name}}}", str(value) if value is not None else "")
        return text
    except Exception as e:
        logger.error(f"Error resolving variables in text: {e}")
        return text

def setting_var(context: dict, name: str, value: str | dict) -> None:
    """
    Set a variable in the context dictionary with the specified name and value.
    Supports nested variable names using dot-separated keys.

    :param context: Dictionary to store the variable.
    :param name: Name of the variable (can be nested, e.g., "user.name").
    :param value: Value to set for the variable.
    """
    keys = name.split(".")
    current = context
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value
