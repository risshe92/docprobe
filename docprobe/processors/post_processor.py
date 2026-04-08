"""
docprobe/processors/post_processor.py

Post-processing pass over any directory of extracted files.

Actions (all opt-in via CLI flags):
  --rename      Rename files using title extracted from content
  --clean       Strip nav boilerplate and frontmatter (.md only)
  --export-pdf  Convert to PDF after processing (pdf | pdf-single, .md only)

Usage:
  python docprobe.py --post-process --input-dir ./output/markdown --rename
  python docprobe.py --post-process --input-dir ./output/markdown --rename --clean
  python docprobe.py --post-process --input-dir ./output/markdown --rename --export-pdf pdf-single
"""

import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Slug helper
# ---------------------------------------------------------------------------

def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[-\s]+", "_", value)
    return value[:80] if value else "untitled"


# ---------------------------------------------------------------------------
# Title extraction per format
# ---------------------------------------------------------------------------

def extract_title_md(content: str) -> str | None:
    """First ATX # heading."""
    for line in content.splitlines():
        m = re.match(r"^#{1,6}\s+(.+)", line.strip())
        if m:
            return m.group(1).strip()
    return None


def extract_title_txt(content: str) -> str | None:
    """First non-empty line."""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def extract_title_html(content: str) -> str | None:
    """First <h1> text, fallback to <title>."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.IGNORECASE | re.DOTALL)
    if m:
        text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if text:
            return text
    m = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
    if m:
        text = m.group(1).strip()
        if text:
            return text
    return None


def extract_title(file: Path) -> str | None:
    content = file.read_text(encoding="utf-8", errors="ignore")
    suffix = file.suffix.lower()
    if suffix == ".md":
        return extract_title_md(content)
    if suffix == ".txt":
        return extract_title_txt(content)
    if suffix in (".html", ".htm"):
        return extract_title_html(content)
    return None


# ---------------------------------------------------------------------------
# Metadata / boilerplate stripping (.md only)
# ---------------------------------------------------------------------------

_NAV_PATTERNS = [
    re.compile(r"^\s*\[.*?\]\(.*?\)\s*$"),
    re.compile(r"^\s*#+\s*(Table of Contents|On This Page|Navigation)\s*$", re.I),
    re.compile(r"^\s*(Previous|Next|Skip to content|Toggle navigation)\s*$", re.I),
]

_FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


def clean_content(content: str) -> str:
    content = _FRONTMATTER_RE.sub("", content)
    lines = content.splitlines()
    cleaned = [line for line in lines if not any(p.match(line) for p in _NAV_PATTERNS)]
    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


# ---------------------------------------------------------------------------
# Rename pass
# ---------------------------------------------------------------------------

def rename_files(input_dir: Path, logger) -> dict:
    renamed = {}
    seen = set()

    for f in sorted(input_dir.iterdir()):
        if not f.is_file():
            continue

        title = extract_title(f)
        if not title:
            logger.warning("No title found in %s, skipping", f.name)
            continue

        slug = slugify(title)

        # Preserve numeric prefix e.g. "0042_"
        prefix_match = re.match(r"^(\d+_)", f.stem)
        prefix = prefix_match.group(1) if prefix_match else ""

        candidate = f"{prefix}{slug}"
        counter = 2
        while candidate in seen:
            candidate = f"{prefix}{slug}_{counter}"
            counter += 1
        seen.add(candidate)

        new_path = f.parent / f"{candidate}{f.suffix}"

        if new_path == f:
            seen.add(candidate)
            continue

        f.rename(new_path)
        renamed[f] = new_path
        logger.info("RENAMED: %s -> %s", f.name, new_path.name)
        print(f"RENAMED: {f.name} -> {new_path.name}")

    return renamed


# ---------------------------------------------------------------------------
# Clean pass (.md only)
# ---------------------------------------------------------------------------

def clean_files(input_dir: Path, logger):
    count = 0
    for f in sorted(input_dir.glob("*.md")):
        original = f.read_text(encoding="utf-8")
        cleaned = clean_content(original)
        if cleaned != original:
            f.write_text(cleaned, encoding="utf-8")
            logger.info("CLEANED: %s", f.name)
            count += 1
    print(f"CLEANED: {count} files updated")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def run_post_process(args, input_dir: Path, logger):
    if not input_dir.exists():
        print(f"Error: input directory not found: {input_dir}")
        raise SystemExit(1)

    files = [f for f in input_dir.iterdir() if f.is_file()]
    print(f"Found {len(files)} files in {input_dir}")

    if args.rename:
        print("Running rename pass...")
        renamed = rename_files(input_dir, logger)
        print(f"RENAME COMPLETE: {len(renamed)} files renamed")

    if args.clean:
        print("Running clean pass...")
        clean_files(input_dir, logger)

    if args.export_pdf in ("pdf", "pdf-single"):
        from docprobe.exporters.pdf_exporter import export_page_pdf, export_single_pdf
        pdf_output_dir = input_dir.parent
        print(f"Exporting PDF ({args.export_pdf})...")
        if args.export_pdf == "pdf":
            export_page_pdf(input_dir, pdf_output_dir, logger)
        else:
            export_single_pdf(input_dir, pdf_output_dir, logger)
        print("EXPORT COMPLETE")

    print("POST_PROCESS_COMPLETE")
