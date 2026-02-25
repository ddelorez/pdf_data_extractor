# PDF Parser Project - Phase 3 Complete

Oil & Gas PDF Data Extractor with Hybrid (Flask + React) Deployment Architecture

**Current Phase**: Phase 3 - React Frontend & Integration Complete  
**Status**: ✅ Phase 1-3 Complete | Ready for Production Deployment

---

## Project Overview

This project extracts production data from Oil & Gas well PDFs and outputs clean Excel and CSV files. Phase 1 establishes the core extraction engine as independent, modular, and testable components that can be integrated with Flask/React GUI in later phases.

### Architecture Highlights

- **Modular Design**: Separation of concerns (extraction, validation, output)
- **CLI Compatible**: Backward-compatible command-line interface
- **Reusable Core**: Core extraction engine independent of GUI layer
- **Docker Ready**: Structured for containerized deployment
- **Well-Designed**: Clean interfaces for future Flask backend integration

---

## Project Structure

```
pdf-parser-project/
├── src/                          # Main source code
│   ├── config.py                 # Centralized configuration
│   ├── core/
│   │   ├── extraction.py         # Well name & record extraction
│   │   └── pdf_processor.py      # PDF processing pipeline
│   ├── data/
│   │   ├── validator.py          # Data validation
│   │   └── deduplicator.py       # Dedup & sorting
│   └── output/
│       ├── excel_writer.py       # Excel template filling
│       └── csv_writer.py         # CSV export
├── cli.py                        # Command-line interface
├── requirements.txt              # Python dependencies
├── input_pdfs/                   # Input PDF directory
├── logs/                         # Application logs (created at runtime)
└── README.md                     # This file
```

---

## Quick Start

### 1. Installation

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Prepare Input

Place PDF files in the `input_pdfs/` directory:

```bash
mkdir input_pdfs
# Copy your well data PDFs here
```

### 3. Create Template (if using Excel output)

Place `template.xlsx` in the project root. The template should have:
- Column headers matching the extraction schema
- Starting data row at row 4 (configurable in `src/config.py`)

### 4. Run Extraction

```bash
# Using default paths
python cli.py

# Custom paths
python cli.py --input ./my_pdfs --output results.xlsx --csv results.csv

# Show help
python cli.py --help
```

### Output

- `output.xlsx` - Extracted data in Excel (requires template)
- `output.csv` - Extracted data in CSV format
- `logs/pdf_parser.log` - Processing details and errors

---

## Module Reference

### `src/config.py`

Centralized configuration including:
- File paths (input, template, output)
- Excel column mapping (`COL_MAP`)
- Regular expression patterns for extraction
- Logging setup

**Key Constants:**
- `START_ROW` - Excel row where data starts (default: 4)
- `COL_MAP` - Field to column mappings

### `src/core/extraction.py`

Well name and production record extraction:

**Functions:**
- `extract_well_name(text)` - Detects well name from PDF text
- `extract_records(text, well_name)` - Extracts daily production records

**Supported Fields:**
- Well, Date, qo (oil), qg (gas), qw (water)
- ptubing, pcasing (pressures), choke, days_on

### `src/core/pdf_processor.py`

PDF processing orchestration:

**Functions:**
- `process_pdf(pdf_path)` - Main entry point for single PDF processing

### `src/data/validator.py`

Data validation and quality checks:

**Functions:**
- `validate_record(record)` - Validates single record
- `validate_records(records)` - Batch validation
- `check_record_completeness(record)` - Quality metrics

### `src/data/deduplicator.py`

Deduplication and sorting:

**Functions:**
- `deduplicate_and_sort(records)` - Removes duplicates, sorts by well+date
- `deduplicate_by_well_date(records)` - Less strict dedup (well+date only)

### `src/output/excel_writer.py`

Excel template filling:

**Functions:**
- `write_excel(df, template, output_path)` - Fills template with data
- `get_excel_summary(df)` - Calculates production statistics

### `src/output/csv_writer.py`

CSV export:

**Functions:**
- `write_csv(df, output_path)` - Basic CSV export
- `write_csv_with_formatting(df, output_path)` - Formatted CSV (ISO dates)

---

## Configuration

Edit `src/config.py` to customize:

```python
# File paths
INPUT_FOLDER = "input_pdfs"
TEMPLATE_FILE = "template.xlsx"
OUTPUT_XLSX = "output.xlsx"
OUTPUT_CSV = "output.csv"

# Excel configuration
START_ROW = 4  # Where to start writing data
COL_MAP = {    # Field to column mapping
    "Well": 1,
    "Date": 2,
    "qo": 3,
    # ... etc
}

# Logging
LOG_LEVEL = logging.INFO
```

---

## Using as a Library

Import and use the modular components in your Flask backend:

```python
from pathlib import Path
from src.core.pdf_processor import process_pdf
from src.data.deduplicator import deduplicate_and_sort
from src.output.excel_writer import write_excel

# Process a PDF
records = process_pdf(Path("my_file.pdf"))

# Clean and organize
df = deduplicate_and_sort(records)

# Export to Excel
output_path = write_excel(df, "template.xlsx", "output.xlsx")
```

