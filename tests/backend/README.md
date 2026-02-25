# Backend Testing Guide

## Overview

Backend tests are organized into unit tests and integration tests, with comprehensive coverage of the extraction pipeline, data validation, and API endpoints.

## Test Structure

```
tests/backend/
├── __init__.py
├── conftest.py                    # Pytest fixtures
├── unit/                          # Fast, isolated tests
│   ├── test_extraction.py         # Extraction logic (90%+ coverage)
│   ├── test_pdf_processor.py      # PDF processing (85%+ coverage)
│   ├── test_validator.py          # Data validation (90%+ coverage)
│   ├── test_deduplicator.py       # Deduplication (85%+ coverage)
│   ├── test_excel_writer.py       # Excel output (80%+ coverage)
│   └── test_csv_writer.py         # CSV output (80%+ coverage)
├── integration/                   # Full workflow tests
│   ├── test_extraction_pipeline.py # End-to-end pipeline (75%+ coverage)
│   └── test_api_endpoints.py      # Flask endpoints (85%+ coverage)
└── fixtures/                      # Test data
    └── sample.pdf                 # Sample test PDF
```

## Quick Start

### Running Tests

```bash
# Run all backend tests
pytest tests/backend

# Run unit tests only
pytest tests/backend/unit -v

# Run integration tests only
pytest tests/backend/integration -v

# Run specific test file
pytest tests/backend/unit/test_extraction.py -v

# Run specific test class
pytest tests/backend/unit/test_extraction.py::TestExtractWellName -v

# Run specific test
pytest tests/backend/unit/test_extraction.py::TestExtractWellName::test_extract_well_name_with_label -v
```

### With Coverage

```bash
# Generate coverage report
pytest tests/backend --cov=src --cov-report=html --cov-report=term

# View HTML coverage report
open htmlcov/index.html

# Check coverage thresholds
coverage report --fail-under=80
```

### By Test Marker

```bash
# Run only unit tests
pytest tests/backend -m unit

# Run only integration tests  
pytest tests/backend -m integration

# Run extraction tests
pytest -m extraction

# Run all but slow tests
pytest -m "not slow"
```

## Fixtures

All fixtures are defined in [`conftest.py`](./conftest.py):

### Sample Data Fixtures

- `sample_records` - Valid production records for testing
- `duplicate_records` - Records with duplicates for dedup testing
- `invalid_records` - Invalid records for validation testing
- `sample_pdf_text` - Sample PDF text for extraction tests
- `sample_extracted_records` - Expected extraction results
- `json_expected_output` - Expected JSON output

### App/Client Fixtures (Flask)

- `app` - Flask test app with temp directories
- `client` - Flask test client
- `app_context` - Application context

Usage:

```python
def test_something(sample_records, client):
    """Test using fixtures"""
    assert len(sample_records) > 0
    response = client.get('/api/health')
    assert response.status_code == 200
```

## Unit Tests

### test_extraction.py

Tests the core extraction logic in `src/core/extraction.py`:

**Well Name Extraction**
- Various label formats (Well:, Lease:, Well Name:)
- Standard O&G nomenclature
- Case insensitivity
- Multiline text handling
- Edge cases (invalid candidates, too short names)

**Record Extraction**
- Basic record extraction
- Date parsing and formatting
- Production volume extraction (oil, gas, water)
- pressure fields (tubing, casing)
- Operational fields (choke, days_on)
- Multiple field label formats
- Missing optional fields
- No production data handling
- Invalid date handling
- Whitespace normalization

**Coverage: 90%+**

```bash
pytest tests/backend/unit/test_extraction.py -v
```

### test_pdf_processor.py

Tests PDF processing in `src/core/pdf_processor.py`:

- File existence validation
- Text extraction from pages
- Multi-page handling
- Error handling
- Corrupted file detection

**Coverage: 85%+**

```bash
pytest tests/backend/unit/test_pdf_processor.py -v
```

### test_validator.py

Tests data validation in `src/data/validator.py`:

- Single record validation
- Required field checking
- Data type validation
- Negative value detection
- Completeness scoring
- Batch validation
- Error annotation

**Coverage: 90%+**

```bash
pytest tests/backend/unit/test_validator.py -v
```

### test_deduplicator.py

Tests deduplication in `src/data/deduplicator.py`:

- Exact duplicate removal
- Deduplication by well+date
- Sorting (well name, date)
- Statistics calculation
- Empty input handling
- Data preservation

**Coverage: 85%+**

```bash
pytest tests/backend/unit/test_deduplicator.py -v
```

### test_excel_writer.py

Tests Excel output in `src/output/excel_writer.py`:

- File creation
- Data preservation
- Date formatting
- Column mapping
- Special characters
- Large values
- Zero values

**Coverage: 80%+**

```bash
pytest tests/backend/unit/test_excel_writer.py -v
```

