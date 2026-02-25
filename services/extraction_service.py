"""
Extraction Service - Business logic layer for PDF processing.
Wraps Phase 1 modules and manages job tracking and file lifecycle.
"""

import os
import uuid
import shutil
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from src.config import get_logger
from src.core.pdf_processor import process_pdf
from src.data.validator import validate_records
from src.data.deduplicator import deduplicate_and_sort
from src.output.excel_writer import write_excel
from src.output.csv_writer import write_csv

logger = get_logger(__name__)


class JobStatus(Enum):
    """Job processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class ProcessingError(Exception):
    """Custom exception for processing errors."""
    pass


class FileValidationError(Exception):
    """Custom exception for file validation errors."""
    pass


class ProcessingJob:
    """
    Represents a processing job with state tracking.
    Manages file uploads, processing progress, and output files.
    """
    
    def __init__(self, job_id: str, upload_folder: str):
        """
        Initialize a processing job.
        
        Args:
            job_id: Unique job identifier (UUID)
            upload_folder: Base directory for file storage
        """
        self.job_id = job_id
        self.upload_folder = Path(upload_folder)
        self.job_folder = self.upload_folder / job_id
        self.job_folder.mkdir(parents=True, exist_ok=True)
        
        self.status = JobStatus.PENDING
        self.created_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        
        self.files_submitted: List[Path] = []
        self.records_extracted = 0
        self.records_valid = 0
        self.records_invalid = 0
        self.unique_wells = 0
        
        self.output_excel: Optional[Path] = None
        self.output_csv: Optional[Path] = None
        
        self.error_message: Optional[str] = None
        self.error_details: Optional[Dict[str, Any]] = None
        
        logger.info(f"Created ProcessingJob: {self.job_id}")
    
    def add_file(self, file_path: Path) -> None:
        """Add a file to the job."""
        if file_path.exists():
            self.files_submitted.append(file_path)
            logger.debug(f"Added file to job {self.job_id}: {file_path.name}")
    
    def set_processing(self) -> None:
        """Mark job as processing."""
        self.status = JobStatus.PROCESSING
        logger.info(f"Job {self.job_id} status: PROCESSING")
    
    def set_completed(self) -> None:
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        logger.info(f"Job {self.job_id} status: COMPLETED")
    
    def set_error(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Mark job as error."""
        self.status = JobStatus.ERROR
        self.error_message = message
        self.error_details = details or {}
        self.completed_at = datetime.utcnow()
        logger.error(f"Job {self.job_id} error: {message}")
    
    def get_progress(self) -> int:
        """Get processing progress as percentage."""
        if self.status == JobStatus.COMPLETED:
            return 100
        elif self.status == JobStatus.PROCESSING:
            return 50  # Mid-processing
        elif self.status == JobStatus.ERROR:
            return 0
        else:
            return 0  # PENDING
    
    def get_status_dict(self) -> Dict[str, Any]:
        """Get job status as dictionary."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "progress": self.get_progress(),
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "files_submitted": len(self.files_submitted),
            "records_extracted": self.records_extracted,
            "records_valid": self.records_valid,
            "records_invalid": self.records_invalid,
            "unique_wells": self.unique_wells,
        }
    
    def cleanup(self) -> None:
        """Clean up temporary files after download or expiration."""
        if self.job_folder.exists():
            try:
                shutil.rmtree(self.job_folder)
                logger.info(f"Cleaned up job folder: {self.job_folder}")
            except Exception as e:
                logger.warning(f"Failed to cleanup job folder {self.job_folder}: {e}")


class ExtractionService:
    """
    Service for managing PDF extraction workflows.
    Coordinates file uploads, processing, and output generation.
    """
    
    def __init__(self, upload_folder: str, template_folder: str, output_folder: str):
        """
        Initialize extraction service.
        
        Args:
            upload_folder: Directory for temporary file storage
            template_folder: Directory containing Excel templates
            output_folder: Directory for processed output files
        """
        self.upload_folder = Path(upload_folder)
        self.template_folder = Path(template_folder)
        self.output_folder = Path(output_folder)
        
        # Create directories if they don't exist
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        self.template_folder.mkdir(parents=True, exist_ok=True)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        # Job tracking
        self.jobs: Dict[str, ProcessingJob] = {}
        
        logger.info("ExtractionService initialized")
        logger.info(f"  Upload folder: {self.upload_folder}")
        logger.info(f"  Template folder: {self.template_folder}")
        logger.info(f"  Output folder: {self.output_folder}")
    
    def submit_files(self, files_list: List) -> str:
        """
        Submit files for extraction processing.
        
        Args:
            files_list: List of uploaded files (Werkzeug FileStorage objects)
        
        Returns:
            Job ID for tracking
        
        Raises:
            FileValidationError: If files are invalid
        """
        if not files_list:
            raise FileValidationError("No files provided")
        
        if len(files_list) > 50:
            raise FileValidationError("Maximum 50 files per batch")
        
        # Create job
        job_id = str(uuid.uuid4())
        job = ProcessingJob(job_id, str(self.upload_folder))
        
        # Save uploaded files
        saved_count = 0
        for file in files_list:
            if not file.filename:
                continue
            
            # Validate file extension
            if not file.filename.lower().endswith('.pdf'):
                raise FileValidationError(
                    f"Invalid file type: {file.filename}. Only PDF files are supported."
                )
            
            # Save file with UUID naming
            file_name = f"{uuid.uuid4().hex}.pdf"
            file_path = job.job_folder / file_name
            
            try:
                file.save(str(file_path))
                job.add_file(file_path)
                saved_count += 1
                logger.info(f"Saved uploaded file: {file_name}")
            except Exception as e:
                raise FileValidationError(f"Failed to save file {file.filename}: {str(e)}")
        
        if saved_count == 0:
            raise FileValidationError("No valid PDF files were uploaded")
        
        # Store job
        self.jobs[job_id] = job
        
        logger.info(f"Job {job_id} submitted with {saved_count} files")
        return job_id
    
    def process_job(self, job_id: str, template_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Process uploaded PDFs for a job.
        
        Args:
            job_id: Job ID to process
            template_path: Optional path to Excel template
        
        Returns:
            Processing results dictionary
        
        Raises:
            ProcessingError: If processing fails
        """
        # Get job
        if job_id not in self.jobs:
            raise ProcessingError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        
        if not job.files_submitted:
            raise ProcessingError("No files to process")
        
        try:
            job.set_processing()
            
            # Process all PDFs and collect records
            all_records = []
            for pdf_path in job.files_submitted:
                try:
                    records = process_pdf(pdf_path)
                    all_records.extend(records)
                    logger.info(f"Extracted {len(records)} records from {pdf_path.name}")
                except Exception as e:
                    logger.error(f"Failed to process {pdf_path.name}: {e}")
                    raise ProcessingError(f"Failed to process {pdf_path.name}: {str(e)}")
            
            job.records_extracted = len(all_records)
            
            if not all_records:
                raise ProcessingError("No records extracted from any PDF files")
            
            # Validate records
            valid_records, invalid_records = validate_records(all_records)
            job.records_valid = len(valid_records)
            job.records_invalid = len(invalid_records)
            
            if not valid_records:
                raise ProcessingError(
                    f"All {len(invalid_records)} extracted records failed validation"
                )
            
            logger.info(f"Validation: {len(valid_records)} valid, {len(invalid_records)} invalid")
            
            # Deduplicate and sort
            df = deduplicate_and_sort(valid_records)
            
            logger.info(f"After dedup: {len(df)} records")
            job.unique_wells = df['Well'].nunique() if 'Well' in df.columns else 0
            
            # Find template
            if template_path and Path(template_path).exists():
                template = Path(template_path)
            else:
                # Look for template.xlsx in project root
                template = Path(__file__).parent.parent / "template.xlsx"
            
            if not template.exists():
                raise ProcessingError(
                    f"Excel template not found: {template}. "
                    "Please ensure template.xlsx exists in the project root."
                )
            
            # Write Excel output
            excel_output_path = self.output_folder / f"{job_id}_output.xlsx"
            try:
                write_excel(df, template, excel_output_path)
                job.output_excel = excel_output_path
                logger.info(f"Excel file written: {excel_output_path}")
            except Exception as e:
                raise ProcessingError(f"Failed to write Excel file: {str(e)}")
            
            # Write CSV output
            csv_output_path = self.output_folder / f"{job_id}_output.csv"
            try:
                write_csv(df, csv_output_path)
                job.output_csv = csv_output_path
                logger.info(f"CSV file written: {csv_output_path}")
            except Exception as e:
                raise ProcessingError(f"Failed to write CSV file: {str(e)}")
            
            job.set_completed()
            
            return {
                "status": "success",
                "job_id": job_id,
                "records": job.records_valid,
                "unique_wells": job.unique_wells,
                "invalid_records": job.records_invalid,
                "excel_url": f"/download/{job_id}/output.xlsx",
                "csv_url": f"/download/{job_id}/output.csv",
            }
        
        except ProcessingError as e:
            job.set_error(str(e))
            raise
        except Exception as e:
            logger.exception(f"Unexpected error processing job {job_id}")
            job.set_error(
                "Unexpected error during processing",
                {"details": str(e), "type": type(e).__name__}
            )
            raise ProcessingError(f"Unexpected error: {str(e)}")
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get status of a processing job.
        
        Args:
            job_id: Job ID to check
        
        Returns:
            Status dictionary
        
        Raises:
            ProcessingError: If job not found
        """
        if job_id not in self.jobs:
            raise ProcessingError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        result = job.get_status_dict()
        
        if job.error_message:
            result["error"] = job.error_message
            result["error_details"] = job.error_details
        
        return result
    
    def get_download_path(self, job_id: str, format: str) -> Path:
        """
        Get path to download file.
        
        Args:
            job_id: Job ID
            format: Output format ('xlsx' or 'csv')
        
        Returns:
            Path to output file
        
        Raises:
            ProcessingError: If file not found
        """
        if job_id not in self.jobs:
            raise ProcessingError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        
        if format.lower() == 'xlsx':
            if not job.output_excel or not job.output_excel.exists():
                raise ProcessingError("Excel output file not found")
            return job.output_excel
        elif format.lower() == 'csv':
            if not job.output_csv or not job.output_csv.exists():
                raise ProcessingError("CSV output file not found")
            return job.output_csv
        else:
            raise ProcessingError(f"Unsupported format: {format}")