---

## Logging

Application logs are written to:
- **Console**: INFO level and above
- **File**: `logs/pdf_parser.log` with DEBUG level

View logs while running or check the log file for detailed debugging.

---

## Error Handling

The system is designed to:
- Continue processing even if one PDF fails
- Report skipped records and reasons
- Preserve all valid data
- Provide detailed logging for troubleshooting

Common issues:
- **"Template file not found"** - Create/place `template.xlsx` in project root
- **"No PDF files found"** - Ensure PDFs are in `input_pdfs/` folder
- **"No records extracted"** - Verify PDF matches expected well report format

---

## Phase Completion Status

- ✅ **Phase 1**: Core extraction engine with CLI
- ✅ **Phase 2**: Flask backend API with Docker
- ✅ **Phase 3**: React frontend with Vite and Nginx reverse proxy
- 🎯 **Phase 4+**: Advanced features (Auth, Database, Advanced Reporting)

### Phase 3 Integration
The complete frontend-to-backend integration is now ready:
- React frontend with drag-and-drop file upload
- Real-time processing status via polling
- File download (Excel/CSV) functionality
- Professional responsive UI with dark mode support
- Full Docker stack with docker-compose

See [PHASE_3_IMPLEMENTATION.md](PHASE_3_IMPLEMENTATION.md) for complete Phase 3 details.

---

## Development Notes

### Extending the Extraction

To add support for additional PDF formats or fields:

1. Add patterns to `PRODUCTION_PATTERNS` or `WELL_NAME_PATTERNS` in `src/config.py`
2. Update `extract_records()` in `src/core/extraction.py`
3. Add field to `COL_MAP` and `EXPECTED_FIELDS`
4. Update `src/data/validator.py` for new fields
5. Update Excel template with new columns

### Adding Validators

Create custom validation rules in `src/data/validator.py`:

```python
def validate_custom_field(value):
    """Your custom validation logic"""
    if not is_valid(value):
        return False, "Error message"
    return True, None
```

---

## Troubleshooting

**Q: "Import error" when running cli.py?**  
A: Ensure you're running from the project root and have installed `requirements.txt`

**Q: No output files created?**  
A: Check logs in `logs/pdf_parser.log` for detailed error information

**Q: Excel output looks wrong?**  
A: Verify `template.xlsx` exists and `COL_MAP` matches your template columns

---

## Version

- **Project Version**: 2.0.0
- **Phase**: 3 (React Frontend Complete)
- **Release Date**: 2026-02-25
- **Status**: Production Ready

---

## Complete Architecture (Phases 1-3)

```
Phase 1: Core Engine (✅ COMPLETE)
├─ Modular extraction
├─ CLI interface
└─ File I/O

Phase 2: Flask Backend (✅ COMPLETE)
├─ REST API endpoints
├─ File upload/download
├─ Background task queue
└─ Docker containerization

Phase 3: React Frontend (✅ COMPLETE)
├─ Drag-and-drop file upload
├─ Real-time processing status
├─ File downloads (Excel/CSV)
├─ Responsive design & dark mode
└─ Full Docker stack

Phase 4: Advanced Features (→ Future)
├─ User authentication
├─ Multi-user support
├─ Job history & database
├─ Advanced reporting
└─ CI/CD pipeline
```

### Current System Architecture
```
┌─────────────────────────────────────────────────────┐
│          User Browser (http://localhost:3000)       │
├─────────────────────────────────────────────────────┤
│                                                       │
│  React Application (Vite)                           │
│  ├─ FileUpload Component                            │
│  ├─ ProcessingStatus Component                      │
│  ├─ ResultsViewer Component                         │
│  └─ ErrorNotification Component                     │
│                                                       │
├─────────────────────────────────────────────────────┤
│                  Nginx (Port 3000)                   │
│  ├─ Serves React static files                       │
│  └─ Proxies API requests to backend                 │
├─────────────────────────────────────────────────────┤
│                                                       │
│  Flask Backend (Internal Port 5000)                 │
│  ├─ /api/extract - File upload                      │
│  ├─ /api/process/{job_id} - Process files           │
│  ├─ /api/status/{job_id} - Job status               │
│  ├─ /download/{job_id}/output.xlsx - Download      │
│  └─ /download/{job_id}/output.csv - Download       │
│                                                       │
│  Processing Pipeline                                │
│  ├─ Phase 1 Core: PDF extraction                    │
│  ├─ Data validation & deduplication                 │
│  └─ Excel/CSV output generation                     │
│                                                       │
└─────────────────────────────────────────────────────┘

Docker Compose Stack:
├─ frontend (nginx + react static files)
├─ backend (flask api + core engine)
└─ Network: pdf-extractor-network
```

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in `logs/pdf_parser.log`
3. Verify configuration in `src/config.py`
4. Check if sample PDFs match expected format

---

**This Phase 1 foundation is ready for integration with Flask backend and React frontend.**
