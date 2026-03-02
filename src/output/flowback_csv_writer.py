"""
Flowback CSV output writer module.
Produces a 3-row-header CSV matching the flowback column layout (23 columns).
"""

import csv
import datetime
from pathlib import Path
from typing import Any, Dict, List, Union

from src.config import (
    get_logger,
    FLOWBACK_COL_MAP,
    FLOWBACK_HEADER_ROW_1,
    FLOWBACK_HEADER_MERGES_ROW_1,
    FLOWBACK_HEADER_ROW_2,
    FLOWBACK_HEADER_ROW_3,
    FLOWBACK_START_ROW,
)

logger = get_logger(__name__)

# Total number of columns in the flowback layout
_NUM_COLS = max(FLOWBACK_COL_MAP.values())  # 23


def write_flowback_csv(
    records: List[Dict[str, Any]],
    output_path: Union[str, Path],
) -> str:
    """
    Write flowback records to a CSV file with a 3-row header.

    Layout:
    * Row 1 — Group headers: group label written in the first column of each
      group; subsequent columns in the same group are left empty.
    * Row 2 — Field name headers (``FLOWBACK_HEADER_ROW_2``).
    * Row 3 — Unit strings (``FLOWBACK_HEADER_ROW_3``).
    * Row 4+ — One data row per record in column order per ``FLOWBACK_COL_MAP``.

    Args:
        records:     List of dicts from the flowback extractor.
                     The ``_format`` key is silently stripped before writing.
        output_path: Destination ``.csv`` file path.

    Returns:
        The resolved output path as a string.

    Raises:
        Exception: Re-raises any I/O error encountered while writing.

    Example:
        >>> records = [{"Name": "OMAHA 12", "Date": datetime.date(2024, 1, 15),
        ...             "qo": 120}]
        >>> write_flowback_csv(records, "flowback_output.csv")
        'flowback_output.csv'
    """
    output_path = Path(output_path)
    logger.info(f"Writing flowback CSV → {output_path.name} ({len(records)} records)")

    # Pre-compute the set of columns that start a merged group (row 1 labels
    # are only written in the leftmost column of each group).
    _group_label_cols = set(FLOWBACK_HEADER_ROW_1.keys())

    # Build row 1 (group labels)
    row1: List[str] = [""] * _NUM_COLS
    for col, label in FLOWBACK_HEADER_ROW_1.items():
        row1[col - 1] = label if label else ""

    # Build row 2 (field names)
    row2: List[str] = [""] * _NUM_COLS
    for col, label in FLOWBACK_HEADER_ROW_2.items():
        row2[col - 1] = label if label else ""

    # Build row 3 (units)
    row3: List[str] = [""] * _NUM_COLS
    for col, unit in FLOWBACK_HEADER_ROW_3.items():
        row3[col - 1] = unit if unit else ""

    # Reverse map: col_number (1-indexed) → field_name, for building data rows
    col_to_field: Dict[int, str] = {v: k for k, v in FLOWBACK_COL_MAP.items()}

    try:
        with open(output_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(row1)
            writer.writerow(row2)
            writer.writerow(row3)

            for record in records:
                rec = {k: v for k, v in record.items() if k != "_format"}
                data_row: List[Any] = [""] * _NUM_COLS

                for col_number in range(1, _NUM_COLS + 1):
                    field_name = col_to_field.get(col_number)
                    if field_name is None:
                        continue
                    value = rec.get(field_name)
                    if value is None:
                        continue
                    # Format date as M/D/YYYY
                    if field_name == "Date" and isinstance(
                        value, (datetime.date, datetime.datetime)
                    ):
                        value = f"{value.month}/{value.day}/{value.year}"
                    data_row[col_number - 1] = value

                writer.writerow(data_row)

        logger.info(f"✅ Flowback CSV written: {output_path}")
    except Exception as exc:
        logger.error(f"Failed to write flowback CSV: {exc}")
        raise

    return str(output_path)
