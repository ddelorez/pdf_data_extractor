"""
Centralized configuration and constants for PDF Parser Project
"""

import logging
import logging.handlers
import os
from pathlib import Path

# ========================= PATHS =========================
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_FOLDER = PROJECT_ROOT / "input_pdfs"
TEMPLATE_FILE = PROJECT_ROOT / "template.xlsx"
OUTPUT_XLSX = PROJECT_ROOT / "output.xlsx"
OUTPUT_CSV = PROJECT_ROOT / "output.csv"
LOGS_FOLDER = PROJECT_ROOT / "logs"

# Create directories if they don't exist
INPUT_FOLDER.mkdir(exist_ok=True)
LOGS_FOLDER.mkdir(exist_ok=True)

# ========================= EXCEL TEMPLATE =========================
# Row where data starts (1-indexed)
START_ROW = 4

# Column mapping for data fields
# Maps field names to Excel column numbers (1-indexed)
COL_MAP = {
    'Well': 1,         # A - Well Name
    'Date': 2,         # B - Date
    'qo': 3,           # C - Oil (BO)
    'qg': 4,           # D - Gas (mcf)
    'qw': 5,           # E - Water (BW)
    'ptubing': 6,      # F - Tubing Pressure
    'pcasing': 7,      # G - Casing Pressure
    'choke': 8,        # H - Choke
    'days_on': 9,      # I - Days On
    'company': 10,     # J - Company
    'field': 11,       # K - Field/Formation
    'county': 12,      # L - County
    'state': 13,       # M - State
    'status': 14,      # N - Status (Active/Drilling/etc)
    'tvd': 15,         # O - True Vertical Depth
    'tmd': 16,         # P - Total Measured Depth
    'afe_num': 17,     # Q - AFE Number
    'afe_cost': 18,    # R - AFE Cost
    'cc_cost': 19,     # S - CC Cost (Cumulative)
    'present_op': 20,  # T - Present Operation
    'wi': 21,          # U - Working Interest %
    'cap_budget': 22,  # V - Capital Budget Number
}

