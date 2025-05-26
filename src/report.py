import mistune

from pathlib import Path
from jinja2 import Template, Environment, FileSystemLoader
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
            violations_count += len(result.get('violations', []))
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

# language=HTML
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WCAG Report {{timestamp}}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, Arial, sans-serif;
            line-height: 1.6;
            margin: auto;
            padding: 20px;
            max-width: 1200px;
            color: #333;
            background-color: #f4f7fa;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #007bff;
            color: #fff;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        tr:hover {
            background-color: #f1f1f1;
        }
        img {
            max-width: 100%;
            height: auto;
            border: 1px solid #ccc;
            border-radius: 5px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        img[alt^=\"Element\"] {
            cursor: pointer;
        }
        img.large {
            transform: scale(4);
            transform-origin: center;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        .color-point {
            display: inline-block;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
            border-radius: 50%;
            width: 16px;
            height: 16px;
        }
        blockquote {
            font-style: italic;
            color: #555;
            border-left: 4px solid #007bff;
            margin: 1.5em 10px;
            padding: 0.5em 10px;
            background-color: #f9f9f9;
        }
        blockquote p {
          margin: 0;
        }
        li {
            font-size: 14px;
        }
        li > p {
            margin: 0;
        }
        a {
            color: #007bff;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
{{html_content}}
<script>
const images = document.querySelectorAll('img[alt^=\"Element\"');
images.forEach((image) => {
    image.addEventListener('click', () => {
        image.classList.toggle('large');
    });
});
</script>
</body>
</html>
"""


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
        Template(html_template).stream(
            html_content=html_content,
            timestamp=json_data.get('timestamp')
        ).dump(html_file)

