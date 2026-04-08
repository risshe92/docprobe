import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from docprobe.config import AppConfig
from docprobe.core.browser import BrowserSession
from docprobe.detectors.content_detector import detect_content
from docprobe.detectors.link_enumerator import enumerate_toolbar_links
from docprobe.detectors.page_classifier import classify_page
from docprobe.detectors.site_classifier import classify_site
from docprobe.detectors.toolbar_detector import detect_toolbar

from docprobe.extractors.html_extractor import extract_html
from docprobe.extractors.markdown_extractor import extract_markdown
from docprobe.extractors.ocr_extractor import extract_ocr
from docprobe.extractors.text_extractor import extract_text

from docprobe.logging_utils import setup_logging
from docprobe.writers.file_writer import (
    ensure_output_dir,
    write_extraction_output,
    write_meta,
)

# Map --export-as value to internal extraction method
EXPORT_AS_TO_METHOD = {
    "md":   "markdown",
    "txt":  "text",
    "html": "html",
    "ocr":  "ocr",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Docprobe - Universal documentation extractor"
    )

    parser.add_argument("--url", required=False, default=None)

    parser.add_argument(
        "--export-as",
        choices=["md", "txt", "html", "ocr"],
        default="md",
        help="Output format (default: md)",
    )

    parser.add_argument("--concurrency", type=int, default=4)

    parser.add_argument(
        "-o", "--output-dir",
        default=None,
        help="Output directory. Defaults to ./output/<format>/",
    )

    parser.add_argument(
        "--debug",
        choices=["off", "error", "info", "debug"],
        default="off",
    )

    parser.add_argument(
        "--crawl-toolbar",
        action="store_true",
        help="Crawl all links found in the toolbar navigation",
    )

    parser.add_argument("--max-pages", type=int, default=0)

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip already-processed pages",
    )

    parser.add_argument(
        "--export-pdf",
        choices=["none", "pdf", "pdf-single"],
        default="none",
        help="Export to PDF after crawl",
    )

    parser.add_argument(
        "--post-process",
        action="store_true",
        help="Run post-processing on an existing directory (no crawl)",
    )

    parser.add_argument(
        "--input-dir",
        default=None,
        help="Input directory for --post-process",
    )

    parser.add_argument(
        "--rename",
        action="store_true",
        help="Rename files using their title or first heading",
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Strip nav boilerplate and frontmatter (markdown only)",
    )

    return parser.parse_args()


def resolve_output_dir(args) -> Path:
    """Use -o if given, otherwise default to ./output/<format>/"""
    if args.output_dir:
        return Path(args.output_dir)
    return Path("./output") / args.export_as


def _export_as_to_method(export_as: str) -> str:
    return EXPORT_AS_TO_METHOD.get(export_as, "markdown")


def _extract_by_method(page, content_info, method, output_dir, logger, page_index=None):
    if method == "markdown":
        return extract_markdown(page, content_info, logger)
    if method == "text":
        return extract_text(page, content_info, logger)
    if method == "html":
        return extract_html(page, content_info, logger)
    if method == "ocr":
        return extract_ocr(page, content_info, logger, output_dir, page_index)
    raise ValueError(f"Unknown method: {method}")


def _result_is_weak(result):
    if not result.get("success"):
        return True
    content_length = result.get("content_length", 0)
    if content_length < 200:
        return True
    content = (result.get("content") or "").strip()
    junk_markers = [
        "toggle navigation", "search", "skip to content",
        "table of contents", "on this page",
    ]
    lower = content.lower()
    junk_hits = sum(1 for m in junk_markers if m in lower)
    if junk_hits >= 3 and content_length < 800:
        return True
    return False


def choose_auto_method(page, content_info, logger):
    profile = classify_page(page, content_info, logger)
    logger.info("Auto method recommended: %s", profile["recommended_mode"])
    return profile["recommended_mode"], profile


def run_extraction(page, content_info, method, output_dir, logger, page_index=None):
    if method != "auto":
        return _extract_by_method(page, content_info, method, output_dir, logger, page_index)

    recommended, page_profile = choose_auto_method(page, content_info, logger)

    if recommended == "markdown":
        chain = ["markdown", "text", "ocr"]
    elif recommended == "text":
        chain = ["text", "ocr"]
    else:
        chain = ["ocr"]

    last = None
    for i, candidate in enumerate(chain):
        logger.info("Trying method: %s", candidate)
        result = _extract_by_method(page, content_info, candidate, output_dir, logger, page_index)
        result["page_profile"] = page_profile
        if i > 0:
            result["fallback_from"] = chain[i - 1]
        if not _result_is_weak(result):
            return result
        logger.info("Weak result from %s, trying fallback", candidate)
        last = result

    return last


