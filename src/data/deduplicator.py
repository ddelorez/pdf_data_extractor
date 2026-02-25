"""
Data deduplication and sorting module.
"""

from typing import List, Dict, Any

import pandas as pd

from src.config import get_logger

logger = get_logger(__name__)


def deduplicate_and_sort(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert records to DataFrame, deduplicate, and sort by well and date.
    
    Deduplication strategy:
    - Removes exact duplicates (same well, date, and all values)
    - Keeps first occurrence if duplicates exist
    - Logs number of duplicates removed
    
    Sorting strategy:
    - Primary: Well name (alphabetical)
    - Secondary: Date (chronological, oldest first)
    
    Args:
        records: List of record dictionaries from extraction
    
    Returns:
        Clean pandas DataFrame sorted by well and date
    
    Example:
        >>> records = [
        ...     {"Well": "W-01", "Date": date(2024, 1, 15), "qo": 100},
        ...     {"Well": "W-01", "Date": date(2024, 1, 15), "qo": 100},  # duplicate
        ...     {"Well": "W-01", "Date": date(2024, 1, 14), "qo": 105},
        ... ]
        >>> df = deduplicate_and_sort(records)
        >>> len(df)
        2
    """
    if not records:
        logger.warning("No records to deduplicate")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(records)
    
    initial_count = len(df)
    logger.info(f"Starting with {initial_count} records")
    
    # Remove duplicate rows (all columns must match)
    df = df.drop_duplicates(subset=None, keep='first')
    duplicates_removed = initial_count - len(df)
    
    if duplicates_removed > 0:
        logger.info(f"Removed {duplicates_removed} duplicate records")
    
    # Sort by Well (ascending alphabetical) then Date (ascending chronological)
    df = df.sort_values(by=['Well', 'Date'], ascending=[True, True])
    
    logger.info(f"Final deduplicated records: {len(df)}")
    logger.info(f"Unique wells: {df['Well'].nunique()}")
    
    return df.reset_index(drop=True)


def deduplicate_by_well_date(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Deduplicate by well and date (less strict than full record dedup).
    
    Removes rows where the combination of Well + Date is duplicated.
    Keeps first occurrence. Useful if same well has multiple readings per day
    and you want only one entry per well per day.
    
    Args:
        records: List of record dictionaries
    
    Returns:
        Deduplicated DataFrame by well and date
    
    Example:
        >>> records = [
        ...     {"Well": "W-01", "Date": date(2024, 1, 15), "qo": 100},
        ...     {"Well": "W-01", "Date": date(2024, 1, 15), "qo": 102},  # same day
        ... ]
        >>> df = deduplicate_by_well_date(records)
        >>> len(df)
        1
    """
    if not records:
        logger.warning("No records to deduplicate")
        return pd.DataFrame()
    
    df = pd.DataFrame(records)
    initial_count = len(df)
    
    # Remove duplicates by well + date combination
    df = df.drop_duplicates(subset=['Well', 'Date'], keep='first')
    duplicates_removed = initial_count - len(df)
    
    if duplicates_removed > 0:
        logger.info(f"Removed {duplicates_removed} records with duplicate Well+Date")
    
    # Sort
    df = df.sort_values(by=['Well', 'Date'], ascending=[True, True])
    
    return df.reset_index(drop=True)


def get_deduplication_stats(original_count: int, final_count: int) -> Dict[str, Any]:
    """
    Calculate deduplication statistics.
    
    Args:
        original_count: Number of records before deduplication
        final_count: Number of records after deduplication
    
    Returns:
        Dictionary with statistics
    
    Example:
        >>> stats = get_deduplication_stats(100, 95)
        >>> stats["duplicates_found"]
        5
        >>> stats["percent_removed"]
        5.0
    """
    duplicates_found = original_count - final_count
    percent_removed = (duplicates_found / original_count * 100) if original_count > 0 else 0
    
    return {
        "original_count": original_count,
        "final_count": final_count,
        "duplicates_found": duplicates_found,
        "percent_removed": percent_removed,
        "percent_retained": 100 - percent_removed,
    }
