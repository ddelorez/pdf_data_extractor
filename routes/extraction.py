"""
API Routes for PDF extraction processing.
Handles file uploads, processing, and downloads.
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from pathlib import Path
import os

from src.config import get_logger
from services.extraction_service import ExtractionService, ProcessingError, FileValidationError

logger = get_logger(__name__)

# Create blueprint
extraction_bp = Blueprint('extraction', __name__)

# Service instance (will be set by app)
_service: ExtractionService = None


def set_service(service: ExtractionService) -> None:
    """Set the extraction service instance."""
    global _service
    _service = service


# ====================== ENDPOINTS ======================

@extraction_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for Docker/Kubernetes.
    
    Returns:
        JSON with health status
    """
    from datetime import datetime
    return jsonify({
        "status": "healthy",
        "version": "2.0",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@extraction_bp.route('/extract', methods=['POST'])
def extract_files():
    """
    Upload PDF files for extraction.
    
    Accepts: multipart/form-data with file(s) field
    
    Returns:
        JSON: {
            "status": "processing",
            "job_id": "uuid",
            "files_received": N
        }
    
    Errors:
        400: No files provided or invalid file types
        413: File too large
        500: Server error
    """
    try:
        logger.info(f"Extract request: {len(request.files)} file(s)")
        
        # Check if files are provided
        if 'files' not in request.files:
            logger.warning("Extract request with no 'files' field")
            return jsonify({
                "status": "error",
                "message": "No files provided. Use 'files' form field."
            }), 400
        
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({
                "status": "error",
                "message": "No files selected"
            }), 400
        
        # Submit files to service
        job_id = _service.submit_files(files)
        
        logger.info(f"Submitted {len(files)} files for job {job_id}")
        
        return jsonify({
            "status": "processing",
            "job_id": job_id,
            "files_received": len(files)
        }), 202  # 202 Accepted
    
    except FileValidationError as e:
        logger.warning(f"File validation error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    
    except Exception as e:
        logger.exception("Unexpected error in extract endpoint")
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "details": str(e)
        }), 500


@extraction_bp.route('/process/<job_id>', methods=['POST'])
def process_job(job_id: str):
    """
    Process uploaded PDFs for a job.
    
    URL Parameters:
        job_id: Job ID from extraction
    
    Returns:
        JSON: {
            "status": "success",
            "job_id": "uuid",
            "records": N,
            "unique_wells": N,
            "excel_url": "/download/job_id/output.xlsx",
            "csv_url": "/download/job_id/output.csv"
        }
    
    Errors:
        404: Job not found
        422: No files in job or processing error
        500: Server error
    """
    try:
        logger.info(f"Processing job {job_id}")
        
        # Get optional template path from request
        template_path = request.json.get('template_path') if request.is_json else None
        
        result = _service.process_job(job_id, template_path)
        
        logger.info(f"Job {job_id} processing completed successfully")
        
        return jsonify(result), 200
    
    except ProcessingError as e:
        logger.warning(f"Processing error for job {job_id}: {e}")
        
        # Check if job not found
        if "Job not found" in str(e):
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 404
        
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 422  # 422 Unprocessable Entity
    
    except Exception as e:
        logger.exception(f"Unexpected error processing job {job_id}")
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "details": str(e)
        }), 500


@extraction_bp.route('/status/<job_id>', methods=['GET'])
def get_status(job_id: str):
    """
    Get processing status of a job.
    
    URL Parameters:
        job_id: Job ID to check
    
    Returns:
        JSON: {
            "job_id": "uuid",
            "status": "pending|processing|completed|error",
            "progress": 0-100,
            "created_at": "ISO8601",
            "completed_at": "ISO8601 or null",
            "files_submitted": N,
            "records_extracted": N,
            "records_valid": N,
            "records_invalid": N,
            "unique_wells": N,
            "error": "error message if status is error",
            "error_details": {...}
        }
    
    Errors:
        404: Job not found
        500: Server error
    """
    try:
        status_dict = _service.get_job_status(job_id)
        return jsonify(status_dict), 200
    
    except ProcessingError as e:
        if "Job not found" in str(e):
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 404
        
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
    except Exception as e:
        logger.exception(f"Error getting status for job {job_id}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500


@extraction_bp.route('/download/<job_id>/output.xlsx', methods=['GET'])
def download_excel(job_id: str):
    """
    Download processed Excel file.
    
    URL Parameters:
        job_id: Job ID
    
    Returns:
        Binary Excel file (.xlsx)
    
    Errors:
        404: Job or file not found
        500: Server error
    """
    try:
        file_path = _service.get_download_path(job_id, 'xlsx')
        
        logger.info(f"Downloading Excel for job {job_id}: {file_path}")
        
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=f"{job_id}_output.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except ProcessingError as e:
        logger.warning(f"Download error for job {job_id}: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 404
    
    except Exception as e:
        logger.exception(f"Error downloading Excel for job {job_id}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500


@extraction_bp.route('/download/<job_id>/output.csv', methods=['GET'])
def download_csv(job_id: str):
    """
    Download processed CSV file.
    
    URL Parameters:
        job_id: Job ID
    
    Returns:
        CSV file with UTF-8 encoding
    
    Errors:
        404: Job or file not found
        500: Server error
    """
    try:
        file_path = _service.get_download_path(job_id, 'csv')
        
        logger.info(f"Downloading CSV for job {job_id}: {file_path}")
        
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=f"{job_id}_output.csv",
            mimetype='text/csv'
        )
    
    except ProcessingError as e:
        logger.warning(f"Download error for job {job_id}: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 404
    
    except Exception as e:
        logger.exception(f"Error downloading CSV for job {job_id}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500
