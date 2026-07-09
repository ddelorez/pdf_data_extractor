"""Unit tests for src/core/excel_dpr_extraction.py.

Drives the coordinate-based extractor against synthetic Walter Oil workbooks.
"""

from datetime import date

import pytest
from openpyxl import load_workbook

from src.core.excel_dpr_extraction import extract_dpr_records
from tests.backend.fixtures.dpr_builder import build_dpr_workbook, DEFAULT_WELLS


# 15 significant digits: survives Excel's float storage exactly, so this proves
# the extractor does not round values (a rounded value would be e.g. 2041.95).
PRECISE_OIL = 2041.95062750134


def _records_by_sheet(records, sheet):
    return [r for r in records if r["_sheet"] == sheet]


def _find(records, sheet, well):
    for r in records:
        if r["_sheet"] == sheet and r["well"] == well:
            return r
    raise AssertionError(f"no record for sheet={sheet} well={well}")


class TestExtractDprRecords:
    def test_record_count(self, tmp_path):
        # 2 daily sheets * 12 wells = 24, minus one blank well per sheet = 22.
        path = build_dpr_workbook(
            tmp_path / "dpr.xlsx",
            {"1": date(2026, 4, 30), "2": date(2026, 4, 2)},
            blank_wells=["SS003"],
        )
        records = extract_dpr_records(path)
        assert len(records) == 2 * (len(DEFAULT_WELLS) - 1)

    def test_date_comes_from_n4_not_sheet_name(self, tmp_path):
        # Sheet "1" holds a *later* N4 (month wrap) than sheet "2".
        path = build_dpr_workbook(
            tmp_path / "dpr.xlsx",
            {"1": date(2026, 4, 30), "2": date(2026, 4, 2)},
        )
        records = extract_dpr_records(path)
        for r in _records_by_sheet(records, "1"):
            assert r["date"] == date(2026, 4, 30)
        for r in _records_by_sheet(records, "2"):
            assert r["date"] == date(2026, 4, 2)

    def test_sentinels_become_none(self, tmp_path):
        path = build_dpr_workbook(
            tmp_path / "dpr.xlsx",
            {"2": date(2026, 4, 2)},
            values={"2": {"A-2": {"BHP": "S/I", "FTP": "NA", "Choke Size": "N/A"}}},
        )
        records = extract_dpr_records(path)
        r = _find(records, "2", "A-2")
        assert r["BHP"] is None
        assert r["FTP"] is None
        assert r["Choke Size"] is None

    def test_genuine_zero_preserved(self, tmp_path):
        path = build_dpr_workbook(
            tmp_path / "dpr.xlsx",
            {"2": date(2026, 4, 2)},
            values={"2": {"A-3": {"Daily Water": 0}}},
        )
        records = extract_dpr_records(path)
        r = _find(records, "2", "A-3")
        assert r["Daily Water"] == 0.0
        assert r["Daily Water"] is not None

    def test_full_precision_preserved(self, tmp_path):
        path = build_dpr_workbook(
            tmp_path / "dpr.xlsx",
            {"2": date(2026, 4, 2)},
            values={"2": {"A-1": {"Daily Oil": PRECISE_OIL}}},
        )
        records = extract_dpr_records(path)
        r = _find(records, "2", "A-1")
        assert r["Daily Oil"] == PRECISE_OIL

    def test_summary_and_meter_sheets_ignored(self, tmp_path):
        path = build_dpr_workbook(
            tmp_path / "dpr.xlsx",
            {"1": date(2026, 4, 1)},
        )
        records = extract_dpr_records(path)
        assert records  # sanity
        # Only integer-named daily sheets should appear as a source.
        assert all(r["_sheet"].isdigit() for r in records)
        assert not any(r["_sheet"] in {"Summary", "Meter totals"} for r in records)

    def test_blank_gap_row_20_skipped(self, tmp_path):
        path = build_dpr_workbook(
            tmp_path / "dpr.xlsx",
            {"2": date(2026, 4, 2)},
        )
        # Plant a stray value in the gap row (row 20, col C) that must be ignored.
        wb = load_workbook(path)
        wb["2"]["C20"] = "GAP-WELL"
        wb.save(path)

        records = extract_dpr_records(path)
        assert not any(r["well"] == "GAP-WELL" for r in records)

    def test_source_defaults_to_filename(self, tmp_path):
        path = build_dpr_workbook(
            tmp_path / "dpr.xlsx",
            {"2": date(2026, 4, 2)},
        )
        records = extract_dpr_records(path)
        assert all(r["_source"] == "dpr.xlsx" for r in records)

    def test_unknown_format_key_raises(self, tmp_path):
        path = build_dpr_workbook(
            tmp_path / "dpr.xlsx",
            {"2": date(2026, 4, 2)},
        )
        with pytest.raises(ValueError):
            extract_dpr_records(path, format_key="nope")
