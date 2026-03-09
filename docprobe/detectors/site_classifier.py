def classify_site(page, logger):
    html = ""
    try:
        html = (page.content() or "").lower()
    except Exception:
        pass

    site_markers = {
        "docusaurus": [
            "docusaurus",
            "theme-doc-sidebar",
            "theme-doc-markdown",
            "docusaurus-theme",
        ],
        "mkdocs": [
            "mkdocs",
            "material for mkdocs",
            "md-sidebar",
            "md-content",
        ],
        "readthedocs": [
            "readthedocs",
            "wy-nav-side",
            "rst-content",
            "wy-nav-content",
        ],
        "gitbook": [
            "gitbook",
            "book-summary",
            "page-inner",
            "gitbook-root",
        ],
        "pdf_viewer": [
            "pdf.js",
            "pdfviewer",
            "react-pdf",
            "viewercontainer",
            "pdf-viewer",
        ],
    }

    for site_type, markers in site_markers.items():
        if any(marker in html for marker in markers):
            logger.info("Detected site type: %s", site_type)
            return site_type

    logger.info("Detected site type: custom_spa")
    return "custom_spa"
