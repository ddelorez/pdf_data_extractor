"""
CSV output writer module.
Handles exporting data to CSV format.
"""

from pathlib import Path
from typing import Union, Optional

import pandas as pd

from src.config import get_logger, OUTPUT_CSV

logger = get_logger(__name__)


def write_csv(
    df: pd.DataFrame,
    output_path: Optional[Union[str, Path]] = None,
    index: bool = False,
) -> Path:
    """
    Write extracted data to CSV file.
    
    Args:
        df: Pandas DataFrame with extracted records
        output_path: Where to save CSV (default: config.OUTPUT_CSV)
        index: Whether to include row index in CSV (default: False)
    
    Returns:
        Path to written CSV file
    
    Raises:
        Exception: If CSV writing fails (e.g., permission denied)
    
    Example:
        >>> df = pd.DataFrame([
        ...     {"Well": "W-01", "Date": "2024-01-15", "qo": 100}
        ... ])
        >>> output_path = write_csv(df)
        >>> print(f"Written to {output_path}")
    """
    output_path = Path(output_path or OUTPUT_CSV)
    
    logger.info(f"Writing CSV file: {output_path.name}")
    
    try:
        # Write CSV (pandas handles various data types automatically)
        df.to_csv(output_path, index=index)
        logger.info(f"✅ CSV file written: {output_path}")
    except Exception as e:
        logger.error(f"Failed to write CSV file: {e}")
        raise
    
    return output_path


def write_csv_with_formatting(
    df: pd.DataFrame,
    output_path: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Write CSV with specific formatting:
    - Dates as ISO format strings (YYYY-MM-DD)
    - No row index
    - Standard UTF-8 encoding
    
    Args:
        df: Pandas DataFrame with extracted records
        output_path: Where to save CSV (default: config.OUTPUT_CSV)
    
    Returns:
        Path to written CSV file
    
    Example:
        >>> write_csv_with_formatting(df, "output.csv")
    """
    output_path = Path(output_path or OUTPUT_CSV)
    
    # Create a copy to avoid modifying original
    df_copy = df.copy()
    
    # Format date columns to ISO format strings
    for col in df_copy.columns:
        if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
            df_copy[col] = df_copy[col].dt.strftime("%Y-%m-%d")
    
    logger.info(f"Writing formatted CSV: {output_path.name}")
    
    try:
        df_copy.to_csv(
            output_path,
            index=False,
            encoding="utf-8",
        )
        logger.info(f"✅ CSV file written: {output_path}")
    except Exception as e:
        logger.error(f"Failed to write CSV file: {e}")
        raise
    
    return output_path
