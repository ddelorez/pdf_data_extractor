# GUI-Enabled PDF Data Extractor for Oil & Gas Well Data
## Comprehensive Design Document

**Document Version:** 1.0  
**Target Users:** Oil & Gas Engineers (non-technical)  
**Primary Deployment:** Windows Standalone Executable  
**Secondary Deployment:** Docker Container  
**GUI Framework:** PyQt5  

---

## 1. Executive Summary

This design document outlines a comprehensive solution to add professional GUI capabilities to the existing PDF data extraction system while maintaining backward compatibility with the command-line interface. The solution prioritizes **reliability, ease-of-use, and minimal deployment friction** for non-technical end users in the Oil & Gas sector.

### Key Design Principles
- **User-First Design**: GUI optimized for Oil & Gas engineers, not software developers
- **Reliability Over Features**: Focus on rock-solid core functionality
- **Minimal Dependencies**: PyQt5 as single GUI dependency, bundled with Windows EXE
- **Backward Compatible**: CLI maintains full feature parity with GUI
- **Graceful Degradation**: Clear error messages when PDFs don't match expected format

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────┐
│         User Layer                               │
├─────────────────────────────────────────────────┤
│  GUI (PyQt5)          │     CLI (Command Line)  │
└─────┬─────────────────┴────────────┬────────────┘
      │                              │
      └──────────────┬───────────────┘
                     ▼
      ┌──────────────────────────────┐
      │   Application Core Layer      │
      │  (Shared Business Logic)      │
      ├──────────────────────────────┤
      │ • PDF Extraction Module       │
      │ • Data Mapping Engine         │
      │ • Validation & Deduplication │
      │ • Excel/CSV Output            │
      └──────────────┬───────────────┘
                     ▼
      ┌──────────────────────────────┐
      │    Integration Layer          │
      ├──────────────────────────────┤
      │ • pdfplumber (PDF parsing)   │
      │ • openpyxl (Excel output)    │
      │ • pandas (data handling)     │
      │ • python-dateutil (dates)    │
      └──────────────────────────────┘
