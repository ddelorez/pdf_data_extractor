"""Unit tests for src/core/excel_format_detector.py.

Uses synthetic workbooks (no dependency on gitignored Reference-files/).
"""

from datetime import date

import pytest

from src.core.excel_format_detector import (
    ExcelFormat,
    detect_excel_format,
    detect_dpr_format_key,
)
from tests.backend.fixtures.dpr_builder import (
    build_dpr_workbook,
    build_master_workbook,
    build_plain_workbook,
)


class TestDetectExcelFormat:
    def test_raw_dpr_detected(self, tmp_path):
        path = build_dpr_workbook(
            tmp_path / "raw.xlsx",
            {"1": date(2026, 4, 1), "2": date(2026, 4, 2)},
        )
        assert detect_excel_format(path) == ExcelFormat.DPR_RAW

    def test_master_detected(self, tmp_path):
        path = build_master_workbook(
            tmp_path / "master.xlsx",
            [{"well": "A-1", "date": date(2026, 4, 1), "Daily Oil": 100.0}],
        )
        assert detect_excel_format(path) == ExcelFormat.DPR_MASTER

    def test_unrelated_workbook_unknown(self, tmp_path):
        path = build_plain_workbook(tmp_path / "plain.xlsx")
        assert detect_excel_format(path) == ExcelFormat.UNKNOWN


class TestDetectDprFormatKey:
    def test_raw_returns_walter_oil_dpr(self, tmp_path):
        path = build_dpr_workbook(
            tmp_path / "raw.xlsx",
            {"1": date(2026, 4, 1)},
        )
        assert detect_dpr_format_key(path) == "walter_oil_dpr"

    def test_master_returns_none(self, tmp_path):
        path = build_master_workbook(
            tmp_path / "master.xlsx",
            [{"well": "A-1", "date": date(2026, 4, 1)}],
        )
        assert detect_dpr_format_key(path) is None

    def test_plain_returns_none(self, tmp_path):
        path = build_plain_workbook(tmp_path / "plain.xlsx")
        assert detect_dpr_format_key(path) is None
