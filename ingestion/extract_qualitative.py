"""
extract_qualitative.py
Extracts qualitative risk disclosures (Items 1A, 7, 7A) from a 10-K HTML filing.

Handles the common gotcha where "Item 1A", "Item 7", etc. appear TWICE in a 10-K:
once in the Table of Contents (a short hyperlink line) and once as the real
section heading (followed by substantial body text). This script finds all
candidate matches for each heading and picks the one followed by the most text,
rather than just the first match — which would grab the TOC instead of content.

Usage:
    python3 extract_qualitative.py data/raw/svb_2022.html
"""

import sys
import re
import json
import os
from bs4 import BeautifulSoup

PROCESSED_DIR = "data/processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)

# (output filename, section title, start heading pattern, end heading pattern)
SECTIONS = [
    ("risk_factors.json", "Item 1A - Risk Factors",
     r"item\s+1a\.?\s*[-–—]?\s*risk\s+factors",
     r"item\s+1b\.?\s*[-–—]?\s*unresolved"),
    ("mdna.json", "Item 7 - Management's Discussion and Analysis",
     r"item\s+7\.?\s*[-–—]?\s*management'?s?\s+discussion",
     r"item\s+7a\.?\s*[-–—]?\s*quantitative"),
    ("market_risk.json", "Item 7A - Quantitative and Qualitative Disclosures About Market Risk",
     r"item\s+7a\.?\s*[-–—]?\s*quantitative",
     r"item\s+8\.?\s*[-–—]?\s*financial\s+statements"),
]

MIN_SECTION_LENGTH = 1000  # a real section is at least this many characters; TOC hits are short


def load_html(filepath):
    """Load and parse the HTML filing, returning the full page text with tags stripped
    but paragraph/heading structure loosely preserved via newlines."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        raw_html = f.read()
    soup = BeautifulSoup(raw_html, "html.parser")

    # Strip elements that only add noise
    for tag in soup(["script", "style", "table"]):
        tag.decompose()

    # get_text with a separator keeps some structure instead of one giant blob
    text = soup.get_text(separator="\n")
    return text


def clean_text(text):
    """Collapse excess whitespace/blank lines and strip page-number-only lines."""
    lines = [line.strip() for line in text.split("\n")]
    # Drop empty lines and lines that are just page numbers or stray punctuation
    lines = [ln for ln in lines if ln and not re.fullmatch(r"[\d\-–—\.\s]{1,5}", ln)]
    cleaned = "\n".join(lines)
    # Collapse 3+ consecutive newlines down to 2
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_section(full_text, start_pattern, end_pattern, min_length=MIN_SECTION_LENGTH):
    """
    Finds all matches of start_pattern in full_text. For each, looks for the nearest
    end_pattern match after it and measures the length of text between them. Returns
    the longest such span that clears min_length — this is what skips the Table of
    Contents (short spans) and lands on the real section (long span).
    Raises ValueError if no candidate section clears min_length.
    """
    start_matches = list(re.finditer(start_pattern, full_text, re.IGNORECASE))
    end_matches = list(re.finditer(end_pattern, full_text, re.IGNORECASE))

    if not start_matches:
        raise ValueError(f"No match found for start pattern: {start_pattern}")
    if not end_matches:
        raise ValueError(f"No match found for end pattern: {end_pattern}")

    best_span = None
    best_length = 0

    for sm in start_matches:
        start_pos = sm.end()
        # nearest end match that comes after this start match
        candidate_ends = [em.start() for em in end_matches if em.start() > start_pos]
        if not candidate_ends:
            continue
        end_pos = min(candidate_ends)
        length = end_pos - start_pos
        if length > best_length:
            best_length = length
            best_span = (start_pos, end_pos)

    if best_span is None or best_length < min_length:
        raise ValueError(
            f"Could not find a section long enough (best candidate was {best_length} chars, "
            f"need >= {min_length}). The heading patterns may not match this filing's actual "
            f"wording — try adjusting start_pattern/end_pattern."
        )

    return full_text[best_span[0]:best_span[1]].strip()


def save_json(filepath, title, text):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({"title": title, "text": text}, f, indent=2)
    print(f"Saved {filepath} ({len(text)} chars)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_qualitative.py <path_to_10k.html>")
        sys.exit(1)

    html_path = sys.argv[1]
    print(f"Loading {html_path}...")
    raw_text = load_html(html_path)
    full_text = clean_text(raw_text)
    print(f"Loaded and cleaned. Total document length: {len(full_text)} chars")

    for filename, title, start_pat, end_pat in SECTIONS:
        print(f"\nExtracting: {title}")
        try:
            section_text = extract_section(full_text, start_pat, end_pat)
            save_json(os.path.join(PROCESSED_DIR, filename), title, section_text)
        except ValueError as e:
            print(f"  FAILED: {e}")
            print(f"  Skipping {filename} — you may need to extract this one manually instead.")


if __name__ == "__main__":
    main()