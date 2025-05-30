import sys
from dataclasses import fields
from urllib.parse import urlparse
from pathlib import Path
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from src.logger_setup import logger

def get_element_colors_old(element: WebElement) -> tuple:
    """
    Extract the foreground and background colors of a WebElement.

    :param element: The WebElement from which the colors should be extracted.
    :return: A tuple with foreground and background colors as RGB values.
    """
    foreground_color = element.value_of_css_property("color")
    background_color = element.value_of_css_property("background-color")

    # convert color rgba() in rgb - if transparent or a channel return None
    def parse_color(color: str) -> tuple|None:
        if color == "transparent" or "rgba(0, 0, 0, 0)" in color:
            return None
        rgba = color.replace("rgba(", "").replace("rgb(", "").replace(")", "").split(",")
        if len(rgba) == 4 and float(rgba[3].strip()) == 0:  # check alpha channel
            return None
        return tuple(map(int, rgba[:3]))

    return parse_color(foreground_color), parse_color(background_color)

from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver

def get_element_colors(driver: webdriver, element: WebElement) -> tuple:
    """
    Ermittelt Vordergrund- und Hintergrundfarben eines Elements mit JavaScript.

    :param driver: Selenium WebDriver-Instanz.
    :param element: Das WebElement, dessen Farben abgerufen werden sollen.
    :return: Ein Tupel mit Vordergrund- und Hintergrundfarben als RGB-Werte.
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

def define_get_path_script(driver: webdriver) -> None:
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


def get_xpath(driver: webdriver, element: WebElement) -> str:
    """
    Determines the full XPath of a WebElement using JavaScript.

    :param driver: Selenium WebDriver instance.
    :param element: The WebElement for which to get the XPath.
    :return: The XPath of the WebElement as a string.
    """
    return driver.execute_script("return getXPath(arguments[0]);", element)

def get_csspath(driver: webdriver, element: WebElement) -> str:
    """
    Determines the full CSS Path of a WebElement using JavaScript.

    :param driver: Selenium WebDriver instance.
    :param element: The WebElement for which to get the XPath.
    :return: The CSS Path of the WebElement as a string.
    """
    return driver.execute_script("return getCSSPath(arguments[0]);", element)

def reset_window_size(driver: webdriver, width: int = 1920, height: int = 1080) -> None:
    """
    Reset the browser window size to the default dimensions.

    :param driver: The Selenium WebDriver instance.
    :param width: The width to set the browser window to (default: 1920).
    :param height: The height to set the browser window to (default: 1080).
    """
    driver.set_window_size(width, height)
    logger.debug(f"Browser window size reset to: {width}x{height}")

# language=JS
script_viewport_size = """
const dimensions = {
    scrollWidth:  document.body.scrollWidth,
    scrollHeight: document.body.scrollHeight,
    browserUIWidth: window.outerWidth - window.innerWidth,
    browserUIHeight: window.outerHeight - window.innerHeight
};
window.scrollTo(0, 0);
return dimensions;
"""

def set_window_size_to_viewport(driver: webdriver) -> None:
    """
    Set the browser window size to match the viewport dimensions.
    This is necessary to capture the full page screenshot correctly.

    :param driver: The Selenium WebDriver instance.
    """
    dimensions = driver.execute_script(script_viewport_size)
    scrollWidth = dimensions["scrollWidth"]
    scrollHeight = dimensions["scrollHeight"]
    browser_ui_height = dimensions["browserUIHeight"]
    browser_ui_width = dimensions["browserUIWidth"]
    scrollWidth += browser_ui_width  # Adjust for browser UI width
    scrollHeight += browser_ui_height  # Adjust for browser UI height
    driver.set_window_size(scrollWidth, scrollHeight)
    logger.debug(f"Browser window set to viewport size: {scrollWidth}x{scrollHeight} (including UI: {browser_ui_width}x{browser_ui_height})")

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
    r, g, b = [c / 255.0 for c in color]  # narmalization to 0-1 for calculation
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

def take_element_Screenshot(driver: webdriver, element: WebElement, index: int, screenshot_path: Path) -> None:
    """
    Take a screenshot of a specific WebElement and save it to the specified path.
    :param driver: Selenium WebDriver instance.
    :param element: The WebElement to take a screenshot of.
    :param index: Index of the element for log output.
    :param screenshot_path: Path where the screenshot will be saved.
    """
    logger.debug(f"[Element {index}] Take screenshot of element")
    driver.execute_script("arguments[0].scrollIntoView({ behavior: 'instant', block: 'center' });", element)
    element.screenshot(str(screenshot_path))
    logger.debug(f"[Element {index}] Screenshot saved to: {screenshot_path}")


def get_full_base_url(driver: webdriver) -> str:
    parsed_url = urlparse(driver.current_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url

def call_url(driver: webdriver, url: str) -> None:
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

def wait_page_loaded(driver: webdriver) -> None:
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
