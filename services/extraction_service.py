"""
Extraction Service - Business logic layer for PDF processing.
Wraps Phase 1 modules and manages job tracking and file lifecycle.
"""

import os
import uuid
import shutil
import json
import tempfile
import threading
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from openpyxl import Workbook
from openpyxl.styles import Font
from src.config import get_logger, START_ROW, COL_MAP
from src.core.pdf_processor import process_pdf
from src.data.validator import validate_records
from src.data.deduplicator import deduplicate_and_sort
from src.output.excel_writer import write_excel
from src.output.csv_writer import write_csv

logger = get_logger(__name__)

# Maximum number of files allowed per batch (environment-configurable)
MAX_BATCH_FILES = int(os.environ.get('MAX_BATCH_FILES', '50'))


class JobStatus(Enum):
    """Job processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


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

        self.files_processed: int = 0
        self._cancel_requested: bool = False
        
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

    def request_cancel(self):
        """Request cancellation of this job."""
        self._cancel_requested = True
        self.status = JobStatus.CANCELLED

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_requested

    def get_progress(self) -> int:
        """Get processing progress as percentage."""
        if self.status == JobStatus.COMPLETED:
            return 100
        elif self.status == JobStatus.ERROR:
            return 0
        elif self.status == JobStatus.CANCELLED:
            return self._calculate_file_progress()
        elif self.status == JobStatus.PROCESSING:
            return self._calculate_file_progress()
        else:
            return 0  # PENDING

    def _calculate_file_progress(self) -> int:
        """Calculate progress based on files processed."""
        total = len(self.files_submitted) if self.files_submitted else 0
        if total == 0:
            return 0
        # Reserve 10% for upload phase, 90% for processing
        return min(10 + int((self.files_processed / total) * 90), 99)
    
    def get_status_dict(self) -> Dict[str, Any]:
        """Get job status as dictionary."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "progress": self.get_progress(),
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "files_submitted": len(self.files_submitted),
            "files_processed": self.files_processed,
            "records_extracted": self.records_extracted,
            "records_valid": self.records_valid,
            "records_invalid": self.records_invalid,
            "unique_wells": self.unique_wells,
            "records": self.records_valid,     # alias for frontend
            "wells": self.unique_wells,        # alias for frontend
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

        # Job persistence directory (inside the volume-mounted output folder)
        self.jobs_dir = self.output_folder / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

        # Thread safety for self.jobs dict access
        self._lock = threading.Lock()

        # Job tracking (in-memory cache)
        self.jobs: Dict[str, ProcessingJob] = {}

        # Restore jobs from disk on startup
        self._reload_jobs()

        logger.info("ExtractionService initialized")
        logger.info(f"  Upload folder: {self.upload_folder}")
        logger.info(f"  Template folder: {self.template_folder}")
        logger.info(f"  Output folder: {self.output_folder}")
        logger.info(f"  Jobs dir: {self.jobs_dir}")
    
    # ------------------------------------------------------------------
    # Job persistence helpers
    # ------------------------------------------------------------------

    def _persist_job(self, job: 'ProcessingJob') -> None:
        """
        Serialize a job's state to a JSON file atomically.

        Writes to a temporary file then renames to avoid partial writes
        from concurrent access or process crashes.
        """
        data = {
            "job_id": job.job_id,
            "upload_folder": str(job.upload_folder),
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "files_submitted": [str(p) for p in job.files_submitted],
            "records_extracted": job.records_extracted,
            "records_valid": job.records_valid,
            "records_invalid": job.records_invalid,
            "unique_wells": job.unique_wells,
            "output_excel": str(job.output_excel) if job.output_excel else None,
            "output_csv": str(job.output_csv) if job.output_csv else None,
            "error_message": job.error_message,
            "error_details": job.error_details,
            "files_processed": job.files_processed,
            "cancel_requested": job._cancel_requested,
        }
        job_file = self.jobs_dir / f"{job.job_id}.json"
        try:
            fd, tmp_path = tempfile.mkstemp(dir=str(self.jobs_dir), suffix=".tmp")
            try:
                with os.fdopen(fd, 'w') as f:
                    json.dump(data, f)
                os.replace(tmp_path, str(job_file))
            except Exception:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except Exception as e:
            logger.error(f"Failed to persist job {job.job_id}: {e}")

    def _load_job(self, job_id: str) -> Optional['ProcessingJob']:
        """
        Deserialize a job from its JSON file on disk.

        Returns a fully-restored ProcessingJob, or None if the file
        does not exist or cannot be parsed.
        """
        job_file = self.jobs_dir / f"{job_id}.json"
        if not job_file.exists():
            return None
        try:
            with open(str(job_file), 'r') as f:
                data = json.load(f)

            # Reconstruct object using the current upload folder so that
            # paths remain valid even if the container was recreated.
            job = ProcessingJob(job_id, str(self.upload_folder))
            job.status = JobStatus(data["status"])
            job.created_at = datetime.fromisoformat(data["created_at"])
            job.completed_at = (
                datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at") else None
            )
            job.files_submitted = [Path(p) for p in data.get("files_submitted", [])]
            job.records_extracted = data.get("records_extracted", 0)
            job.records_valid = data.get("records_valid", 0)
            job.records_invalid = data.get("records_invalid", 0)
            job.unique_wells = data.get("unique_wells", 0)
            job.output_excel = Path(data["output_excel"]) if data.get("output_excel") else None
            job.output_csv = Path(data["output_csv"]) if data.get("output_csv") else None
            job.error_message = data.get("error_message")
            job.error_details = data.get("error_details")
            job.files_processed = data.get("files_processed", 0)
            job._cancel_requested = data.get("cancel_requested", False)
            return job
        except Exception as e:
            logger.error(f"Failed to load job {job_id} from disk: {e}")
            return None

    def _reload_jobs(self) -> None:
        """
        Scan the jobs directory on startup and restore all job files into
        the in-memory cache.  This allows the service to recover after a
        worker restart without losing previously submitted jobs.
        """
        count = 0
        try:
            for job_file in sorted(self.jobs_dir.glob("*.json")):
                job_id = job_file.stem
                job = self._load_job(job_id)
                if job is not None:
                    self.jobs[job_id] = job
                    count += 1
        except Exception as e:
            logger.error(f"Error during job reload: {e}")
        if count:
            logger.info(f"Restored {count} job(s) from disk on startup")

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
        
        if len(files_list) > MAX_BATCH_FILES:
            raise FileValidationError(f"Maximum {MAX_BATCH_FILES} files per batch")
        
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

        # Store job and persist to disk (lock guards the in-memory dict)
        with self._lock:
            self.jobs[job_id] = job
        self._persist_job(job)

        # Auto-trigger background processing
        processing_thread = threading.Thread(
            target=self._background_process,
            args=(job_id,),
            daemon=True
        )
        processing_thread.start()
        logger.info(f"Background processing started for job {job_id}")

        logger.info(f"Job {job_id} submitted with {saved_count} files")
        return job_id

    def _background_process(self, job_id: str):
        """Run process_job in a background thread."""
        try:
            self.process_job(job_id)
        except Exception as e:
            logger.error(f"Background processing failed for job {job_id}: {e}")
            # process_job already handles setting error status
    
    def process_job(self, job_id: str, template_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
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
        # Get job — fall back to disk if not in the in-memory cache
        with self._lock:
            if job_id not in self.jobs:
                loaded = self._load_job(job_id)
                if loaded is None:
                    raise ProcessingError(f"Job not found: {job_id}")
                self.jobs[job_id] = loaded
            job = self.jobs[job_id]

        if not job.files_submitted:
            raise ProcessingError("No files to process")

        try:
            job.set_processing()
            self._persist_job(job)

            # Process all PDFs and collect records
            all_records = []
            for pdf_path in job.files_submitted:
                # Check cancellation before processing each file
                if job.is_cancelled:
                    logger.info(f"Job {job_id} cancelled by user")
                    self._persist_job(job)
                    return
                try:
                    records = process_pdf(pdf_path)
                    all_records.extend(records)
                    logger.info(f"Extracted {len(records)} records from {pdf_path.name}")
                except Exception as e:
                    logger.error(f"Failed to process {pdf_path.name}: {e}")
                    raise ProcessingError(f"Failed to process {pdf_path.name}: {str(e)}")
                job.records_extracted = len(all_records)
                job.files_processed += 1
                self._persist_job(job)  # Persist progress update
            
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
            
            # Write Excel output
            excel_output_path = self.output_folder / f"{job_id}_output.xlsx"
            try:
                if template.exists():
                    write_excel(df, template, excel_output_path)
                else:
                    # Template not found — create Excel directly using openpyxl
                    logger.warning(
                        f"Template not found at {template}, creating Excel without template"
                    )
                    wb = Workbook()
                    ws = wb.active or wb.create_sheet("Sheet")
                    # Write bold headers in row 3 (one row above data START_ROW=4)
                    header_row = START_ROW - 1
                    _bold = Font(bold=True)
                    for _field_name, _col_num in COL_MAP.items():
                        _hcell = ws.cell(row=header_row, column=_col_num, value=_field_name)
                        _hcell.font = _bold
                    for i, row_data in enumerate(df.itertuples(index=False)):
                        excel_row = START_ROW + i
                        for field_name, col_number in COL_MAP.items():
                            if hasattr(row_data, field_name):
                                value = getattr(row_data, field_name)
                                if field_name == "Date" and value is not None:
                                    if not isinstance(value, datetime):
                                        try:
                                            value = datetime.combine(
                                                value, datetime.min.time()
                                            )
                                        except Exception:
                                            value = None
                                ws.cell(row=excel_row, column=col_number, value=value)
                    wb.save(str(excel_output_path))
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
            self._persist_job(job)

            return {
                "status": "success",
                "job_id": job_id,
                "records": job.records_valid,
                "unique_wells": job.unique_wells,
                "invalid_records": job.records_invalid,
                "excel_url": f"/api/download/{job_id}/output.xlsx",
                "csv_url": f"/api/download/{job_id}/output.csv",
            }
        
        except ProcessingError as e:
            job.set_error(str(e))
            self._persist_job(job)
            raise
        except Exception as e:
            logger.exception(f"Unexpected error processing job {job_id}")
            job.set_error(
                "Unexpected error during processing",
                {"details": str(e), "type": type(e).__name__}
            )
            self._persist_job(job)
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
        with self._lock:
            if job_id not in self.jobs:
                loaded = self._load_job(job_id)
                if loaded is None:
                    raise ProcessingError(f"Job not found: {job_id}")
                self.jobs[job_id] = loaded
            job = self.jobs[job_id]

        result = job.get_status_dict()
        
        if job.error_message:
            result["error"] = job.error_message
            result["error_details"] = job.error_details
        
        return result
    
    def cancel_job(self, job_id: str) -> dict:
        """Cancel a processing job."""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                job = self._load_job(job_id)
                if job:
                    self.jobs[job_id] = job

        if not job:
            raise ProcessingError(f"Job not found: {job_id}")

        if job.status in (JobStatus.COMPLETED, JobStatus.ERROR, JobStatus.CANCELLED):
            return job.get_status_dict()

        job.request_cancel()
        self._persist_job(job)
        logger.info(f"Job {job_id} cancellation requested")
        return job.get_status_dict()

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
        with self._lock:
            if job_id not in self.jobs:
                loaded = self._load_job(job_id)
                if loaded is None:
                    raise ProcessingError(f"Job not found: {job_id}")
                self.jobs[job_id] = loaded
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
