"""
Pytest configuration and fixtures for backend tests.
Provides common test setup and mock data.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import date
import json

from app import create_app


@pytest.fixture
def app():
    """Create and configure Flask app for testing"""
    app = create_app()
    app.config['TESTING'] = True
    
    # Create temporary directory for test uploads
    temp_dir = tempfile.mkdtemp()
    app.config['UPLOAD_FOLDER'] = temp_dir
    app.config['OUTPUT_FOLDER'] = temp_dir
    
    yield app
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Push application context for testing"""
    with app.app_context():
        yield app


@pytest.fixture
def sample_records():
    """Sample extraction records for testing"""
    return [
        {
            "Well": "HORIZON 10-01-15A",
            "Date": date(2024, 1, 15),
            "qo": 125,
            "qg": 5680,
            "qw": 45,
            "ptubing": 2150,
            "pcasing": 3400,
            "choke": 32,
            "days_on": 28,
        },
        {
            "Well": "HORIZON 10-01-15A",
            "Date": date(2024, 1, 16),
            "qo": 128,
            "qg": 5720,
            "qw": 42,
            "ptubing": 2160,
            "pcasing": 3410,
            "choke": 32,
            "days_on": 29,
        },
        {
            "Well": "HORIZON 10-01-15A",
            "Date": date(2024, 1, 17),
            "qo": 130,
            "qg": 5750,
            "qw": 40,
            "ptubing": 2170,
            "pcasing": 3420,
            "choke": 32,
            "days_on": 30,
        },
        {
            "Well": "WILDCAT 05-12-18B",
            "Date": date(2024, 1, 15),
            "qo": 95,
            "qg": 4200,
            "qw": 60,
            "ptubing": 1850,
            "pcasing": 2900,
            "choke": 24,
            "days_on": 25,
        },
        {
            "Well": "WILDCAT 05-12-18B",
            "Date": date(2024, 1, 16),
            "qo": 97,
            "qg": 4250,
            "qw": 58,
            "ptubing": 1860,
            "pcasing": 2910,
            "choke": 24,
            "days_on": 26,
        },
    ]


@pytest.fixture
def duplicate_records():
    """Sample records with duplicates for testing deduplication"""
    base_records = [
        {
            "Well": "TEST-01",
            "Date": date(2024, 1, 15),
            "qo": 100,
            "qg": 5000,
            "qw": 50,
            "ptubing": 2000,
            "pcasing": 3000,
            "choke": 30,
            "days_on": 28,
        },
    ]
    # Add exact duplicate
    base_records.append(base_records[0].copy())
    # Add similar but different record
    base_records.append({
        "Well": "TEST-01",
        "Date": date(2024, 1, 15),
        "qo": 102,
        "qg": 5100,
        "qw": 48,
        "ptubing": 2010,
        "pcasing": 3010,
        "choke": 30,
        "days_on": 28,
    })
    return base_records


@pytest.fixture
def invalid_records():
    """Sample invalid records for validation testing"""
    return [
        {
            "Well": "INVALID-01",
            "Date": "2024-01-15",  # Should be date object
            "qo": 100,
            "qg": 5000,
            "qw": 50,
        },
        {
            "Well": "INVALID-02",
            "Date": date(2024, 1, 15),
            "qo": -100,  # Negative production
            "qg": 5000,
            "qw": 50,
        },
        {
            "Well": "INVALID-03",
            "Date": date(2024, 1, 15),
            # Missing required fields
            "qo": 100,
        },
        {
            "Well": "INVALID-04",
            "Date": date(2024, 1, 15),
            "qo": "100",  # Should be int
            "qg": 5000,
            "qw": 50,
        },
    ]


@pytest.fixture
def sample_pdf_text():
    """Sample PDF text for extraction testing"""
    return """
WELL PRODUCTION DATA REPORT
Well Name: HORIZON 10-01-15A
Lease: OIL FIELD AREA

Daily Production Summary

Date: 01/15/2024
Oil Production (BBL/D): 125
Gas Production (MCF/D): 5680
Water Production (BBL/D): 45
Tubing Pressure (PSI): 2150
Casing Pressure (PSI): 3400
Choke Setting: 32
Days On Production: 28

Date: 01/16/2024
Oil Production (BBL/D): 128
Gas Production (MCF/D): 5720
Water Production (BBL/D): 42
TP: 2160
FCP: 3410
Choke: 32
Days on: 29

Date: 01/17/2024
Oil Production (BBL/D): 130
Gas Production (MCF/D): 5750
Water Production (BBL/D): 40
Tubing: 2170
Casing: 3420
Choke on: 32
Days On: 30
"""


@pytest.fixture
def sample_extracted_records():
    """Expected records from sample_pdf_text"""
    return [
        {
            "Well": "HORIZON 10-01-15A",
            "Date": date(2024, 1, 15),
            "qo": 125,
            "qg": 5680,
            "qw": 45,
            "ptubing": 2150,
            "pcasing": 3400,
            "choke": 32,
            "days_on": 28,
        },
        {
            "Well": "HORIZON 10-01-15A",
            "Date": date(2024, 1, 16),
            "qo": 128,
            "qg": 5720,
            "qw": 42,
            "ptubing": 2160,
            "pcasing": 3410,
            "choke": 32,
            "days_on": 29,
        },
        {
            "Well": "HORIZON 10-01-15A",
            "Date": date(2024, 1, 17),
            "qo": 130,
            "qg": 5750,
            "qw": 40,
            "ptubing": 2170,
            "pcasing": 3420,
            "choke": 32,
            "days_on": 30,
        },
    ]


@pytest.fixture
def json_expected_output():
    """Expected JSON output for integration tests"""
    return {
        "status": "success",
        "stats": {
            "total_records": 5,
            "valid_records": 4,
            "invalid_records": 0,
            "wells": ["HORIZON 10-01-15A", "WILDCAT 05-12-18B"],
        },
    }


# Pytest markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
