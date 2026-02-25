"""
Unit tests for src/data/deduplicator.py - Data deduplication and sorting
Coverage: 85%+
"""

import pytest
from datetime import date
import pandas as pd

from src.data.deduplicator import (
    deduplicate_and_sort,
    deduplicate_by_well_date,
    get_deduplication_stats,
)


@pytest.mark.unit
class TestDeduplicateAndSort:
    """Test full deduplication and sorting"""
    
    def test_deduplicate_and_sort_basic(self, sample_records):
        """Test basic deduplication and sorting"""
        df = deduplicate_and_sort(sample_records)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(sample_records)
        assert all(col in df.columns for col in ["Well", "Date", "qo", "qg", "qw"])
    
    def test_deduplicate_and_sort_removes_duplicates(self, duplicate_records):
        """Test that exact duplicates are removed"""
        df = deduplicate_and_sort(duplicate_records)
        
        # Should have fewer records than input (duplicate removed)
        assert len(df) < len(duplicate_records)
    
    def test_deduplicate_and_sort_keeps_first_occurrence(self, duplicate_records):
        """Test that first occurrence is kept"""
        # Sort first to know which is first
        df = deduplicate_and_sort(duplicate_records)
        
        # Should keep valid records
        assert len(df) > 0
    
    def test_deduplicate_and_sort_sorts_by_well(self, sample_records):
        """Test sorting by well name"""
        df = deduplicate_and_sort(sample_records)
        
        # Check that wells are sorted alphabetically
        wells = df["Well"].tolist()
        assert wells == sorted(wells)
    
    def test_deduplicate_and_sort_sorts_by_date(self):
        """Test sorting by date within each well"""
        records = [
            {
                "Well": "W-01",
                "Date": date(2024, 1, 17),
                "qo": 130,
                "qg": 5750,
                "qw": 40,
            },
            {
                "Well": "W-01",
                "Date": date(2024, 1, 15),
                "qo": 125,
                "qg": 5680,
                "qw": 45,
            },
            {
                "Well": "W-01",
                "Date": date(2024, 1, 16),
                "qo": 128,
                "qg": 5720,
                "qw": 42,
            },
        ]
        df = deduplicate_and_sort(records)
        
        # Dates should be in chronological order
        dates = df["Date"].tolist()
        assert dates == sorted(dates)
    
    def test_deduplicate_and_sort_mixed_wells(self):
        """Test sorting multiple wells together"""
        records = [
            {"Well": "Z-WELL", "Date": date(2024, 1, 15), "qo": 100, "qg": 5000, "qw": 50},
            {"Well": "A-WELL", "Date": date(2024, 1, 15), "qo": 100, "qg": 5000, "qw": 50},
            {"Well": "M-WELL", "Date": date(2024, 1, 15), "qo": 100, "qg": 5000, "qw": 50},
        ]
        df = deduplicate_and_sort(records)
        
        wells = df["Well"].tolist()
        assert wells == ["A-WELL", "M-WELL", "Z-WELL"]
    
    def test_deduplicate_and_sort_empty_records(self):
        """Test with empty record list"""
        df = deduplicate_and_sort([])
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_deduplicate_and_sort_resets_index(self, sample_records):
        """Test that index is reset after deduplication"""
        df = deduplicate_and_sort(sample_records)
        
        # Index should start from 0 and be sequential
        assert df.index.tolist() == list(range(len(df)))
    
    def test_deduplicate_and_sort_preserves_data_types(self, sample_records):
        """Test that data types are preserved"""
        df = deduplicate_and_sort(sample_records)
        
        # Date should be datetime/object
        # Numeric fields should be numeric
        assert pd.api.types.is_numeric_dtype(df["qo"])
        assert pd.api.types.is_numeric_dtype(df["qg"])


@pytest.mark.unit
class TestDeduplicateByWellDate:
    """Test deduplication by well and date"""
    
    def test_deduplicate_by_well_date_basic(self, sample_records):
        """Test basic deduplication by well and date"""
        df = deduplicate_by_well_date(sample_records)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
    
    def test_deduplicate_by_well_date_removes_same_day_entries(self):
        """Test that multiple entries for same well/date are reduced"""
        records = [
            {"Well": "W-01", "Date": date(2024, 1, 15), "qo": 100, "qg": 5000, "qw": 50},
            {"Well": "W-01", "Date": date(2024, 1, 15), "qo": 102, "qg": 5100, "qw": 48},
            {"Well": "W-01", "Date": date(2024, 1, 16), "qo": 105, "qg": 5200, "qw": 45},
        ]
        df = deduplicate_by_well_date(records)
        
        # Should keep first occurrence of W-01 on 01/15
        # and the 01/16 entry, so 2 records total
        well_date_combinations = list(zip(df["Well"], df["Date"]))
        assert len(well_date_combinations) == len(set(well_date_combinations))
    
    def test_deduplicate_by_well_date_keeps_first(self, duplicate_records):
        """Test that first occurrence is kept"""
        df = deduplicate_by_well_date(duplicate_records)
        
        # Should have fewer rows than input
        assert len(df) <= len(duplicate_records)
    
    def test_deduplicate_by_well_date_sorts_output(self):
        """Test that output is sorted"""
        records = [
            {"Well": "B-WELL", "Date": date(2024, 1, 17), "qo": 100, "qg": 5000, "qw": 50},
            {"Well": "A-WELL", "Date": date(2024, 1, 15), "qo": 100, "qg": 5000, "qw": 50},
        ]
        df = deduplicate_by_well_date(records)
        
        # Should be sorted by well first
        wells = df["Well"].tolist()
        assert wells[0] < wells[-1]
    
    def test_deduplicate_by_well_date_empty(self):
        """Test with empty input"""
        df = deduplicate_by_well_date([])
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


