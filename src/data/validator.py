"""
Data validation module for extracted production records.
"""

from typing import Dict, Any, List, Tuple
from datetime import date

from src.config import (
    get_logger,
    EXPECTED_FIELDS,
    REQUIRED_FIELDS,
    NUMERIC_FIELDS,
)

logger = get_logger(__name__)


def validate_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single production record.
    
    Checks:
    - All required fields present and not None
    - Data types are appropriate (dates as date objects, numbers as int)
    - No obviously invalid values
    
    Args:
        record: Dictionary containing well data
    
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
        - If valid: (True, [])
        - If invalid: (False, ["error1", "error2", ...])
    
    Example:
        >>> record = {
        ...     "Well": "WELL-01",
        ...     "Date": date(2024, 1, 15),
        ...     "qo": 100,
        ...     "qg": 5000,
        ...     "qw": 50,
        ... }
        >>> is_valid, errors = validate_record(record)
        >>> is_valid
        True
    """
    errors = []
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"Missing required field: {field}")
        elif record[field] is None:
            errors.append(f"Required field is None: {field}")
    
    # Check data types
    if "Date" in record and record["Date"] is not None:
        if not isinstance(record["Date"], date):
            errors.append(f"Date field is not a date object: {type(record['Date'])}")
    
    # Check numeric fields are integers or None
    for field in NUMERIC_FIELDS:
        if field in record and record[field] is not None:
            if not isinstance(record[field], int):
                errors.append(f"Numeric field {field} is not int: {type(record[field])}")
    
    # Check for unreasonable values (optional sanity checks)
    if "qo" in record and record["qo"] is not None and record["qo"] < 0:
        errors.append("Oil production (qo) cannot be negative")
    
    if "qg" in record and record["qg"] is not None and record["qg"] < 0:
        errors.append("Gas production (qg) cannot be negative")
    
    if "qw" in record and record["qw"] is not None and record["qw"] < 0:
        errors.append("Water production (qw) cannot be negative")
    
    is_valid = len(errors) == 0
    
    if not is_valid:
        logger.warning(f"Record validation failed: {errors}")
    
    return is_valid, errors


def validate_records(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validate a batch of production records.
    
    Separates valid records from invalid ones.
    
    Args:
        records: List of record dictionaries
    
    Returns:
        Tuple of (valid_records, invalid_records)
    
    Example:
        >>> valid, invalid = validate_records(raw_records)
        >>> print(f"Valid: {len(valid)}, Invalid: {len(invalid)}")
    """
    valid_records = []
    invalid_records = []
    
    for record in records:
        is_valid, errors = validate_record(record)
        
        if is_valid:
            valid_records.append(record)
        else:
            invalid_record = record.copy()
            invalid_record["_validation_errors"] = errors
            invalid_records.append(invalid_record)
    
    if invalid_records:
        logger.warning(f"Filtered out {len(invalid_records)} invalid records")
    
    return valid_records, invalid_records


def check_record_completeness(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate completeness of a record (what percentage of fields are populated).
    
    Useful for quality assessment and logging.
    
    Args:
        record: Record dictionary
    
    Returns:
        Dictionary with completeness metrics:
        {
            "total_fields": int,
            "populated_fields": int,
            "completeness_percent": float,
            "missing_fields": List[str]
        }
    
    Example:
        >>> completeness = check_record_completeness(record)
        >>> completeness["completeness_percent"]
        78.5
    """
    total_fields = len(EXPECTED_FIELDS)
    populated_fields = sum(
        1 for field in EXPECTED_FIELDS if field in record and record[field] is not None
    )
    missing_fields = [
        field for field in EXPECTED_FIELDS if field not in record or record[field] is None
    ]
    
    completeness_percent = (populated_fields / total_fields * 100) if total_fields > 0 else 0
    
    return {
        "total_fields": total_fields,
        "populated_fields": populated_fields,
        "completeness_percent": completeness_percent,
        "missing_fields": missing_fields,
    }
