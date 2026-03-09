PLATFORM_CONTENT_SELECTORS = {
    "docusaurus": [
        "main article",
        ".theme-doc-markdown",
        "main",
        "article",
    ],
    "mkdocs": [
        ".md-content",
        "main",
        "article",
    ],
    "readthedocs": [
        ".rst-content",
        ".wy-nav-content",
        "main",
        "article",
    ],
    "gitbook": [
        ".page-inner",
        "main",
        "article",
    ],
    "pdf_viewer": [
        "main",
        "article",
        "[role='main']",
        "body",
    ],
    "custom_spa": [
        "main",
        "article",
        "[role='main']",
        ".theme-doc-markdown",
        ".markdown",
        ".content",
        ".docItemContainer",
        ".docs-content",
        ".md-content",
        ".rst-content",
        ".wy-nav-content",
    ],
}


def _safe_inner_text(locator) -> str:
    try:
        return (locator.inner_text(timeout=3000) or "").strip()
    except Exception:
        return ""


def _safe_count(locator, selector: str) -> int:
    try:
        return locator.locator(selector).count()
    except Exception:
        return 0


def _score_content(locator):
    text = _safe_inner_text(locator)
    paragraphs = _safe_count(locator, "p")
    headings = (
        _safe_count(locator, "h1")
        + _safe_count(locator, "h2")
        + _safe_count(locator, "h3")
    )
    code_blocks = _safe_count(locator, "pre") + _safe_count(locator, "code")
    images = _safe_count(locator, "img")
    canvases = _safe_count(locator, "canvas")

    score = 0
    if len(text) >= 200:
        score += 3
    if len(text) >= 1000:
        score += 2
    if paragraphs >= 3:
        score += 2
    if headings >= 1:
        score += 2
    if code_blocks >= 1:
        score += 1
    if images >= 1 or canvases >= 1:
        score += 1

    return {
        "score": score,
        "text_len": len(text),
        "paragraphs": paragraphs,
        "headings": headings,
        "code_blocks": code_blocks,
        "images": images,
        "canvases": canvases,
        "text_preview": text[:300],
    }


def detect_content(page, logger, site_type="custom_spa"):
    selectors = PLATFORM_CONTENT_SELECTORS.get(
        site_type,
        PLATFORM_CONTENT_SELECTORS["custom_spa"],
    )

    best = None

    for selector in selectors:
        try:
            count = page.locator(selector).count()
        except Exception:
            continue

        logger.debug(
            "Content selector '%s' matched %d elements for site_type=%s",
            selector,
            count,
            site_type,
        )

        for i in range(count):
            try:
                loc = page.locator(selector).nth(i)
                if not loc.is_visible(timeout=1000):
                    continue

                result = _score_content(loc)
                candidate = {
                    "detected": result["score"] >= 4,
                    "selector": selector,
                    "index": i,
                    "score": result["score"],
                    "text_len": result["text_len"],
                    "paragraphs": result["paragraphs"],
                    "headings": result["headings"],
                    "code_blocks": result["code_blocks"],
                    "images": result["images"],
                    "canvases": result["canvases"],
                    "text_preview": result["text_preview"],
                    "site_type": site_type,
                }

                if best is None or candidate["score"] > best["score"]:
                    best = candidate
            except Exception:
                continue

    if best is None:
        body_text = page.locator("body").inner_text().strip()
        return {
            "detected": True,
            "selector": "body",
            "index": 0,
            "score": 1,
            "text_len": len(body_text),
            "paragraphs": 0,
            "headings": 0,
            "code_blocks": 0,
            "images": 0,
            "canvases": 0,
            "text_preview": body_text[:300],
            "site_type": site_type,
        }

    return best
