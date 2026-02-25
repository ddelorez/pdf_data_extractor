# GUI PDF Extractor - Architecture Diagrams & Reference

## 1. System Architecture Overview

```mermaid
graph TB
    subgraph "User Layer"
        GUI["PyQt5 GUI Application"]
        CLI["Command Line Interface"]
        WEB["Web Interface (Hybrid Option)"]
    end
    
    subgraph "Application Core"
        CORE["Extraction Engine"]
        MAPPER["Data Mapper"]
        VALIDATOR["Validator"]
        DEDUP["Deduplicator"]
    end
    
    subgraph "Integration Layer"
        PDF["pdfplumber"]
        EXCEL["openpyxl"]
        PANDAS["pandas"]
        DATEUTIL["python-dateutil"]
    end
    
    subgraph "Output"
        EXCEL_OUT["Excel Files"]
        CSV_OUT["CSV Files"]
    end
    
    GUI --> CORE
    CLI --> CORE
    WEB --> CORE
    CORE --> MAPPER
    MAPPER --> VALIDATOR
    VALIDATOR --> DEDUP
    DEDUP --> PDF
    DEDUP --> PANDAS
    PANDAS --> EXCEL
    PANDAS --> DATEUTIL
    EXCEL --> EXCEL_OUT
    PANDAS --> CSV_OUT
```

---

## 2. PyQt5 GUI Component Architecture

```mermaid
graph TB
    subgraph "PyQt5 MainWindow"
        MENU["QMenuBar"]
        TABS["QTabWidget"]
        STATUS["QStatusBar"]
    end
    
    subgraph "Tab 1: File Processing"
        FILE_LIST["FileListWidget"]
        BROWSE["QPushButton: Browse"]
        OPTIONS["OptionsWidget"]
        PROGRESS["ProgressBarWidget"]
        CONTROLS["QPushButton: Process/Clear/Exit"]
    end
    
    subgraph "Tab 2: History"
        HISTORY_TABLE["QTableWidget"]
        PREVIEW["PreviewWidget"]
    end
    
    subgraph "Tab 3: Settings"
        PATH_SETTING["PathSettingWidget"]
        TEMPLATE_SELECT["TemplateSelectionWidget"]
        PREFS["PreferenceCheckboxes"]
    end
    
    TABS --> FILE_LIST
    TABS --> HISTORY_TABLE
    TABS --> PATH_SETTING
    FILE_LIST --> BROWSE
    FILE_LIST --> OPTIONS
    FILE_LIST --> PROGRESS
    FILE_LIST --> CONTROLS
```

---

## 3. Data Processing Pipeline

```mermaid
graph LR
    START["User Selects PDFs"] --> VALIDATE["Validate Files"]
    VALIDATE -->|Valid| LOAD["Load PDF"]
    VALIDATE -->|Invalid| ERROR1["Show Error Dialog"]
    
    LOAD --> PARSE["Extract Text"]
    PARSE --> DETECT["Detect Well Name"]
    DETECT -->|Found| EXTRACT["Extract Fields"]
    DETECT -->|Not Found| WARN["Log Warning"]
    
    EXTRACT --> MAP["Map to Schema"]
    MAP --> VALIDATE_DATA["Validate Data Types"]
    VALIDATE_DATA -->|Valid| DEDUP["Deduplicate"]
    VALIDATE_DATA -->|Invalid| PARTIAL["Use Partial Data"]
    
    DEDUP --> AGGREGATE["Aggregate Results"]
    PARTIAL --> AGGREGATE
    
    AGGREGATE --> WRITE_EXCEL["Write Excel"]
    AGGREGATE --> WRITE_CSV["Write CSV (if enabled)"]
    
    WRITE_EXCEL --> REPORT["Generate Report"]
    WRITE_CSV --> REPORT
    
    REPORT --> SUCCESS["Show Success Dialog"]
    
    ERROR1 --> CONTINUE{Continue Processing?}
    CONTINUE -->|Yes| START
    CONTINUE -->|No| END["Exit"]
    
    SUCCESS --> END
```

---

## 4. Threading Model for Responsive UI

