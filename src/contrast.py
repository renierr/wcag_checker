import logging
import numpy as np
import cv2
from numpy import ndarray
from selenium.webdriver.remote.webdriver import WebDriver
from sklearn.cluster import KMeans
from pathlib import Path

from PIL import Image
from selenium.webdriver.remote.webelement import WebElement

from src.logger_setup import logger
from src.recommend_colors import suggest_wcag_colors
from src.utils import get_element_colors, log_colored_char, rgb_to_hex, contrast_ratio, relative_luminance, \
    take_element_screenshot
from src.config import Config, ColorSource, ReportLevel, ProcessingConfig


def get_dominant_colors_from_element(driver, element: WebElement) -> list[tuple[int, int, int]]:
    """
    Get the dominant colors of a WebElement.
    This function uses the WebElement's CSS properties to get the foreground and background colors.
    The function returns the foreground and background colors as RGB values.

    :param element: The WebElement to get the colors from.
    :return: A tuple with the foreground and background colors as RGB values.
    """
    fg_color, bg_color = get_element_colors(driver, element)
    if fg_color is None or bg_color is None:
        return []
    return [fg_color, bg_color]

def get_dominant_colors_from_image(image: ndarray, mask: ndarray=None, n_colors=2) -> list[tuple[int, int, int]]:
    """
    Get the dominant colors in an image using K-Means clustering.
    This function uses K-Means clustering to find the most common colors in an image.
    The image is first converted to an array, and then the K-Means algorithm is applied to find the dominant colors.
    The function returns the dominant colors sorted by frequency.
    The function also applies a mask to the image to only consider pixels where the mask is 255.

    The mask is a binary image where the pixels to be considered are set to 255 and the rest are set to 0.
    If no mask is provided, the entire image is considered.

    :param image: The input image as a NumPy array.
    :param mask: The mask to apply to the image. Only pixels where the mask is 255 are considered.
    :param n_colors: The number of dominant colors to find.
    :return: A list of the dominant colors in the image.
    """
    # convert image to array, only if mask = 255
    pixels = image[mask == 255].reshape(-1, 3) if mask is not None else image.reshape(-1, 3)

    if len(pixels) == 0:
        raise ValueError("No valid Pixels available to find dominant colors.")

    # K-Means-Clustering - use additional of n_colors to account for color anti aliasing, we choose the top 2
    kmeans = KMeans(n_clusters=n_colors+1, random_state=0).fit(pixels)
    dominant_colors = kmeans.cluster_centers_.astype(int)

    # sort dominant colors by frequency
    labels = kmeans.labels_
    color_counts = np.bincount(labels)
    sorted_indices = np.argsort(color_counts)[::-1]
    dominant_colors = dominant_colors[sorted_indices]

    return [tuple(color) for color in dominant_colors]

def apply_antialias(image_path):
    """
    Apply anti-aliasing to an image_path.
    This function uses OpenCV to apply anti-aliasing to an image.

    :param image_path: The path to the image file.
    :return: The processed image and the mask, mask is always None.
    """
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB

    # Apply edge-preserving smoothing (bilateral filter)
    # Reduces anti-aliasing while preserving edges
    smoothed_img = cv2.bilateralFilter(img_rgb, d=15, sigmaColor=75, sigmaSpace=75)

    if logger.isEnabledFor(logging.DEBUG):
        Image.fromarray(smoothed_img).save(f"{image_path}.antialias.png")

    return smoothed_img, None

def apply_canny_edge_detection(image_path: str, low_threshold: int = 50, high_threshold: int = 150, blur_size: int = 5):
    """
    Apply Canny edge detection to an image_path.
    This function uses the Canny edge detection algorithm to find the edges in an image.
    The function first applies a Gaussian blur to the image to reduce noise, and then
    applies the Canny edge detection algorithm to find the edges.
    The function returns the edges and the non-edges as a binary mask.
    The non-edges are the areas of the image where the Canny edge detection algorithm did not find any edges.
    The function also inverts the mask so that the non-edges are set to 255 and the edges are set to 0.
    The function also saves the processed image with edges and non-edges for debugging purposes.

    :param image_path: the path to the image file.
    :param low_threshold: low threshold for Canny edge detection.
    :param high_threshold: high threshold for Canny edge detection.
    :param blur_size: size of the Gaussian blur kernel.
    :return: the processed image and the mask.
    """
    # load image (BGR-Format)
    img = cv2.imread(image_path)
    # convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Gauss Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)
    # Canny-Edge detection
    edges = cv2.Canny(blurred, low_threshold, high_threshold)
    # edge invert (not edge = 255, edge = 0)
    non_edges_mask = cv2.bitwise_not(edges)

    # original image in RGB format
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # save intermediate images for debugging
    if logger.isEnabledFor(logging.DEBUG):
        cv2.imwrite(f"{image_path}.edges.png", edges)
        cv2.imwrite(f"{image_path}.edges_invert.png", non_edges_mask)
        result = np.zeros_like(img_rgb)
        result[non_edges_mask == 255] = img_rgb[non_edges_mask == 255]
        Image.fromarray(result).save(f"{image_path}.non_edges_image.png")

    return img_rgb, non_edges_mask

