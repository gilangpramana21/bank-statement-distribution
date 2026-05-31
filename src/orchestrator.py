"""
Main Orchestrator for Bank Statement Distribution System.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from src.config import config
from src.database import db
from src.models import (
    StatementFile, ProcessingStatus, ExecutionSummary, 
    SystemHealth, OperationOutcome
)
from src.statement_scanner import StatementScanner
from src.entity_grouper import EntityGrouper
from src.package_manager import PackageManager, Package
from src.email_distributor import EmailDistributor
from src.audit_logger import AuditLogger
from src.logger import get_logger
import json

logger = get_logger(__name__)


class Orchestrator:
    """Main orchestrator for the bank statement distribution workflow."""
    
    def __init__(self):
        """Initialize Orchestrator."""
        self.execution_id = str(uuid.uuid4())
        self.start_time = None
        self.end_time = None
        
        # Initialize components
        self.scanner = StatementScanner()
        self.grouper = EntityGrouper()
        self.packager = PackageManager()
        self.distributor = EmailDistributor()
        self.audit_logger = AuditLogger()
        
        # Execution statistics
        self.stats = {
            'files_discovered': 0,
            'files_processed': 0,
            'emails_sent': 0,
            'delivery_failures': 0,
            'failure_details': []
        }
    
    def execute(self, 
                entity_filter: Optional[str] = None,
                date_filter: Optional[str] = None) -> Dict:
        """
        Execute the complete distribution workflow.
        
        Args:
            entity_filter: Optional entity name filter
            date_filter: Optional date filter (ISO 8601 format)
            
        Returns:
            Execution summary dictionary
        """
        self.start_time = datetime.utcnow()
        
        try:
            logger.info("execution_started", 
                       execution_id=self.execution_id,
                       entity_filter=entity_filter,
                       date_filter=date_filter)
            
            # Step 1: Discover statements
            logger.info("step_1_discovery_started")
            discovered_files = self._discover_statements()
            self.stats['files_discovered'] = len(discovered_files)
            logger.info("step_1_discovery_completed", count=len(discovered_files))
            
            if not discovered_files:
                logger.info("no_files_to_process")
                return self._generate_summary()
            
            # Apply filters
            if entity_filter or date_filter:
                discovered_files = self._apply_filters(
                    discovered_files, 
                    entity_filter, 
                    date_filter
                )
                logger.info("filters_applied", count=len(discovered_files))
            
            # Step 2: Group by entity
            logger.info("step_2_grouping_started")
            entity_groups = self._group_by_entity(discovered_files)
            logger.info("step_2_grouping_completed", entity_count=len(entity_groups))
            
            # Step 3: Create packages
            logger.info("step_3_packaging_started")
            packages = self._create_packages(entity_groups)
            logger.info("step_3_packaging_completed", 
                       total_packages=sum(len(p) for p in packages.values()))
            
            # Step 4: Distribute packages
            logger.info("step_4_distribution_started")
            successful, failed = self._distribute_packages(packages)
            self.stats['emails_sent'] = successful
            self.stats['delivery_failures'] = failed
            logger.info("step_4_distribution_completed", 
                       successful=successful, 
                       failed=failed)
            
            # Step 5: Cleanup
            logger.info("step_5_cleanup_started")
            self._cleanup(packages)
            logger.info("step_5_cleanup_completed")
            
            # Generate summary
            summary = self._generate_summary()
            
            # Send summary report
            self._send_summary_report(summary)
            
            # Update system health
            self._update_system_health(success=True)
            
            logger.info("execution_completed", execution_id=self.execution_id)
            
            return summary
            
        except Exception as e:
            logger.error("execution_failed", 
                        execution_id=self.execution_id,
                        error=str(e))
            
            self.audit_logger.log_error(
                component_name="Orchestrator",
                error_type=type(e).__name__,
                error_message=str(e),
                context={'execution_id': self.execution_id}
            )
            
            self._update_system_health(success=False)
            
            raise
    
    def _discover_statements(self) -> List[StatementFile]:
        """
        Discover new bank statements.
        
        Returns:
            List of discovered StatementFile objects
        """
        try:
            # Get unprocessed and pending files
            with db.get_session() as session:
                files = session.query(StatementFile).filter(
                    StatementFile.status.in_([
                        ProcessingStatus.UNPROCESSED,
                        ProcessingStatus.PENDING
                    ])
                ).all()
            
            # If no pending files, discover new ones
            if not files:
                files = self.scanner.discover_statements()
            
            # Log discoveries
            for file in files:
                self.audit_logger.log_discovery(
                    file_path=file.file_path,
                    entity_name=file.entity_name,
                    outcome=OperationOutcome.SUCCESS
                )
            
            return files
            
        except Exception as e:
            logger.error("discovery_failed", error=str(e))
            raise
    
    def _apply_filters(self, 
                      files: List[StatementFile],
                      entity_filter: Optional[str],
                      date_filter: Optional[str]) -> List[StatementFile]:
        """
        Apply filters to file list.
        
        Args:
            files: List of StatementFile objects
            entity_filter: Entity name filter
            date_filter: Date filter (ISO 8601)
            
        Returns:
            Filtered list of StatementFile objects
        """
        filtered_files = files
        
        if entity_filter:
            filtered_files = [f for f in filtered_files if f.entity_name == entity_filter]
        
        if date_filter:
            try:
                filter_date = datetime.fromisoformat(date_filter)
                filtered_files = [f for f in filtered_files if f.last_modified >= filter_date]
            except ValueError:
                logger.warning("invalid_date_filter", date_filter=date_filter)
        
        return filtered_files
    
    def _group_by_entity(self, files: List[StatementFile]) -> Dict[str, List[StatementFile]]:
        """
        Group files by entity.
        
        Args:
            files: List of StatementFile objects
            
        Returns:
            Dictionary mapping entity names to file lists
        """
        try:
            # Group files
            entity_groups = self.grouper.group_by_entity(files)
            
            # Detect and remove duplicates
            entity_groups = self.grouper.detect_duplicates(entity_groups)
            
            # Check for cross-entity duplicates
            self.grouper.check_cross_entity_duplicates(entity_groups)
            
            # Log grouping
            for entity, entity_files in entity_groups.items():
                self.audit_logger.log_grouping(
                    entity_name=entity,
                    file_count=len(entity_files),
                    outcome=OperationOutcome.SUCCESS
                )
            
            return entity_groups
            
        except Exception as e:
            logger.error("grouping_failed", error=str(e))
            raise
    
    def _create_packages(self, entity_groups: Dict[str, List[StatementFile]]) -> Dict[str, List[Package]]:
        """
        Create packages for each entity.
        
        Args:
            entity_groups: Dictionary mapping entity names to file lists
            
        Returns:
            Dictionary mapping entity names to package lists
        """
        try:
            packages = self.packager.create_packages(entity_groups)
            
            # Log packaging
            for entity, entity_packages in packages.items():
                self.audit_logger.log_packaging(
                    entity_name=entity,
                    package_count=len(entity_packages),
                    outcome=OperationOutcome.SUCCESS
                )
            
            return packages
            
        except Exception as e:
            logger.error("packaging_failed", error=str(e))
            raise
    
    def _distribute_packages(self, packages: Dict[str, List[Package]]) -> Tuple[int, int]:
        """
        Distribute packages to financiers.
        
        Args:
            packages: Dictionary mapping entity names to package lists
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        try:
            successful, failed = self.distributor.distribute_packages(packages)
            
            self.stats['files_processed'] = sum(
                len(pkg.files) for entity_pkgs in packages.values() for pkg in entity_pkgs
            )
            
            return successful, failed
            
        except Exception as e:
            logger.error("distribution_failed", error=str(e))
            raise
    
    def _cleanup(self, packages: Dict[str, List[Package]]) -> None:
        """
        Cleanup temporary files.
        
        Args:
            packages: Dictionary of packages to cleanup
        """
        try:
            self.packager.cleanup_packages(packages)
            logger.info("cleanup_completed")
            
        except Exception as e:
            logger.warning("cleanup_failed", error=str(e))
            # Don't raise - cleanup failure shouldn't stop execution
    
    def _generate_summary(self) -> Dict:
        """
        Generate execution summary.
        
        Returns:
            Summary dictionary
        """
        self.end_time = datetime.utcnow()
        duration = (self.end_time - self.start_time).total_seconds()
        
        summary = {
            'execution_id': self.execution_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_seconds': int(duration),
            'files_discovered': self.stats['files_discovered'],
            'files_processed': self.stats['files_processed'],
            'emails_sent': self.stats['emails_sent'],
            'delivery_failures': self.stats['delivery_failures'],
            'failure_details': self.stats['failure_details']
        }
        
        # Save to database
        try:
            with db.get_session() as session:
                exec_summary = ExecutionSummary(
                    execution_id=self.execution_id,
                    start_time=self.start_time,
                    end_time=self.end_time,
                    duration_seconds=int(duration),
                    files_discovered=self.stats['files_discovered'],
                    files_processed=self.stats['files_processed'],
                    emails_sent=self.stats['emails_sent'],
                    delivery_failures=self.stats['delivery_failures'],
                    failure_details=json.dumps(self.stats['failure_details'])
                )
                session.add(exec_summary)
        except Exception as e:
            logger.error("summary_save_failed", error=str(e))
        
        # Log to audit
        self.audit_logger.log_summary_report(summary)
        
        return summary
    
    def _send_summary_report(self, summary: Dict) -> None:
        """
        Send summary report to admin users.
        
        Args:
            summary: Summary dictionary
        """
        try:
            # In production, this would send email to admin users
            # For now, just log it
            logger.info("summary_report_generated", summary=summary)
            
        except Exception as e:
            logger.error("summary_report_send_failed", error=str(e))
            # Don't raise - summary send failure shouldn't stop execution
    
    def _update_system_health(self, success: bool) -> None:
        """
        Update system health status.
        
        Args:
            success: Whether execution was successful
        """
        try:
            with db.get_session() as session:
                health = session.query(SystemHealth).first()
                
                if not health:
                    health = SystemHealth()
                    session.add(health)
                
                health.last_execution_timestamp = self.end_time or datetime.utcnow()
                health.last_execution_status = "success" if success else "failed"
                health.updated_at = datetime.utcnow()
                
        except Exception as e:
            logger.error("system_health_update_failed", error=str(e))
    
    def check_timeout(self) -> None:
        """Check if execution has exceeded timeout."""
        if not self.start_time:
            return
        
        elapsed = (datetime.utcnow() - self.start_time).total_seconds() / 60
        
        # Warning timeout
        if elapsed > config.warning_timeout_minutes:
            logger.warning("execution_timeout_warning",
                         elapsed_minutes=elapsed,
                         warning_threshold=config.warning_timeout_minutes)
        
        # Hard timeout
        if elapsed > config.execution_timeout_minutes:
            logger.error("execution_timeout_exceeded",
                       elapsed_minutes=elapsed,
                       timeout_threshold=config.execution_timeout_minutes)
            raise TimeoutError(f"Execution exceeded timeout of {config.execution_timeout_minutes} minutes")
