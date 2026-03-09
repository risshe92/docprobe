import re
import subprocess
from pathlib import Path


# ---------------------------------------------------------------------------
# Sanitisation helpers
# ---------------------------------------------------------------------------

def _split_code_blocks(md_text: str):
    """
    Yield (is_code, chunk) tuples so we can apply transformations only to
    prose, leaving fenced/indented code blocks untouched.
    """
    # Matches fenced code blocks (``` or ~~~) and inline code spans (`...`)
    pattern = re.compile(
        r"(```[\s\S]*?```|~~~[\s\S]*?~~~|`[^`\n]+`)",
        re.MULTILINE,
    )
    last = 0
    for m in pattern.finditer(md_text):
        if m.start() > last:
            yield False, md_text[last : m.start()]
        yield True, m.group()
        last = m.end()
    if last < len(md_text):
        yield False, md_text[last:]


def sanitize_markdown_for_latex(md_text: str) -> str:
    """
    Prepare markdown for pandoc + xelatex:
      - Strip emoji and other non-ASCII *outside* code blocks
      - Strip zero-width chars everywhere
      - Escape LaTeX special chars ($, %) *outside* code blocks only
      - Replace image links with '[Image: <alt>]' so pandoc doesn't
        try to load web-relative paths
    """
    # Remove image links before splitting (avoids path errors)
    md_text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"[Image: \1]", md_text)
    # Reference-style images
    md_text = re.sub(r"!\[([^\]]*)\]\[[^\]]*\]", r"[Image: \1]", md_text)
    # Raw HTML img tags
    md_text = re.sub(r"<img[^>]*>", "[Image]", md_text, flags=re.IGNORECASE)

    # Zero-width chars everywhere (safe to remove universally)
    md_text = md_text.replace("\u200b", "").replace("\ufeff", "")

    result = []
    for is_code, chunk in _split_code_blocks(md_text):
        if is_code:
            result.append(chunk)
        else:
            # Strip non-ASCII (emoji, special unicode) from prose only
            chunk = re.sub(r"[^\x00-\x7F]+", "", chunk)
            # Escape bare $ (math mode trigger) — NOT inside code blocks
            # Use a negative lookbehind to avoid double-escaping
            chunk = re.sub(r"(?<!\\)\$", r"\\$", chunk)
            result.append(chunk)

    return "".join(result)


def sanitize_markdown_for_html(md_text: str) -> str:
    """
    Light sanitisation for the WeasyPrint / HTML path.
    Images are replaced so broken web-relative paths don't cause errors.
    Everything else (emoji, unicode) is left intact — browsers handle it fine.
    """
    md_text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"*[Image: \1]*", md_text)
    md_text = re.sub(r"!\[([^\]]*)\]\[[^\]]*\]", r"*[Image: \1]*", md_text)
    md_text = re.sub(r"<img[^>]*>", "*[Image]*", md_text, flags=re.IGNORECASE)
    md_text = md_text.replace("\u200b", "").replace("\ufeff", "")
    return md_text


# ---------------------------------------------------------------------------
# Per-file export (pandoc + xelatex)
# ---------------------------------------------------------------------------

def export_page_pdf(markdown_dir: Path, output_dir: Path, logger):
    pdf_dir = output_dir / "pdf"
    pdf_dir.mkdir(exist_ok=True)

    for md_file in sorted(markdown_dir.glob("*.md")):
        with open(md_file, encoding="utf-8") as f:
            text = f.read()

        cleaned = sanitize_markdown_for_latex(text)
        temp_md = md_file.parent / (md_file.stem + "_clean.md")

        with open(temp_md, "w", encoding="utf-8") as f:
            f.write(cleaned)

        pdf_file = pdf_dir / (md_file.stem + ".pdf")

        try:
            subprocess.run(
                [
                    "pandoc",
                    str(temp_md),
                    "--pdf-engine=xelatex",
                    "-V", "geometry:margin=1in",
                    # Suppress missing-glyph warnings that aren't fatal
                    "--quiet",
                    "-o", str(pdf_file),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info("PDF exported: %s", pdf_file)
        except subprocess.CalledProcessError as e:
            logger.error("PDF export failed for %s:\n%s", md_file, e.stderr)
        finally:
            temp_md.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Combined PDF (pandoc + xelatex)
# ---------------------------------------------------------------------------

def export_single_pdf(markdown_dir: Path, output_dir: Path, logger):
    combined = output_dir / "combined_manual.md"

    with open(combined, "w", encoding="utf-8") as outfile:
        for md in sorted(markdown_dir.glob("*.md")):
            with open(md, encoding="utf-8") as f:
                outfile.write(sanitize_markdown_for_latex(f.read()))
            outfile.write("\n\n---\n\n")  # page-break hint

    pdf_file = output_dir / "documentation_manual.pdf"

    try:
        subprocess.run(
            [
                "pandoc",
                str(combined),
                "--toc",
                "--number-sections",
                "--pdf-engine=xelatex",
                "-V", "geometry:margin=1in",
                "--quiet",
                "-o", str(pdf_file),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info("Combined PDF exported: %s", pdf_file)
    except subprocess.CalledProcessError as e:
        logger.error("Combined PDF export failed:\n%s", e.stderr)


# ---------------------------------------------------------------------------
# WeasyPrint backend (better Unicode / emoji support, no LaTeX)
# ---------------------------------------------------------------------------

def export_pdf_weasyprint(markdown_dir: Path, output_dir: Path, logger):
    """
    Convert markdown → HTML → PDF via WeasyPrint.
    Requires:  pip install weasyprint markdown
    Advantages over pandoc+xelatex:
      - Full emoji / Unicode support (rendered via system fonts)
      - Missing images are silently skipped
      - No LaTeX escaping needed
      - Faster for large batches
    """
    try:
        import markdown
        from weasyprint import HTML, CSS
    except ImportError:
        logger.error(
            "WeasyPrint backend requires: pip install weasyprint markdown"
        )
        return

    pdf_dir = output_dir / "pdf_wp"
    pdf_dir.mkdir(exist_ok=True)

    css = CSS(string="""
        @page { margin: 1in; }
        body { font-family: sans-serif; font-size: 11pt; line-height: 1.6; }
        h1, h2, h3 { color: #222; }
        pre, code { background: #f4f4f4; font-size: 9pt; }
        pre { padding: 0.5em; overflow-wrap: break-word; white-space: pre-wrap; }
        img { max-width: 100%; }
    """)

    md_converter = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "attr_list"]
    )

    for md_file in sorted(markdown_dir.glob("*.md")):
        with open(md_file, encoding="utf-8") as f:
            text = f.read()

        cleaned = sanitize_markdown_for_html(text)
        md_converter.reset()
        body_html = md_converter.convert(cleaned)

        html = f"""<!DOCTYPE html>
<html><head>
  <meta charset="utf-8">
  <title>{md_file.stem}</title>
</head><body>
{body_html}
</body></html>"""

        pdf_file = pdf_dir / (md_file.stem + ".pdf")
        try:
            HTML(string=html).write_pdf(pdf_file, stylesheets=[css])
            logger.info("PDF exported (WeasyPrint): %s", pdf_file)
        except Exception as e:
            logger.error("WeasyPrint failed for %s: %s", md_file, e)

