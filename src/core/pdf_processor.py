"""
PDF processing module handling PDF file loading and text extraction.
"""

from pathlib import Path
from typing import List, Dict, Any

import pdfplumber

from src.config import get_logger
from src.core.extraction import extract_well_name, extract_records
from src.core.format_detector import detect_format, PDFFormat
from src.core.flowback_extraction import extract_flowback_records

logger = get_logger(__name__)


def process_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    Process a single PDF file and extract production records.
    
    Orchestrates the PDF processing pipeline:
    1. Detect PDF format (tabular flowback vs. narrative SOR)
    2a. For TABULAR_FLOWBACK: delegate to extract_flowback_records()
    2b. For NARRATIVE_SOR / UNKNOWN: load text and use existing extraction logic
    
    Args:
        pdf_path: Path to the PDF file to process
    
    Returns:
        List of production records extracted from the PDF.
        Empty list if no records found or error occurs.
    
    Raises:
        FileNotFoundError: If PDF file does not exist
        Exception: Re-raised after logging if PDF cannot be parsed
    
    Example:
        >>> records = process_pdf(Path("well_data.pdf"))
        >>> print(f"Found {len(records)} records")
        Found 30 records
    """
    pdf_path = Path(pdf_path)
    
    logger.info(f"Processing {pdf_path.name}")
    
    if not pdf_path.exists():
        logger.error(f"PDF file not found: {pdf_path}")
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Detect PDF format and route accordingly
    fmt = detect_format(pdf_path)
    logger.info(f"  Detected format: {fmt.value}")
    
    if fmt == PDFFormat.TABULAR_FLOWBACK:
        logger.info(f"  Routing to flowback extraction pipeline")
        records = extract_flowback_records(pdf_path)
        logger.info(f"  → Flowback extraction yielded {len(records)} records")
        return records
    
    # NARRATIVE_SOR or UNKNOWN — use existing text-based extraction
    text = ""
    
    try:
        # Open and extract text from all pages
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text() or ""
                text += "\n" + page_text
                logger.debug(f"  Extracted text from page {page_num}")
    
    except Exception as e:
        logger.error(f"Failed to parse PDF {pdf_path.name}: {e}")
        raise
    
    # Extract well name and records from combined text
    well_name = extract_well_name(text)
    records = extract_records(text, well_name)
    
    # Tag records with format for downstream format-aware processing
    for record in records:
        record["_format"] = "narrative_sor"
    
    logger.info(f"  → Found well: {well_name} | {len(records)} records")
    
    return records
