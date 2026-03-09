def extract_text(page, content_info, logger):
    selector = content_info["selector"]
    index = content_info["index"]

    locator = page.locator(selector).nth(index)

    try:
        title = page.title().strip()
    except Exception:
        title = ""

    try:
        content = locator.inner_text(timeout=5000).strip()
    except Exception:
        content = ""

    logger.debug("Text extraction length: %d", len(content))

    return {
        "method": "text",
        "success": bool(content),
        "title": title,
        "content": content,
        "content_length": len(content),
    }
