from urllib.parse import urljoin, urlparse


def _safe_text(locator) -> str:
    try:
        return (locator.inner_text(timeout=1000) or "").strip()
    except Exception:
        return ""


def expand_toolbar(page, toolbar_info: dict, logger, rounds: int = 8):
    """
    Expand collapsible sections inside the detected toolbar.
    Repeats multiple rounds because expanding one section may reveal more controls.
    """
    if not toolbar_info.get("detected"):
        return 0

    selector = toolbar_info["selector"]
    index = toolbar_info["index"]

    total_clicks = 0

    try:
        toolbar = page.locator(selector).nth(index)
    except Exception as exc:
        logger.error("Failed to locate toolbar for expansion: %s", exc)
        return 0

    for round_no in range(rounds):
        round_clicks = 0

        candidates = [
            "button",
            "[role='button']",
            "[aria-expanded='false']",
            "summary",
        ]

        for candidate_selector in candidates:
            try:
                items = toolbar.locator(candidate_selector)
                count = items.count()
            except Exception:
                continue

            for i in range(count):
                try:
                    item = items.nth(i)

                    if not item.is_visible(timeout=500):
                        continue

                    aria_expanded = item.get_attribute("aria-expanded")
                    text = _safe_text(item).lower()

                    # Prefer explicitly collapsed controls
                    should_click = False
                    if aria_expanded == "false":
                        should_click = True

                    # Also click likely expandable nav labels
                    keywords = [
                        "installation",
                        "upgrade",
                        "administration",
                        "security",
                        "how-to",
                        "developers",
                        "release notes",
                        "experimental",
                        "persistent data",
                        "config import",
                        "windows",
                        "autoscale",
                        "troubleshooting",
                        "compute",
                        "user guide",
                    ]
                    if any(k in text for k in keywords):
                        should_click = True

                    if not should_click:
                        continue

                    item.click(timeout=1000)
                    page.wait_for_timeout(200)
                    round_clicks += 1
                    total_clicks += 1

                except Exception:
                    continue

        logger.debug("Toolbar expand round %d clicked %d items", round_no + 1, round_clicks)

        if round_clicks == 0:
            break

    logger.info("Expanded toolbar with %d click(s)", total_clicks)
    return total_clicks


def enumerate_toolbar_links(page, base_url: str, toolbar_info: dict, logger):
    """
    Expand toolbar first, then extract links from the detected toolbar element,
    normalize them, keep same-host URLs, and preserve discovery order.
    """
    if not toolbar_info.get("detected"):
        return []

    expand_toolbar(page, toolbar_info, logger)

    selector = toolbar_info["selector"]
    index = toolbar_info["index"]

    try:
        toolbar = page.locator(selector).nth(index)
        anchors = toolbar.locator("a")
        count = anchors.count()
    except Exception as exc:
        logger.error("Failed to enumerate toolbar links: %s", exc)
        return []

    logger.debug("Enumerating %d anchors from toolbar", count)

    base_parsed = urlparse(base_url)
    base_host = base_parsed.netloc

    results = []
    seen = set()

    for i in range(count):
        try:
            a = anchors.nth(i)
            href = (a.get_attribute("href") or "").strip()
            text = (a.inner_text(timeout=1000) or "").strip()

            if not href:
                continue
            if href.startswith("#"):
                continue
            if href.startswith("javascript:"):
                continue
            if href.startswith("mailto:"):
                continue
            if href.startswith("tel:"):
                continue

            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)

            if parsed.netloc != base_host:
                continue

            normalized_url = parsed._replace(fragment="").geturl()

            if normalized_url in seen:
                continue
            seen.add(normalized_url)

            results.append(
                {
                    "text": text,
                    "href": href,
                    "url": normalized_url,
                }
            )
        except Exception:
            continue

    logger.info("Discovered %d unique toolbar links", len(results))
    return results