```mermaid
graph TB
    subgraph "Main GUI Thread"
        GUI_THREAD["GUI Event Loop"]
        USER_INPUT["User Interactions"]
        UI_UPDATE["Update Display"]
        SIGNALS["PyQt Signals"]
    end
    
    subgraph "Worker Thread"
        WORKER["ProcessingThread<br/>QThread"]
        PDF_WORK["Process PDFs"]
        EMIT_PROGRESS["Emit Progress Signal"]
        EMIT_COMPLETE["Emit Complete Signal"]
    end
    
    GUI_THREAD --> USER_INPUT
    USER_INPUT -->|Click Process| WORKER
    WORKER --> PDF_WORK
    PDF_WORK --> EMIT_PROGRESS
    EMIT_PROGRESS --> SIGNALS
    PDF_WORK --> EMIT_COMPLETE
    EMIT_COMPLETE --> SIGNALS
    SIGNALS --> UI_UPDATE
    UI_UPDATE --> GUI_THREAD
    
    style GUI_THREAD fill:#e1f5ff
    style WORKER fill:#fff3e0
```

---

## 5. Hybrid Approach: Development vs Deployment

```mermaid
graph TB
    subgraph "DEVELOPMENT PHASE"
        DEV_BACKEND["Flask Backend<br/>Python API"]
        DEV_FRONTEND["React Frontend<br/>TypeScript/CSS"]
        DEV_CORE["Core Extraction<br/>Python Modules"]
        DEV_SERVER["Local Dev Server<br/>http://localhost:5000"]
        HOT_RELOAD["Hot Reload<br/>Change detection"]
    end
    
    subgraph "TESTING PHASE"
        TEST_BACKEND["pytest<br/>Backend tests"]
        TEST_FRONTEND["Jest<br/>Frontend tests"]
        TEST_INTEGRATION["E2E Tests<br/>Full workflow"]
    end
    
    subgraph "DEPLOYMENT PHASE"
        COLLECT_FILES["Collect Files"]
        MINIMIZE["Minimize/Uglify<br/>Frontend"]
        BUNDLE_PYTHON["Create Python<br/>Package"]
        ARCHIVE["Archive"]
        PYINSTALLER["PyInstaller"]
        WRAP["Create Wrapper"]
    end
    
    subgraph "FINAL DELIVERY"
        EXE["PDFExtractor.exe<br/>70-80 MB"]
        USER["End User<br/>Double-Click and Run"]
    end
    
    DEV_BACKEND --> DEV_SERVER
    DEV_FRONTEND --> DEV_SERVER
    DEV_CORE --> DEV_SERVER
    DEV_SERVER --> HOT_RELOAD
    HOT_RELOAD --> DEV_BACKEND
    HOT_RELOAD --> DEV_FRONTEND
    
    DEV_BACKEND --> TEST_BACKEND
    DEV_FRONTEND --> TEST_FRONTEND
    TEST_BACKEND --> TEST_INTEGRATION
    TEST_FRONTEND --> TEST_INTEGRATION
    
    TEST_INTEGRATION --> COLLECT_FILES
    COLLECT_FILES --> MINIMIZE
    MINIMIZE --> BUNDLE_PYTHON
    BUNDLE_PYTHON --> ARCHIVE
    ARCHIVE --> PYINSTALLER
    PYINSTALLER --> WRAP
    WRAP --> EXE
    EXE --> USER
```

---

## 6. Error Handling Strategy

```mermaid
graph TB
    START["Process PDF"] --> TRY["Try Extract"]
    
    TRY -->|Success| VALIDATE["Validate Data"]
    TRY -->|File Error| CATCH_FILE["Catch: PDFParseError"]
    TRY -->|Other Error| CATCH_OTHER["Catch: Exception"]
    
    CATCH_FILE --> LOG_FILE["Log Error Details"]
    LOG_FILE --> MSG_FILE["Show User Message:<br/>PDF format error"]
    MSG_FILE --> CONTINUE["Continue with Next PDF"]
    
    CATCH_OTHER --> LOG_OTHER["Log Exception<br/>Get Stack Trace"]
    LOG_OTHER --> MSG_OTHER["Show Generic Error:<br/>Unexpected issue"]
    MSG_OTHER --> CONTINUE
    
    VALIDATE -->|Valid| SUCCESS["Add to Results"]
    VALIDATE -->|Invalid| WARN["Log Warning"]
    WARN --> PARTIAL["Use Partial Data"]
    PARTIAL --> SUCCESS
    
    SUCCESS --> NEXT["Next File]
    CONTINUE --> NEXT
    
    NEXT -->|More Files| START
    NEXT -->|Done| REPORT["Generate Report"]
    REPORT --> DISPLAY["Display Summary"]
    
    style CATCH_FILE fill:#ffebee
    style CATCH_OTHER fill:#ffebee
    style SUCCESS fill:#e8f5e9
```

---

## 7. Windows EXE Deployment Architecture

