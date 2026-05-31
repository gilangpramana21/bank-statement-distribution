"""
Unit tests for Entity Grouper component.
"""

import pytest
from datetime import datetime
from src.entity_grouper import EntityGrouper
from src.models import StatementFile, ProcessingStatus


class TestEntityGrouper:
    """Test cases for EntityGrouper."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.grouper = EntityGrouper()
        
        # Create sample statement files
        self.sample_files = [
            StatementFile(
                file_id=1,
                file_path="/BCA/SMI/statement1.pdf",
                bank_name="BCA",
                entity_name="SMI",
                file_size=1024,
                last_modified=datetime(2024, 1, 1),
                checksum="abc123",
                status=ProcessingStatus.UNPROCESSED
            ),
            StatementFile(
                file_id=2,
                file_path="/BCA/PBS/statement2.pdf",
                bank_name="BCA",
                entity_name="PBS",
                file_size=2048,
                last_modified=datetime(2024, 1, 2),
                checksum="def456",
                status=ProcessingStatus.UNPROCESSED
            ),
            StatementFile(
                file_id=3,
                file_path="/Mandiri/SMI/statement3.pdf",
                bank_name="Mandiri",
                entity_name="SMI",
                file_size=3072,
                last_modified=datetime(2024, 1, 3),
                checksum="ghi789",
                status=ProcessingStatus.UNPROCESSED
            ),
        ]
    
    def test_group_by_entity(self):
        """Test grouping files by entity."""
        entity_groups = self.grouper.group_by_entity(self.sample_files)
        
        # Check entity count
        assert len(entity_groups) == 2
        assert "SMI" in entity_groups
        assert "PBS" in entity_groups
        
        # Check SMI group
        assert len(entity_groups["SMI"]) == 2
        assert entity_groups["SMI"][0].entity_name == "SMI"
        assert entity_groups["SMI"][1].entity_name == "SMI"
        
        # Check PBS group
        assert len(entity_groups["PBS"]) == 1
        assert entity_groups["PBS"][0].entity_name == "PBS"
    
    def test_group_by_entity_empty_list(self):
        """Test grouping with empty file list."""
        entity_groups = self.grouper.group_by_entity([])
        
        assert len(entity_groups) == 0
    
    def test_detect_duplicates(self):
        """Test duplicate detection."""
        # Create duplicate files
        duplicate_files = [
            StatementFile(
                file_id=1,
                file_path="/BCA/SMI/statement1.pdf",
                bank_name="BCA",
                entity_name="SMI",
                file_size=1024,
                last_modified=datetime(2024, 1, 1),
                checksum="abc123",
                status=ProcessingStatus.UNPROCESSED
            ),
            StatementFile(
                file_id=2,
                file_path="/BCA/SMI/statement1.pdf",
                bank_name="BCA",
                entity_name="SMI",
                file_size=1024,
                last_modified=datetime(2024, 1, 2),  # Newer
                checksum="abc123",
                status=ProcessingStatus.UNPROCESSED
            ),
        ]
        
        entity_groups = {"SMI": duplicate_files}
        cleaned_groups = self.grouper.detect_duplicates(entity_groups)
        
        # Should keep only the newer file
        assert len(cleaned_groups["SMI"]) == 1
        assert cleaned_groups["SMI"][0].file_id == 2
    
    def test_validation_failure(self):
        """Test validation failure when file count doesn't match."""
        # This test would require mocking the validation logic
        # For now, we just ensure the method exists
        assert hasattr(self.grouper, '_validate_grouping')


if __name__ == '__main__':
    pytest.main([__file__])
