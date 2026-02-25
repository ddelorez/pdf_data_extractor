# Phase 2: Flask Backend and Docker Foundation - Implementation Guide

## Overview

Phase 2 implements a production-ready Flask REST API that wraps the Phase 1 PDF extraction engine and enables Docker containerized deployment. The system is designed for scalability, error handling, and easy integration with a React frontend in Phase 3.

**Version:** 2.0  
**Status:** Complete and ready for testing  
**Deployment:** Docker containerized (primary method)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Flask Application                        │
│                          (app.py)                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Routes Layer          Services Layer         Phase 1 Modules    │
│  ───────────────       ──────────────        ─────────────────   │
│  • extract()      -->  ProcessingJob   -->   • pdf_processor.py  │
│  • process()           ExtractionService      • extraction.py    │
│  • status()       -->  Business Logic   -->   • validator.py     │
│  • download()                                • deduplicator.py   │
│  • health()                            -->   • excel_writer.py   │
│                                              • csv_writer.py     │
└─────────────────────────────────────────────────────────────────┘
         ↓
    Docker Container (Gunicorn WSGI)
         ↓
    Port 5000
```

---

## File Structure

```
c:\Users\ddelorez\Downloads\PDF Parser Project\
├── app.py                          # Main Flask app factory
├── requirements.txt                # Updated with Flask dependencies
├── .env.example                    # Environment configuration template
├── .gitignore                      # Git exclusions
├── .dockerignore                   # Docker build exclusions
├── Dockerfile                      # Production container build
├── docker-compose.yml              # Container orchestration
│
├── routes/
│   ├── __init__.py
│   └── extraction.py               # API endpoints (all return JSON)
│
├── services/
│   ├── __init__.py
│   └── extraction_service.py       # Business logic & job tracking
│
├── templates/
│   └── index.html                  # Server status page with docs
│
├── uploads/                        # Temporary file storage
├── outputs/                        # Processed output files
├── logs/                           # Application logs
│
├── src/                            # Phase 1 modules (unchanged)
│   ├── config.py
│   ├── core/
│   │   ├── extraction.py
│   │   └── pdf_processor.py
│   ├── data/
│   │   ├── validator.py
│   │   └── deduplicator.py
│   └── output/
│       ├── excel_writer.py
│       └── csv_writer.py
│
└── PHASE_2_IMPLEMENTATION.md       # This file
```

---

## API Endpoints

### 1. **POST /api/extract** - Upload PDF Files

**Purpose:** Receive PDF files for processing

**Request:**
```bash
curl -F "files=@document1.pdf" -F "files=@document2.pdf" \
     http://localhost:5000/api/extract
```

**Request Format:** `multipart/form-data`
- Field name: `files`
- Type: Multiple PDF files
- Max size: 100 MB total (configurable)

**Response (202 Accepted):**
```json
{
  "status": "processing",
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "files_received": 2
}
```

**Error Responses:**
- `400` - No files provided or invalid file types
- `413` - File too large
- `500` - Server error

---

### 2. **POST /api/process/<job_id>** - Process PDFs

**Purpose:** Start PDF processing and generate outputs

**Request:**
```bash
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"template_path": "/app/templates/template.xlsx"}' \
     http://localhost:5000/api/process/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Parameters:**
- `job_id` (URL): UUID from extract endpoint
- `template_path` (JSON body, optional): Custom template path

**Response (200 OK):**
```json
{
  "status": "success",
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "records": 1250,
  "unique_wells": 47,
  "invalid_records": 3,
  "excel_url": "/download/a1b2c3d4-e5f6-7890-abcd-ef1234567890/output.xlsx",
  "csv_url": "/download/a1b2c3d4-e5f6-7890-abcd-ef1234567890/output.csv"
}
```

**Error Response (422 Unprocessable Entity):**
```json
{
  "status": "error",
  "message": "No files to process"
}
```

---

### 3. **GET /api/status/<job_id>** - Check Processing Status

**Purpose:** Track job progress and completion

**Request:**
```bash
curl http://localhost:5000/api/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Response (200 OK):**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "processing",
  "progress": 50,
  "created_at": "2026-02-25T21:54:08.593Z",
  "completed_at": null,
  "files_submitted": 2,
  "records_extracted": 2500,
  "records_valid": 2497,
  "records_invalid": 3,
  "unique_wells": 47
}
```

**Status Values:**
- `pending` - Waiting to be processed
- `processing` - Currently processing
- `completed` - Successfully completed
- `error` - Processing failed

---

### 4. **GET /download/<job_id>/output.xlsx** - Download Excel

**Purpose:** Download processed data in Excel format

**Request:**
```bash
curl -o result.xlsx \
     http://localhost:5000/download/a1b2c3d4-e5f6-7890-abcd-ef1234567890/output.xlsx
```

**Response:** Binary .xlsx file with proper headers
- MIME type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Filename: `{job_id}_output.xlsx`

---

### 5. **GET /download/<job_id>/output.csv** - Download CSV

**Purpose:** Download processed data in CSV format

