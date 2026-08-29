"""
syllabus_parser.py
Turns one big syllabus upload (a whole PDF or a wall of pasted text) into
separate chapters automatically, so the user never has to type each
chapter in by hand.

Detection strategy: look for lines that look like chapter headings
("Chapter 3: Water Resources", "Unit 2 - Motion", etc.) and split there.
If nothing matches, the whole thing is saved as one chapter.
"""

import re
import pdfplumber

# Matches lines like "Chapter 3: Water Resources", "CHAPTER 1", "Unit 4 - Forces"
CHAPTER_HEADING_PATTERN = re.compile(
    r"(?im)^\s*(?:chapter|unit)\s+\d+\s*[:\-\.]?\s*.*$"
)


def extract_text_from_pdf(uploaded_file) -> str:
    """uploaded_file is a Streamlit UploadedFile (file-like object)."""
    text_parts = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def split_into_chapters(full_text: str) -> list[tuple[str, str]]:
    """
    Returns a list of (chapter_name, chapter_content) tuples.
    If no 'Chapter N' / 'Unit N' style headings are found, the entire
    text becomes a single chapter called 'Full Syllabus'.
    """
    full_text = full_text.strip()
    if not full_text:
        return []

    matches = list(CHAPTER_HEADING_PATTERN.finditer(full_text))

    if not matches:
        return [("Full Syllabus", full_text)]

    chapters = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        chunk = full_text[start:end].strip()

        heading_line = match.group().strip()
        # Keep heading short and clean even if the line ran on
        chapter_name = heading_line.split("\n")[0][:80]

        if chunk:  # skip empty chapters (e.g. duplicate/blank headings)
            chapters.append((chapter_name, chunk))

    return chapters