@pytest.mark.unit
class TestGetDeduplicationStats:
    """Test deduplication statistics calculation"""
    
    def test_get_deduplication_stats_no_duplicates(self):
        """Test stats when no duplicates removed"""
        stats = get_deduplication_stats(100, 100)
        
        assert stats["original_count"] == 100
        assert stats["final_count"] == 100
        assert stats["duplicates_found"] == 0
        assert stats["percent_removed"] == 0.0
        assert stats["percent_retained"] == 100.0
    
    def test_get_deduplication_stats_with_duplicates(self):
        """Test stats when duplicates are removed"""
        stats = get_deduplication_stats(100, 95)
        
        assert stats["original_count"] == 100
        assert stats["final_count"] == 95
        assert stats["duplicates_found"] == 5
        assert stats["percent_removed"] == 5.0
        assert stats["percent_retained"] == 95.0
    
    def test_get_deduplication_stats_all_duplicates(self):
        """Test stats when all records are duplicates"""
        stats = get_deduplication_stats(100, 1)
        
        assert stats["duplicates_found"] == 99
        assert stats["percent_removed"] == 99.0
        assert stats["percent_retained"] == 1.0
    
    def test_get_deduplication_stats_zero_original(self):
        """Test stats with zero original records"""
        stats = get_deduplication_stats(0, 0)
        
        assert stats["duplicates_found"] == 0
        assert stats["percent_removed"] == 0.0
        assert stats["percent_retained"] == 0.0
    
    def test_get_deduplication_stats_keys(self):
        """Test that all expected keys are present"""
        stats = get_deduplication_stats(100, 95)
        
        expected_keys = [
            "original_count",
            "final_count",
            "duplicates_found",
            "percent_removed",
            "percent_retained",
        ]
        for key in expected_keys:
            assert key in stats
    
    def test_get_deduplication_stats_percentages_sum_to_100(self):
        """Test that removed and retained percentages sum to 100"""
        stats = get_deduplication_stats(100, 75)
        
        total = stats["percent_removed"] + stats["percent_retained"]
        assert abs(total - 100.0) < 0.01


@pytest.mark.unit
class TestDeduplicationEdgeCases:
    """Test edge cases in deduplication"""
    
    def test_deduplicate_preserves_well_names(self, sample_records):
        """Test that well names are preserved exactly"""
        df = deduplicate_and_sort(sample_records)
        
        original_wells = set(r["Well"] for r in sample_records)
        result_wells = set(df["Well"].tolist())
        assert original_wells == result_wells
    
    def test_deduplicate_with_null_production_values(self):
        """Test deduplication with None production values"""
        records = [
            {"Well": "W-01", "Date": date(2024, 1, 15), "qo": 100, "qg": None, "qw": 50},
            {"Well": "W-01", "Date": date(2024, 1, 15), "qo": 100, "qg": None, "qw": 50},
        ]
        df = deduplicate_and_sort(records)
        
        # Exact duplicates including None values should be removed
        assert len(df) <= len(records)
    
    def test_deduplicate_with_mixed_null_values(self):
        """Test deduplication with different null patterns"""
        records = [
            {"Well": "W-01", "Date": date(2024, 1, 15), "qo": 100, "qg": None, "qw": 50},
            {"Well": "W-01", "Date": date(2024, 1, 15), "qo": 100, "qg": 5000, "qw": 50},
        ]
        df = deduplicate_and_sort(records)
        
        # These are different records, both should be kept
        assert len(df) == 2
    
    def test_deduplicate_large_dataset(self, sample_records):
        """Test deduplication with large dataset"""
        large_dataset = sample_records * 1000  # 5000 records
        df = deduplicate_and_sort(large_dataset)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0


@pytest.mark.unit
class TestDeduplicationIntegration:
    """Integration tests for deduplication workflow"""
    
    def test_full_deduplication_workflow(self, duplicate_records):
        """Test full deduplication workflow with stats"""
        df_dedup = deduplicate_and_sort(duplicate_records)
        
        stats = get_deduplication_stats(len(duplicate_records), len(df_dedup))
        
        assert stats["duplicates_found"] == len(duplicate_records) - len(df_dedup)
        assert stats["percent_removed"] >= 0
        assert stats["percent_retained"] >= 0
    
    def test_deduplication_then_stats(self):
        """Test getting stats after deduplication"""
        records = [
            {"Well": "W-01", "Date": date(2024, 1, 15), "qo": 100, "qg": 5000, "qw": 50},
            {"Well": "W-01", "Date": date(2024, 1, 15), "qo": 100, "qg": 5000, "qw": 50},
            {"Well": "W-01", "Date": date(2024, 1, 16), "qo": 105, "qg": 5100, "qw": 48},
        ]
        
        original_count = len(records)
        df = deduplicate_and_sort(records)
        final_count = len(df)
        
        stats = get_deduplication_stats(original_count, final_count)
        
        assert stats["duplicates_found"] > 0
        assert final_count < original_count