```mermaid
graph TB
    subgraph "BUILD PROCESS"
        SOURCE["Python Source Code"]
        DEPS["Dependencies<br/>pdfplumber, openpyxl,<br/>pandas, PyQt5"]
        PYTHON_RUNTIME["Python Runtime<br/>v3.11 Embedded"]
    end
    
    subgraph "PYINSTALLER"
        ANALYZER["Analyze Code"]
        HOOK["Apply Hooks"]
        BUNDLE["Bundle Assets"]
        UPX["Compress<br/>Optional"]
    end
    
    subgraph "SIGNING & TEST"
        SIGN["Code Signing<br/>Certificate"]
        SCAN["AV Scan<br/>Malware Check"]
        TEST["Test on Clean PC"]
    end
    
    subgraph "DELIVERY"
        EXE["PDFExtractor.exe"]
        TEMPLATE["default_template.xlsx"]
        README["README.txt"]
        QUICKSTART["QUICK_START.txt"]
        ZIP["PDFExtractor_v1.0.zip"]
    end
    
    subgraph "USER MACHINE"
        DL["Download ZIP"]
        EXTRACT["Extract Files"]
        RUN["Double-Click .exe"]
        APP["Application Runs<br/>GUI Appears"]
    end
    
    SOURCE --> ANALYZER
    DEPS --> BUNDLE
    PYTHON_RUNTIME --> BUNDLE
    ANALYZER --> HOOK
    HOOK --> BUNDLE
    BUNDLE --> UPX
    UPX --> EXE
    EXE --> SIGN
    SIGN --> SCAN
    SCAN --> TEST
    TEST --> ZIP
    EXE --> ZIP
    TEMPLATE --> ZIP
    README --> ZIP
    QUICKSTART --> ZIP
    ZIP --> DL
    DL --> EXTRACT
    EXTRACT --> RUN
    RUN --> APP
```

---

## 8. Docker Deployment Architecture

```mermaid
graph TB
    subgraph "DOCKER BUILD"
        DOCKERFILE["Dockerfile"]
        BASE["FROM python<br/>3.11-slim"]
        INSTALL["pip install<br/>dependencies"]
        COPY_SRC["Copy src/"]
        COPY_TEMPLATE["Copy templates/"]
        ENTRY["ENTRYPOINT<br/>CLI handler"]
    end
    
    subgraph "DOCKER IMAGE"
        IMAGE["pdf-extractor:1.0<br/>~400 MB"]
    end
    
    subgraph "DEPLOYMENT OPTIONS"
        SINGLE["Single Container<br/>Local GPU"]
        SWARM["Docker Swarm<br/>Team Deploy"]
        K8S["Kubernetes<br/>Enterprise Scale"]
    end
    
    subgraph "RUNTIME"
        VOLUMES["Volume Mounts<br/>/input /output"]
        ENV["Environment<br/>Variables"]
        CLI_ARGS["CLI Arguments"]
    end
    
    DOCKERFILE --> BASE
    BASE --> INSTALL
    INSTALL --> COPY_SRC
    COPY_SRC --> COPY_TEMPLATE
    COPY_TEMPLATE --> ENTRY
    ENTRY --> IMAGE
    
    IMAGE --> SINGLE
    IMAGE --> SWARM
    IMAGE --> K8S
    
    SINGLE --> VOLUMES
    VOLUMES --> ENV
    ENV --> CLI_ARGS
    CLI_ARGS --> RUN["docker run"]
```

---

## 9. Project File Structure

```
pdf-parser-project/
│
├── src/                           # Application source
│   ├── __init__.py
│   ├── core/                      # Core extraction logic
│   │   ├── pdf_parser.py
│   │   ├── well_detector.py
│   │   └── field_extractor.py
│   ├── data/                      # Data processing
│   │   ├── mapper.py
│   │   ├── validator.py
│   │   ├── deduplicator.py
│   │   └── schemas.py
│   ├── output/                    # Output generation
│   │   ├── excel_writer.py
│   │   ├── csv_writer.py
│   │   └── file_manager.py
│   ├── gui/                       # PyQt5 GUI
│   │   ├── application.py
│   │   ├── main_window.py
│   │   ├── dialogs/
│   │   ├── widgets/
│   │   └── styles/
│   ├── cli/                       # Command-line
│   │   └── cli.py
│   └── utils/                     # Utilities
│       ├── logger.py
│       ├── config.py
│       └── exceptions.py
│
├── tests/                         # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── build/                         # Build configurations
│   ├── windows/                   # PyInstaller
│   │   ├── build.spec
│   │   └── build_exe.bat
│   └── docker/                    # Docker
│       ├── Dockerfile
│       └── docker-compose.yml
│
├── templates/                     # Excel templates
│   └── default_template.xlsx
│
├── docs/                          # Documentation
├── requirements/                  # Dependencies
└── config/                        # Configuration
```

