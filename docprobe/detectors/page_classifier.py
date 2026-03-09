def _safe_count(page, selector: str) -> int:
    try:
        return page.locator(selector).count()
    except Exception:
        return 0


def _safe_text(page, selector: str) -> str:
    try:
        loc = page.locator(selector).first
        if loc.count() > 0:
            return (loc.inner_text(timeout=3000) or "").strip()
    except Exception:
        pass
    return ""


def classify_page(page, content_info: dict, logger):
    selector = content_info.get("selector", "body")
    index = content_info.get("index", 0)

    try:
        content = page.locator(selector).nth(index)
    except Exception:
        content = page.locator("body")

    try:
        content_text = (content.inner_text(timeout=3000) or "").strip()
    except Exception:
        content_text = ""

    heading_count = 0
    paragraph_count = 0
    code_block_count = 0
    image_count = 0
    canvas_count = 0
    iframe_count = 0
    table_count = 0
    link_count = 0
    pre_count = 0

    for sel, name in [
        ("h1, h2, h3, h4, h5, h6", "heading_count"),
        ("p", "paragraph_count"),
        ("code", "code_block_count"),
        ("img", "image_count"),
        ("canvas", "canvas_count"),
        ("iframe", "iframe_count"),
        ("table", "table_count"),
        ("a", "link_count"),
        ("pre", "pre_count"),
    ]:
        try:
            count = content.locator(sel).count()
        except Exception:
            count = 0

        if name == "heading_count":
            heading_count = count
        elif name == "paragraph_count":
            paragraph_count = count
        elif name == "code_block_count":
            code_block_count = count
        elif name == "image_count":
            image_count = count
        elif name == "canvas_count":
            canvas_count = count
        elif name == "iframe_count":
            iframe_count = count
        elif name == "table_count":
            table_count = count
        elif name == "link_count":
            link_count = count
        elif name == "pre_count":
            pre_count = count

    text_length = len(content_text)

    page_html_lower = ""
    try:
        page_html_lower = (page.content() or "").lower()
    except Exception:
        pass

    looks_like_pdf_viewer = any(
        hint in page_html_lower
        for hint in [
            "pdf.js",
            "pdf-viewer",
            "react-pdf",
            "viewercontainer",
            "pdfviewer",
        ]
    )

    looks_visual_heavy = (canvas_count > 0 or iframe_count > 0) and text_length < 500
    looks_structured_docs = (
        heading_count >= 2
        or paragraph_count >= 3
        or pre_count >= 1
        or table_count >= 1
    )

    recommended_mode = "text"

    if looks_like_pdf_viewer:
        recommended_mode = "ocr"
    elif looks_visual_heavy:
        recommended_mode = "ocr"
    elif looks_structured_docs and text_length >= 500:
        recommended_mode = "markdown"
    elif text_length >= 200:
        recommended_mode = "text"
    else:
        recommended_mode = "ocr"

    profile = {
        "text_length": text_length,
        "heading_count": heading_count,
        "paragraph_count": paragraph_count,
        "code_block_count": code_block_count,
        "image_count": image_count,
        "canvas_count": canvas_count,
        "iframe_count": iframe_count,
        "table_count": table_count,
        "link_count": link_count,
        "pre_count": pre_count,
        "looks_like_pdf_viewer": looks_like_pdf_viewer,
        "looks_visual_heavy": looks_visual_heavy,
        "looks_structured_docs": looks_structured_docs,
        "recommended_mode": recommended_mode,
    }

    logger.debug("Page profile: %s", profile)
    return profile
