# Phase 2: Quick Start Guide

## 🚀 Running Locally (Python)

### 1. Setup Virtual Environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Create Configuration
```bash
cp .env.example .env
# Edit .env if needed (defaults should work for local testing)
```

### 4. Create Required Directories
```bash
mkdir -p uploads outputs logs
```

### 5. Start Flask Server
```bash
python app.py
```

**Output:**
```
 * Serving Flask app 'app'
 * Running on http://0.0.0.0:5000
 * Press CTRL+C to quit
```

**Access:**
- API: http://localhost:5000/api/health
- Docs: http://localhost:5000/
- Status: http://localhost:5000/api/docs

---

## 🐳 Running with Docker

### 1. Build Image
```bash
docker-compose build
```

### 2. Start Container
```bash
docker-compose up -d
```

### 3. Check Status
```bash
docker-compose ps
docker-compose logs pdf-extractor
```

### 4. Stop Container
```bash
docker-compose down
```

---

## 📝 Testing the API

### Test 1: Health Check
```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.0",
  "timestamp": "2026-02-25T21:54:08.593Z"
}
```

### Test 2: Upload PDF Files

**Create a test PDF first** (or use existing PDFs):
```bash
# Windows - create empty test.pdf
type nul > test.pdf

# macOS/Linux - create empty test.pdf
touch test.pdf
```

**Upload:**
```bash
curl -F "files=@test.pdf" http://localhost:5000/api/extract
```

Expected response:
```json
{
  "status": "processing",
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "files_received": 1
}
```

**Save job_id for next steps** (replace in commands below with your actual ID)

### Test 3: Check Status
```bash
curl http://localhost:5000/api/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Test 4: Process Job
```bash
curl -X POST http://localhost:5000/api/process/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Test 5: Download Results
```bash
# Download Excel
curl -o result.xlsx http://localhost:5000/download/a1b2c3d4-e5f6-7890-abcd-ef1234567890/output.xlsx

# Download CSV
curl -o result.csv http://localhost:5000/download/a1b2c3d4-e5f6-7890-abcd-ef1234567890/output.csv
```

---

## 🔍 Directory Structure

```
c:/Users/ddelorez/Downloads/PDF Parser Project/
├── app.py                    # Main Flask app entry point
├── requirements.txt          # Python dependencies
├── .env.example             # Environment configuration template
├── .env                     # Your local configuration (create from example)
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose orchestration
├── PHASE_2_IMPLEMENTATION.md # Complete documentation
├── QUICK_START.md          # This file
│
├── routes/
│   └── extraction.py       # API endpoints (/api/extract, /api/process, etc.)
│
├── services/
│   └── extraction_service.py # Business logic layer
│
├── templates/
│   └── index.html          # Server status page
│
├── uploads/                # Temporary PDF storage (created at runtime)
├── outputs/                # Processed Excel/CSV files (created at runtime)
├── logs/                   # Application logs (created at runtime)
│
└── src/                    # Phase 1 modules (DO NOT MODIFY)
    ├── config.py
    ├── core/
    │   ├── extraction.py
    │   └── pdf_processor.py
    ├── data/
    │   ├── validator.py
    │   └── deduplicator.py
    └── output/
        ├── excel_writer.py
        └── csv_writer.py
```

---

## 🛠️ API Endpoints Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | Health check |
| GET | `/` | Server status page |
| GET | `/api/docs` | API documentation |
| POST | `/api/extract` | Upload PDF files |
| POST | `/api/process/<job_id>` | Process uploaded PDFs |
| GET | `/api/status/<job_id>` | Check job status |
| GET | `/download/<job_id>/output.xlsx` | Download Excel |
| GET | `/download/<job_id>/output.csv` | Download CSV |

---

## 📋 Typical Workflow

```
1. POST /api/extract                  → Get job_id
   Upload PDF files
   ↓
2. GET /api/status/<job_id>           → Check if ready
   Wait for "pending" status
   ↓
3. POST /api/process/<job_id>         → Start processing
   
4. GET /api/status/<job_id>           → Monitor progress
   Polling loop until "completed" or "error"
   ↓
5. GET /download/<job_id>/output.*    → Download results
   Get Excel and/or CSV files
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Windows - Find what's using port 5000
netstat -ano | findstr :5000

# macOS/Linux - Find what's using port 5000
lsof -i :5000

# Kill the process or use different port
# Edit FLASK_PORT in .env
```

### Flask Won't Start
```bash
# Check if dependencies installed
pip list | grep -i flask

# Reinstall requirements
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.10+
```

### Docker Build Fails
```bash
# Clean build (no cache)
docker-compose build --no-cache

# Check Docker is running
docker --version

# View build logs
docker-compose build pdf-extractor
```

### Files Not Processing
```bash
# Check if template.xlsx exists in project root
# "PDF template" is required for Excel output

# Check logs
tail -f logs/pdf_parser.log

# View container logs
docker-compose logs -f pdf-extractor
```

---

## 🔑 Environment Variables

Quick reference for `.env`:

```bash
# Development/Testing
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-key-12345

# Production
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=secure-random-key-min-32-chars

# Sizes and Paths
MAX_UPLOAD_SIZE=104857600  # 100 MB
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=outputs

# Server
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

---

## ✅ Verification Checklist

- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created from `.env.example`
- [ ] `uploads/`, `outputs/`, `logs/` directories exist
- [ ] Flask starts without errors (`python app.py`)
- [ ] Health endpoint responds (`curl http://localhost:5000/api/health`)
- [ ] File upload works (`curl -F "files=@test.pdf" http://localhost:5000/api/extract`)
- [ ] Docker image builds (`docker-compose build`)
- [ ] Docker container runs (`docker-compose up -d`)
- [ ] Container health check passes (`docker-compose ps`)

---

## 📚 Next Steps

- Read [`PHASE_2_IMPLEMENTATION.md`](PHASE_2_IMPLEMENTATION.md) for complete API documentation
- See [`PHASE_1_VERIFICATION.md`](PHASE_1_VERIFICATION.md) for extraction engine details
- Prepare for Phase 3 (React frontend)

---

## 💡 Tips

1. **Use Postman/Insomnia** for testing - easier than curl commands
2. **Watch logs in real-time**: `docker-compose logs -f`
3. **Keep job_id format** - it's a UUID (36 characters)
4. **Check file sizes** - max 100 MB default per file
5. **Template required** - Excel output needs `template.xlsx` in project root

---

## 🚨 Common Errors

| Error | Solution |
|-------|----------|
| "Template file not found" | Ensure `template.xlsx` exists in project root |
| "File too large" | Increase `MAX_UPLOAD_SIZE` in `.env` |
| "Job not found" | Job_id doesn't exist or expired; use correct ID |
| "Port 5000 in use" | Change `FLASK_PORT` in `.env` or stop other app |
| "Module not found" | Run `pip install -r requirements.txt` |

---

**Ready to test?** Start with the [Testing the API](#-testing-the-api) section above! 🎯
