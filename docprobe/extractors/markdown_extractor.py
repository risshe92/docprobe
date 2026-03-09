from markdownify import markdownify as md

from docprobe.extractors.html_extractor import extract_html
from docprobe.extractors.markdown_cleanup import clean_markdown


def extract_markdown(page, content_info, logger):
    html_result = extract_html(page, content_info, logger)

    html = html_result["content"]
    markdown = ""

    if html:
        markdown = md(html, heading_style="ATX")

    markdown = clean_markdown(markdown)

    logger.debug("Markdown extraction length: %d", len(markdown))

    return {
        "method": "markdown",
        "success": bool(markdown),
        "title": html_result["title"],
        "content": markdown,
        "content_length": len(markdown),
    }
