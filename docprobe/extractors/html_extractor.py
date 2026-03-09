def extract_html(page, content_info, logger):
    selector = content_info["selector"]
    index = content_info["index"]

    locator = page.locator(selector).nth(index)

    try:
        title = page.title().strip()
    except Exception:
        title = ""

    try:
        html = locator.inner_html(timeout=5000)
    except Exception:
        html = ""

    logger.debug("HTML extraction length: %d", len(html))

    return {
        "method": "html",
        "success": bool(html),
        "title": title,
        "content": html,
        "content_length": len(html),
    }
