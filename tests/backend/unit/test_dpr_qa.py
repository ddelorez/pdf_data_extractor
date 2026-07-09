"""Unit tests for src/data/dpr_qa.py (date-sanity and month-gap QA checks)."""

from datetime import date

import pytest

from src.data.dpr_qa import check_workbook_dates, check_month_gaps
from tests.backend.fixtures.dpr_builder import build_dpr_workbook


class TestCheckWorkbookDates:
    def test_clean_workbook_no_flags(self, tmp_path):
        path = build_dpr_workbook(
            tmp_path / "dpr.xlsx",
            {"1": date(2026, 4, 30), "2": date(2026, 4, 2), "3": date(2026, 4, 3)},
        )
        assert check_workbook_dates(path) == []

    def test_out_of_month_flagged_once(self, tmp_path):
        # Two April sheets set the modal month; the December sheet is the outlier.
        path = build_dpr_workbook(
            tmp_path / "dpr.xlsx",
            {"1": date(2026, 4, 30), "2": date(2026, 4, 2), "3": date(2023, 12, 31)},
        )
        flags = check_workbook_dates(path)
        assert len(flags) == 1
        flag = flags[0]
        assert flag["Sheet"] == "3"
        assert "2023-12-31" in flag["Concern"]

    def test_source_name_used_in_workbook_column(self, tmp_path):
        path = build_dpr_workbook(
            tmp_path / "dpr.xlsx",
            {"1": date(2026, 4, 1), "2": date(2023, 12, 31)},
        )
        flags = check_workbook_dates(path, source_name="April.xlsx")
        assert flags[0]["Workbook"] == "April.xlsx"


class TestCheckMonthGaps:
    def test_gap_flagged_for_february(self):
        flags = check_month_gaps([date(2026, 1, 15), date(2026, 3, 15)])
        assert len(flags) == 1
        assert "2026-02" in flags[0]["Sheet"]
        assert "2026-02" in flags[0]["Concern"]

    def test_contiguous_months_no_gaps(self):
        flags = check_month_gaps([date(2026, 1, 15), date(2026, 2, 15)])
        assert flags == []

    def test_single_month_no_gaps(self):
        flags = check_month_gaps([date(2026, 1, 1), date(2026, 1, 28)])
        assert flags == []

    def test_empty_no_gaps(self):
        assert check_month_gaps([]) == []

    def test_source_label_used(self):
        flags = check_month_gaps(
            [date(2026, 1, 1), date(2026, 3, 1)], source_label="My Uploads"
        )
        assert flags[0]["Workbook"] == "My Uploads"
