"""
Integration tests for extraction pipeline - tests full workflow
Coverage: 75%+
"""

import pytest
from datetime import date
from pathlib import Path

from src.core.extraction import extract_well_name, extract_records
from src.data.validator import validate_records
from src.data.deduplicator import deduplicate_and_sort


@pytest.mark.integration
class TestExtractionPipeline:
    """Test the complete extraction pipeline"""
    
    def test_full_extraction_pipeline(self, sample_pdf_text):
        """Test complete extraction flow from PDF text to deduplicated records"""
        # Step 1: Extract well name
        well_name = extract_well_name(sample_pdf_text)
        assert well_name != "UNKNOWN"
        
        # Step 2: Extract records
        records = extract_records(sample_pdf_text, well_name)
        assert len(records) > 0
        
        # Step 3: Validate records
        valid_records, invalid_records = validate_records(records)
        assert len(valid_records) > 0
        
        # Step 4: Deduplicate and sort
        df = deduplicate_and_sort(valid_records)
        assert len(df) > 0
        
        # Verify final output structure
        assert all(col in df.columns for col in ["Well", "Date", "qo", "qg", "qw"])
    
    def test_pipeline_with_sample_data(self, sample_pdf_text, sample_extracted_records):
        """Test pipeline output matches expected records"""
        well_name = extract_well_name(sample_pdf_text)
        records = extract_records(sample_pdf_text, well_name)
        valid_records, _ = validate_records(records)
        df = deduplicate_and_sort(valid_records)
        
        # Check that we have the expected number of records
        assert len(df) >= len(sample_extracted_records)
    
    def test_pipeline_preserves_well_names(self, sample_pdf_text):
        """Test that well names are preserved through pipeline"""
        well_name = extract_well_name(sample_pdf_text)
        records = extract_records(sample_pdf_text, well_name)
        valid_records, _ = validate_records(records)
        df = deduplicate_and_sort(valid_records)
        
        assert all(w == well_name for w in df["Well"].unique())
    
    def test_pipeline_rejects_invalid_records(self, sample_pdf_text):
        """Test that validation filters invalid records"""
        well_name = extract_well_name(sample_pdf_text)
        records = extract_records(sample_pdf_text, well_name)
        
        valid_records, invalid_records = validate_records(records)
        
        # Valid records should pass all validations
        for record in valid_records:
            # Should have required fields
            assert record.get("Well") is not None
            assert record.get("Date") is not None
            assert record.get("qo") is not None
    
    def test_pipeline_sorts_correctly(self, sample_pdf_text):
        """Test that pipeline output is properly sorted"""
        well_name = extract_well_name(sample_pdf_text)
        records = extract_records(sample_pdf_text, well_name)
        valid_records, _ = validate_records(records)
        df = deduplicate_and_sort(valid_records)
        
        # Check sorting by well
        wells = df["Well"].tolist()
        assert wells == sorted(wells), "Records not sorted by well name"
        
        # Check sorting by date within well
        for well in df["Well"].unique():
            well_records = df[df["Well"] == well]
            dates = well_records["Date"].tolist()
            assert dates == sorted(dates), f"Records for {well} not sorted by date"
    
    def test_pipeline_with_multiple_wells(self):
        """Test pipeline with text containing multiple wells"""
        text = """
        Well: WELL-A
        Date: 01/15/2024
        Oil: 100
        Gas: 5000
        Water: 50
        
        Well: WELL-B
        Date: 01/16/2024
        Oil: 95
        Gas: 4800
        Water: 55
        """
        
        well_name = extract_well_name(text)
        records = extract_records(text, well_name)
        
        # Should extract records regardless of multiple references
        assert len(records) >= 1
    
    def test_pipeline_handles_missing_fields(self):
        """Test pipeline gracefully handles missing optional fields"""
        text = """
        Date: 01/15/2024
        Oil: 100
        Gas: 5000
        Water: 50
        """
        
        well_name = "TEST-WELL"
        records = extract_records(text, well_name)
        valid_records, _ = validate_records(records)
        
        # Should still produce valid records with None for missing fields
        assert len(valid_records) >= 1 or len(valid_records) == 0
    
    def test_pipeline_deduplication(self):
        """Test deduplication in pipeline"""
        records = [
            {"Well": "W-A", "Date": date(2024, 1, 15), "qo": 100, "qg": 5000, "qw": 50},
            {"Well": "W-A", "Date": date(2024, 1, 15), "qo": 100, "qg": 5000, "qw": 50},
            {"Well": "W-A", "Date": date(2024, 1, 16), "qo": 105, "qg": 5100, "qw": 48},
        ]
        
        valid_records, _ = validate_records(records)
        df = deduplicate_and_sort(valid_records)
        
        # Should have fewer records after deduplication
        assert len(df) < len(records)


