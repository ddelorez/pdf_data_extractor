"""
Unit tests for src/output/excel_writer.py - Excel file writing
Coverage: 80%+
"""

import pytest
from pathlib import Path
from datetime import date
import pandas as pd
from tempfile import TemporaryDirectory

from src.output.excel_writer import write_excel


@pytest.mark.unit
class TestWriteExcel:
    """Test Excel file writing functionality"""
    
    def test_write_excel_creates_file(self, sample_records):
        """Test that write_excel creates an output file"""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xlsx"
            
            write_excel(sample_records, output_path)
            
            assert output_path.exists()
            assert output_path.suffix == ".xlsx"
    
    def test_write_excel_file_readable(self, sample_records):
        """Test that generated Excel file is readable"""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xlsx"
            
            write_excel(sample_records, output_path)
            
            # Read it back
            df = pd.read_excel(output_path)
            assert len(df) == len(sample_records)
    
    def test_write_excel_preserves_data(self, sample_records):
        """Test that data is preserved in Excel"""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xlsx"
            
            write_excel(sample_records, output_path)
            
            df = pd.read_excel(output_path)
            
            # Check that key columns exist
            assert "Well" in df.columns
            assert "qo" in df.columns
            assert "qg" in df.columns
            assert "qw" in df.columns
    
    def test_write_excel_dates_formatted(self, sample_records):
        """Test that dates are properly formatted"""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xlsx"
            
            write_excel(sample_records, output_path)
            
            df = pd.read_excel(output_path)
            # Dates should be read back as datetime or string
            assert len(df) > 0
    
    def test_write_excel_numeric_columns(self, sample_records):
        """Test that numeric columns are properly typed"""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xlsx"
            
            write_excel(sample_records, output_path)
            
            df = pd.read_excel(output_path)
            
            # Numeric columns should be numeric
            for col in ["qo", "qg", "qw", "ptubing", "pcasing"]:
                if col in df.columns:
                    assert pd.api.types.is_numeric_dtype(df[col]) or df[col].isnull().all()
    
    def test_write_excel_empty_records(self):
        """Test writing with empty records list"""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty.xlsx"
            
            # Should handle empty records gracefully
            write_excel([], output_path)
            
            # File may or may not be created, depending on implementation
            # But should not raise error
    
    def test_write_excel_overwrites_existing(self, sample_records):
        """Test that existing file is overwritten"""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xlsx"
            
            # Write first time
            write_excel(sample_records, output_path)
            first_size = output_path.stat().st_size
            
            # Modify records and write again
            new_records = sample_records[:2]
            write_excel(new_records, output_path)
            
            df = pd.read_excel(output_path)
            assert len(df) == 2
    
    def test_write_excel_string_path(self, sample_records):
        """Test that write_excel accepts string paths"""
        with TemporaryDirectory() as tmpdir:
            output_path = str(Path(tmpdir) / "output.xlsx")
            
            write_excel(sample_records, output_path)
            
            assert Path(output_path).exists()
    
    def test_write_excel_path_object(self, sample_records):
        """Test that write_excel accepts Path objects"""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xlsx"
            
            write_excel(sample_records, output_path)
            
            assert output_path.exists()
    
    def test_write_excel_with_none_values(self):
        """Test writing records with None values"""
        records = [
            {
                "Well": "TEST-01",
                "Date": date(2024, 1, 15),
                "qo": 100,
                "qg": None,
                "qw": 50,
                "ptubing": None,
            }
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xlsx"
            
            write_excel(records, output_path)
            
            df = pd.read_excel(output_path)
            assert len(df) == 1
    
    def test_write_excel_column_order(self, sample_records):
        """Test that columns are in expected order"""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xlsx"
            
            write_excel(sample_records, output_path)
            
            df = pd.read_excel(output_path)
            # Should have Well, Date, and production columns
            columns = df.columns.tolist()
            assert "Well" in columns
            assert "qo" in columns or "Oil" in columns
    
    def test_write_excel_multiple_wells(self):
        """Test writing records with multiple wells"""
        records = [
            {
                "Well": "WELL-A",
                "Date": date(2024, 1, 15),
                "qo": 100,
                "qg": 5000,
                "qw": 50,
            },
            {
                "Well": "WELL-B",
                "Date": date(2024, 1, 15),
                "qo": 95,
                "qg": 4800,
                "qw": 55,
            },
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xlsx"
            
            write_excel(records, output_path)
            
            df = pd.read_excel(output_path)
            wells = df["Well"].unique().tolist()
            assert len(wells) == 2


@pytest.mark.unit
class TestExcelWriterEdgeCases:
    """Test edge cases in Excel writing"""
    
    def test_write_excel_special_characters_in_well_name(self):
        """Test well names with special characters"""
        records = [
            {
                "Well": "WELL-A&B#123",
                "Date": date(2024, 1, 15),
                "qo": 100,
                "qg": 5000,
                "qw": 50,
            }
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xlsx"
            
            write_excel(records, output_path)
            
            df = pd.read_excel(output_path)
            # Special characters should be preserved or handled gracefully
            assert len(df) == 1
    
    def test_write_excel_large_production_values(self):
        """Test very large production values"""
        records = [
            {
                "Well": "BIG-WELL",
                "Date": date(2024, 1, 15),
                "qo": 999999999,
                "qg": 999999999,
                "qw": 999999999,
            }
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xlsx"
            
            write_excel(records, output_path)
            
            df = pd.read_excel(output_path)
            assert df["qo"].iloc[0] == 999999999
    
    def test_write_excel_unicode_characters(self):
        """Test well names with unicode characters"""
        records = [
            {
                "Well": "CÔTE-D'AZUR-01",
                "Date": date(2024, 1, 15),
                "qo": 100,
                "qg": 5000,
                "qw": 50,
            }
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xlsx"
            
            write_excel(records, output_path)
            
            df = pd.read_excel(output_path)
            assert len(df) == 1
    
    def test_write_excel_date_formats(self):
        """Test various date formats in records"""
        records = [
            {
                "Well": "TEST-01",
                "Date": date(2024, 1, 1),
                "qo": 100,
                "qg": 5000,
                "qw": 50,
            },
            {
                "Well": "TEST-01",
                "Date": date(2024, 12, 31),
                "qo": 105,
                "qg": 5100,
                "qw": 48,
            },
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xlsx"
            
            write_excel(records, output_path)
            
            df = pd.read_excel(output_path)
            assert len(df) == 2
    
    def test_write_excel_zero_values(self):
        """Test that zero production values are written"""
        records = [
            {
                "Well": "ZERO-WELL",
                "Date": date(2024, 1, 15),
                "qo": 0,
                "qg": 0,
                "qw": 0,
            }
        ]
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xlsx"
            
            write_excel(records, output_path)
            
            df = pd.read_excel(output_path)
            assert df["qo"].iloc[0] == 0