def load_completed_urls(output_dir):
    results_file = output_dir / "meta" / "crawl_results.json"
    if not results_file.exists():
        return set()
    try:
        with open(results_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {x["url"] for x in data if "url" in x}
    except Exception:
        return set()


def process_single_page(session, url, method, output_dir, logger, page_index):
    page = session.new_page()
    try:
        session.goto(url, page=page)
        site_type = classify_site(page, logger)
        toolbar = detect_toolbar(page, logger)
        content = detect_content(page, logger, site_type=site_type)
        result = run_extraction(page, content, method, output_dir, logger, page_index)
        file_path = write_extraction_output(output_dir, result, page_index)
        return {
            "url": url,
            "site_type": site_type,
            "toolbar": toolbar,
            "content": content,
            "extraction": {
                "method": result.get("method"),
                "success": result.get("success"),
                "content_length": result.get("content_length"),
                "title": result.get("title"),
                "fallback_from": result.get("fallback_from"),
                "page_profile": result.get("page_profile"),
            },
            "saved_file": str(file_path),
            "success": result.get("success"),
        }
    finally:
        page.close()


def process_single_page_isolated(url, method, output_dir, debug, page_index):
    logger = setup_logging(debug)
    with BrowserSession(logger=logger, headless=True) as session:
        return process_single_page(session, url, method, output_dir, logger, page_index)


def main():
    args = parse_args()

    output_dir = resolve_output_dir(args)

    config = AppConfig(
        url=args.url,
        export_as=args.export_as,
        concurrency=args.concurrency,
        output_dir=output_dir,
        debug=args.debug,
    )

    logger = setup_logging(config.debug)

    # --- Post-process mode: no crawl, no browser ---
    if args.post_process:
        if not args.input_dir:
            print("Error: --input-dir is required with --post-process")
            raise SystemExit(1)
        from docprobe.processors.post_processor import run_post_process
        run_post_process(args, Path(args.input_dir), logger)
        return

    # --- Crawl mode: URL required ---
    if not args.url:
        print("Error: --url is required unless using --post-process")
        raise SystemExit(1)

    ensure_output_dir(output_dir)
    (output_dir / "meta").mkdir(parents=True, exist_ok=True)

    method = _export_as_to_method(config.export_as)

    logger.info("URL: %s", config.url)
    logger.info("Export as: %s (method: %s)", config.export_as, method)
    logger.info("Concurrency: %d", config.concurrency)
    logger.info("Output directory: %s", config.output_dir)

    with BrowserSession(logger=logger) as session:
        session.goto(config.url)
        page = session.page

        site_type = classify_site(page, logger)
        toolbar = detect_toolbar(page, logger)
        content = detect_content(page, logger, site_type=site_type)

        result = run_extraction(page, content, method, config.output_dir, logger, 1)
        first_file = write_extraction_output(config.output_dir, result, 1)
        print("SAVED_FILE:", first_file)

        write_meta(output_dir, "run.json", {
            "url": config.url,
            "export_as": config.export_as,
            "method": method,
            "concurrency": config.concurrency,
            "crawl_toolbar": args.crawl_toolbar,
            "max_pages": args.max_pages,
            "resume": args.resume,
            "export_pdf": args.export_pdf,
            "first_saved_file": str(first_file),
        })
        write_meta(output_dir, "toolbar.json", toolbar)
        write_meta(output_dir, "content.json", content)
        write_meta(output_dir, "extraction.json", {
            "method": result.get("method"),
            "success": result.get("success"),
            "content_length": result.get("content_length"),
            "title": result.get("title"),
            "fallback_from": result.get("fallback_from"),
            "page_profile": result.get("page_profile"),
        })

        if not args.crawl_toolbar:
            if args.export_pdf == "pdf":
                from docprobe.exporters.pdf_exporter import export_page_pdf
                export_page_pdf(config.output_dir, output_dir, logger)
            elif args.export_pdf == "pdf-single":
                from docprobe.exporters.pdf_exporter import export_single_pdf
                export_single_pdf(config.output_dir, output_dir, logger)
            return

        links = enumerate_toolbar_links(page, config.url, toolbar, logger)

    if args.max_pages:
        links = links[: args.max_pages]

    if args.resume:
        completed = load_completed_urls(output_dir)
        links = [x for x in links if x["url"] not in completed]
        logger.info("Resume enabled, remaining pages: %d", len(links))

    results = []
    with ThreadPoolExecutor(max_workers=config.concurrency) as executor:
        futures = [
            executor.submit(
                process_single_page_isolated,
                item["url"],
                method,
                config.output_dir,
                config.debug,
                i,
            )
            for i, item in enumerate(links, start=2)
        ]
        for f in as_completed(futures):
            try:
                r = f.result()
                results.append(r)
                print("CRAWLED:", r["url"], "->", r["saved_file"])
            except Exception as e:
                logger.error("Crawl worker failed: %s", e)

    write_meta(output_dir, "crawl_results.json", results)
    print("CRAWL_COMPLETED:", len(results))

    if args.export_pdf == "pdf":
        from docprobe.exporters.pdf_exporter import export_page_pdf
        export_page_pdf(config.output_dir, output_dir, logger)
    elif args.export_pdf == "pdf-single":
        from docprobe.exporters.pdf_exporter import export_single_pdf
        export_single_pdf(config.output_dir, output_dir, logger)
