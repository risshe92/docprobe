# Docprobe

Docprobe is a universal documentation extraction tool built to archive modern documentation websites that do not provide downloadable versions.

It automatically detects common documentation frameworks such as Docusaurus, MkDocs, GitBook, and ReadTheDocs, then extracts content using intelligent fallback strategies.

## Features

- Automatic documentation platform detection
- Extracts dynamic SPA documentation sites
- Toolbar crawling and sidebar navigation discovery
- Smart extraction fallback: Markdown → Text → OCR
- Concurrent crawling
- Resume interrupted crawls
- Post-processing: rename files by chapter title, strip nav boilerplate
- PDF export support (per-page or single combined manual)
- OCR support for difficult or image-heavy pages
- Designed for modern JavaScript-rendered documentation portals

## Supported Documentation Platforms

- Docusaurus
- MkDocs
- GitBook
- ReadTheDocs
- Custom SPA documentation sites
- PDF-viewer style documentation pages
- Image-heavy documentation pages via OCR fallback

## Installation

**1. Clone the repository**
```bash
git clone https://github.com/risshe92/docprobe.git
cd docprobe
```

**2. Create and activate a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Install Python dependencies**
```bash
pip install -r requirements.txt
```

**4. Install Playwright browser dependencies**
```bash
playwright install chromium
```

**5. Install system dependencies**

Debian/Ubuntu:
```bash
sudo apt install tesseract-ocr pandoc texlive-xetex
```

Arch:
```bash
sudo pacman -S tesseract pandoc texlive-core
```

## Quick Start

Extract a single documentation page:
```bash
python3 docprobe.py --url https://docs.example.com/docs
```

Crawl a documentation sidebar automatically:
```bash
python3 docprobe.py --url https://docs.example.com/docs --crawl-toolbar
```

Resume an interrupted crawl:
```bash
python3 docprobe.py --url https://docs.example.com/docs --crawl-toolbar --resume
```

Export extracted markdown pages to individual PDFs:
```bash
python3 docprobe.py --url https://docs.example.com/docs --crawl-toolbar --export-pdf pdf
```

Generate a single combined PDF manual:
```bash
python3 docprobe.py --url https://docs.example.com/docs --crawl-toolbar --export-pdf pdf-single
```

## Command Line Options

### Crawl Options

| Argument | Default | Description |
|---|---|---|
| `--url` | required | Target documentation URL |
| `--export-as` | `md` | Output format: `md`, `txt`, `html`, `ocr` |
| `-o`, `--output-dir` | `./output/<format>/` | Output directory |
| `--crawl-toolbar` | off | Crawl all links in the sidebar/toolbar |
| `--max-pages` | `0` (no limit) | Limit number of pages crawled |
| `--resume` | off | Skip already-processed URLs |
| `--concurrency` | `4` | Number of concurrent crawl workers |
| `--export-pdf` | `none` | Export to PDF after crawl: `none`, `pdf`, `pdf-single` |
| `--debug` | `off` | Log level: `off`, `error`, `info`, `debug` |

### Post-process Options

| Argument | Description |
|---|---|
| `--post-process` | Run post-processing on an existing directory (no crawl) |
| `--input-dir` | Input directory to process (required with `--post-process`) |
| `--rename` | Rename files using their first heading or title |
| `--clean` | Strip nav boilerplate and frontmatter (markdown only) |
| `--export-pdf` | Export to PDF after processing: `pdf`, `pdf-single` |

## Export Formats

`--export-as` controls the output format during crawl:

| Value | Output |
|---|---|
| `md` | Markdown (default) |
| `txt` | Plain text |
| `html` | Rendered HTML |
| `ocr` | OCR text from page screenshots |

Output is written to `./output/<format>/` by default, or to `-o` if specified.

## Extraction Strategy

When using the default `md` mode, Docprobe analyzes the page and applies a fallback chain automatically:

```
markdown → text → ocr
```

This allows Docprobe to recover from poor Markdown extraction and still capture difficult content.

## Post-Processing

Post-processing runs on an existing directory of extracted files without re-crawling.

Rename files by chapter title:
```bash
python3 docprobe.py --post-process --input-dir ./output/md --rename
```

Clean nav boilerplate from markdown files:
```bash
python3 docprobe.py --post-process --input-dir ./output/md --clean
```

Rename, clean, then export a single combined PDF:
```bash
python3 docprobe.py --post-process --input-dir ./output/md --rename --clean --export-pdf pdf-single
```

## Output Structure

```
output/
└── md/              # or txt/, html/, ocr/ depending on --export-as
    ├── 0001_overview.md
    ├── 0002_getting_started.md
    └── ...
    meta/
    ├── run.json
    ├── crawl_results.json
    ├── toolbar.json
    ├── content.json
    └── extraction.json
documentation_manual.pdf   # if --export-pdf pdf-single was used
```

## Example Commands

Single page, default markdown mode:
```bash
python3 docprobe.py --url https://docs.example.com/docs
```

Crawl toolbar with concurrency:
```bash
python3 docprobe.py \
  --url https://docs.example.com/docs \
  --crawl-toolbar \
  --concurrency 8 \
  --debug info
```

Crawl first 20 pages only:
```bash
python3 docprobe.py \
  --url https://docs.example.com/docs \
  --crawl-toolbar \
  --max-pages 20
```

Save output to a custom directory:
```bash
python3 docprobe.py \
  --url https://docs.example.com/docs \
  --crawl-toolbar \
  -o /home/user/docs_archive
```

Resume a previous crawl:
```bash
python3 docprobe.py \
  --url https://docs.example.com/docs \
  --crawl-toolbar \
  --resume
```

Export as plain text:
```bash
python3 docprobe.py \
  --url https://docs.example.com/docs \
  --crawl-toolbar \
  --export-as txt
```

Force OCR mode:
```bash
python3 docprobe.py \
  --url https://docs.example.com/docs \
  --crawl-toolbar \
  --export-as ocr
```

## Notes

- OCR requires `tesseract` to be installed on the system.
- PDF export requires `pandoc` and a LaTeX engine (`xelatex`).
- Some sites may require site-specific tuning depending on frontend complexity.
- Large crawls work best with `--resume` to handle interruptions.
