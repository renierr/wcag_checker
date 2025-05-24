import colorsys
import numpy as np

from src.config import Config
from src.utils import hex_to_rgb, rgb_to_hex, relative_luminance, contrast_ratio


def suggest_wcag_colors(config: Config, result_dict: dict,
                        color1: tuple[int, int, int], color2: tuple[int, int, int]) -> list:
    """
    Suggests WCAG-compliant color combinations that are close to the original colors.

    :param: config: Configuration object containing settings.
    :param: result_dict: Dictionary containing the results to add.
    :param: color1: First color in RGB format (tuple of 3 integers)
    :param: color2: Second color in RGB format (tuple of 3 integers)
    :return: List of WCAG-compliant color combinations (HEX values) with contrast ratios.
    """
    # Suggest WCAG-compliant colors
    if not config.alternate_color_suggestion:
        suggestions = _suggest_wcag_colors(color1, color2)
    else:
        suggestions = _alternate_suggest_wcag_colors(color1, color2, config.contrast_threshold)

    # Add contrast ratios to suggestions
    suggestions_with_contrast = [
        {
            "colors": (pair[0], pair[1]),
            "contrast": pair[2]
        }
        for pair in suggestions
    ]

    # Add suggestions to the result dictionary
    result_dict["color_suggestions"] = suggestions_with_contrast

    return suggestions_with_contrast


def _suggest_wcag_colors(color1_rgb: tuple[int, int, int], color2_rgb: tuple[int, int, int],
                         min_contrast: float = 4.5) -> list[tuple[str, str, float]]:
    """
    Suggests WCAG-compliant color combinations that are close to the original colors.
    Uses the colorsys library for color conversions and contrast calculations.
    The color is converted to HLS (Hue, Lightness, Saturation) and brightness is adjusted
    in 5% steps (±40%) to find colors that meet the contrast ratio requirement.
    It returns the 3 best suggestions based on minimal deviation from the original colors or less if none could be found.

    :param: color1: first color in rgb format (tuple of 3 integers)
    :param: color2: second color in rgb format (tuple of 3 integers)
    :param: min_contrast: Minimum contrast ratio (default: 4.5)
    :return: List of tuples with WCAG-compliant color combinations (HEX values)
    """

    h1, l1, s1 = colorsys.rgb_to_hls(*(c / 255.0 for c in color1_rgb))
    h2, l2, s2 = colorsys.rgb_to_hls(*(c / 255.0 for c in color2_rgb))

    suggestions = []
    seen_suggestions = set()

    # Try brightness adjustments (±40% in 5% steps)
    for l1_adj in range(-40, 41, 5):
        for l2_adj in range(-40, 41, 5):
            # New brightness values (in percent)
            new_l1 = max(0, min(1, l1 + l1_adj / 100))
            new_l2 = max(0, min(1, l2 + l2_adj / 100))

            # Create new colors with adjusted brightness
            new_color1_rgb = tuple(int(c * 255) for c in colorsys.hls_to_rgb(h1, new_l1, s1))
            new_color2_rgb = tuple(int(c * 255) for c in colorsys.hls_to_rgb(h2, new_l2, s2))
            ratio = contrast_ratio(
                relative_luminance(new_color1_rgb),
                relative_luminance(new_color2_rgb)
            )

            if ratio >= min_contrast:
                suggestion = (rgb_to_hex(new_color1_rgb), rgb_to_hex(new_color2_rgb), ratio)
                if suggestion[:2] not in seen_suggestions:  # Check for duplicates
                    seen_suggestions.add(suggestion[:2])  # Add unique color pair
                    suggestions.append(suggestion)

    # Sort by minimal deviation (based on luminance difference)
    suggestions.sort(key=lambda x: (
            abs(relative_luminance(hex_to_rgb(x[0])) - relative_luminance(color1_rgb)) +
            abs(relative_luminance(hex_to_rgb(x[1])) - relative_luminance(color2_rgb))
    ))

    # Return the three best suggestions (or fewer if not enough are found)
    return suggestions[:3]


def _alternate_suggest_wcag_colors(color1_rgb: tuple[int, int, int], color2_rgb: tuple[int, int, int],
                                   min_contrast: float = 4.5, max_iterations: int = 1000) -> list[tuple[str, str, float]]:
    """
    Suggests WCAG-compliant color combinations that are close to the original colors.

    :param color1_rgb: first color in rgb format (tuple of 3 integers)
    :param color2_rgb: second color in rgb format (tuple of 3 integers)
    :param min_contrast: Minimum contrast ratio (default: 4.5)
    :param max_iterations: Maximum number of iterations for the optimization (default: 1000)
    :return: List of tuples with WCAG-compliant color combinations (HEX values)
    """
    suggestions = []
    seen_suggestions = set()
    orig_rgb1 = np.array(color1_rgb, dtype=float)
    orig_rgb2 = np.array(color2_rgb, dtype=float)

    def color_distance(rgb1, rgb2) -> float:
        """Calculates the Euclidean distance between two colors in the RGB space."""
        return np.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))

    def objective_function(rgb1: np.ndarray, rgb2: np.ndarray) -> float:
        """Objective function: Minimize color deviation, maintain contrast."""
        c1 = tuple(np.clip(rgb1, 0, 255).astype(int))
        c2 = tuple(np.clip(rgb2, 0, 255).astype(int))
        contrast = contrast_ratio(relative_luminance(c1), relative_luminance(c2))
        dist = color_distance(c1, color1_rgb) + color_distance(c2, color2_rgb)
        penalty = 1000 * max(0, min_contrast - contrast)  # penalty for not meeting contrast
        return dist + penalty

    current_rgb1, current_rgb2 = orig_rgb1.copy(), orig_rgb2.copy()
    best_score = float('inf')
    best_colors = None

    # Systematic search with random perturbations.
    for _ in range(max_iterations):
        # random perturbation
        perturbation1 = np.random.uniform(-20, 20, 3)
        perturbation2 = np.random.uniform(-20, 20, 3)
        new_rgb1 = np.clip(current_rgb1 + perturbation1, 0, 255)
        new_rgb2 = np.clip(current_rgb2 + perturbation2, 0, 255)

        # calc score
        score = objective_function(new_rgb1, new_rgb2)
        rgb1 = tuple(new_rgb1.astype(int))
        rgb2 = tuple(new_rgb2.astype(int))

        # check if the contrast ratio meets the minimum
        ratio = contrast_ratio(relative_luminance(rgb1), relative_luminance(rgb2))
        if ratio >= min_contrast:
            suggestion = (rgb_to_hex(rgb1), rgb_to_hex(rgb2), ratio)
            if (rgb1, rgb2) not in seen_suggestions and score < best_score:
                seen_suggestions.add((rgb1, rgb2))
                suggestions.append(suggestion)
                best_score = score
                best_colors = (rgb1, rgb2)

        # accept new colors with a probability of 10% even if the score is worse
        if score < objective_function(current_rgb1, current_rgb2) or np.random.random() < 0.1:
            current_rgb1, current_rgb2 = new_rgb1, new_rgb2

    # sort after distance to original colors
    suggestions.sort(key=lambda x: color_distance(hex_to_rgb(x[0]), color1_rgb) + color_distance(hex_to_rgb(x[1]), color2_rgb))
    return suggestions[:3]
