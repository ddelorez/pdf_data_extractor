"""Extraction module for tabular Flowback Report PDFs.

Handles structured table PDFs where data is in columnar format,
with multiple wells per page and date propagation across blank date cells.

Typical table structure (from UL Carla Daily Production PDFs):

    Row 0: column headers — "Unit Name", "Date", "Prod Method",
                             "New Prod Oil", "New Prod Gas", "New Prod Wat",
                             "Cum. Oil", "Cum. Gas", "Cum. Water",
                             "Tubing", "Casing", "ESP Pump Intake",
                             "ESP Speed", "Gas Lift Inj", "Tubing Choke",
                             "Days On", "Down Time", "Down Reason", "Comment"
    Row 1+: data rows, where the Date cell may be blank when the date is
            shared with the row above (date propagation required).
"""

import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pdfplumber

from src.config import get_logger, FLOWBACK_PDF_COLUMN_MAP

logger = get_logger(__name__)

# Format tag written into every record produced by this module
_FORMAT_TAG = "tabular_flowback"


def extract_flowback_records(pdf_path: Path) -> List[Dict[str, Any]]:
    """Extract production records from a tabular Flowback Report PDF.

    Process:
      1. Open PDF with pdfplumber.
      2. For each page, call ``page.extract_tables()``.
      3. Identify the header row in each table by matching known column names
         (via :func:`_identify_header_row`).
      4. Build a column-index map (:func:`_build_column_index`).
      5. For each data row after the header row:

         a. Skip Total/summary rows (:func:`_is_total_row`).
         b. Propagate date from the most recent non-blank date cell.
         c. Parse numeric values (strip commas).
         d. Build the record dict and append to results.

      6. Tag every record with ``_format = 'tabular_flowback'``.
      7. Also store ``'Well'`` as an alias for ``'Name'`` so that the
         existing deduplicator (which sorts on ``'Well'``) works unchanged.

    Args:
        pdf_path: Path to the flowback PDF file.

    Returns:
        List of record dicts.  Each dict contains at minimum ``'Name'``,
        ``'Well'``, ``'Date'``, and ``'_format'``, plus whichever production
        fields were present in the table.
    """
    pdf_path = Path(pdf_path)
    records: List[Dict[str, Any]] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                logger.debug("Processing page %d of %s", page_num, pdf_path.name)

                try:
                    tables = page.extract_tables()
                except Exception as exc:
                    logger.warning(
                        "extract_tables() failed on page %d of %s: %s",
                        page_num,
                        pdf_path.name,
                        exc,
                    )
                    tables = []

                for table_idx, table in enumerate(tables):
                    if not table:
                        continue

                    page_records = _process_table(
                        table,
                        source=f"{pdf_path.name} p{page_num} t{table_idx}",
                    )
                    records.extend(page_records)

    except FileNotFoundError:
        raise
    except Exception as exc:
        logger.error(
            "Failed to extract flowback records from %s: %s", pdf_path.name, exc
        )
        raise

    logger.info(
        "Extracted %d flowback records from %s", len(records), pdf_path.name
    )
    return records


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _process_table(
    table: List[List[Optional[str]]],
    source: str = "",
) -> List[Dict[str, Any]]:
    """Extract records from a single pdfplumber table (2-D list of strings).

    Args:
        table: 2-D list where ``table[row][col]`` is a cell value or ``None``.
        source: Human-readable identifier for logging (file + page + table).

    Returns:
        List of record dicts extracted from the table.
    """
    header_row_idx = _identify_header_row(table)
    if header_row_idx is None:
        logger.debug("No header row found in table %s — skipping", source)
        return []

    header_row = table[header_row_idx]
    col_index = _build_column_index(header_row)

    if not col_index:
        logger.debug("Empty column index for table %s — skipping", source)
        return []

    name_col = col_index.get("Name")
    date_col = col_index.get("Date")

    records: List[Dict[str, Any]] = []
    last_date: Optional[date] = None

    for row in table[header_row_idx + 1 :]:
        # Skip entirely blank rows
        if all(cell is None or str(cell).strip() == "" for cell in row):
            continue

        # Skip Total/summary rows
        if name_col is not None and _is_total_row(row, name_col):
            logger.debug("Skipping total row: %s", row)
            continue

        # --- Date propagation ---
        raw_date = _safe_cell(row, date_col)
        parsed_date = _parse_date(raw_date)
        if parsed_date is not None:
            last_date = parsed_date
        current_date = last_date  # may still be None if no date seen yet

        # --- Build record dict ---
        record: Dict[str, Any] = {"_format": _FORMAT_TAG}

        for field_name, col_idx in col_index.items():
            if field_name == "Date":
                record["Date"] = current_date
                continue

            raw_value = _safe_cell(row, col_idx)

            # Numeric fields
            if field_name in _NUMERIC_FIELD_SET:
                record[field_name] = _parse_numeric(raw_value)
            else:
                # Text fields — strip whitespace but keep as string/None
                record[field_name] = (
                    raw_value.strip() if raw_value and raw_value.strip() else None
                )

        # Alias 'Name' → 'Well' for pipeline compatibility
        if "Name" in record:
            record["Well"] = record["Name"]

        records.append(record)

    return records


