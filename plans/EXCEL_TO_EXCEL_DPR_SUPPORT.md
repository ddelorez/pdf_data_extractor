# Excel → Excel DPR Conversion — Implementation Plan

Status: **proposed** (2026-07-09). Adds a parallel Excel-input pipeline for partner
"Walter Oil" monthly offshore Daily Production Reports (DPR), producing/appending the
internal flat "master" workbook.

Reference material: `Reference-files/Excel-to-excel_conversions/`
- `Walter_Oil_reports-raw/` — raw monthly input (e.g. `4-April DPR EW-834 2026.xlsx`)
- `Desired-output/Master_DPR_Combined_Template 2025-26.xlsx` — accumulating target
- `Desired-output/Daily Production Template.xlsx` — single-month sample of the same shape

## Locked decisions
1. **Append to an existing master** — user uploads master + new month(s); tool returns updated master.
2. **Config/mapping-driven**, one format now (Walter Oil DPR), extensible to other partners.
3. **Full decimal precision** (match `Master_DPR_Combined`, not the rounded sample).
4. **Sentinels → blank** — any non-numeric (`S/I`, `N/A`, `NA`) in a numeric column becomes an empty cell; genuine `0` stays `0`.
5. **Newest upload wins** on `(well, date)` overlap between consecutive monthly files.

## Source format geometry (Walter Oil DPR)
Monthly workbook, ~32 sheets: ` Summary`, daily sheets named `1`–`30/31`, `Meter totals`.
**Only daily sheets feed output.** Per daily sheet (fixed coordinates):
- `E3` platform name, `N3` Report Date, **`N4` Production Date (authoritative)**
- Header row 8; well rows **11–19** (A-1..A-9), blank row 20, **21–23** (SS001-SS003); row 24 `PLATFORM SALES` (skip)
- Columns: `C` Well, `D` FTP, `E` BHP, `H` Choke#2, `I` Est Gas, `J` Est Oil, `K` Est Water

**Critical gotcha:** sheet name = *report* day; production date (N4) = day − 1; sheet `1` is
last and wraps to end-of-month. Iterate **all** digit-named sheets and key off `N4`, never the
sheet name. Consecutive monthly files therefore overlap by one production day → resolved by the
`(well, date)` dedup (newest wins).

## Target format
Sheet `Data`, long format, one row per (well, day):

`well | date | Daily Oil | Daily Gas | Daily Water | BHP | FTP | (3 blank cols) | Choke Size`

Note Gas/Oil **reorder** vs. source. Second sheet `QA Flags`: `Workbook | Sheet | Concern`.

## Mapping config (new)
Add to `src/config.py` (or a dedicated `src/config_excel_formats.py`) a declarative spec so
new partner layouts are data, not code:

```python
DPR_EXCEL_FORMATS = {
  "walter_oil_dpr": {
    "detect": {"platform_cell": "E3", "date_label_cell": "L4", "date_label": "Production Date",
               "header_row": 8, "header_signature": ["Well Number", "Choke #2", "Est Allocated Daily"]},
    "sheet_select": "digit_named",          # skip ' Summary', 'Meter totals'
    "date_cell": "N4",
    "well_row_ranges": [(11, 19), (21, 23)],
    "well_col": "C",
    "columns": {                            # output field -> source column letter
        "Daily Oil": "J", "Daily Gas": "I", "Daily Water": "K",
        "BHP": "E", "FTP": "D", "Choke Size": "H"},
    "sentinels": ["S/I", "N/A", "NA"],      # -> blank
    "output_order": ["well","date","Daily Oil","Daily Gas","Daily Water",
                     "BHP","FTP",None,None,None,"Choke Size"],
  }
}
```

## New / changed modules
1. `src/core/excel_format_detector.py` — mirror of `format_detector.py`; open with openpyxl,
   test the `detect` signature, return a format key or `UNKNOWN`.
2. `src/core/excel_dpr_extraction.py` — given workbook + format config, iterate daily sheets,
   read N4, walk well rows, apply sentinel→blank, emit records
   `{well, date, Daily Oil, Daily Gas, Daily Water, BHP, FTP, Choke Size, _sheet}`.
3. `src/output/dpr_master_writer.py` — write/append the master:
   - load uploaded master's `Data` sheet → DataFrame
   - concat new records, dedup on `(well, date)` keeping newest (incoming), sort by `date, well`
   - write `Data` (full precision) + `QA Flags`.
4. `src/data/dpr_qa.py` — QA rules:
   - **N4 sanity**: production date must fall in the workbook's month/year (derived from
     ` Summary!L4/Q4` or filename); else flag `"N4 date was <value>"`.
   - **Month-gap**: after append, list any calendar month between min and max date with no rows →
     `"No uploaded DPR workbook for <YYYY-MM>"`.
   - (optional) overlap value-conflict flag if incoming ≠ existing for same (well, date).

## Service / route / frontend wiring
- `services/extraction_service.py`
  - `submit_files` (line ~415): accept `.xlsx` (magic bytes `PK\x03\x04`) alongside `.pdf`;
    generalize `NonPdfFileError` gate (line ~445) to an allowlist; store with real extension
    (line ~463). Accept an optional **master** file input for the append target.
  - `process_job` (line ~499): branch on input type — PDF → existing path; XLSX → detect format,
    extract, append to master, write output.
- `routes/extraction.py`: `/extract` accepts xlsx; update the 418 copy; add a master-file field
  (or a second endpoint `/convert-dpr`). Keep the same job/status/download contract.
- `frontend`: allow `.xlsx` in the dropzone; add "existing master (optional)" upload; label the
  DPR flow. (Reuses existing job polling + download UI.)

## Tests (pytest, mirror `tests/backend`)
- Unit: detector (positive/negative), extractor (N4 wrap on sheet `1`, sentinel→blank, well-row
  ranges, blank row 20 skipped), master append (dedup newest-wins, sort), QA rules.
- Integration: raw `4-April DPR EW-834 2026.xlsx` → assert row count (12 wells × days),
  spot-check known values against `Desired-output`, verify overlap day dedups.
- Fixtures: copy the reference raw + a tiny synthetic master into `tests/backend/fixtures/`.
  (Reference-files/ is gitignored, so tests must not depend on it.)

## Open risks / to confirm during build
- Layout stability across months (31-day months; year-end December→January wrap; missing days).
- Multiple platforms (EW-834 only sample); well universe may differ per platform.
- Master schema drift: the sample master has literal `Unnamed: 7..10` header text in the 3 blank
  columns — decide whether to preserve or clean.
- Whether `Summary`/`Meter totals` are ever needed downstream (currently dropped).
