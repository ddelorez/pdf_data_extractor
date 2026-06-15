"""
Unit tests for flowback table parsing (src/core/flowback_extraction.py).

These drive the parsing logic with constructed 2-D tables (as pdfplumber would
return), so no real PDF is needed — exercising _process_table and its helpers.
"""

from datetime import date

import pytest

from src.core.flowback_extraction import (
    _process_table,
    _identify_header_row,
    _build_column_index,
    _is_total_row,
    _parse_numeric,
    _parse_date,
    _safe_cell,
)

# Header row using PDF column names (subset of FLOWBACK_PDF_COLUMN_MAP keys)
HEADER = [
    "Unit Name", "Date", "New Prod Oil", "New Prod Gas", "New Prod Wat",
    "Tubing", "Casing", "Days On", "Comment",
]


class TestParseNumeric:
    @pytest.mark.parametrize("raw,expected", [
        ("1,041", 1041),
        ("80", 80),
        ("2.5", 2.5),
        ("2,144", 2144),
        ("12 STB", 12),     # trailing units stripped
        ("", None),
        (None, None),
        ("abc", None),
        ("-5", -5),
    ])
    def test_parse_numeric(self, raw, expected):
        assert _parse_numeric(raw) == expected

    def test_whole_floats_return_int(self):
        assert isinstance(_parse_numeric("100.0"), int)


class TestParseDate:
    @pytest.mark.parametrize("raw,expected", [
        ("2/24/2026", date(2026, 2, 24)),
        ("02/24/2026", date(2026, 2, 24)),
        ("2026-02-24", date(2026, 2, 24)),
        ("2026-02-24 0:00:00", date(2026, 2, 24)),
        ("", None),
        (None, None),
        ("not a date", None),
        ("13/40/2026", None),   # invalid month/day
    ])
    def test_parse_date(self, raw, expected):
        assert _parse_date(raw) == expected


class TestSafeCell:
    def test_in_bounds(self):
        assert _safe_cell(["a", "b", "c"], 1) == "b"

    def test_out_of_bounds_returns_none(self):
        assert _safe_cell(["a"], 5) is None

    def test_none_index_returns_none(self):
        assert _safe_cell(["a"], None) is None

    def test_none_cell_returns_none(self):
        assert _safe_cell([None, "x"], 0) is None


class TestIsTotalRow:
    def test_detects_total(self):
        assert _is_total_row(["Total", "", ""], 0) is True

    def test_non_total(self):
        assert _is_total_row(["OMAHA 12", "", ""], 0) is False

    def test_index_out_of_range(self):
        assert _is_total_row(["x"], 5) is False


class TestIdentifyAndIndex:
    def test_identify_header_row(self):
        table = [["junk", "preamble"], HEADER, ["OMAHA", "2/24/2026"]]
        assert _identify_header_row(table) == 1

    def test_no_header_row(self):
        assert _identify_header_row([["a", "b"], ["c", "d"]]) is None

    def test_build_column_index(self):
        idx = _build_column_index(HEADER)
        assert idx["Name"] == 0
        assert idx["Date"] == 1
        assert idx["qo"] == 2
        assert idx["qg"] == 3
        assert idx["qw"] == 4
        assert idx["ptubing"] == 5
        assert idx["pcasing"] == 6
        assert idx["days_on"] == 7
        assert idx["comment"] == 8


class TestProcessTable:
    def test_extracts_records_with_aliases_and_format(self):
        table = [
            HEADER,
            ["OMAHA 12", "2/24/2026", "1,041", "5,400", "30", "2100", "3300", "28", "ok"],
        ]
        recs = _process_table(table)
        assert len(recs) == 1
        r = recs[0]
        assert r["Name"] == "OMAHA 12"
        assert r["Well"] == "OMAHA 12"           # alias
        assert r["_format"] == "tabular_flowback"
        assert r["Date"] == date(2026, 2, 24)
        assert r["qo"] == 1041
        assert r["qg"] == 5400
        assert r["days_on"] == 28
        assert r["comment"] == "ok"

    def test_date_propagation_to_blank_date_cells(self):
        table = [
            HEADER,
            ["OMAHA 12", "2/24/2026", "100", "", "", "", "", "", ""],
            ["OMAHA 12", "", "110", "", "", "", "", "", ""],   # blank date inherits
        ]
        recs = _process_table(table)
        assert len(recs) == 2
        assert recs[0]["Date"] == date(2026, 2, 24)
        assert recs[1]["Date"] == date(2026, 2, 24)

    def test_total_and_blank_rows_skipped(self):
        table = [
            HEADER,
            ["OMAHA 12", "2/24/2026", "100", "", "", "", "", "", ""],
            [None, None, None, None, None, None, None, None, None],  # blank
            ["Total", "", "200", "", "", "", "", "", ""],            # total
        ]
        recs = _process_table(table)
        assert len(recs) == 1
        assert recs[0]["Name"] == "OMAHA 12"

    def test_no_header_returns_empty(self):
        assert _process_table([["foo", "bar"], ["1", "2"]]) == []
