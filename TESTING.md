# Phase 4: Comprehensive Testing Suite and CI/CD Pipeline

## Overview

This document describes the testing infrastructure for the PDF Data Extractor project. Phase 4 implements comprehensive unit tests, integration tests, and end-to-end testing, along with GitHub Actions CI/CD pipelines for automated testing and quality assurance.

## Test Structure

```
tests/
├── backend/
│   ├── conftest.py                    # Pytest fixtures and configuration
│   ├── unit/
│   │   ├── test_extraction.py         # Core extraction logic tests
│   │   ├── test_pdf_processor.py      # PDF processing tests
│   │   ├── test_validator.py          # Data validation tests
│   │   ├── test_deduplicator.py       # Deduplication tests
│   │   ├── test_excel_writer.py       # Excel output tests
│   │   └── test_csv_writer.py         # CSV output tests
│   ├── integration/
│   │   ├── test_extraction_pipeline.py # Full extraction pipeline
│   │   └── test_api_endpoints.py       # Flask API endpoints
│   └── fixtures/
│       ├── sample.pdf                  # Sample test PDF
│       └── expected_output.json         # Expected extraction results
└── frontend/
    └── src/
        ├── services/
        │   └── api.test.js              # API service tests
        ├── components/
        │   ├── FileUpload.test.jsx      # File upload component tests
        │   ├── ProcessingStatus.test.jsx # Status display tests
        │   ├── ResultsViewer.test.jsx   # Results display tests
        │   └── ErrorNotification.test.jsx # Error handling tests
        ├── hooks/
        │   ├── useFileUpload.test.js    # File upload hook tests
        │   └── usePolling.test.js       # Polling hook tests
        └── test/
            ├── setup.js                  # Vitest configuration
            └── mockResponses.js          # Mock API responses
```

## Backend Testing

### Running Backend Tests

```bash
# All tests
pytest tests/backend

# Unit tests only
pytest tests/backend/unit -v

# Integration tests only
pytest tests/backend/integration -v

# Specific test file
pytest tests/backend/unit/test_extraction.py -v

# Specific test class
pytest tests/backend/unit/test_extraction.py::TestExtractWellName -v

# Specific test
pytest tests/backend/unit/test_extraction.py::TestExtractWellName::test_extract_well_name_with_label -v

# With coverage
pytest tests/backend --cov=src --cov-report=html --cov-report=term

# Watch mode (requires pytest-watch)
ptw tests/backend
```

### Test Categories

#### Unit Tests (90%+ coverage target)

1. **Extraction Tests** (`test_extraction.py`)
   - Well name detection with various formats
   - Record extraction and field parsing
   - Date parsing and formatting
   - Handling of missing/optional fields
   - Edge cases and regex robustness

2. **PDF Processor Tests** (`test_pdf_processor.py`)
   - PDF file validation
   - Text extraction from multiple pages
   - Error handling (corrupted files, permissions)

3. **Validator Tests** (`test_validator.py`)
   - Record validation logic
   - Data type checking
   - Required field validation
   - Negative value detection
   - Batch validation

4. **Deduplicator Tests** (`test_deduplicator.py`)
   - Exact duplicate removal
   - Sorting (well name, date)
   - Statistics calculation
   - Deduplication by well+date

5. **Writer Tests** (`test_excel_writer.py` and `test_csv_writer.py`)
   - File creation and format validation
   - Data preservation
   - Character encoding (UTF-8)
   - Special character handling

#### Integration Tests (75%+ coverage target)

1. **Pipeline Tests** (`test_extraction_pipeline.py`)
   - End-to-end extraction workflow
   - Data flow through components
   - Error recovery
   - Data consistency

2. **API Endpoint Tests** (`test_api_endpoints.py`)
   - All endpoints availability
   - Request/response validation
   - Error handling and status codes
   - CORS headers
   - Workflow integration

### Coverage Thresholds

```ini
Backend Coverage Requirements:
- Overall: 80%
- src/core/: 90%
- src/data/: 85%
- src/output/: 85%
- routes/: 80%
- services/: 80%
```

## Frontend Testing

### Running Frontend Tests

```bash
# Navigate to frontend directory
cd frontend

# Run all tests
npm test

# Run tests once (CI mode)
npm run test:run

# Run with UI
npm run test:ui

# Generate coverage report
npm run coverage

# Watch mode
npm test -- --watch
```

### Test Categories

#### Component Tests (80%+ coverage target)

1. **FileUpload Component**
   - File selection
   - Drag-and-drop
   - File validation
   - Upload button state

2. **ProcessingStatus Component**
   - Progress bar display
   - Status updates
   - Polling simulation

3. **ResultsViewer Component**
   - Results display
   - Download buttons
   - Statistics

4. **ErrorNotification Component**
   - Error display
   - Dismiss functionality
   - Retry button

#### Hook Tests (85%+ coverage target)

1. **useFileUpload Hook**
   - State management
   - File validation
   - Upload flow

2. **usePolling Hook**
   - Polling intervals
   - Stop on completion
   - Error recovery

#### Service Tests (90%+ coverage target)