**Request:**
```bash
curl -o result.csv \
     http://localhost:5000/download/a1b2c3d4-e5f6-7890-abcd-ef1234567890/output.csv
```

**Response:** CSV file with UTF-8 encoding
- MIME type: `text/csv`
- Filename: `{job_id}_output.csv`

---

### 6. **GET /api/health** - Health Check

**Purpose:** Docker/Kubernetes health monitoring

**Request:**
```bash
curl http://localhost:5000/api/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "2.0",
  "timestamp": "2026-02-25T21:54:08.593Z"
}
```

---

## Core Components

### app.py - Flask Application Factory

**Responsibilities:**
- Flask app initialization and configuration
- Blueprint registration
- CORS configuration
- Error handlers
- Service instantiation
- Logging setup

**Key Features:**
- Environment variable support via `.env`
- Global error handling with JSON responses
- CORS enabled for React frontend
- Configurable upload size limits

---

### routes/extraction.py - API Endpoints

**Implements:**
- `POST /api/extract` - File upload handler
- `POST /api/process/<job_id>` - Processing orchestrator
- `GET /api/status/<job_id>` - Status checker
- `GET /download/<job_id>/output.xlsx` - Excel download
- `GET /download/<job_id>/output.csv` - CSV download
- `GET /api/health` - Health check

**Features:**
- Multipart file upload handling
- UUID-based job tracking
- Comprehensive error handling
- JSON response standardization
- File type validation
- Secure filename handling

---

### services/extraction_service.py - Business Logic

**ProcessingJob Class:**
- Tracks job state through lifecycle
- Manages temporary file storage
- Records processing metrics
- Handles error states
- Supports status queries

**ExtractionService Class:**
- Coordinates file uploads
- Orchestrates Phase 1 modules
- Manages job registry
- Generates outputs
- Handles file lifecycle

**Key Methods:**
```python
service.submit_files(files)              # → job_id
service.process_job(job_id)              # → results dict
service.get_job_status(job_id)           # → status dict
service.get_download_path(job_id, fmt)   # → Path
```

---

## Phase 1 Integration

The service layer wraps Phase 1 modules without modification:

```python
# PDF Processing
from src.core.pdf_processor import process_pdf
records = process_pdf(pdf_path)

# Data Validation
from src.data.validator import validate_records
valid, invalid = validate_records(records)

# Deduplication & Sorting
from src.data.deduplicator import deduplicate_and_sort
df = deduplicate_and_sort(valid_records)

# Excel Output
from src.output.excel_writer import write_excel
write_excel(df, template_path, output_path)

# CSV Output
from src.output.csv_writer import write_csv
write_csv(df, output_path)
```

**No modifications to Phase 1 code** - complete separation of concerns maintained.

---

## Running Locally

### Prerequisites
- Python 3.10+
- pip
- Virtual environment recommended

### Setup

**1. Create virtual environment:**
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Create .env file:**
```bash
cp .env.example .env
# Edit .env with your settings
```

**4. Create required directories:**
```bash
mkdir -p uploads outputs logs templates
```

### Running

**Development mode:**
```bash
python app.py
```

**Production with gunicorn:**
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 "app:create_app()"
```

**Access:**
- API: `http://localhost:5000/api/...`
- Docs: `http://localhost:5000/`
- Health: `http://localhost:5000/api/health`

---

## Docker Deployment

### Build

**Build Docker image:**
```bash
docker build -t pdf-extractor:2.0 .
```

**Or using docker-compose:**
```bash
docker-compose build
```

### Run

**Start container with docker-compose:**
```bash
docker-compose up -d
```

**Or direct Docker command:**
```bash
docker run -d \
  -p 5000:5000 \
  -v ./uploads:/app/uploads \
  -v ./outputs:/app/outputs \
  -v ./templates:/app/templates \
  -v ./logs:/app/logs \
  -e SECRET_KEY=your-secret-here \
  pdf-extractor:2.0
```

### Docker Compose Features

- **Multi-stage build** for minimal image size
- **Non-root user** (appuser) for security
- **Health checks** for container monitoring
- **Volume mounts** for persistent storage
- **Resource limits** (configurable)
- **Logging** with json-file driver
- **Auto-restart** with `unless-stopped` policy
- **Network** isolation with custom bridge

---

## Environment Configuration

### .env Variables

```bash
# Flask Configuration
FLASK_ENV=production              # development or production
FLASK_DEBUG=0                     # 0 = off, 1 = on
SECRET_KEY=your-secret-key       # Min 32 chars recommended

# File Upload
MAX_UPLOAD_SIZE=104857600        # 100 MB in bytes
UPLOAD_FOLDER=uploads            # Relative or absolute path
TEMPLATE_FOLDER=templates        # Excel templates directory
OUTPUT_FOLDER=outputs            # Processed files directory

# Logging
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR

# Server
FLASK_HOST=0.0.0.0              # Bind address
FLASK_PORT=5000                 # Listen port

# CORS (Phase 3 React frontend)
CORS_ORIGINS=*                  # Or: https://frontend.com,https://api.com

# PDF Processing
DEFAULT_TIMEOUT=30              # Seconds per PDF
MAX_BATCH_FILES=50              # Max files per upload
```

