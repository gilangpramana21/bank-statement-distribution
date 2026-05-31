"""
Entity Grouper component for reorganizing statements by entity.
"""

from typing import Dict, List
from collections import defaultdict
from src.database import db
from src.models import StatementFile, ProcessingStatus
from src.logger import get_logger

logger = get_logger(__name__)


class EntityGrouper:
    """Reorganizes statements from bank-based hierarchy to entity-based grouping."""
    
    def __init__(self):
        """Initialize Entity Grouper."""
        pass
    
    def group_by_entity(self, statement_files: List[StatementFile]) -> Dict[str, List[StatementFile]]:
        """
        Group statement files by entity.
        
        Args:
            statement_files: List of StatementFile objects
            
        Returns:
            Dictionary mapping entity names to lists of StatementFile objects
        """
        try:
            entity_groups = defaultdict(list)
            
            for statement_file in statement_files:
                # Validate entity metadata
                if not statement_file.entity_name or statement_file.entity_name.strip() == '':
                    logger.error("missing_entity_metadata", 
                               file_path=statement_file.file_path)
                    continue
                
                entity_groups[statement_file.entity_name].append(statement_file)
            
            # Validate grouping
            self._validate_grouping(statement_files, entity_groups)
            
            logger.info("entity_grouping_complete", 
                       entity_count=len(entity_groups),
                       total_files=len(statement_files))
            
            return dict(entity_groups)
            
        except Exception as e:
            logger.error("entity_grouping_failed", error=str(e))
            raise
    
    def _validate_grouping(self, 
                          original_files: List[StatementFile], 
                          entity_groups: Dict[str, List[StatementFile]]) -> None:
        """
        Validate that all files are assigned to exactly one entity.
        
        Args:
            original_files: Original list of statement files
            entity_groups: Grouped files by entity
            
        Raises:
            ValueError: If validation fails
        """
        # Count total files in groups
        grouped_file_count = sum(len(files) for files in entity_groups.values())
        
        # Check if counts match
        if grouped_file_count != len(original_files):
            error_msg = (
                f"Grouping validation failed: "
                f"original={len(original_files)}, grouped={grouped_file_count}"
            )
            logger.error("grouping_validation_failed", 
                        original_count=len(original_files),
                        grouped_count=grouped_file_count)
            raise ValueError(error_msg)
        
        # Check for duplicate assignments
        seen_file_ids = set()
        for entity, files in entity_groups.items():
            for file in files:
                if file.file_id in seen_file_ids:
                    logger.error("duplicate_file_assignment", 
                               file_id=file.file_id,
                               entity=entity)
                    raise ValueError(f"File {file.file_id} assigned to multiple entities")
                seen_file_ids.add(file.file_id)
        
        logger.info("grouping_validation_passed")
    
    def detect_duplicates(self, entity_groups: Dict[str, List[StatementFile]]) -> Dict[str, List[StatementFile]]:
        """
        Detect and remove duplicate files within each entity group.
        
        Args:
            entity_groups: Dictionary mapping entity names to lists of StatementFile objects
            
        Returns:
            Cleaned entity groups with duplicates removed
        """
        cleaned_groups = {}
        
        for entity, files in entity_groups.items():
            # Group by filename and checksum
            file_map = {}
            
            for file in files:
                key = (file.file_path.lower(), file.checksum)
                
                if key in file_map:
                    # Duplicate found - keep the one with most recent modification time
                    existing = file_map[key]
                    
                    if file.last_modified > existing.last_modified:
                        logger.info("duplicate_resolved_by_timestamp",
                                  entity=entity,
                                  kept_file=file.file_path,
                                  removed_file=existing.file_path)
                        file_map[key] = file
                    elif file.last_modified == existing.last_modified:
                        # Same timestamp - use longest path as tiebreaker
                        if len(file.file_path) > len(existing.file_path):
                            logger.info("duplicate_resolved_by_path_length",
                                      entity=entity,
                                      kept_file=file.file_path,
                                      removed_file=existing.file_path)
                            file_map[key] = file
                        else:
                            logger.info("duplicate_resolved_by_path_length",
                                      entity=entity,
                                      kept_file=existing.file_path,
                                      removed_file=file.file_path)
                    else:
                        logger.info("duplicate_resolved_by_timestamp",
                                  entity=entity,
                                  kept_file=existing.file_path,
                                  removed_file=file.file_path)
                else:
                    file_map[key] = file
            
            cleaned_groups[entity] = list(file_map.values())
            
            duplicates_removed = len(files) - len(file_map)
            if duplicates_removed > 0:
                logger.info("duplicates_removed",
                          entity=entity,
                          duplicates_count=duplicates_removed)
        
        return cleaned_groups
    
    def check_cross_entity_duplicates(self, entity_groups: Dict[str, List[StatementFile]]) -> None:
        """
        Check for duplicate files across different entities.
        
        Args:
            entity_groups: Dictionary mapping entity names to lists of StatementFile objects
        """
        # Build a map of (filename, checksum) -> list of entities
        file_entity_map = defaultdict(list)
        
        for entity, files in entity_groups.items():
            for file in files:
                key = (file.file_path.lower(), file.checksum)
                file_entity_map[key].append((entity, file.file_path))
        
        # Check for cross-entity duplicates
        for key, entity_file_pairs in file_entity_map.items():
            if len(entity_file_pairs) > 1:
                entities = [pair[0] for pair in entity_file_pairs]
                file_paths = [pair[1] for pair in entity_file_pairs]
                
                logger.warning("cross_entity_duplicate_detected",
                             entities=entities,
                             file_paths=file_paths)