def check_contrast(driver: WebDriver, config: ProcessingConfig, index: int, element: WebElement, image_path: Path, results: list[dict],
                   element_path: str = None, low_threshold=50, high_threshold=150) -> bool:
    """
    Check the contrast ratio of the element.
    This function uses Canny edge detection to find the edges in the image and then
    applies K-Means clustering to find the most common colors in the non-edge areas of the image.
    The function then calculates the contrast ratio between the two most common colors
    and checks if it meets the WCAG requirements.
    The function also logs the result and appends it to the results list.

    :param driver: The Selenium WebDriver instance.
    :param config: configuration for the contrast checks
    :param index: current index of the element
    :param element: The WebElement to check.
    :param image_path: The path to the screenshot image.
    :param results: The list to store results.
    :param element_path: The XPath of the element.
    :param low_threshold: threshold for Canny-edge detection
    :param high_threshold: threshold for Canny-edge detection
    :return: True if the contrast ratio meets the threshold, False otherwise.
    """

    target_ratio = config.contrast_threshold
    invalid_only = config.report_level == ReportLevel.INVALID
    logger.debug(f"[Element {index}] Check contrast ratio for element path: {element_path}")

    # extract dominant colors
    if config.color_source == ColorSource.IMAGE:
        take_element_screenshot(driver, element, index, image_path)
        logger.debug(f"[Element {index}] Extracting colors from image: {image_path}")
        if config.use_canny_edge_detection:
            processed_image, mask = apply_canny_edge_detection(image_path, low_threshold, high_threshold)
        elif config.use_antialias:
            processed_image, mask = apply_antialias(image_path)
        else:
            processed_image = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)
            mask = None
        colors = get_dominant_colors_from_image(processed_image, mask, n_colors=2)
    else:
        logger.debug(f"[Element {index}] Extracting colors from element")
        colors = get_dominant_colors_from_element(driver, element)

    if len(colors) < 2:
        logger.info("[Element {index}] Not enough colors to determine contrast ratio.")
        results.append({
            "element_index": index,
            "element_path": element_path,
            "element_text": element.text,
            "screenshot": image_path.as_posix(),
            "error": "Not enough colors to determine contrast ratio."
        })
        return False

    # take/place first 2 in reversed order, because the prominent color is most likely the background color (only image source)
    if config.color_source == ColorSource.IMAGE:
        colors[:2] = colors[:2][::-1]
    color1, color2 = colors[0], colors[1]

    # calc contrast ratio
    ratio = contrast_ratio(relative_luminance(color1), relative_luminance(color2))
    meet_wcag = bool(ratio >= target_ratio)
    result = {
        "element_index": index,
        "element_path": element_path,
        "element_text": element.text,
        "screenshot": image_path.as_posix(),
        "colors": [rgb_to_hex(color) for color in colors],
        "contrast_ratio": ratio,
        "meets_wcag": meet_wcag
    }

    # take screenshot of element if needed
    if config.color_source == ColorSource.ELEMENT and (not invalid_only or not meet_wcag):
        take_element_screenshot(driver, element, index, image_path)

    if not meet_wcag:
        suggest_wcag_colors(config, result, color1, color2)
    if not invalid_only or (invalid_only and not meet_wcag):
        results.append(result)
    color_log_message = log_colored_char(color1, color2)
    if meet_wcag:
        logger.debug(f"[Element {index}] Contrast Ratio: {ratio:.2f} - The contrast ratio meets the WCAG requirements. {color_log_message}")
        return True
    else:
        logger.warning(f"[Element {index}] Image {image_path}; Contrast Ratio: {ratio:.2f} - The contrast ratio is too low. {color_log_message}")
        return False