---

## 10. User Workflow State Machine

```mermaid
stateDiagram-v2
    [*] --> LaunchApp
    
    LaunchApp --> Ready: App loads successfully
    LaunchApp --> Error: App fails to load
    Error --> [*]
    
    Ready --> SelectFiles: User clicks Browse
    SelectFiles --> FileSelected: Files chosen
    FileSelected --> ConfigOptions: Files added to list
    
    ConfigOptions --> OptionsSet: User configures options
    OptionsSet --> ConfirmProcess: Ready to process
    
    ConfirmProcess --> Processing: User clicks Process
    Processing --> Progress: Showing progress bar
    Progress --> Complete: All files processed
    Progress --> UserCancel: User cancels operation
    
    Complete --> ResultsReview: Show results dialog
    ResultsReview --> SelectFiles: Process more files
    ResultsReview --> ExitApp: User closes
    
    UserCancel --> ReadyToRetry: Back to main window
    ReadyToRetry --> SelectFiles
    
    SelectFiles --> ErrorNoFiles: No files selected
    ErrorNoFiles --> SelectFiles
    
    Processing --> ProcessingError: Error during processing
    ProcessingError --> Progress: Continue with next file
    
    ExitApp --> [*]
```

---

## 11. Development Task Dependency Graph

```mermaid
graph LR
    A["1. Refactor run.py<br/>into modules"] --> B["2. Create project<br/>structure"]
    B --> C["3. Implement<br/>core modules"]
    C --> D["4. Implement<br/>data modules"]
    
    B --> E["5. Create PyQt5<br/>main window"]
    E --> F["6. Implement<br/>file widgets"]
    F --> G["7. Implement<br/>progress UI"]
    G --> H["8. Implement<br/>error dialogs"]
    
    C --> I["9. Create CLI<br/>wrapper"]
    I --> J["10. Test CLI<br/>compat"]
    J --> K["11. CLI & GUI<br/>feature parity"]
    
    D --> L["12. Setup<br/>unit tests"]
    L --> M["13. Write core<br/>tests"]
    M --> N["14. Achieve 80%<br/>coverage"]
    
    H --> O["15. PyInstaller<br/>configuration"]
    N --> O
    K --> O
    O --> P["16. Build .exe"]
    P --> Q["17. Test on<br/>clean PC"]
    Q --> R["18. Code sign"]
    
    B --> S["19. Docker<br/>setup"]
    S --> T["20. Docker<br/>testing"]
    
    R --> U["21. Create<br/>documentation"]
    T --> U
    U --> V["COMPLETE:<br/>Ready for Release"]
```

---

## 12. PyQt5 Signal/Slot Communication Pattern

```mermaid
graph TB
    subgraph "Main Thread"
        MAIN_WIN["MainWindow"]
        PROGRESS["ProgressWidget"]
    end
    
    subgraph "Worker Thread"
        WORKER["ProcessingThread<br/>QThread"]
        PROGRESS_UPDATE["progress_update<br/>Signal"]
        COMPLETE_UPDATE["processing_complete<br/>Signal"]
        ERROR_UPDATE["processing_error<br/>Signal"]
    end
    
    MAIN_WIN -->|Connect Signals| WORKER
    
    WORKER -->|Emit: 10%<br/>Processing file 1| PROGRESS_UPDATE
    WORKER -->|Emit: 50%<br/>Processing file 3| PROGRESS_UPDATE
    WORKER -->|Emit: 100%<br/>All complete| COMPLETE_UPDATE
    
    PROGRESS_UPDATE -->|Receive| PROGRESS
    PROGRESS -->|Update progress bar| MAIN_WIN
    
    COMPLETE_UPDATE -->|Receive| MAIN_WIN
    MAIN_WIN -->|Show results| MAIN_WIN
    
    WORKER -->|Error occurred| ERROR_UPDATE
    ERROR_UPDATE -->|Receive| MAIN_WIN
    MAIN_WIN -->|Show error dialog| MAIN_WIN
```

---

## 13. Data Model Relationships

