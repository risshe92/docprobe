from pathlib import Path
import uuid
import time

import pytesseract
from PIL import Image


def _ocr_image(image_path: Path) -> str:
    with Image.open(image_path) as image:
        image.load()
        return pytesseract.image_to_string(image).strip()


def extract_ocr(page, content_info, logger, output_dir: Path, page_index=None):
    selector = content_info["selector"]
    index = content_info["index"]
    locator = page.locator(selector).nth(index)

    ocr_dir = output_dir / "ocr"
    ocr_dir.mkdir(parents=True, exist_ok=True)

    try:
        title = page.title().strip()
    except Exception:
        title = ""

    prefix = f"{page_index:04d}_" if page_index is not None else ""
    unique_id = uuid.uuid4().hex[:8]

    try:
        box = locator.bounding_box()
        if not box:
            raise RuntimeError("Could not determine content bounding box")

        viewport = page.viewport_size or {"width": 1280, "height": 720}
        shot_height = max(400, min(int(viewport["height"] * 0.85), 1400))

        total_height = int(box["height"])
        x = int(box["x"])
        y = int(box["y"])
        width = int(box["width"])

        parts = []
        offset = 0
        part_num = 1

        while offset < total_height:
            page.evaluate(f"window.scrollTo(0, {max(0, y + offset - 50)})")
            page.wait_for_timeout(500)

            clip = {
                "x": max(0, x),
                "y": max(0, y + offset),
                "width": max(100, width),
                "height": max(100, min(shot_height, total_height - offset)),
            }

            screenshot_path = ocr_dir / f"{prefix}content_{unique_id}_part{part_num:03d}.png"
            page.screenshot(path=str(screenshot_path), clip=clip)

            text = _ocr_image(screenshot_path)
            if text:
                parts.append(text)

            offset += shot_height - 120
            part_num += 1

        combined = "\n\n".join(parts).strip()

    except Exception as exc:
        logger.error("OCR extraction failed: %s", exc)
        return {
            "method": "ocr",
            "success": False,
            "title": title,
            "content": "",
            "content_length": 0,
            "error": str(exc),
        }

    return {
        "method": "ocr",
        "success": bool(combined),
        "title": title,
        "content": combined,
        "content_length": len(combined),
    }