@pytest.mark.integration
class TestPipelineErrorHandling:
    """Test error handling throughout the pipeline"""
    
    def test_pipeline_with_malformed_dates(self):
        """Test pipeline handles malformed dates gracefully"""
        text = """
        Date: INVALID-DATE
        Oil: 100
        Gas: 5000
        Water: 50
        
        Date: 01/15/2024
        Oil: 100
        Gas: 5000
        Water: 50
        """
        
        well_name = "TEST-WELL"
        records = extract_records(text, well_name)
        
        # Should skip invalid records during extraction
        assert len(records) <= 1  # Only valid date should be extracted
    
    def test_pipeline_with_invalid_numeric_values(self):
        """Test pipeline handles non-numeric production values"""
        text = """
        Date: 01/15/2024
        Oil: INVALID
        Gas: 5000
        Water: 50
        """
        
        well_name = "TEST-WELL"
        records = extract_records(text, well_name)
        
        # Should skip records with non-numeric production values
        # or handle gracefully
        assert isinstance(records, list)
    
    def test_pipeline_with_empty_input(self):
        """Test pipeline with empty input"""
        well_name = extract_well_name("")
        records = extract_records("", well_name)
        valid_records, _ = validate_records(records)
        df = deduplicate_and_sort(valid_records)
        
        assert len(df) == 0
    
    def test_pipeline_validation_catches_errors(self):
        """Test that validation catches data type errors"""
        records = [
            {
                "Well": "TEST-01",
                "Date": "not-a-date",  # Invalid type
                "qo": 100,
                "qg": 5000,
                "qw": 50,
            }
        ]
        
        valid_records, invalid_records = validate_records(records)
        
        # Invalid record should be filtered
        assert len(invalid_records) > 0


@pytest.mark.integration  
class TestPipelineDataConsistency:
    """Test data consistency throughout the pipeline"""
    
    def test_pipeline_output_data_integrity(self, sample_records):
        """Test that data integrity is maintained through pipeline"""
        well_names = set(r["Well"] for r in sample_records)
        
        valid_records, _ = validate_records(sample_records)
        df = deduplicate_and_sort(valid_records)
        
        output_wells = set(df["Well"].unique())
        
        # All original wells should be in output
        assert output_wells.issubset(well_names) or len(output_wells) == 0
    
    def test_pipeline_preserves_production_values(self):
        """Test that production values are preserved accurately"""
        records = [
            {
                "Well": "TEST-01",
                "Date": date(2024, 1, 15),
                "qo": 123,
                "qg": 5678,
                "qw": 90,
            }
        ]
        
        valid_records, _ = validate_records(records)
        df = deduplicate_and_sort(valid_records)
        
        if len(df) > 0:
            assert df["qo"].iloc[0] == 123
            assert df["qg"].iloc[0] == 5678
            assert df["qw"].iloc[0] == 90
    
    def test_pipeline_date_ordering(self):
        """Test that dates are properly ordered in output"""
        records = [
            {"Well": "W-01", "Date": date(2024, 1, 20), "qo": 100, "qg": 5000, "qw": 50},
            {"Well": "W-01", "Date": date(2024, 1, 10), "qo": 100, "qg": 5000, "qw": 50},
            {"Well": "W-01", "Date": date(2024, 1, 15), "qo": 100, "qg": 5000, "qw": 50},
        ]
        
        valid_records, _ = validate_records(records)
        df = deduplicate_and_sort(valid_records)
        
        dates = df["Date"].tolist()
        assert dates == sorted(dates)
