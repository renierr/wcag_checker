import mistune

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from src.config import Config
from src.utils import create_color_span, get_embedded_file_path
from src.logger_setup import logger

def join_color_span(colors):
    """
    Join the color spans into a single string.

    :param colors: List of colors to join.
    :return: Joined color span string.
    """
    return " ".join(create_color_span(color) for color in colors)

def count_violations(results):
    violations_count = 0
    for result in results:
        if 'violations' in result:
            for violation in result.get('violations', []):
                violations_count += len(violation.get('nodes', []))
        else:
            return len(results)  # Contrast-Mode
    return violations_count  # Axe-Mode

def build_markdown(config: Config, json_data: dict) -> str:
    """
    Build a markdown report from the given data.

    :param config: The configuration object.
    :param json_data: JSON data to generate the markdown from.
    :return: Markdown report as string.
    """

    env = Environment(loader=FileSystemLoader(get_embedded_file_path(Path("src") / "templates")))
    env.filters['join_color_span'] = join_color_span
    env.filters['create_color_span'] = create_color_span
    env.filters['count_violations'] = count_violations

    template_name = "markdown_report.md"
    md = (env.get_template(template_name)
          .render(config=config, json_data=json_data, output=config.output))
    return md


def generate_markdown_report(config: Config, json_data: dict, markdown_data: str = None) -> None:
    """
    Generate a markdown report from the given data.

    :param config: The configuration object.
    :param json_data: Json data to generate the markdown from.
    :param markdown_data: Optional markdown data to use instead of json_data. (pre build markdown)
    :return: None
    """
    if markdown_data is None:
        report = build_markdown(config, json_data)
    else:
        report = markdown_data

    results_file = Path(config.output) /  f"wcag_results.md"
    with results_file.open("w", encoding="utf-8") as markdown_file:
        markdown_file.write(report)

def generate_html_report(config: Config, json_data: dict, markdown_data: str = None) -> None:
    """
    Generate a HTML report from the given data.

    :param config: The configuration object.
    :param json_data: Json data to generate the HTML from.
    :param markdown_data: Optional markdown data to use instead of json_data. (pre build markdown)
    :return: None
    """
    if markdown_data is None:
        report = build_markdown(config, json_data)
    else:
        report = markdown_data

    logger.debug("Generating HTML from markdown")
    html_content = mistune.html(report)

    logger.debug("Generating HTML report from template direct to file")
    html_file_path = Path(config.output) / f"wcag_results.html"
    with html_file_path.open("w", encoding="utf-8") as html_file:
        env = Environment(loader=FileSystemLoader(get_embedded_file_path(Path("src") / "templates")))
        template = env.get_template("html_report.html")
        rendered_content = template.render(html_content=html_content, timestamp=json_data.get('timestamp'))
        html_file.write(rendered_content)

