"""
Package Manager component for creating and splitting ZIP archives.
"""

import os
import zipfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
from src.config import config
from src.models import StatementFile
from src.logger import get_logger
import json

logger = get_logger(__name__)


class Package:
    """Represents a ZIP package."""
    
    def __init__(self, entity: str, part_number: int = None):
        """
        Initialize package.
        
        Args:
            entity: Entity name
            part_number: Part number for split archives (None for single archive)
        """
        self.entity = entity
        self.part_number = part_number
        self.file_path = None
        self.files = []
        self.size = 0
    
    def get_filename(self) -> str:
        """
        Get package filename.
        
        Returns:
            Filename string
        """
        date_str = datetime.now().strftime("%Y-%m")
        
        if self.part_number is not None:
            return f"{self.entity}_{date_str}_part{self.part_number}.zip"
        else:
            return f"{self.entity}_{date_str}.zip"


class PackageManager:
    """Creates compressed archives and manages file splitting."""
    
    def __init__(self):
        """Initialize Package Manager."""
        self.temp_dir = Path(tempfile.gettempdir()) / "bank_statements"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def create_packages(self, entity_groups: Dict[str, List[StatementFile]]) -> Dict[str, List[Package]]:
        """
        Create ZIP packages for each entity.
        
        Args:
            entity_groups: Dictionary mapping entity names to lists of StatementFile objects
            
        Returns:
            Dictionary mapping entity names to lists of Package objects
        """
        packages = {}
        
        for entity, files in entity_groups.items():
            try:
                logger.info("creating_packages", entity=entity, file_count=len(files))
                
                # Check if files need to be split
                total_size = sum(f.file_size for f in files)
                
                if total_size > config.max_attachment_size_bytes:
                    # Need to split
                    entity_packages = self._create_split_packages(entity, files)
                else:
                    # Single package
                    entity_packages = [self._create_single_package(entity, files)]
                
                packages[entity] = entity_packages
                
                logger.info("packages_created", 
                          entity=entity, 
                          package_count=len(entity_packages))
                
            except Exception as e:
                logger.error("package_creation_failed", 
                           entity=entity, 
                           error=str(e))
                raise
        
        return packages
    
    def _create_single_package(self, entity: str, files: List[StatementFile]) -> Package:
        """
        Create a single ZIP package.
        
        Args:
            entity: Entity name
            files: List of StatementFile objects
            
        Returns:
            Package object
        """
        package = Package(entity)
        package_path = self.temp_dir / package.get_filename()
        
        try:
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in files:
                    # In production, you would download the file from Google Drive
                    # For now, we'll just add file metadata
                    file_name = Path(file.file_path).name
                    
                    # Add file to ZIP (placeholder - actual implementation would download from GDrive)
                    # zipf.write(local_file_path, arcname=file_name)
                    
                    package.files.append(file)
                
                # Create manifest
                manifest = self._create_manifest(files)
                zipf.writestr('manifest.txt', manifest)
            
            # Validate package
            self._validate_package(package_path, files)
            
            package.file_path = str(package_path)
            package.size = package_path.stat().st_size
            
            logger.info("single_package_created", 
                       entity=entity, 
                       size_bytes=package.size)
            
            return package
            
        except Exception as e:
            logger.error("single_package_creation_failed", 
                       entity=entity, 
                       error=str(e))
            raise
    
    def _create_split_packages(self, entity: str, files: List[StatementFile]) -> List[Package]:
        """
        Create multiple split ZIP packages.
        
        Args:
            entity: Entity name
            files: List of StatementFile objects
            
        Returns:
            List of Package objects
        """
        packages = []
        current_package_files = []
        current_size = 0
        part_number = 1
        
        # Sort files by size (largest first) for better packing
        sorted_files = sorted(files, key=lambda f: f.file_size, reverse=True)
        
        for file in sorted_files:
            # Check if file exceeds limit by itself
            if file.file_size > config.max_attachment_size_bytes:
                logger.error("file_exceeds_limit", 
                           file_path=file.file_path,
                           size_bytes=file.file_size,
                           limit_bytes=config.max_attachment_size_bytes)
                continue
            
            # Check if adding this file would exceed limit
            if current_size + file.file_size > config.max_attachment_size_bytes:
                # Create package with current files
                if current_package_files:
                    package = self._create_package_part(entity, current_package_files, part_number)
                    packages.append(package)
                    part_number += 1
                    
                    # Check max parts limit
                    if part_number > config.max_split_parts:
                        logger.error("max_split_parts_exceeded", 
                                   entity=entity,
                                   max_parts=config.max_split_parts)
                        raise ValueError(f"Entity {entity} exceeds maximum split parts limit")
                    
                    # Reset for next package
                    current_package_files = []
                    current_size = 0
            
            current_package_files.append(file)
            current_size += file.file_size
        
        # Create final package
        if current_package_files:
            package = self._create_package_part(entity, current_package_files, part_number)
            packages.append(package)
        
        # Validate all files are included
        self._validate_split_packages(files, packages)
        
        logger.info("split_packages_created", 
                   entity=entity, 
                   package_count=len(packages))
        
        return packages
    
    def _create_package_part(self, entity: str, files: List[StatementFile], part_number: int) -> Package:
        """
        Create a single part of a split package.
        
        Args:
            entity: Entity name
            files: List of StatementFile objects for this part
            part_number: Part number
            
        Returns:
            Package object
        """
        package = Package(entity, part_number)
        package_path = self.temp_dir / package.get_filename()
        
        try:
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in files:
                    file_name = Path(file.file_path).name
                    # Add file to ZIP (placeholder)
                    package.files.append(file)
                
                # Create manifest for this part
                manifest = self._create_manifest(files)
                zipf.writestr('manifest.txt', manifest)
            
            # Validate package
            self._validate_package(package_path, files)
            
            package.file_path = str(package_path)
            package.size = package_path.stat().st_size
            
            # Ensure package is under limit
            if package.size > config.max_attachment_size_bytes:
                logger.error("package_part_exceeds_limit",
                           entity=entity,
                           part_number=part_number,
                           size_bytes=package.size)
                raise ValueError(f"Package part {part_number} exceeds size limit")
            
            logger.info("package_part_created", 
                       entity=entity, 
                       part_number=part_number,
                       size_bytes=package.size)
            
            return package
            
        except Exception as e:
            logger.error("package_part_creation_failed", 
                       entity=entity, 
                       part_number=part_number,
                       error=str(e))
            raise
    
    def _create_manifest(self, files: List[StatementFile]) -> str:
        """
        Create manifest file content.
        
        Args:
            files: List of StatementFile objects
            
        Returns:
            Manifest content as string
        """
        manifest_lines = ["File Manifest", "=" * 50, ""]
        
        for file in files:
            file_name = Path(file.file_path).name
            manifest_lines.append(f"File: {file_name}")
            manifest_lines.append(f"Size: {file.file_size} bytes")
            manifest_lines.append(f"Checksum (SHA-256): {file.checksum}")
            manifest_lines.append("")
        
        return "\n".join(manifest_lines)
    
    def _validate_package(self, package_path: Path, expected_files: List[StatementFile]) -> None:
        """
        Validate ZIP package integrity.
        
        Args:
            package_path: Path to ZIP package
            expected_files: List of expected StatementFile objects
            
        Raises:
            ValueError: If validation fails
        """
        try:
            with zipfile.ZipFile(package_path, 'r') as zipf:
                # Test ZIP integrity
                bad_file = zipf.testzip()
                if bad_file:
                    raise ValueError(f"Corrupted file in ZIP: {bad_file}")
                
                # Check file count (excluding manifest)
                zip_files = [f for f in zipf.namelist() if f != 'manifest.txt']
                
                # Note: In actual implementation, we would verify all expected files are present
                # For now, we just check the ZIP is valid
                
                logger.debug("package_validation_passed", package_path=str(package_path))
                
        except zipfile.BadZipFile as e:
            logger.error("package_validation_failed", 
                       package_path=str(package_path),
                       error=str(e))
            raise ValueError(f"Invalid ZIP package: {package_path}")
    
    def _validate_split_packages(self, original_files: List[StatementFile], packages: List[Package]) -> None:
        """
        Validate that split packages contain all original files exactly once.
        
        Args:
            original_files: Original list of files
            packages: List of Package objects
            
        Raises:
            ValueError: If validation fails
        """
        # Collect all files from packages
        packaged_files = []
        for package in packages:
            packaged_files.extend(package.files)
        
        # Check counts
        if len(packaged_files) != len(original_files):
            logger.error("split_package_validation_failed",
                       original_count=len(original_files),
                       packaged_count=len(packaged_files))
            raise ValueError("Split packages do not contain all original files")
        
        # Check for duplicates
        packaged_file_ids = [f.file_id for f in packaged_files]
        if len(packaged_file_ids) != len(set(packaged_file_ids)):
            logger.error("split_package_contains_duplicates")
            raise ValueError("Split packages contain duplicate files")
        
        logger.info("split_package_validation_passed")
    
    def cleanup_packages(self, packages: Dict[str, List[Package]]) -> None:
        """
        Clean up temporary package files.
        
        Args:
            packages: Dictionary of packages to clean up
        """
        for entity, entity_packages in packages.items():
            for package in entity_packages:
                if package.file_path and Path(package.file_path).exists():
                    try:
                        Path(package.file_path).unlink()
                        logger.debug("package_cleaned_up", file_path=package.file_path)
                    except Exception as e:
                        logger.warning("package_cleanup_failed", 
                                     file_path=package.file_path,
                                     error=str(e))
