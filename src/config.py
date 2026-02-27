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
