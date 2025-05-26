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
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: auto;
            padding: 20px;
            max-width: 1200px;
            color: #333;
            background-color: #f9f9f9;
        }
        table {
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
        }
        th {
            background-color: #f4f4f4;
            text-align: left;
        }
        img {
            max-width: 100%;
            height: auto;
            border: 1px dashed #a1a1a1;
        }
        img[alt^=\"Element\"] {
            cursor: pointer;
            transition: transform 0.3s ease;
        }
        img.large {
            transform: scale(4);
            transform-origin: left;
        }
        .color-point {
            display: inline-block;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        }
        .toc {
            background-color: #f4f4f4;
            border: 1px solid #ddd;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .toc h2 {
            font-size: 1.5em;
            margin-bottom: 10px;
            color: #333;
        }
        .toc ul {
            list-style: none;
            padding-left: 0;
        }
        .toc ul li {
            margin: 5px 0;
        }
        .toc ul li a {
            text-decoration: none;
            color: #007bff;
            font-size: 1em;
            transition: color 0.3s ease;
        }
        .toc ul li a:hover {
            color: #0056b3;
        }
        .toc ul li ul {
            margin-left: 20px;
            border-left: 2px solid #ddd;
            padding-left: 10px;
        }
        blockquote {
          font-style: italic;
          color: #555;
          border-left: 4px solid #ccc;
          margin: 1.5em 10px;
          padding: 0.5em 10px;
          background-color: #f9f9f9;
        }

        blockquote p {
          margin: 0;
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

