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
    - Page-level fields: company, field, county, state, status, tvd, tmd,
      afe_num, afe_cost, cc_cost, present_op, wi, cap_budget
    
    Features:
    - Multiple regex patterns with fallbacks for robustness
    - Graceful handling of missing fields (returns None for optional fields)
    - Whitespace normalization for cleaner matching
    
    Args:
        text: Raw text extracted from PDF
        well_name: Well name to associate with all records
    
    Returns:
        List of dictionaries, one per day of production data.
        Each dict contains Well, Date, qo, qg, qw, ptubing, pcasing, choke,
        days_on, and any page-level fields successfully extracted.
    
    Example:
        >>> records = extract_records(pdf_text, "WELL-01")
        >>> len(records)
        45
        >>> records[0]["Date"]
        datetime.date(2024, 1, 15)
    """
    # Normalize whitespace for cleaner pattern matching
    text = re.sub(r'[ \t]+', ' ', text)

    # ------------------------------------------------------------------
    # Page-level field extraction (Bug 4C)
    # These fields appear once per page/report rather than per day block,
    # so we extract them from the full page text and stamp them on every
    # record produced from this page.
    # ------------------------------------------------------------------
    page_fields: Dict[str, Any] = {}

    # Company name — first line containing a legal-entity suffix
    company_match = re.search(
        r'^(.*?(?:Corp|Inc|LLC|Company|Co\.|Ltd)\.?)', text, re.I | re.M
    )
    if company_match:
        page_fields['company'] = company_match.group(1).strip()

    # Field/Formation name
    field_match = re.search(
        r'([\w\s]+(?:GENESIS|FORMATION|FIELD|UNIT))', text, re.I
    )
    if field_match:
        page_fields['field'] = field_match.group(1).strip()

    # County and State — e.g. "CARTER COUNTY, OK"
    # Use [A-Za-z ]+ to avoid matching digits or newlines from adjacent text
    county_state_match = re.search(
        r'([A-Z][A-Z ]+?)\s+COUNTY[,\s]+([A-Z]{2})\b', text, re.I
    )
    if county_state_match:
        page_fields['county'] = county_state_match.group(1).strip()
        page_fields['state'] = county_state_match.group(2).strip()

    # Well status
    status_match = re.search(
        r'\b(Active|Drilling|Completing|Shut[\s-]?in|Plugging|Testing|Flowing|Flowback)\b',
        text, re.I
    )
    if status_match:
        page_fields['status'] = status_match.group(1).strip()

    # True Vertical Depth
    tvd_match = re.search(r'TVD[:\s]*([0-9,]+)', text, re.I)
    if tvd_match:
        page_fields['tvd'] = tvd_match.group(1).replace(',', '')

    # Total Measured Depth
    tmd_match = re.search(r'TMD[:\s]*([0-9,]+)', text, re.I)
    if tmd_match:
        page_fields['tmd'] = tmd_match.group(1).replace(',', '')

    # AFE Number
    afe_match = re.search(r'AFE#?\s*:?\s*(\d+)', text, re.I)
    if afe_match:
        page_fields['afe_num'] = afe_match.group(1)

    # AFE Cost
    afe_cost_match = re.search(r'AFE\s+Cost[:\s]*\$?([\d,]+)', text, re.I)
    if afe_cost_match:
        page_fields['afe_cost'] = afe_cost_match.group(1).replace(',', '')

    # CC Cost (Cumulative Cost) — match CC: or CC(AFE):
    cc_match = re.search(r'CC(?:\(AFE\))?[:\s]*\$?([\d,]+)', text, re.I)
    if cc_match:
        page_fields['cc_cost'] = cc_match.group(1).replace(',', '')

    # Present Operation
    op_match = re.search(
        r'(?:Present\s+)?Operation[:\s]*(.+?)(?:\.|$)', text, re.I | re.M
    )
    if op_match:
        page_fields['present_op'] = op_match.group(1).strip()

    # Working Interest
    wi_match = re.search(r'(?:COG\s+)?WI[:\s]*([\d.]+)%', text, re.I)
    if wi_match:
        page_fields['wi'] = wi_match.group(1)

    # Capital Budget Number
    cap_match = re.search(r'CapBudget#?\s*:?\s*(\d+)', text, re.I)
    if cap_match:
        page_fields['cap_budget'] = cap_match.group(1)

    # ------------------------------------------------------------------
    # Split into daily blocks by date pattern
    # ------------------------------------------------------------------
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
        
        # Extract pressures — support both "TP 1192" and "1192# TP" orderings (Bug 1 & 2)
        tubing_match = re.search(
            r'(?:(?:TP|Tubing\s*(?:Pres(?:sure)?)?)[:\s]*(\d+[\d,]*)|(\d+[\d,]*)#?\s*TP\b)',
            block, re.I
        )
        if tubing_match:
            _tp_val = (tubing_match.group(1) or tubing_match.group(2)).replace(',', '')
            try:
                tubing_pressure = int(_tp_val)
            except ValueError:
                tubing_pressure = None
        else:
            tubing_pressure = None

        # CP/FCP regex: support "FCP 340", "CP 340", and "340# CP" orderings (Bug 2)
        casing_match = re.search(
            r'(?:(?:F?CP|Casing\s*(?:Pres(?:sure)?)?)[:\s]*(\d+[\d,]*)|(\d+[\d,]*)#?\s*F?CP\b)',
            block, re.I
        )
        if casing_match:
            _cp_val = (casing_match.group(1) or casing_match.group(2)).replace(',', '')
            try:
                casing_pressure = int(_cp_val)
            except ValueError:
                casing_pressure = None
        else:
            casing_pressure = None
        
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
        
        # Merge page-level fields extracted above (Bug 4C)
        record.update(page_fields)

        records.append(record)
        logger.debug(f"Record extracted: {record['Well']} on {record['Date']}")
    
    return records
