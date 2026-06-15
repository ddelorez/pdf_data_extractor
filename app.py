"""
Flask Application - PDF Extractor API
Phase 2: Backend API with Docker containerization

Main application factory and configuration setup.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

from src.config import get_logger
from services.extraction_service import ExtractionService
from routes.extraction import extraction_bp, set_service

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

# Known-insecure SECRET_KEY values that must never be used in production.
# The app refuses to boot if FLASK_ENV=production and the key is missing or one
# of these placeholders (see resolve_secret_key / issue #1.6).
INSECURE_SECRET_KEYS = {
    "",
    "dev-key-not-for-production",
    "your-secure-secret-key-here",
    "change-me",
    "changeme",
    "secret",
}

DEV_SECRET_KEY = "dev-key-not-for-production"


def resolve_secret_key(testing: bool = False) -> str:
    """
    Resolve the Flask SECRET_KEY, failing fast on an insecure production config.

    In production (FLASK_ENV=production) a real, non-placeholder key is required
    or the app refuses to start. Outside production (and under TESTING) a
    development fallback is used so local/test runs work without configuration.
    """
    secret_key = os.getenv("SECRET_KEY")
    is_production = os.getenv("FLASK_ENV", "").strip().lower() == "production"

    if is_production and not testing:
        if not secret_key or secret_key.strip().lower() in INSECURE_SECRET_KEYS:
            raise RuntimeError(
                "SECRET_KEY must be set to a secure, non-default value when "
                "FLASK_ENV=production. Set the SECRET_KEY environment variable "
                "(e.g. `python -c \"import secrets; print(secrets.token_hex(32))\"`)."
            )
        return secret_key

    return secret_key or DEV_SECRET_KEY


def create_app(config=None):
    """
    Application factory for Flask.
    
    Creates and configures Flask app with:
    - CORS support for React frontend
    - Blueprint registration
    - Error handlers
    - Service initialization
    
    Args:
        config: Optional config dict to override defaults
    
    Returns:
        Configured Flask app instance
    """
    app = Flask(__name__, template_folder='templates')

    # ====================== CONFIGURATION ======================

    # Get configuration from environment or defaults.
    #
    # Size limits (issue #1.8) — there are three distinct ceilings:
    #   * MAX_CONTENT_LENGTH (here)  — Flask caps the *entire* multipart request
    #     body at MAX_UPLOAD_SIZE (default 100 MB). This is the real upload cap:
    #     all files in one /api/extract request must together fit under it
    #     (over -> 413).
    #   * MAX_BATCH_FILES (services) — at most 50 files per request.
    #   * Container memory (docker-compose) — 2 GB hard limit.
    # So the worst-case in-flight upload is ~100 MB (one request), not
    # 50 x 100 MB; the per-file size is bounded only by the request total.
    app.config['MAX_CONTENT_LENGTH'] = int(
        os.getenv('MAX_UPLOAD_SIZE', 104857600)  # 100 MB default
    )
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', '/app/uploads')
    app.config['TEMPLATE_FOLDER'] = os.getenv('TEMPLATE_FOLDER', '/app/templates')
    app.config['OUTPUT_FOLDER'] = os.getenv('OUTPUT_FOLDER', '/app/outputs')
    app.config['JSON_SORT_KEYS'] = False

    # Resolve SECRET_KEY (fail-fast on insecure production config — issue #1.6).
    # Use the incoming config's TESTING flag so the test suite is exempt.
    app.config['SECRET_KEY'] = resolve_secret_key(
        testing=bool((config or {}).get('TESTING'))
    )

    # Override with provided config
    if config:
        app.config.update(config)
    
    logger.info("Flask app configuration:")
    logger.info(f"  Max upload size: {app.config['MAX_CONTENT_LENGTH']} bytes")
    logger.info(f"  Upload folder: {app.config['UPLOAD_FOLDER']}")
    logger.info(f"  Output folder: {app.config['OUTPUT_FOLDER']}")
    
    # ====================== SERVICE INITIALIZATION ======================
    
    # Create and initialize extraction service
    extraction_service = ExtractionService(
        upload_folder=app.config['UPLOAD_FOLDER'],
        template_folder=app.config['TEMPLATE_FOLDER'],
        output_folder=app.config['OUTPUT_FOLDER']
    )
    
    # Pass service to routes
    set_service(extraction_service)

    # Start the background TTL sweeper that garbage-collects expired job
    # artifacts. Skipped under TESTING so the test suite doesn't spawn threads.
    if not app.config.get('TESTING'):
        extraction_service.start_cleanup_sweeper()

    # ====================== CORS CONFIGURATION ======================
    #
    # CORS is owned entirely by the nginx reverse proxy (frontend/nginx.conf),
    # which is the single entry point in the deployed topology. Flask-CORS was
    # removed (issue #1.9) to avoid duplicate/ conflicting Access-Control-* headers.
    # If the backend is ever exposed directly (without nginx), CORS must be
    # reintroduced here or handled by whatever proxy fronts it.

    # ====================== BLUEPRINT REGISTRATION ======================
    
    # Register API blueprint
    app.register_blueprint(extraction_bp, url_prefix='/api')
    logger.info("Registered blueprint: /api")
    
    # ====================== ERROR HANDLERS ======================
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request."""
        return jsonify({
            "status": "error",
            "message": "Bad request",
            "details": str(error)
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found."""
        return jsonify({
            "status": "error",
            "message": "Resource not found",
            "details": str(error)
        }), 404
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle 413 Payload Too Large."""
        return jsonify({
            "status": "error",
            "message": "File too large",
            "max_size_bytes": app.config['MAX_CONTENT_LENGTH']
        }), 413
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error."""
        logger.exception("Internal server error")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500
    
    # ====================== MAIN ROUTES ======================
    
    @app.route('/', methods=['GET'])
    def index():
        """Serve index page with API documentation."""
        return render_template('index.html')
    
    @app.route('/api/docs', methods=['GET'])
    def api_docs():
        """Return API documentation as JSON."""
        return jsonify({
            "title": "PDF Extractor API - Phase 2",
            "version": "2.0",
            "description": "REST API for PDF data extraction and processing",
            "endpoints": {
                "POST /api/extract": {
                    "description": "Upload PDF files for extraction",
                    "parameters": {
                        "files": "List of PDF files (multipart/form-data)"
                    },
                    "returns": {
                        "status": "processing",
                        "job_id": "uuid",
                        "files_received": "number"
                    }
                },
                "POST /api/process/<job_id>": {
                    "description": "Process uploaded PDFs",
                    "returns": {
                        "status": "success",
                        "records": "number",
                        "unique_wells": "number",
                        "excel_url": "download URL",
                        "csv_url": "download URL"
                    }
                },
                "GET /api/status/<job_id>": {
                    "description": "Get job processing status",
                    "returns": {
                        "job_id": "uuid",
                        "status": "pending|processing|completed|error",
                        "progress": "0-100"
                    }
                },
                "GET /api/download/<job_id>/output.xlsx": {
                    "description": "Download Excel output file"
                },
                "GET /api/download/<job_id>/output.csv": {
                    "description": "Download CSV output file"
                },
                "GET /api/health": {
                    "description": "Health check endpoint"
                }
            }
        }), 200
    
    # ====================== LOGGING ======================
    
    logger.info("Flask application created successfully")
    logger.info("=" * 50)
    logger.info("PDF Extractor API - Phase 2")
    logger.info("=" * 50)
    
    return app


def main():
    """Entry point for running the Flask development server."""
    app = create_app()
    
    # Development settings
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    logger.info(f"Starting Flask server on {host}:{port} (debug={debug})")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
