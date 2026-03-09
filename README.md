# Docprobe

Docprobe is a universal documentation extraction tool built to archive modern documentation websites that do not provide downloadable versions.

It automatically detects common documentation frameworks such as Docusaurus, MkDocs, GitBook, and ReadTheDocs, then extracts content using intelligent fallback strategies.

# Features
- Automatic documentation platform detection
- Extracts dynamic SPA documentation sites
- Toolbar crawling and sidebar navigation discovery
- Smart extraction fallback: Markdown → Text → OCR
- Concurrent crawling
- Resume interrupted crawls
- PDF export support
- OCR support for difficult or image-heavy pages
- Designed for modern JavaScript-rendered documentation portals

# Supported Documentation Platforms
- Docusaurus
- MkDocs
- GitBook
- ReadTheDocs
- Custom SPA documentation sites
- PDF-viewer style documentation pages
- Image-heavy documentation pages via OCR fallback

# Installation
## 1. Clone the repository
```bash
git clone https://github.com/risshe92/docprobe.git

cd docprobe
```
2. Create and activate a virtual environment

```
python3 -m venv venv
source venv/bin/activate
```
3. Install Python dependencies
```pip install -r requirements.txt```
4. Install Playwright browser dependencies
```playwright install chromium```
5. Install system dependencies
### Debian
```sudo apt install tesseract-ocr pandoc texlive-xetex```
### Arch
```sudo pacman -S tesseract pandoc texlive-core```


# Quick Start
-  *Extract a single documentation page:*
```python3 docprobe.py --url https://docs.kasm.com/docs```

- *Crawl a documentation sidebar automatically:*
```python3 docprobe.py --url https://docs.kasm.com/docs --crawl-toolbar```
  
- *Resume an interrupted crawl:*

  ```python3 docprobe.py --url https://docs.kasm.com/docs --crawl-toolbar --resume```

- *Export extracted markdown pages to PDF:*

  ```python3 docprobe.py --url https://docs.kasm.com/docs --crawl-toolbar --export pdf```

- *Generate a single combined PDF manual:*
  ```python3 docprobe.py --url https://docs.kasm.com/docs --crawl-toolbar --export pdf-single```

  # Command Line Options
  - Required Argument
  ```--url```
Purpose: Target documentation URL.
Example: ```--url https://docs.kasm.com/docs```

# Extraction Mode
```--mode```
Purpose: Controls how content is extracted.

## Supported values:
- auto
Smart mode. Automatically chooses the best extraction method based on page analysis.
- markdown
Extract rendered HTML and convert to Markdown.
- text
Extract plain visible text content.
- html
Extract rendered HTML from the main content area.
- ocr
Use OCR on screenshots of the page content.

Default:
--mode auto

Examples:
--mode auto
--mode markdown
--mode text
--mode html
--mode ocr

## Crawling Options

- --crawl-toolbar
Purpose: Detect and crawl links found in the documentation sidebar / toolbar.
Example:
``--crawl-toolbar``
- --max-pages
Purpose: Limit how many pages are crawled from the detected toolbar.
Example:
``--max-pages 10``
Default:
``--max-pages 0``
0 means no limit.
- --resume
Purpose: Skip URLs that were already processed in a previous crawl.
Example:
```--resume```
Purpose: Useful for large documentation sets or interrupted runs.
- --concurrency
Number of concurrent workers used during crawl.
Example:
``--concurrency 8``
Default:
``--concurrency 4``
Higher values may improve speed, but increase CPU, memory, and browser usage.

## Output Options
--output-dir
Directory where all extracted content and metadata will be written.
Example:
``--output-dir ./output``
```--output-dir /home/user/docs_archive```
Default:
--output-dir ./output
--export

Optional export mode after extraction.
Supported values:
- none
  No PDF export
- pdf
  Generate one PDF per Markdown page
- pdf-single
  Generate one combined PDF manual
Examples:
```--export none```

```--export pdf```

```--export pdf-single```

Default:
--export none
Extraction Strategy
When --mode auto is used, Docprobe analyzes the page and chooses the best method automatically.

## Typical behavior:
- Structured docs page → markdown
- Plain content page → text
- Image-heavy / viewer-like page → ocr
- Fallback chain in auto mode:
- markdown → text → ocr
This allows Docprobe to recover from poor Markdown extraction and still capture difficult content.

## Output Structure
Example output layout:
```
output/
├── html/
├── markdown/
├── meta/
├── ocr/
├── pdf/
└── text/
```

### Folder meanings
```markdown/``` Extracted Markdown pages
```text/``` Plain text output
```html/``` Extracted rendered HTML
```ocr/``` OCR text output and OCR-rel`ated files
```pdf/``` Exported PDF files
```meta/``` Crawl metadata, run info, extraction metadata, and crawl results


## Example Commands
 - Single page, automatic mode
```
python3 docprobe.py \
  --url https://docs.kasm.com/docs \
  --mode auto
```
- Crawl toolbar with concurrency
```
python3 docprobe.py \
  --url https://docs.kasm.com/docs \
  --crawl-toolbar \
  --concurrency 8 \
  --debug info
```
- Crawl only first 20 pages
```
python3 docprobe.py \
  --url https://docs.kasm.com/docs \
  --crawl-toolbar \
  --max-pages 20
```

- Force OCR mode
```
python3 docprobe.py \
  --url https://docs.kasm.com/docs \
  --mode ocr \
  --crawl-toolbar
```

Resume a previous crawl
```
python3 docprobe.py \
  --url https://docs.kasm.com/docs \
  --crawl-toolbar \
  --resume \
  --debug info
```

Export per-page PDFs
```
python3 docprobe.py \
  --url https://docs.kasm.com/docs \
  --crawl-toolbar \
  --export pdf
```

Export one combined PDF manual
```
python3 docprobe.py \
  --url https://docs.kasm.com/docs \
  --crawl-toolbar \
  --export pdf-single
```
## Notes
- OCR requires tesseract to be installed on the system.
- PDF export requires pandoc and a LaTeX PDF engine such as xelatex.
- Some sites may still require site-specific tuning depending on how heavily they customize their frontend.
- Very large crawls are best used with --resume.