### test_csv_writer.py

Tests CSV output in `src/output/csv_writer.py`:

- File creation
- UTF-8 encoding
- CSV formatting
- Special characters
- Newlines handling
- Unicode support

**Coverage: 80%+**

```bash
pytest tests/backend/unit/test_csv_writer.py -v
```

## Integration Tests

### test_extraction_pipeline.py

Tests the complete extraction workflow:

- End-to-end pipeline (extraction → validation → deduplication)
- Well name preservation
- Multiple wells handling
- Data consistency
- Error recovery
- Sorting verification
- Deduplication effectiveness

**Coverage: 75%+**

```bash
pytest tests/backend/integration/test_extraction_pipeline.py -v -m integration
```

### test_api_endpoints.py

Tests Flask API endpoints in `routes/`:

**Endpoints Tested:**
- `GET /api/health` - Health check
- `POST /api/extract` - File upload
- `GET /api/status/<job_id>` - Job status
- `POST /api/process/<job_id>` - Process job
- `GET /download/<job_id>/output.xlsx` - Excel download
- `GET /download/<job_id>/output.csv` - CSV download

**Tests Include:**
- Endpoint availability
- Request validation
- Response format
- Error handling (400, 404, 413, 422, 500)
- CORS headers
- Request/response flow

**Coverage: 85%+**

```bash
pytest tests/backend/integration/test_api_endpoints.py -v -m api
```

## Coverage Thresholds

Minimum coverage targets:

```ini
[Coverage]
overall = 80%
src/core = 90%
src/data = 85%
src/output = 85%
routes = 80%
services = 80%
```

Check coverage:
```bash
pytest tests/backend --cov=src --cov=routes --cov=services --cov-report=term
```

## CI/CD Integration

Tests run automatically on:
- Push to main, develop, feature/* branches
- Pull requests to main, develop
- File changes (filtered by path)

See [`.github/workflows/backend-tests.yml`](.github/workflows/backend-tests.yml) for workflow details.

## Debugging Tests

### Debugging with pdb

```python
def test_example():
    import pdb; pdb.set_trace()
    # Code to debug here
```

Run with:
```bash
pytest tests/backend --pdb
```

### Drop to debugger on failure

```bash
pytest tests/backend -x --pdb
```

### Verbose output

```bash
pytest tests/backend -vv

# With full diff
pytest tests/backend -vv --tb=long
```

### Show print statements

```bash
pytest tests/backend -s
```

## Performance

###Test Execution Times

- Unit tests: ~5-10 seconds
- Integration tests: ~5-10 seconds
- Total with coverage: ~30-40 seconds

### Optimization

```bash
# Run tests in parallel (requires pytest-xdist)
pytest tests/backend -n auto

# Run only new/changed tests
pytest tests/backend --lf

# Run failed tests first
pytest tests/backend --ff
```

## Troubleshooting

### Import errors

Ensure you're running pytest from root directory:
```bash
pytest tests/backend  # from project root
```

### Fixture not found

Check that `conftest.py` is in the correct directory:
```
tests/backend/conftest.py  # Should be here
```

### Coverage shows 0%

```bash
# Clear coverage cache
rm .coverage
pytest tests/backend --cov=src --cov-report=html
```

### Tests timeout

Increase timeout in pytest.ini or pass on command line:
```bash
pytest tests/backend --timeout=300
```

## Best Practices

1. **Use fixtures** for common test data
2. **Test edge cases** not just happy paths
3. **Mock external dependencies** (file I/O, network)
4. **Keep tests small** and focused
5. **Use descriptive names** that explain what's tested
6. **Avoid test interdependencies**
7. **Clean up** after tests (temp files, mocks)
8. **Use markers** to categorize tests

## Adding New Tests

### Structure

```python
import pytest
from module import function_to_test

@pytest.mark.unit
class TestFunctionality:
    """Test category description"""
    
    def test_basic_case(self, fixture_name):
        """Test description"""
        # Arrange
        input_data = fixture_name
        
        # Act
        result = function_to_test(input_data)
        
        # Assert
        assert result is not None
```

### Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Fixtures: `fixture_name`
- Helpers: `helper_*` or `make_*`

### Common Patterns

**Testing exceptions:**
```python
def test_raises_error():
    with pytest.raises(ValueError):
        function_that_raises()
```

**Parametrized tests:**
```python
@pytest.mark.parametrize('input,expected', [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_multiply(input, expected):
    assert input * 2 == expected
```

**Mocking:**
```python
from unittest.mock import patch

def test_with_mock(monkeypatch):
    monkeypatch.setattr('module.function', lambda: 'mocked')
    result = other_function()
    assert result == 'expected'
```

## Related Documentation

- [Main Testing Guide](../../TESTING.md)
- [Frontend Testing Guide](../../frontend/TESTING.md)
- [pytest Documentation](https://docs.pytest.org/)
