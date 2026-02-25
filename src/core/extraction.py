"""
PDF text extraction and well data parsing module.
Contains logic for well name detection and production record extraction.
"""

import re
from datetime import date
from typing import Dict, List, Optional, Any

from dateutil import parser as date_parser

from src.config import (
    get_logger,
    WELL_NAME_PATTERNS,
    PRODUCTION_PATTERNS,
    DATE_PATTERN,
    DATE_BLOCK_PATTERN,
    DEFAULT_WELL_NAME,
)

logger = get_logger(__name__)


def extract_well_name(text: str) -> str:
    """
    Auto-detect well name from PDF text using multiple pattern matching strategies.
    
    Optimized for Oil & Gas naming conventions. Tries patterns in order:
    1. Explicit "Well:" or "Lease:" labels
    2. Standard O&G nomenclature (e.g., "ABC 01-23-04-18XHM")
    3. Well names in headers/titles
    
    Args:
        text: Raw text extracted from PDF
    
    Returns:
        Detected well name, or "UNKNOWN" if no match found
    
    Example:
        >>> extract_well_name("Well Name: HORIZON 10-01-15A")
        "HORIZON 10-01-15A"
    """
    for pattern in WELL_NAME_PATTERNS:
        match = re.search(pattern, text, re.M | re.I)
        if match:
            # Extract candidate and validate
            candidate = match.group(1).strip().upper()
            
            # Valid well name should contain alphanumeric and be reasonably long
            if re.search(r'\d', candidate) and len(candidate) > 8:
                logger.debug(f"Well name detected: {candidate}")
                return candidate
    
    logger.debug(f"No well name pattern matched, returning default: {DEFAULT_WELL_NAME}")
    return DEFAULT_WELL_NAME


def extract_records(text: str, well_name: str) -> List[Dict[str, Any]]:
    """
    Robust field-by-field extraction from well production data.
    
    Splits text into daily blocks and extracts:
    - Date (required)
    - Production volumes: oil (qo), gas (qg), water (qw)
    - Pressures: tubing (ptubing), casing (pcasing)
    - Operational: choke, days_on
    
    Features:
    - Multiple regex patterns with fallbacks for robustness
    - Graceful handling of missing fields (returns None for optional fields)
    - Whitespace normalization for cleaner matching
    
    Args:
        text: Raw text extracted from PDF
        well_name: Well name to associate with all records
    
    Returns:
        List of dictionaries, one per day of production data.
        Each dict contains Well, Date, qo, qg, qw, ptubing, pcasing, choke, days_on
    
    Example:
        >>> records = extract_records(pdf_text, "WELL-01")
        >>> len(records)
        45
        >>> records[0]["Date"]
        datetime.date(2024, 1, 15)
    """
    # Normalize whitespace for cleaner pattern matching
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Split into daily blocks by date pattern
    blocks = re.split(DATE_BLOCK_PATTERN, text)
    
    records = []
    
    for block in blocks:
        # Extract date
        date_match = re.search(DATE_PATTERN, block)
        if not date_match:
            continue
        
        try:
            parsed_date = date_parser.parse(date_match.group(1)).date()
        except Exception as e:
            logger.debug(f"Failed to parse date: {date_match.group(1)}, {e}")
            continue
        
        # Extract production (oil, gas, water) using multiple patterns + fallbacks
        oil = gas = water = None
        
        for pattern in PRODUCTION_PATTERNS:
            match = re.search(pattern, block, re.I)
            if match:
                try:
                    oil, gas, water = map(int, match.groups())
                    break
                except (ValueError, IndexError) as e:
                    logger.debug(f"Production pattern extracted non-numeric values: {e}")
                    continue
        
        # Skip blocks with no production data
        if oil is None and gas is None and water is None:
            continue
        
        # Extract pressures
        tubing_match = re.search(r'(?:TP|Tubing)[:\s]*(\d+)', block, re.I)
        tubing_pressure = int(tubing_match.group(1)) if tubing_match else None
        
        casing_match = re.search(r'(?:FCP|Casing)[:\s]*(\d+)', block, re.I)
        casing_pressure = int(casing_match.group(1)) if casing_match else None
        
        # Extract days on production
        days_match = re.search(r'(?:Day|Days?\s*on)[:\s]*(\d+)', block, re.I)
        days_on = int(days_match.group(1)) if days_match else None
        
        # Extract choke
        choke_match = re.search(r'(?:on|choke)[:\s]*(\d+)(?:/|\s)', block, re.I)
        choke = int(choke_match.group(1)) if choke_match else None
        
        # Build record dictionary
        record = {
            "Well": well_name,
            "Date": parsed_date,
            "qo": oil,
            "qg": gas,
            "qw": water,
            "ptubing": tubing_pressure,
            "pcasing": casing_pressure,
            "choke": choke,
            "days_on": days_on,
        }
        
        records.append(record)
        logger.debug(f"Record extracted: {record['Well']} on {record['Date']}")
    
    return records