```mermaid
erDiagram
    PDF ||--o{ WELL : contains
    WELL ||--o{ EXTRACTION : has
    EXTRACTION ||--o{ VALIDATION : passes
    VALIDATION ||--o{ DEDUPLICATION : checked
    DEDUPLICATION ||--o{ OUTPUT : produces
    
    PDF {
        string filepath
        int size_bytes
        timestamp extracted_at
    }
    
    WELL {
        string well_name
        int record_count
        date extraction_date
    }
    
    EXTRACTION {
        float oil_production
        float gas_production
        float water_production
        float pressure_tubing
        float pressure_casing
        float choke_size
        int days_on
    }
    
    VALIDATION {
        string field_name
        boolean is_valid
        string validation_error
    }
    
    DEDUPLICATION {
        int duplicate_count
        string dedup_method
        array removed_records
    }
    
    OUTPUT {
        string excel_file
        string csv_file
        timestamp creation_time
    }
```

---

## 14. Performance Metrics & Targets

```mermaid
graph TB
    subgraph "Single File Processing"
        LOAD_TIME["PDF Load: 100-200ms"]
        PARSE_TIME["Text Extract: 150-300ms"]
        DETECT_TIME["Well Detection: 50-100ms"]
        EXTRACT_TIME["Field Extraction: 200-400ms"]
        MAP_TIME["Data Mapping: 50-100ms"]
        TOTAL_SINGLE["Target: <1.0 sec per file"]
    end
    
    subgraph "Batch Processing"
        BATCH_5["5 files: 3-5 sec"]
        BATCH_10["10 files: 6-10 sec"]
        BATCH_20["20 files: 12-20 sec"]
        BATCH_TARGET["Target: Keep UI responsive"]
    end
    
    subgraph "Memory"
        MEM_STARTUP["Startup: 80-120 MB"]
        MEM_PROCESSING["Per file: +20-40 MB"]
        MEM_TOTAL["Total limit: 500 MB"]
        MEM_THREAD["Max threads: 4<br/>(prevent exhaustion)"]
    end
    
    LOAD_TIME --> TOTAL_SINGLE
    PARSE_TIME --> TOTAL_SINGLE
    DETECT_TIME --> TOTAL_SINGLE
    EXTRACT_TIME --> TOTAL_SINGLE
    MAP_TIME --> TOTAL_SINGLE
    
    BATCH_5 --> BATCH_TARGET
    BATCH_10 --> BATCH_TARGET
    BATCH_20 --> BATCH_TARGET
```

---

## 15. Risk Mitigation Roadmap

```mermaid
graph TB
    subgraph "RISK 1: PyQt5 Complexity"
        R1_PROBLEM["Steep learning curve"]
        R1_MITIGATION["Use template patterns<br/>Keep UI separate<br/>Good documentation"]
        R1_MONITOR["Code review<br/>Unit tests"]
    end
    
    subgraph "RISK 2: .exe Antivirus"
        R2_PROBLEM["Flagged as malware"]
        R2_MITIGATION["Code signing cert<br/>Reputable build process<br/>Community reporting"]
        R2_MONITOR["Test with VirusTotal<br/>Defender scan"]
    end
    
    subgraph "RISK 3: PDF Parsing"
        R3_PROBLEM["Edge case failures"]
        R3_MITIGATION["Test samples<br/>Error handling<br/>Logging & diagnostics"]
        R3_MONITOR["User reports<br/>Log analysis"]
    end
    
    subgraph "RISK 4: Performance"
        R4_PROBLEM["Slow batch processing"]
        R4_MITIGATION["Threading<br/>Batch limits<br/>Memory mgmt"]
        R4_MONITOR["Performance tests<br/>User feedback"]
    end
    
    R1_PROBLEM --> R1_MITIGATION
    R1_MITIGATION --> R1_MONITOR
    
    R2_PROBLEM --> R2_MITIGATION
    R2_MITIGATION --> R2_MONITOR
    
    R3_PROBLEM --> R3_MITIGATION
    R3_MITIGATION --> R3_MONITOR
    
    R4_PROBLEM --> R4_MITIGATION
    R4_MITIGATION --> R4_MONITOR
```

---

## Key Takeaways from Diagrams

1. **System Architecture**: Clear separation between GUI, Core Logic, and Integration layers
2. **Threading**: Worker threads keep GUI responsive during long operations
3. **Error Handling**: Graceful degradation - one file's error doesn't stop batch
4. **Deployment**: PyInstaller creates single .exe with all dependencies bundled
5. **Hybrid Approach**: Flask + React frontend offers faster development iteration
6. **Testing**: Comprehensive unit tests and integration tests at each phase
7. **User Experience**: State machine ensures logical workflow and error recovery
8. **Performance**: Threading limits and batch processing prevent resource exhaustion

All diagrams are compatible with both PyQt5 Desktop and Hybrid (Flask+React) approaches.

