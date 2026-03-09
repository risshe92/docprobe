import re


def clean_markdown(text: str) -> str:
    if not text:
        return text

    text = text.replace("\r", "")
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = text.splitlines()
    cleaned = []
    prev_nonempty = None

    junk_lines = {
        "search",
        "table of contents",
        "on this page",
        "previous",
        "next",
    }

    for line in lines:
        stripped = line.strip()
        lowered = stripped.lower()

        if lowered in junk_lines:
            continue

        if stripped and prev_nonempty == stripped:
            continue

        cleaned.append(line)

        if stripped:
            prev_nonempty = stripped

    text = "\n".join(cleaned)

    # normalize overly broken spacing
    text = re.sub(r"\n{3,}", "\n\n", text)

    # trim huge runs of spaces
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip() + "\n"