---

## Error Handling

### Service Layer Exceptions

```python
class FileValidationError(Exception):
    """Raised when file validation fails"""
    
class ProcessingError(Exception):
    """Raised during processing"""
```

### HTTP Error Responses

All errors return JSON with consistent format:

```json
{
  "status": "error",
  "message": "User-friendly description",
  "details": "Technical details (optional)"
}
```

**Error Codes:**
- `400` - Bad request (invalid files, missing data)
- `404` - Resource not found (invalid job_id)
- `413` - File too large
- `422` - Unprocessable (processing error)
- `500` - Server error

---

## Logging

### Log Levels

Set via `LOG_LEVEL` environment variable:
- **DEBUG** - Detailed diagnostic information
- **INFO** - General events (default)
- **WARNING** - Warning messages
- **ERROR** - Error events
- **CRITICAL** - Critical system failures

### Log Output

Logs are written to both:
- **Console** - Real-time monitoring
- **File** - `logs/pdf_parser.log`

### Docker Logs

```bash
# View container logs
docker-compose logs pdf-extractor

# Watch live logs
docker-compose logs -f pdf-extractor

# Last 100 lines
docker-compose logs --tail 100
```

---

## Testing

### Manual Testing

**1. Health check:**
```bash
curl http://localhost:5000/api/health
```

**2. Upload files:**
```bash
curl -F "files=@sample1.pdf" -F "files=@sample2.pdf" \
     http://localhost:5000/api/extract
```

**3. Process job (replace JOB_ID):**
```bash
curl -X POST http://localhost:5000/api/process/{JOB_ID}
```

**4. Check status:**
```bash
curl http://localhost:5000/api/status/{JOB_ID}
```

**5. Download results:**
```bash
curl -o output.xlsx http://localhost:5000/download/{JOB_ID}/output.xlsx
curl -o output.csv http://localhost:5000/download/{JOB_ID}/output.csv
```

### Automated Testing (Phase 4)

The API is designed for pytest-based testing:
- Single responsibility routes
- Mockable service layer
- Clear input/output contracts
- Comprehensive error codes

---

## Production Deployment

### Best Practices

1. **Security:**
   - Set strong `SECRET_KEY`
   - Use HTTPS (reverse proxy)
   - Implement authentication (Phase 3)
   - Run as non-root user ✓ (in Dockerfile)

2. **Scaling:**
   - Use load balancer (nginx, AWS ALB)
   - Run multiple containers
   - External storage for uploads/outputs
   - Database for job persistence (Phase 3)

3. **Monitoring:**
   - Enable `/api/health` checks
   - Aggregate logs (ELK, Datadog)
   - Track processing metrics
   - Alert on errors

4. **Performance:**
   - 4 worker processes (configurable)
   - 2 threads per worker
   - 60-second timeout per request
   - Connection pooling

### Kubernetes Deployment

The Docker image is Kubernetes-ready:
- Accepts environment variables
- Implements health check endpoint
- Non-root user for security
- Graceful shutdown support

Example Kubernetes manifest coming in Phase 3.

---

## Next Steps (Phase 3: React Frontend)

Phase 3 will implement:
- React frontend UI
- Real-time job progress display
- File drag-and-drop upload
- Results visualization
- User authentication
- Job history persistence (database)
- Admin dashboard

**Integration Points:**
- All Phase 2 API endpoints remain unchanged
- CORS already configured (`CORS_ORIGINS` env var)
- JWT authentication ready (add auth middleware)
- WebSocket support possible (for live updates)

---

## Troubleshooting

### Common Issues

**Issue:** "Template not found"
```
Solution: Ensure template.xlsx exists in project root or specify template_path
```

**Issue:** "File too large"
```
Solution: Increase MAX_UPLOAD_SIZE in .env (default: 100 MB)
curl -X POST http://localhost:5000/api/process/{JOB_ID}
```

**Issue:** Container won't start
```bash
# Check logs
docker-compose logs pdf-extractor

# Verify image built correctly
docker-compose build --no-cache

# Check port availability
netstat -an | grep 5000  # or: lsof -i :5000
```

**Issue:** Permission denied in uploads directory
```bash
# Fix ownership
docker-compose exec pdf-extractor chown -R appuser:appuser /app/uploads
```

---

## Summary

✅ **Completed in Phase 2:**
- Production Flask REST API with 6 endpoints
- Job tracking and status monitoring
- File upload handling with validation
- Phase 1 module integration
- Excel and CSV export
- Docker containerization
- Docker Compose orchestration
- Comprehensive error handling
- CORS configuration
- Health check monitoring
- Detailed documentation

✅ **Ready for:**
- Development testing with curl/Postman
- Docker deployment
- React frontend integration (Phase 3)
- Production scaling

---

## References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Docker Guide](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Gunicorn](https://gunicorn.org/)
- [REST API Best Practices](https://restfulapi.net/)

---

**Phase 2 Implementation Complete** ✓  
**Version 2.0** | **2026-02-25**
