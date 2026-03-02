"""
Command-line interface for PDF Parser Project.
Backward-compatible wrapper that maintains original run.py behavior while using modularized components.
"""

import argparse
import sys
from pathlib import Path

from src.config import (
    get_logger,
    INPUT_FOLDER,
    TEMPLATE_FILE,
    OUTPUT_XLSX,
    OUTPUT_CSV,
)
from src.core.pdf_processor import process_pdf
from src.data.validator import validate_records
from src.data.deduplicator import deduplicate_and_sort
from src.output.excel_writer import write_excel, get_excel_summary
from src.output.csv_writer import write_csv_with_formatting
from src.output.flowback_excel_writer import write_flowback_excel
from src.output.flowback_csv_writer import write_flowback_csv

logger = get_logger(__name__)


def main():
    """
    Main CLI entry point.
    
    Orchestrates the complete PDF extraction pipeline:
    1. Parse command-line arguments
    2. Collect all PDFs from input directory
    3. Process each PDF to extract records
    4. Validate extracted records
    5. Deduplicate and sort
    6. Write to Excel (using template) and CSV
    7. Report results
    """
    parser = argparse.ArgumentParser(
        description="Oil & Gas PDF Data Extractor → Excel/CSV ETL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Use defaults
  %(prog)s --input ./pdfs --output out.xlsx   # Custom paths
  %(prog)s --template custom_template.xlsx    # Custom template
        """,
    )
    
    parser.add_argument(
        "--input",
        default=str(INPUT_FOLDER),
        help=f"Input PDF folder (default: {INPUT_FOLDER})",
    )
    parser.add_argument(
        "--template",
        default=str(TEMPLATE_FILE),
        help=f"Excel template path (default: {TEMPLATE_FILE})",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_XLSX),
        help=f"Output Excel file (default: {OUTPUT_XLSX})",
    )
    parser.add_argument(
        "--csv",
        default=str(OUTPUT_CSV),
        help=f"Output CSV file (default: {OUTPUT_CSV})",
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    input_dir = Path(args.input)
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        return 1
    
    template_path = Path(args.template)
    if not template_path.exists():
        logger.warning(f"Template file not found: {template_path}")
        logger.info("Proceeding without template (Excel output may be limited)")
    
    # Collect all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {input_dir}")
        return 1
    
    logger.info(f"Found {len(pdf_files)} PDF files")
    
    # Process all PDFs
    all_records = []
    
    for pdf_file in pdf_files:
        try:
            records = process_pdf(pdf_file)
            all_records.extend(records)
        except Exception as e:
            logger.error(f"Failed to process {pdf_file.name}: {e}")
            # Continue with next file
            continue
    
    if not all_records:
        logger.error("No records extracted from any PDF!")
        return 1
    
    logger.info(f"Total records extracted: {len(all_records)}")
    
    # Validate records
    valid_records, invalid_records = validate_records(all_records)
    
    if invalid_records:
        logger.warning(f"Filtered out {len(invalid_records)} invalid records")
    
    if not valid_records:
        logger.error("No valid records after validation!")
        return 1
    
    # Deduplicate and sort
    df = deduplicate_and_sort(valid_records)

    # Determine output format from _format tag on records
    format_tags = list(df['_format'].unique()) if '_format' in df.columns else ['narrative_sor']
    logger.info(f"Detected format tag(s): {format_tags}")

    if len(format_tags) > 1:
        logger.error(
            "Mixed PDF formats detected. Please separate SOR and Flowback PDFs into separate runs."
        )
        return 1

    detected_format = format_tags[0] if format_tags else 'narrative_sor'
    is_flowback = detected_format == 'tabular_flowback'
    logger.info(f"Using {'flowback' if is_flowback else 'SOR'} output writers")

    # Write outputs
    try:
        if is_flowback:
            # Flowback format — use flowback-specific writers
            flowback_records = [
                {str(k): v for k, v in row.items()} for row in df.to_dict('records')
            ]
            excel_output = write_flowback_excel(flowback_records, args.output)
            csv_output = write_flowback_csv(flowback_records, args.csv)
        else:
            # SOR / narrative format — existing logic
            if template_path.exists():
                excel_output = write_excel(df, template_path, args.output)
            else:
                logger.info("Skipping Excel output (template not found)")
                excel_output = None

            csv_output = write_csv_with_formatting(df, args.csv)

        # Report results
        logger.info("\n" + "="*50)
        logger.info("✅ PROCESSING COMPLETE!")
        logger.info("="*50)
        logger.info(f"Records processed: {len(df)}")
        if 'Well' in df.columns:
            logger.info(f"Unique wells: {df['Well'].nunique()}")

        if excel_output:
            logger.info(f"Excel output: {excel_output}")
        logger.info(f"CSV output:   {csv_output}")

        if not is_flowback:
            # Show SOR summary stats
            summary = get_excel_summary(df)
            logger.info("\nSummary Statistics:")
            logger.info(f"  Total Oil Production: {summary['total_oil']:,} BO")
            logger.info(f"  Total Gas Production: {summary['total_gas']:,} MCF")
            logger.info(f"  Total Water Production: {summary['total_water']:,} BW")
            if summary['date_range']:
                logger.info(f"  Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")

        logger.info("="*50)

        return 0
    
    except Exception as e:
        logger.error(f"Failed to write output files: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
