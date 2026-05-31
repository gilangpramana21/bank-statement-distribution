"""
Audit Logger component for comprehensive operation logging.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import and_
from src.database import db
from src.models import AuditLog, OperationType, OperationOutcome
from src.logger import get_logger
import json

logger = get_logger(__name__)


class AuditLogger:
    """Manages comprehensive audit logging."""
    
    def __init__(self):
        """Initialize Audit Logger."""
        pass
    
    def log_discovery(self, file_path: str, entity_name: str, outcome: OperationOutcome) -> None:
        """
        Log file discovery operation.
        
        Args:
            file_path: Path to discovered file
            entity_name: Entity name
            outcome: Operation outcome
        """
        self._log_operation(
            operation_type=OperationType.DISCOVERY,
            outcome=outcome,
            component_name="StatementScanner",
            entity_name=entity_name,
            file_path=file_path
        )
    
    def log_grouping(self, entity_name: str, file_count: int, outcome: OperationOutcome) -> None:
        """
        Log entity grouping operation.
        
        Args:
            entity_name: Entity name
            file_count: Number of files grouped
            outcome: Operation outcome
        """
        context = {"file_count": file_count}
        
        self._log_operation(
            operation_type=OperationType.GROUPING,
            outcome=outcome,
            component_name="EntityGrouper",
            entity_name=entity_name,
            context_info=json.dumps(context)
        )
    
    def log_packaging(self, entity_name: str, package_count: int, outcome: OperationOutcome) -> None:
        """
        Log package creation operation.
        
        Args:
            entity_name: Entity name
            package_count: Number of packages created
            outcome: Operation outcome
        """
        context = {"package_count": package_count}
        
        self._log_operation(
            operation_type=OperationType.PACKAGING,
            outcome=outcome,
            component_name="PackageManager",
            entity_name=entity_name,
            context_info=json.dumps(context)
        )
    
    def log_delivery(self, 
                    financier_email: str, 
                    entity_name: str, 
                    attachment_names: List[str],
                    attachment_sizes: List[int],
                    checksums: List[str],
                    outcome: OperationOutcome) -> None:
        """
        Log email delivery operation.
        
        Args:
            financier_email: Financier email address
            entity_name: Entity name
            attachment_names: List of attachment filenames
            attachment_sizes: List of attachment sizes in bytes
            checksums: List of file checksums
            outcome: Operation outcome
        """
        self._log_operation(
            operation_type=OperationType.DELIVERY,
            outcome=outcome,
            component_name="EmailDistributor",
            entity_name=entity_name,
            financier_email=financier_email,
            attachment_names=json.dumps(attachment_names),
            attachment_sizes=json.dumps(attachment_sizes),
            checksum=checksums[0] if checksums else None
        )
    
    def log_error(self, 
                 component_name: str,
                 error_type: str,
                 error_message: str,
                 context: Optional[Dict] = None) -> None:
        """
        Log error operation.
        
        Args:
            component_name: Name of component where error occurred
            error_type: Type of error
            error_message: Error message
            context: Additional context information
        """
        self._log_operation(
            operation_type=OperationType.ERROR,
            outcome=OperationOutcome.FAILURE,
            component_name=component_name,
            error_type=error_type,
            error_message=error_message,
            context_info=json.dumps(context) if context else None
        )
    
    def log_summary_report(self, summary_data: Dict) -> None:
        """
        Log execution summary report.
        
        Args:
            summary_data: Summary report data
        """
        self._log_operation(
            operation_type=OperationType.SUMMARY_REPORT,
            outcome=OperationOutcome.SUCCESS,
            component_name="System",
            context_info=json.dumps(summary_data)
        )
    
    def _log_operation(self, 
                      operation_type: OperationType,
                      outcome: OperationOutcome,
                      component_name: Optional[str] = None,
                      entity_name: Optional[str] = None,
                      financier_email: Optional[str] = None,
                      file_path: Optional[str] = None,
                      attachment_names: Optional[str] = None,
                      attachment_sizes: Optional[str] = None,
                      checksum: Optional[str] = None,
                      error_type: Optional[str] = None,
                      error_message: Optional[str] = None,
                      context_info: Optional[str] = None) -> None:
        """
        Log an operation to the audit log.
        
        Args:
            operation_type: Type of operation
            outcome: Operation outcome
            component_name: Name of component
            entity_name: Entity name
            financier_email: Financier email
            file_path: File path
            attachment_names: JSON array of attachment names
            attachment_sizes: JSON array of attachment sizes
            checksum: File checksum
            error_type: Error type
            error_message: Error message
            context_info: Additional context as JSON
        """
        try:
            with db.get_session() as session:
                audit_entry = AuditLog(
                    timestamp=datetime.utcnow(),
                    operation_type=operation_type,
                    outcome=outcome,
                    component_name=component_name,
                    entity_name=entity_name,
                    financier_email=financier_email,
                    file_path=file_path,
                    attachment_names=attachment_names,
                    attachment_sizes=attachment_sizes,
                    checksum=checksum,
                    error_type=error_type,
                    error_message=error_message,
                    context_info=context_info
                )
                
                session.add(audit_entry)
                
        except Exception as e:
            logger.error("audit_log_write_failed", error=str(e))
            # Don't raise - audit logging failure shouldn't stop the system
    
    def query_logs(self, 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   entity_name: Optional[str] = None,
                   financier_email: Optional[str] = None,
                   limit: int = 1000) -> List[Dict]:
        """
        Query audit logs.
        
        Args:
            start_date: Start date for query
            end_date: End date for query
            entity_name: Filter by entity name
            financier_email: Filter by financier email
            limit: Maximum number of results
            
        Returns:
            List of audit log entries as dictionaries
        """
        try:
            with db.get_session() as session:
                query = session.query(AuditLog)
                
                # Apply filters
                if start_date:
                    query = query.filter(AuditLog.timestamp >= start_date)
                
                if end_date:
                    query = query.filter(AuditLog.timestamp <= end_date)
                
                if entity_name:
                    query = query.filter(AuditLog.entity_name == entity_name)
                
                if financier_email:
                    query = query.filter(AuditLog.financier_email == financier_email)
                
                # Order by timestamp descending
                query = query.order_by(AuditLog.timestamp.desc())
                
                # Limit results
                query = query.limit(limit)
                
                # Execute query
                results = query.all()
                
                # Convert to dictionaries
                logs = []
                for result in results:
                    log_dict = {
                        'log_id': result.log_id,
                        'timestamp': result.timestamp.isoformat(),
                        'operation_type': result.operation_type.value,
                        'outcome': result.outcome.value,
                        'component_name': result.component_name,
                        'entity_name': result.entity_name,
                        'financier_email': result.financier_email,
                        'file_path': result.file_path,
                        'error_type': result.error_type,
                        'error_message': result.error_message
                    }
                    logs.append(log_dict)
                
                return logs
                
        except Exception as e:
            logger.error("audit_log_query_failed", error=str(e))
            return []
    
    def cleanup_old_logs(self, retention_months: int = 24) -> int:
        """
        Clean up audit logs older than retention period.
        
        Args:
            retention_months: Number of months to retain logs
            
        Returns:
            Number of logs deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_months * 30)
            
            with db.get_session() as session:
                deleted_count = session.query(AuditLog).filter(
                    AuditLog.timestamp < cutoff_date
                ).delete()
                
                logger.info("audit_logs_cleaned_up", 
                          deleted_count=deleted_count,
                          cutoff_date=cutoff_date.isoformat())
                
                return deleted_count
                
        except Exception as e:
            logger.error("audit_log_cleanup_failed", error=str(e))
            return 0