def _identify_header_row(
    table: List[List[Optional[str]]],
) -> Optional[int]:
    """Find the row index that contains the PDF column headers.

    Scans rows (up to the first 5) looking for cells whose text matches
    keys in :data:`FLOWBACK_PDF_COLUMN_MAP`.

    Args:
        table: 2-D list of cell values from pdfplumber.

    Returns:
        Row index of the header row, or ``None`` if not found.
    """
    known_headers = set(FLOWBACK_PDF_COLUMN_MAP.keys())

    for row_idx, row in enumerate(table[:5]):
        if row is None:
            continue
        matches = sum(
            1
            for cell in row
            if cell and any(
                re.sub(r"\s+", " ", kw).lower()
                in re.sub(r"\s+", " ", str(cell)).lower()
                for kw in known_headers
            )
        )
        if matches >= 2:
            logger.debug("Header row found at index %d (matches=%d)", row_idx, matches)
            return row_idx

    return None


def _build_column_index(
    header_row: List[Optional[str]],
) -> Dict[str, int]:
    """Build a mapping from internal field name to column index.

    Uses :data:`FLOWBACK_PDF_COLUMN_MAP` to translate PDF header text to
    record dict keys.  Matching is done via case-insensitive substring search
    so minor OCR variations are tolerated.

    Args:
        header_row: List of header cell values (from the identified header row).

    Returns:
        Dict mapping ``field_name → column_index`` (0-based).
        Only fields whose PDF header text was successfully matched are included.
        Fields mapped to ``None`` in :data:`FLOWBACK_PDF_COLUMN_MAP` are
        excluded from the returned mapping.
    """
    col_index: Dict[str, int] = {}

    # Sort map entries longest-key-first so that specific headers like
    # "Tubing Choke" are tried before the shorter "Tubing".
    sorted_map = sorted(
        FLOWBACK_PDF_COLUMN_MAP.items(),
        key=lambda pair: len(pair[0]),
        reverse=True,
    )

    for col_idx, cell in enumerate(header_row):
        if cell is None:
            continue
        # Normalise whitespace — pdfplumber headers often contain \n
        cell_norm = re.sub(r"\s+", " ", str(cell).strip()).lower()

        for pdf_header, field_name in sorted_map:
            if field_name is None:
                continue  # explicitly excluded
            header_norm = re.sub(r"\s+", " ", pdf_header).lower()
            if header_norm in cell_norm:
                col_index[field_name] = col_idx
                break  # first (longest) match wins

    logger.debug("Built column index: %s", col_index)
    return col_index


