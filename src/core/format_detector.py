"""PDF format detection module.

Detects whether a PDF is a narrative SOR report or a tabular Flowback Report
by examining the first page's content and table structure.
"""

import logging
from enum import Enum
from pathlib import Path
from typing import List, Optional

import pdfplumber

from src.config import get_logger, FLOWBACK_HEADER_KEYWORDS

logger = get_logger(__name__)

# Minimum number of keyword matches to classify a table as flowback format
FLOWBACK_KEYWORD_THRESHOLD = 3


class PDFFormat(Enum):
    """Supported PDF extraction formats."""

    NARRATIVE_SOR = "narrative_sor"
    TABULAR_FLOWBACK = "tabular_flowback"
    UNKNOWN = "unknown"


def detect_format(pdf_path: Path) -> PDFFormat:
    """Detect whether a PDF is a narrative/SOR or tabular/flowback format.

    Strategy (applied to the first page only):
      1. Attempt ``pdfplumber.extract_tables()`` — if it returns a non-empty
         list with at least one table having ≥ 10 columns, check headers.
      2. If the first table's header row contains ≥ FLOWBACK_KEYWORD_THRESHOLD
         of the FLOWBACK_HEADER_KEYWORDS, classify as TABULAR_FLOWBACK.
      3. Otherwise, classify as NARRATIVE_SOR.

    The function is robust: corrupted PDFs and empty pages are handled with
    try/except blocks and fall through to NARRATIVE_SOR as the safe default.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        :class:`PDFFormat` enum value.
    """
    pdf_path = Path(pdf_path)

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                logger.warning("PDF has no pages: %s", pdf_path.name)
                return PDFFormat.NARRATIVE_SOR

            page = pdf.pages[0]

            # --- Table-based detection ---
            try:
                tables = page.extract_tables()
            except Exception as exc:
                logger.debug("extract_tables() failed on %s: %s", pdf_path.name, exc)
                tables = []

            if tables:
                # Find the widest table
                widest = max(tables, key=lambda t: len(t[0]) if t and t[0] else 0)
                col_count = len(widest[0]) if widest and widest[0] else 0
                logger.debug(
                    "Widest table has %d columns in %s", col_count, pdf_path.name
                )

                if col_count >= 10 and widest:
                    # Check each of the first few rows for header keywords
                    # (some PDFs have a title row before the real header row)
                    for row in widest[:4]:
                        if _check_table_headers(
                            row, FLOWBACK_HEADER_KEYWORDS, FLOWBACK_KEYWORD_THRESHOLD
                        ):
                            logger.info(
                                "Detected TABULAR_FLOWBACK format: %s", pdf_path.name
                            )
                            return PDFFormat.TABULAR_FLOWBACK

            # --- Text-based fallback detection ---
            try:
                text = page.extract_text() or ""
            except Exception as exc:
                logger.debug("extract_text() failed on %s: %s", pdf_path.name, exc)
                text = ""

            if "Flowback Report" in text or "Unit Name" in text:
                # Secondary heuristic: keyword in free text
                kw_hits = sum(1 for kw in FLOWBACK_HEADER_KEYWORDS if kw in text)
                if kw_hits >= FLOWBACK_KEYWORD_THRESHOLD:
                    logger.info(
                        "Detected TABULAR_FLOWBACK format via text: %s", pdf_path.name
                    )
                    return PDFFormat.TABULAR_FLOWBACK

            logger.info("Detected NARRATIVE_SOR format: %s", pdf_path.name)
            return PDFFormat.NARRATIVE_SOR

    except FileNotFoundError:
        raise
    except Exception as exc:
        logger.error(
            "Format detection failed for %s: %s — defaulting to NARRATIVE_SOR",
            pdf_path.name,
            exc,
        )
        return PDFFormat.NARRATIVE_SOR


def _check_table_headers(
    header_row: List[Optional[str]],
    keywords: List[str],
    threshold: int,
) -> bool:
    """Check if a table header row contains enough flowback keywords.

    Joins all cell values into a single string and counts how many *keywords*
    appear via case-insensitive substring matching.

    Args:
        header_row: List of cell values from a table row.
        keywords: Flowback header keywords to search for.
        threshold: Minimum number of keyword matches required.

    Returns:
        ``True`` if the header row contains at least *threshold* keywords.
    """
    if not header_row:
        return False

    # Combine all non-None cell values into one searchable string.
    # Normalise whitespace (pdfplumber headers often contain \n instead of spaces).
    import re as _re

    combined = " ".join(str(cell) for cell in header_row if cell is not None)
    combined_lower = _re.sub(r"\s+", " ", combined).lower()

    matches = sum(
        1 for kw in keywords if _re.sub(r"\s+", " ", kw).lower() in combined_lower
    )
    logger.debug("Header keyword matches: %d / %d required", matches, threshold)
    return matches >= threshold