```

### 2.2 Component Breakdown

#### Core Components

1. **PDF Extraction Engine** (`extraction/pdf_parser.py`)
   - Parses PDF documents using pdfplumber
   - Auto-detects well names
   - Extracts production fields (oil, gas, water, pressures, choke, days_on)
   - Returns structured data as dictionaries/DataFrames

2. **Data Mapping & Validation** (`data/mapper.py`, `data/validator.py`)
   - Maps extracted data to Excel template schema
   - Validates data types and ranges
   - Deduplicates entries
   - Handles missing/malformed data gracefully

3. **Output Generator** (`output/excel_writer.py`, `output/csv_writer.py`)
   - Writes to Excel preserving template formatting
   - Generates CSV exports for data analysis
   - Maintains data consistency across formats

4. **GUI Application** (`gui/main_window.py`, `gui/widgets/*`)
   - File selection and batch processing
   - Real-time progress tracking
   - Error reporting and logging
   - Results preview and export management

5. **CLI Handler** (`cli/cli.py`)
   - Command-line argument parsing
   - Batch file processing
   - Output path configuration
   - Maintains backward compatibility

---

## 3. Technology Stack Selection

### 3.1 GUI Framework: PyQt5

**Selection Rationale:**
- ✅ Professional, native Windows appearance
- ✅ Rich widget library for complex UIs
- ✅ Excellent for non-technical user experience
- ✅ Strong threading support for long-running tasks
- ✅ Can bundle with Windows EXE via PyInstaller
- ⚠️ Single external dependency (but properly managed)

**Alternatives Considered:**
- **Tkinter**: Built-in but limited UI polish; feels dated to non-technical users
- **Web-based (Flask/Electron)**: Better for cross-platform but adds complexity, harder deployment
- **Kivy**: Mobile-first; not ideal for professional desktop application

**Decision:** PyQt5 provides the best balance of professional UI/UX, reliable deployment, and Windows-native experience.

### 3.2 Deployment Technologies

#### Windows Standalone Executable (PRIMARY)
- **Tool**: PyInstaller with `--onefile` option
- **Advantages**:
  - Single .exe file = easy distribution
  - No Python installation required
  - Sets up in seconds on user computer
  - No dependency management for end users
- **Process**:
  1. Create frozen binary with all dependencies
  2. Code-sign executable (optional but recommended)
  3. Distribute via shared drive, email, or internal website

#### Docker Container (SECONDARY)
- **Use Case**: Team deployment, batch processing servers, Linux environments
- **Advantages**:
  - Reproducible environment across machines
  - Easy scaling for multiple users
  - Simplified IT deployment to shared servers
- **Process**:
  1. Build image with all dependencies
  2. Docker run with volume mounts for input/output
  3. Suitable for containerized enterprise deployments

---

## 4. Project Structure

```
pdf-parser-project/
│
├── src/
│   ├── __init__.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py           # PDF extraction logic
│   │   ├── well_detector.py         # Well name detection
│   │   └── field_extractor.py       # Production field extraction
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── mapper.py                # Data schema mapping
│   │   ├── validator.py             # Data validation
│   │   ├── deduplicator.py          # Remove duplicate entries
│   │   └── schemas.py               # Data models/schemas
│   │
│   ├── output/
│   │   ├── __init__.py
│   │   ├── excel_writer.py          # Excel output with template preservation
│   │   ├── csv_writer.py            # CSV export
│   │   └── file_manager.py          # Output file handling
│   │
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── application.py           # Main PyQt5 application entry
│   │   ├── main_window.py           # Primary GUI window
│   │   ├── dialogs/
│   │   │   ├── __init__.py
│   │   │   ├── file_selection.py    # File picker dialog
│   │   │   ├── progress_dialog.py   # Processing progress
│   │   │   ├── error_dialog.py      # Error reporting
│   │   │   └── results_dialog.py    # Results review
│   │   ├── widgets/
│   │   │   ├── __init__.py
│   │   │   ├── file_list.py         # File list widget
│   │   │   ├── progress_bar.py      # Progress tracking
│   │   │   └── output_preview.py    # Results preview
│   │   └── styles/
│   │       └── style.qss            # PyQt5 stylesheets
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   └── cli.py                   # Command-line interface
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py                # Logging configuration
│   │   ├── config.py                # Configuration management
│   │   └── exceptions.py            # Custom exceptions
│   │
│   └── settings/
│       ├── __init__.py
│       ├── defaults.py              # Default settings
│       └── user_config.py           # User preferences storage
│
├── templates/
│   ├── default_template.xlsx       # Default Excel template
│   └── template_config.json        # Template schema definition
│
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_pdf_parser.py
│   │   ├── test_mapper.py
│   │   └── test_validator.py
│   ├── integration/
│   │   ├── test_end_to_end.py
│   │   └── test_file_output.py
│   └── fixtures/
│       └── sample_pdfs/             # Test PDF files
│
├── build/
│   ├── windows/
│   │   ├── build.spec              # PyInstaller spec file
│   │   ├── build_exe.bat           # Build script
│   │   └── requirements-frozen.txt # Pinned dependencies
│   ├── docker/
│   │   ├── Dockerfile              # Docker image definition
│   │   └── docker-compose.yml      # Docker composition
│   └── resources/
│       ├── icon.ico                # Application icon
│       ├── banner_img.png          # Splash screen
│       └── manifest.xml            # Windows manifest
│
├── docs/
│   ├── ARCHITECTURE.md             # This design document
│   ├── USER_GUIDE.md               # End-user documentation
│   ├── DEPLOYMENT.md               # Deployment instructions
│   ├── API_REFERENCE.md            # Core API documentation
│   └── TROUBLESHOOTING.md          # Common issues and fixes
│
├── requirements/
│   ├── base.txt                    # Core dependencies
│   ├── gui.txt                     # GUI dependencies
│   ├── dev.txt                     # Development dependencies
│   └── frozen.txt                  # Pinned versions for PyInstaller
│
├── config/
│   ├── logging_config.yaml         # Logging configuration
│   └── app_config.yaml             # Application settings
│
├── run.py                          # Legacy CLI entry point (maintained)
├── gui_app.py                      # GUI entry point
├── setup.py                        # Package setup
├── README.md                       # Project overview
├── LICENSE                         # License file
└── CHANGELOG.md                    # Version history
```

---

## 5. GUI Design & User Workflow

### 5.1 Main Window Layout (PyQt5)

```
┌────────────────────────────────────────────────────┐
│  PDF Well Data Extractor                     [_][□][x] │
├────────────────────────────────────────────────────┤
│ Tab: File Processing  │  Tab: History  │  Tab: Settings │
├────────────────────────────────────────────────────┤
│                                                    │
│ 📁 Select PDF Files                         [Browse]│
│ ┌──────────────────────────────────────────────┐ │
│ │ ☐ well_report_001.pdf      (1.2 MB)        │ │
│ │ ☐ well_report_002.pdf      (0.9 MB)        │ │
│ │ ☐ well_report_003.pdf      (1.5 MB)        │ │
│ │ ☐ [Select all]              [Clear all]     │ │
│ └──────────────────────────────────────────────┘ │
│                                                    │
│ Output Location: C:\Users\...\Output     [Change] │
│                                                    │
│ Options:                                          │
│ ☐ Generate CSV files   ☐ Preserve template      │
│ ☐ Show results preview ☐ Auto-save settings     │
│                                                    │
│ [Clear Files]  [Process Files]  [Exit]           │
│                                                    │
│ Status: Ready                                     │
│ Progress: [████░░░░░░░░░░░░░░░░░] 20%           │
│                                                    │
└────────────────────────────────────────────────────┘
```

### 5.2 User Workflow (Happy Path)

1. **Launch Application**
   - User double-clicks `PDFWellExtractor.exe`
   - GUI loads with default settings
   - Pre-populated output path (Documents folder or user selection)

2. **Select PDF Files**
   - Click "Browse" button
   - File dialog opens, filtered to PDF files
   - User selects one or multiple files
   - Files appear in list with file size and metadata

3. **Configure Options**
   - Check "Generate CSV" if needed
   - Check "Show preview" to review results before saving
   - Verify output location

4. **Process Files**
   - Click "Process Files" button
   - Progress bar appears showing:
     - Current file processing (e.g., "Processing: well_001.pdf")
     - Overall progress percentage
     - Elapsed time, estimated remaining time

5. **Review Results** (if preview enabled)
   - Results dialog shows summary:
     - Files processed successfully
     - Warnings (no data found in file, partial extraction, etc.)
     - Quick preview of extracted data (first 5 rows)
   - User can choose to save or cancel

6. **Completion**
   - Success notification shows output file locations
   - User can open files, process more PDFs, or exit

### 5.3 Error Handling in GUI

**User-Friendly Error States:**

- **File Selection Errors**
  - "No PDF files selected" → Friendly reminder with Browse button
  - "File not found" → Shows which file and suggests re-selecting

- **Processing Errors**
  - "Cannot read PDF format" → Shows problematic file, suggests checking file integrity
  - "No well data found" → Suggests checking PDF matches expected well report format
  - "Output location not writable" → Prompts to select alternative location

- **Data Validation Errors**
  - "Missing required fields" → Shows which data is missing
  - "Invalid date format" → Suggests format or allows manual correction
  - "Duplicate entries detected" → Shows what was deduplicated

---

## 6. Deployment Strategy

### 6.1 Windows Standalone Executable (PRIMARY)

#### Build Process
```
Source Code → PyInstaller → Single .exe Executable
  ↓
  Include: Python runtime, PyQt5, all dependencies
  Size: ~60-80 MB (after compression)
  Runtime: Instant launch, no installation
```

#### Distribution & Installation
1. **Create Distribution Package**
   ```
   PDFWellExtractor_v1.0/
   ├── PDFWellExtractor.exe
   ├── README.txt
   ├── QUICK_START.txt
   ├── templates/
   │   └── default_template.xlsx
   └── UNINSTALL.txt (instructions)
   ```

2. **Distribution Methods**
   - Shared network drive (departmental)
   - Email with instructions
   - Internal software repository
   - USB drive for offline distribution

3. **User Installation**
   - Unzip folder to desired location (e.g., `C:\Program Files\PDFWellExtractor`)
   - Double-click executable
   - Done - no dependencies to install

#### Advantages & Considerations
- ✅ One-click execution
- ✅ No external dependencies required
- ✅ Self-contained in single directory
- ⚠️ Antivirus may flag unsigned .exe initially (solve with code signing)
- ⚠️ File size ~60-80 MB (acceptable for Windows)

#### Code Signing (Recommended)
- Acquire Windows Code Signing Certificate ($100-300 annually)
- Sign .exe to avoid user warnings
- Builds trust with organization IT

### 6.2 Docker Deployment (SECONDARY)

#### Use Cases
- Team deployment to Linux servers
- Containerized batch processing
- IT department centralized deployment
- Development and testing environments

#### Dockerfile Strategy
```dockerfile
FROM python:3.11-slim-bullseye

WORKDIR /app
COPY requirements/base.txt .
RUN pip install -r base.txt

COPY src/ ./src
COPY templates/ ./templates
COPY config/ ./config

# For headless processing via CLI
ENTRYPOINT ["python", "-m", "src.cli.cli"]
```

#### Build & Run
```bash
# Build image
docker build -f build/docker/Dockerfile -t pdf-extractor:1.0 .

# Run container with volume mounts
docker run -v /input/pdfs:/data/input \
           -v /output:/data/output \
           pdf-extractor:1.0 \
           --input /data/input \
           --output /data/output
```

#### Docker Compose (for team environments)
```yaml
version: '3.8'
services:
  pdf-extractor:
    build: .
    volumes:
      - /shared/pdfs:/data/input
      - /shared/output:/data/output
    environment:
      - LOG_LEVEL=INFO
```

---

## 7. GUI Framework Implementation Details

### 7.1 PyQt5 Component Hierarchy

```python
QMainWindow (Primary window)
├── QMenuBar
│   ├── File (Open, Recent, Exit)
│   ├── Process (Run, Stop, Batch)
│   ├── Tools (Settings, Preferences)
│   └── Help (Documentation, About, Support)
├── QTabWidget
│   ├── ProcessingTab
│   │   ├── FileListWidget
│   │   ├── OutputLocationWidget
│   │   ├── OptionsWidget
│   │   └── ProgressWidget
│   ├── HistoryTab
│   │   ├── ProcessedFilesTable
│   │   └── ResultsPreviewWidget
│   └── SettingsTab
│       ├── DefaultPathSetting
│       ├── TemplateSelectionWidget
│       └── PreferenceCheckboxes
└── QStatusBar (Status messages, file count, etc.)
```

### 7.2 Threading Strategy

**Problem**: PDF processing can take several seconds per file. Without threading, GUI freezes.

**Solution**: QThread for background processing

```python
class ProcessingThread(QThread):
    progress_update = pyqtSignal(int, str)  # percentage, current file
    processing_complete = pyqtSignal(dict)  # results dictionary
    processing_error = pyqtSignal(str)      # error message
    
    def run(self):
        # Execute long-running tasks here
        # GUI thread remains responsive
        # Emit signals to update UI
```

### 7.3 Key PyQt5 Patterns

- **Signals/Slots**: Decoupled communication between components
- **QThreadPool**: Manage multiple file processing tasks
- **QProgressDialog**: Show progress for batch operations
- **QFileDialog**: Native Windows file picker
- **QSettings**: Store user preferences (paths, options)
- **QMessageBox**: Error and success notifications

---

## 8. Data Flow & Processing Pipeline

### 8.1 Processing Sequence

```
User Input (Files + Options)
    ↓
Validation Layer
├─ Check files exist
├─ Check files are readable PDFs
└─ Validate output path writable
    ↓
Processing Engine (per file)
├─ Load PDF
├─ Extract text
├─ Detect well name
├─ Extract fields (oil, gas, water, etc.)
├─ Validate extracted data
└─ Deduplicate against existing data
    ↓
Aggregation
├─ Combine results from all files
├─ Apply global deduplication
└─ Sort/organize by well
    ↓
Output Generation
├─ Excel output (preserve template)
├─ CSV output (if enabled)
└─ Generate processing report
    ↓
Results
├─ Success notification
├─ File statistics
└─ Links to output files
```

### 8.2 Error Recovery Strategy

**Principle**: One file's error shouldn't stop entire batch

```python
for pdf_file in selected_files:
    try:
        result = process_single_file(pdf_file)
        results.append(result)
    except PDFParseError as e:
        errors.append({
            'file': pdf_file,
            'error': 'Could not parse PDF format',
            'details': str(e)
        })
        continue  # Process next file
    except DataExtractionError as e:
        warnings.append({
            'file': pdf_file,
            'warning': 'Partial data extraction',
            'details': str(e)
        })
        results.append(partial_result)
```

---

## 9. Error Handling & User Feedback

### 9.1 Error Categories & Handling

| Error Category | Example | User Message | Recovery |
|---|---|---|---|
| **File Issues** | File not found | "File was moved or deleted. Select files again." | Suggest re-browse |
| **PDF Format** | Unreadable PDF | "This doesn't appear to be a well report PDF." | Suggest file check |
| **Data Extraction** | No wells found | "No well names detected. Check PDF format." | Continue with other files |
| **Validation** | Invalid date | "Date format not recognized. Using blank." | Show what was skipped |
| **Output** | Permission denied | "Cannot write to selected folder. Choose another." | Prompt for new path |
| **System** | Out of memory | "Processing too many large files. Try fewer PDFs." | Suggest batch size |

### 9.2 Logging & Diagnostics

Each operation generates detailed logs:

```
[2026-02-25 14:32:15] INFO: Application started
[2026-02-25 14:32:20] INFO: User selected 3 PDF files
[2026-02-25 14:32:25] INFO: Processing well_001.pdf (1.2 MB)
[2026-02-25 14:32:27] EXTRACTED: Well name = "Well A-01", 12 records
[2026-02-25 14:32:30] DEBUG: Data validation completed, 2 duplicates removed
[2026-02-25 14:32:31] INFO: Output written to: C:\Output\well_data.xlsx
[2026-02-25 14:32:35] INFO: Processing complete. 3 files in 9 seconds.
```

**Log Location**: `%APPDATA%\PDFWellExtractor\logs\` (Windows)

**Log Retention**: Last 10 sessions, auto-archive older logs

---

## 10. Performance Considerations

### 10.1 Processing Performance

| Scenario | Expected Time | Optimization |
|---|---|---|
| Single PDF (1-2 MB) | 0.5-1.0 sec | Baseline |
| Batch of 5 PDFs | 3-5 sec | Parallel processing considered |
| Batch of 20+ PDFs | Sequential processing | Implement chunking (4 at a time) |

**Threading Strategy**: Max 4 parallel threads to prevent resource exhaustion

### 10.2 Memory Management

- Stream large PDFs (don't load entire file to RAM)
- Use generators for data processing where possible
- Limit result preview to first 1000 rows
- Clear processed data after writing to disk

### 10.3 UI Responsiveness

- All long operations run on separate thread
- GUI remains responsive even during batch processing
- User can cancel operation at any time
- Smooth progress updates (every 50ms minimum)

---

## 11. Implementation Roadmap

### Phase 1: Foundation (2-3 weeks)
**Goal**: Core functionality with basic GUI

- [ ] Create project structure and modular organization
- [ ] Refactor existing `run.py` into reusable modules
- [ ] Implement basic PyQt5 main window and file selection
- [ ] Add simple progress indication
- [ ] Create CLI wrapper maintaining backward compatibility
- [ ] Set up logging and error handling framework
- [ ] **Deliverable**: Basic GUI processing 1-3 files without errors

### Phase 2: Enhancement (1-2 weeks)
**Goal**: Polished user experience

- [ ] Add threading to prevent GUI freezing
- [ ] Implement batch processing with progress details
- [ ] Create detailed error dialogs with helpful messages
- [ ] Add results preview functionality
- [ ] Implement user preferences/settings persistence
- [ ] Add history tab showing previous operations
- [ ] **Deliverable**: Production-ready GUI with excellent UX

### Phase 3: Deployment (1 week)
**Goal**: Ready for distribution

- [ ] Create PyInstaller build configuration
- [ ] Build and test Windows .exe
- [ ] Create Docker image and docker-compose
- [ ] Test on clean Windows 10/11 machines
- [ ] Create user documentation and quick-start guide
- [ ] Prepare installation package with templates
- [ ] **Deliverable**: Distributable .exe and Docker image

### Phase 4: Testing & Hardening (1 week)
**Goal**: Production quality

- [ ] Comprehensive unit test coverage (>80%)
- [ ] Integration testing with real PDF samples
- [ ] Performance testing with large batches
- [ ] Edge case testing (corrupted files, unusual formats)
- [ ] Antivirus and Windows Defender scanning
- [ ] User acceptance testing with sample users
- [ ] **Deliverable**: Fully tested, production-ready solution

### Phase 5: Documentation (Final)
**Goal**: User and developer documentation

- [ ] User guide (with screenshots)
- [ ] Troubleshooting guide
- [ ] Deployment instructions
- [ ] API documentation for future maintenance
- [ ] Known issues and limitations document
- [ ] **Deliverable**: Comprehensive documentation

---

## 12. Dependencies & Version Management

### 12.1 Core Dependencies

```
# requirements/base.txt
pdfplumber==0.10.3
openpyxl==3.10.10
pandas==2.0.3
python-dateutil==2.8.2
```

### 12.2 GUI Dependencies

```
# requirements/gui.txt
PyQt5==5.15.9
PyQt5-sip==12.13.0
```

### 12.3 Development Dependencies

```
# requirements/dev.txt
pytest==7.4.0
pytest-cov==4.1.0
black==23.7.0
flake8==6.0.0
mypy==1.5.0
PyInstaller==6.0.0
```

### 12.4 Frozen Dependencies (for PyInstaller)

```
# requirements/frozen.txt
# Exact pinned versions used in built .exe
# Updated after successful build and test
```

---

## 13. Backward Compatibility Strategy

### 13.1 CLI Maintenance

The original `run.py` maintains full feature parity through refactored modules:

```python
# run.py (existing interface)
# Internally uses new modular structure
from src.core import PDFExtractor
from src.data import DataMapper
from src.output import ExcelWriter, CSVWriter

# Users can still run:
# python run.py --input "C:\PDFs" --output "C:\Output"
```

### 13.2 API Stability

- Core extraction functions have stable interface
- Data models documented and versioned
- Output format unchanged (same columns, same order)
- New features additive, not breaking

---

## 14. Success Criteria

The solution is considered complete and successful when:

- ✅ GUI launches successfully on Windows 10/11 without Python installation
- ✅ Non-technical user can process PDF files in < 2 minutes of learning
- ✅ Batch processing 5 files completes in < 10 seconds
- ✅ All error conditions show user-friendly messages
- ✅ Output files identical to existing `run.py` script
- ✅ No external dependencies required beyond PyQt5 (bundled in .exe)
- ✅ Comprehensive user documentation available
- ✅ Original CLI interface remains fully functional
- ✅ Unit test coverage > 80%
- ✅ Code follows PEP 8 standards with type hints

---

## 15. Risk Assessment & Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| **PyQt5 dependency adds complexity** | Medium | Use well-documented PyQt5, keep UI separate from business logic |
| **PDF parsing edge cases** | Medium | Comprehensive error handling, test with varied samples |
| **.exe flagged as malware** | High | Obtain code signing certificate, test with multiple antiviruses |
| **Windows EXE not portable** | Low | Test on different Windows versions; provide fallback Docker option |
| **Performance degradation with large batches** | Low | Implement threading, test with realistic file sizes |
| **User confusion with GUI** | Medium | Invest in intuitive design, provide quick-start guide, tooltips |

---

## 16. Future Enhancements (Out of Scope)

Potential future improvements for consideration:

- **Cloud Integration**: Upload results to SharePoint/OneDrive
- **Advanced Filtering**: Filter PDFs by date range, well name patterns
- **Data Visualization**: Charts/graphs of extracted well data
- **Scheduled Processing**: Automatic monitoring of PDF folder
- **Multi-Language Support**: Industry-specific terminology in different languages
- **Mobile Companion**: Mobile app to review processed results
- **Custom Templates**: User-defined extraction patterns for non-standard PDFs

---

## 17. Appendix: PyQt5 Styling & Professional Look

### 17.1 Modern Application Appearance

- Use Qt stylesheets (.qss files) for consistent professional look
- Native Windows theme integration (Fusion style)
- Subtle color scheme (blue/gray) trusted by enterprise users
- Clear typography with proper hierarchy

### 17.2 Accessibility

- Keyboard shortcuts for all major operations
- High contrast mode support
- Proper tab order through all controls
- Screen reader compatibility (PyQt5 provides MSAA support)

---

## Document End

This design document provides comprehensive guidance for implementation. Each section can serve as specification for the respective development team or mode (GUI team, deployment team, etc.).

**Next Steps After Approval:**
1. Finalize design with stakeholder feedback
2. Create detailed test cases based on scenarios
3. Begin Phase 1 implementation (refactoring, modular structure)
4. Set up development environment and CI/CD pipeline

