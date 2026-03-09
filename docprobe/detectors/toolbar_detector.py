CANDIDATE_SELECTORS = [
    "aside",
    "nav",
    "[role='navigation']",
    "[class*='sidebar']",
    "[class*='SideBar']",
    "[class*='menu']",
    "[class*='toc']",
    "[class*='drawer']",
    "[class*='docs'] nav",
    "[class*='theme-doc-sidebar']",
]


def _safe_count(locator, subselector: str) -> int:
    try:
        return locator.locator(subselector).count()
    except Exception:
        return 0


def _safe_text(locator) -> str:
    try:
        return locator.inner_text(timeout=2000).strip()
    except Exception:
        return ""


def _score_toolbar(locator):
    score = 0
    text = _safe_text(locator)
    links = _safe_count(locator, "a")
    buttons = _safe_count(locator, "button")

    if links >= 5:
        score += 3
    if links >= 10:
        score += 2
    if buttons >= 1:
        score += 1
    if len(text) >= 50:
        score += 1

    lower = text.lower()
    docs_words = [
        "getting started",
        "installation",
        "guide",
        "guides",
        "release notes",
        "security",
        "developers",
        "faq",
        "administration",
        "overview",
        "reference",
        "upgrade",
    ]
    matches = sum(1 for word in docs_words if word in lower)
    score += min(matches, 4)

    return {
        "score": score,
        "links": links,
        "buttons": buttons,
        "text_len": len(text),
        "text_preview": text[:200],
    }


def detect_toolbar(page, logger):
    best = None

    for selector in CANDIDATE_SELECTORS:
        try:
            count = page.locator(selector).count()
        except Exception:
            continue

        logger.debug("Toolbar selector '%s' matched %d elements", selector, count)

        for i in range(count):
            try:
                loc = page.locator(selector).nth(i)
                if not loc.is_visible(timeout=1000):
                    continue

                result = _score_toolbar(loc)
                candidate = {
                    "detected": result["score"] >= 5,
                    "selector": selector,
                    "index": i,
                    "score": result["score"],
                    "links": result["links"],
                    "buttons": result["buttons"],
                    "text_len": result["text_len"],
                    "text_preview": result["text_preview"],
                }

                if best is None or candidate["score"] > best["score"]:
                    best = candidate
            except Exception:
                continue

    if best is None:
        return {
            "detected": False,
            "selector": "",
            "index": -1,
            "score": 0,
            "links": 0,
            "buttons": 0,
            "text_len": 0,
            "text_preview": "",
        }

    return best