def _is_total_row(row: List[Optional[str]], name_col_idx: int) -> bool:
    """Detect whether this row is a Total/summary row that should be skipped.

    Args:
        row: List of cell values.
        name_col_idx: Column index for the Unit Name field.

    Returns:
        ``True`` if the Unit Name cell contains "total" (case-insensitive).
    """
    if name_col_idx >= len(row):
        return False
    cell = row[name_col_idx]
    if cell is None:
        return False
    return "total" in str(cell).lower()


def _parse_numeric(value: Optional[str]) -> Optional[float]:
    """Parse a numeric string, stripping commas, whitespace, and common
    non-numeric suffixes (e.g. units appended by OCR).

    Returns an ``int`` if the value is a whole number, otherwise a ``float``.
    Returns ``None`` if the string is blank or cannot be converted.

    Args:
        value: Raw cell value such as ``'1,041'``, ``'80'``, or ``'2,144'``.

    Returns:
        Numeric value as ``int`` or ``float``, or ``None``.
    """
    if value is None:
        return None

    cleaned = re.sub(r"[,\s]", "", str(value))
    if not cleaned:
        return None

    # Strip any trailing non-numeric characters (units, percent signs, etc.)
    cleaned = re.sub(r"[^\d.\-]+$", "", cleaned)

    try:
        float_val = float(cleaned)
        # Return int if it's a whole number (cleaner output)
        if float_val == int(float_val):
            return int(float_val)
        return float_val
    except (ValueError, OverflowError):
        return None


def _parse_date(value: Optional[str]) -> Optional[date]:
    """Parse a date string in common formats to a :class:`datetime.date` object.

    Recognised formats:
      - ``M/D/YYYY``  (e.g. ``2/24/2026``)
      - ``YYYY-MM-DD`` (e.g. ``2026-02-24``)
      - ``YYYY-MM-DD HH:MM:SS`` (e.g. ``2026-02-24 0:00:00``)
      - ``MM/DD/YYYY``

    Args:
        value: Raw date cell contents.

    Returns:
        :class:`datetime.date` object, or ``None`` if the value is blank or
        cannot be parsed.
    """
    if value is None:
        return None

    stripped = str(value).strip()
    if not stripped:
        return None

    # Try ISO-style datetime first (handles "2026-02-24 0:00:00")
    iso_match = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", stripped)
    if iso_match:
        try:
            return date(
                int(iso_match.group(1)),
                int(iso_match.group(2)),
                int(iso_match.group(3)),
            )
        except ValueError:
            pass

    # Try M/D/YYYY or MM/DD/YYYY
    slash_match = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", stripped)
    if slash_match:
        try:
            return date(
                int(slash_match.group(3)),
                int(slash_match.group(1)),
                int(slash_match.group(2)),
            )
        except ValueError:
            pass

    logger.debug("Could not parse date: %r", stripped)
    return None


def _safe_cell(row: List[Optional[str]], col_idx: Optional[int]) -> Optional[str]:
    """Safely retrieve a cell value from a row by column index.

    Args:
        row: List of cell values.
        col_idx: 0-based column index; may be ``None``.

    Returns:
        Cell value as a string, or ``None`` if out of bounds or ``None``.
    """
    if col_idx is None or col_idx >= len(row):
        return None
    value = row[col_idx]
    return str(value) if value is not None else None


# Pre-build a set of numeric fields for fast O(1) membership tests
_NUMERIC_FIELD_SET = {
    'qo', 'qg', 'qw', 'qo_sep', 'qg_sep', 'qw_sep',
    'psep', 'Tsep', 'pwf', 'ptubing', 'pcasing',
    'qg_gas_lift', 'liquid_level_md', 'line_pressure',
    'choke_size', 'sand_rate', 'power_fluid_rate',
    'power_fluid_surface_pressure', 'esp_frequency',
    'days_on', 'cum_oil', 'cum_gas', 'cum_water',
}