# ========================= LOGGING SETUP =========================
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOGS_FOLDER / "pdf_parser.log"
_log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
LOG_LEVEL = getattr(logging, _log_level_str, logging.INFO)

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(LOG_LEVEL)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(LOG_LEVEL)
        console_formatter = logging.Formatter(LOG_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler (WatchedFileHandler reopens after logrotate renames the file)
        # Wrapped in try/except to gracefully handle permission errors when the
        # logs directory is bind-mounted read-only (e.g., in Docker CI environments)
        try:
            file_handler = logging.handlers.WatchedFileHandler(LOG_FILE)
            file_handler.setLevel(LOG_LEVEL)
            file_formatter = logging.Formatter(LOG_FORMAT)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except (PermissionError, OSError):
            # Fall back to console-only logging if file handler cannot be created
            pass
    
    return logger

# ========================= EXTRACTION PATTERNS =========================
# Regular expression patterns for well name detection
WELL_NAME_PATTERNS = [
    r'(?i)(?:well|lease|name)[:\s-]*( [A-Z0-9\s\-]{8,40} )',
    r'\b([A-Z]{3,}\s+\d{1,2}-\d{1,2}-\d{1,2}-\d{1,2}[A-Z0-9XHM]*)\b',
    r'^([A-Z0-9\s\-]{10,40})\s*(?:daily|production|report|day)',
]

# Regular expression patterns for production data extraction
# All patterns accept both ',' and '&' as field separators to handle
# formats like "141 BO, 6023 mcf & 1230 BW" (value & value) or
# "141 BO, 6023 mcf, 1230 BW" (comma-separated).
PRODUCTION_PATTERNS = [
    r'(?:Produced|Oil|BO)[:\s]*(\d+).*?(?:Gas|MCF|mcf)[:\s]*(\d+).*?(?:Water|BW)[:\s]*(\d+)',
    r'Produced\s+(\d+)\s+BO[,&\s]+(\d+)\s+mcfpd?.*?(\d+)\s+BW',
    r'(\d+)\s+BO[,&\s]+(\d+)\s+mcf[,&\s]+(\d+)\s+BW',
    r'(\d+)\s*BO.*?(\d+)\s*(?:mcf|MCF).*?(\d+)\s*BW',
]

# Date block splitting pattern
DATE_BLOCK_PATTERN = r'(?=(?:^|\n)\s*\d{1,2}[/-]\d{1,2}[/-]\d{4})'

# Date detection pattern
DATE_PATTERN = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b'

# ========================= DEFAULT VALUES =========================
DEFAULT_WELL_NAME = "UNKNOWN"
DEFAULT_TIMEOUT = int(os.environ.get('DEFAULT_TIMEOUT', '30'))  # seconds for PDF processing

# ========================= DATAFRAME FIELDS =========================
# Expected columns in extracted data
EXPECTED_FIELDS = [
    'Well',
    'Date',
    'qo',          # oil production
    'qg',          # gas production
    'qw',          # water production
    'ptubing',     # tubing pressure
    'pcasing',     # casing pressure
    'choke',       # choke size
    'days_on',     # days on production
    'company',     # operator/company name
    'field',       # field or formation name
    'county',      # county
    'state',       # state (2-letter code)
    'status',      # well status (Active/Drilling/etc)
    'tvd',         # true vertical depth
    'tmd',         # total measured depth
    'afe_num',     # AFE number
    'afe_cost',    # AFE cost
    'cc_cost',     # cumulative cost (CC)
    'present_op',  # present operation description
    'wi',          # working interest percentage
    'cap_budget',  # capital budget number
]

# Fields that should not be None for a valid record
REQUIRED_FIELDS = ["Well", "Date"]

# Numeric fields that should be converted to integers
NUMERIC_FIELDS = ["qo", "qg", "qw", "ptubing", "pcasing", "choke", "days_on"]

# ========================= FLOWBACK FORMAT CONFIG =========================

# PDFFormat enum is defined in src/core/format_detector.py but we store
# format-specific column maps and field lists here for central config.

FLOWBACK_COL_MAP = {
    'Name': 1,                           # A — Well/Unit Name
    'Date': 2,                           # B — Date
    'qo': 3,                             # C — Stock Tank Oil (STB/d)
    'qg': 4,                             # D — Stock Tank Gas (Mscf/d)
    'qw': 5,                             # E — Stock Tank Water (STB/d)
    'qo_sep': 6,                         # F — Separator Oil
    'qg_sep': 7,                         # G — Separator Gas
    'qw_sep': 8,                         # H — Separator Water
    'psep': 9,                           # I — Separator Pressure
    'Tsep': 10,                          # J — Separator Temperature
    'pwf': 11,                           # K — BHP / ESP Pump Intake
    'ptubing': 12,                       # L — Tubing Pressure
    'pcasing': 13,                       # M — Casing Pressure
    'qg_gas_lift': 14,                   # N — Gas Lift Injection
    'liquid_level_md': 15,               # O — Liquid Level MD
    'line_pressure': 16,                 # P — Line Pressure
    'choke_size': 17,                    # Q — Choke Size (1/64")
    'sand_rate': 18,                     # R — Sand Rate
    'power_fluid_rate': 19,              # S — Power Fluid Rate
    'power_fluid_surface_pressure': 20,  # T — Power Fluid Surface Pressure
    'esp_frequency': 21,                 # U — ESP Frequency (Hz)
    'days_on': 22,                       # V — Days On
    'comment': 23,                       # W — Comment
}

# 3-row header structure for flowback Excel output
# Row 1: Group headers (merged cells span multiple columns)
FLOWBACK_HEADER_ROW_1 = {
    1:  'Well',
    2:  'Time',
    3:  'Stock Tank Rates',                          # spans cols 3-5
    6:  'Separator Rates and Conditions',            # spans cols 6-10
    11: 'Measured Pressures and Gas-Lift Rates',     # spans cols 11-18
    19: 'BHP Jet Pump',                              # spans cols 19-20
    21: '',                                          # ESP Frequency — no group
    22: '',                                          # Days On — no group
    23: '',                                          # Comment — no group
}

# Row 1 merge ranges: (start_col, end_col) for merged group headers (1-indexed)
FLOWBACK_HEADER_MERGES_ROW_1 = [
    (3, 5),    # Stock Tank Rates: C-E
    (6, 10),   # Separator Rates and Conditions: F-J
    (11, 18),  # Measured Pressures and Gas-Lift Rates: K-R
    (19, 20),  # BHP Jet Pump: S-T
]

# Row 2: Field name headers (1-indexed column → display name)
FLOWBACK_HEADER_ROW_2 = {
    1:  'Name',
    2:  'Date',
    3:  'qo',
    4:  'qg',
    5:  'qw',
    6:  'qo,sep',
    7:  'qg,sep',
    8:  'qw,sep',
    9:  'psep',
    10: 'Tsep',
    11: 'pwf',
    12: 'ptubing',
    13: 'pcasing',
    14: 'qg,gas lift',
    15: 'Liquid Level MD',
    16: 'Line Pressure',
    17: 'Choke Size',
    18: 'Sand Rate',
    19: 'Power Fluid Rate',
    20: 'Power Fluid Surface Pressure',
    21: 'ESP Frequency',
    22: 'Days On',
    23: 'Comment',
}

# Row 3: Units (1-indexed column → unit string)
FLOWBACK_HEADER_ROW_3 = {
    1:  '-',
    2:  '-',
    3:  'STB/d',
    4:  'Mscf/d',
    5:  'STB/d',
    6:  'sep-bbl/d',
    7:  'Mscf/d',
    8:  'sep-bbl/d',
    9:  'psia',
    10: 'F',
    11: 'psia',
    12: 'psia',
    13: 'psia',
    14: 'Mscf/d',
    15: 'ft',
    16: 'psia',
    17: 'in/64',
    18: 'lbm/d',
    19: 'STB/d',
    20: 'psia',
    21: 'Hz',
    22: '#',
    23: 'Text',
}

# Data starts at row 4 (rows 1-3 are the 3-row header)
FLOWBACK_START_ROW = 4

# Expected fields in flowback records (matches FLOWBACK_COL_MAP keys)
FLOWBACK_EXPECTED_FIELDS = [
    'Name',
    'Date',
    'qo',
    'qg',
    'qw',
    'qo_sep',
    'qg_sep',
    'qw_sep',
    'psep',
    'Tsep',
    'pwf',
    'ptubing',
    'pcasing',
    'qg_gas_lift',
    'liquid_level_md',
    'line_pressure',
    'choke_size',
    'sand_rate',
    'power_fluid_rate',
    'power_fluid_surface_pressure',
    'esp_frequency',
    'days_on',
    'comment',
]

# Required fields for flowback validation
FLOWBACK_REQUIRED_FIELDS = ['Name', 'Date']

# Numeric fields for flowback records
FLOWBACK_NUMERIC_FIELDS = [
    'qo', 'qg', 'qw', 'ptubing', 'pcasing',
    'pwf', 'qg_gas_lift', 'choke_size', 'esp_frequency', 'days_on',
]

# Mapping from PDF table header text to internal record dict keys.
# A value of None means the column is parsed but not written to output.
FLOWBACK_PDF_COLUMN_MAP = {
    'Date': 'Date',
    'Unit Name': 'Name',
    'Days On': 'days_on',
    'Prod Method': None,           # informational only
    'New Prod Oil': 'qo',          # bbl/d → STB/d
    'New Prod Gas': 'qg',          # MCF/d → Mscf/d
    'New Prod Wat': 'qw',          # bbl/d → STB/d
    'Cum. Oil': 'cum_oil',         # cumulative — stored but not in primary output
    'Cum. Gas': 'cum_gas',         # cumulative — stored but not in primary output
    'Cum. Water': 'cum_water',     # cumulative — stored but not in primary output
    'Tubing': 'ptubing',           # psi
    'Casing': 'pcasing',           # psi
    'ESP Pump Intake': 'pwf',      # psi
    'ESP Speed': 'esp_frequency',  # Hz
    'Gas Lift Inj': 'qg_gas_lift', # MCF/d
    'Tubing Choke': 'choke_size',  # 1/64"
    'Down Time': None,             # not mapped to output
    'Down Reason': None,           # not mapped to output
    'Comment': 'comment',
}

# Header keywords used for flowback format detection (see format_detector.py)
FLOWBACK_HEADER_KEYWORDS = [
    'Unit Name',
    'New Prod Oil',
    'New Prod Gas',
    'Cum. Oil',
    'ESP Pump Intake',
    'Gas Lift Inj',
    'Tubing Choke',
]


def get_format_config(format_type: str) -> dict:
    """Return the column map, expected fields, required fields, numeric fields,
    and start row for the given format type.

    Args:
        format_type: ``'narrative_sor'`` or ``'tabular_flowback'``

    Returns:
        Dict with keys: ``col_map``, ``expected_fields``, ``required_fields``,
        ``numeric_fields``, ``start_row``

    Raises:
        ValueError: If *format_type* is not recognised.
    """
    if format_type == 'tabular_flowback':
        return {
            'col_map': FLOWBACK_COL_MAP,
            'expected_fields': FLOWBACK_EXPECTED_FIELDS,
            'required_fields': FLOWBACK_REQUIRED_FIELDS,
            'numeric_fields': FLOWBACK_NUMERIC_FIELDS,
            'start_row': FLOWBACK_START_ROW,
        }
    elif format_type == 'narrative_sor':
        return {
            'col_map': COL_MAP,
            'expected_fields': EXPECTED_FIELDS,
            'required_fields': REQUIRED_FIELDS,
            'numeric_fields': NUMERIC_FIELDS,
            'start_row': START_ROW,
        }
    else:
        raise ValueError(f"Unknown format type: {format_type!r}")