1. **API Service**
   - All API methods
   - Error handling
   - Response parsing

### Coverage Thresholds

```ini
Frontend Coverage Requirements:
- Overall: 75%
- components/: 80%
- hooks/: 85%
- services/: 90%
```

## CI/CD Pipelines

### GitHub Actions Workflows

#### Backend Tests Workflow (`backend-tests.yml`)
- Triggers: Push, Pull Request (main, develop, feature/*)
- Matrix: Python 3.10, 3.11
- Tasks:
  - Install dependencies
  - Run unit tests
  - Run integration tests
  - Generate coverage report
  - Upload to Codecov
  - Comment PR with results

#### Frontend Tests Workflow (`frontend-tests.yml`)
- Triggers: Push, Pull Request (main, develop, feature/*)
- Matrix: Node 18.x, 20.x
- Tasks:
  - Install dependencies
  - Run linting
  - Run tests
  - Generate coverage
  - Upload to Codecov
  - Archive artifacts

#### Docker Build Verification Workflow (`docker-build.yml`)
- Triggers: Push, Pull Request (main, develop)
- Tasks:
  - Build backend Docker image
  - Build frontend Docker image
  - Test docker-compose setup
  - Health checks
  - Security scanning (Trivy)

### Workflow Triggering

Workflows are triggered automatically on:
- **Push to branches**: main, develop, feature/*
- **Pull requests** to main, develop
- **File changes** (filtered by path)

## Running Tests Locally

### Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### Backend Tests

```bash
# Run all tests
pytest tests/backend

# Run with coverage
pytest tests/backend --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Generate coverage report
npm run coverage

# View coverage report
open dist/coverage/index.html
```

## Test Configuration

### pytest.ini

Pytest configuration is in [`pytest.ini`](pytest.ini):
- Test discovery patterns
- Markers for test categorization
- Output options
- Logging configuration

### vitest.config.js

Vitest configuration is in [`frontend/vitest.config.js`](frontend/vitest.config.js):
- jsdom environment for DOM testing
- Coverage settings
- Setup files
- Include/exclude patterns

## Coverage Reports

### Backend Coverage

Coverage reports are generated in `htmlcov/`:
```bash
pytest tests/backend --cov=src --cov-report=html
open htmlcov/index.html
```

### Frontend Coverage

Coverage reports are in `frontend/dist/coverage/`:
```bash
cd frontend
npm run coverage
open dist/coverage/index.html
```

## Test Markers

Use pytest markers to categorize and filter tests:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run without slow tests
pytest -m "not slow"

# Run API tests
pytest -m api
```

Available markers:
- `unit` - Unit tests (fast, isolated)
- `integration` - Integration tests
- `slow` - Slow running tests
- `api` - API endpoint tests
- `extraction` - Extraction pipeline tests
- `validation` - Data validation tests
- `deduplication` - Deduplication tests
- `output` - Output writer tests

## Debugging Tests

### Backend Debugging

```python
# Add breakpoint in test
def test_example():
    import pdb; pdb.set_trace()
    # Test code here

# Run with debugging
pytest tests/backend --pdb

# Drop to debugger on failure
pytest tests/backend -x --pdb
```

### Frontend Debugging

```javascript
// Add debugger statement
test('example', () => {
  debugger
  // Test code here
})

// Run with UI for debugging
npm run test:ui
```

## Best Practices

### Backend Tests

1. **Use fixtures** for common test data
2. **Mock external dependencies** (filesystem, API calls)
3. **Test both happy path and error cases**
4. **Use descriptive test names** that explain what's being tested
5. **Keep tests small and focused**
6. **Avoid test interdependencies**

### Frontend Tests

1. **Test user interactions** not implementation details
2. **Use @testing-library** for component testing
3. **Mock API** responses with MSW or jest.mock
4. **Test accessibility** where applicable
5. **Keep tests isolated** with proper cleanup
6. **Use meaningful test descriptions**

## Continuous Improvement

### Monitoring Coverage

- Check coverage badges in README
- Monitor trend in CI/CD
- Set coverage thresholds per directory
- Review uncovered code regularly

### Performance

- Monitor test execution time
- Optimize slow tests
- Parallelize tests when possible
- Profile test suite growth

### Quality Metrics

- Track test pass rate
- Monitor flaky tests
- Review test effectiveness
- Refactor tests as needed

## Troubleshooting

### Common Issues

**Tests fail locally but pass in CI:**
- Check Python/Node version
- Verify all dependencies installed
- Clear cache: `pytest --cache-clear`

**Coverage report shows 0%:**
- Ensure .coverage file created: `coverage file .coverage`
- Check source code paths in coverage config

**Vitest can't find modules:**
- Check import paths
- Verify vitest.config.js setup files
- Clear node_modules: `rm -rf node_modules && npm install`

**Fixture not found errors:**
- Check conftest.py in correct directory
- Verify fixture names match
- Ensure conftest.py is not in __pycache__

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Testing Library Docs](https://testing-library.com/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Codecov Docs](https://docs.codecov.io/)

## Contact

For questions about testing infrastructure, refer to the team's documentation or create an issue in the repository.
