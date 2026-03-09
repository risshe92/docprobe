import json
import re
from pathlib import Path


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[-\s]+", "_", value)
    return value[:150] if value else "untitled"


def ensure_output_dirs(base_dir: Path):
    base_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / "meta").mkdir(exist_ok=True)
    (base_dir / "text").mkdir(exist_ok=True)
    (base_dir / "html").mkdir(exist_ok=True)
    (base_dir / "markdown").mkdir(exist_ok=True)
    (base_dir / "ocr").mkdir(exist_ok=True)


def write_meta(base_dir: Path, filename: str, data):
    path = base_dir / "meta" / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def write_extraction_output(base_dir: Path, extraction_result: dict, page_index: int | None = None):
    method = extraction_result["method"]
    title = extraction_result.get("title", "") or "untitled"
    content = extraction_result.get("content", "")

    slug = slugify(title)
    prefix = f"{page_index:04d}_" if page_index is not None else ""

    if method == "text":
        path = base_dir / "text" / f"{prefix}{slug}.txt"
    elif method == "html":
        path = base_dir / "html" / f"{prefix}{slug}.html"
    elif method == "markdown":
        path = base_dir / "markdown" / f"{prefix}{slug}.md"
    elif method == "ocr":
        path = base_dir / "ocr" / f"{prefix}{slug}.txt"
    else:
        path = base_dir / f"{prefix}{slug}.txt"

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return path
