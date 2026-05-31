"""
Health Check service for monitoring system status.
"""

from datetime import datetime, timedelta
from typing import Dict
from flask import Flask, jsonify
from src.config import config
from src.database import db
from src.models import SystemHealth, DeliveryStatus, ProcessingStatus, ConnectivityStatus
from src.statement_scanner import StatementScanner
from src.email_distributor import EmailDistributor
from src.logger import get_logger

logger = get_logger(__name__)

app = Flask(__name__)


class HealthCheckService:
    """Monitors and reports system health status."""
    
    def __init__(self):
        """Initialize Health Check Service."""
        pass
    
    def get_health_status(self) -> Dict:
        """
        Get comprehensive health status.
        
        Returns:
            Health status dictionary
        """
        try:
            # Check component connectivity
            gdrive_status = self._check_gdrive_connectivity()
            email_status = self._check_email_connectivity()
            db_status = self._check_db_connectivity()
            
            # Get delivery statistics
            pending_count = self._get_pending_deliveries_count()
            failed_count = self._get_failed_deliveries_count()
            
            # Get last execution info
            last_execution = self._get_last_execution_timestamp()
            
            # Determine overall status
            overall_status = "healthy"
            if (gdrive_status != ConnectivityStatus.CONNECTED or
                email_status != ConnectivityStatus.CONNECTED or
                db_status != ConnectivityStatus.CONNECTED or
                failed_count > 0):
                overall_status = "unhealthy"
            
            health_data = {
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "last_execution": last_execution,
                "connectivity": {
                    "google_drive": gdrive_status.value,
                    "email_server": email_status.value,
                    "database": db_status.value
                },
                "deliveries": {
                    "pending": pending_count,
                    "failed_last_24h": failed_count
                }
            }
            
            # Update system health table
            self._update_system_health(health_data)
            
            return health_data
            
        except Exception as e:
            logger.error("health_check_failed", error=str(e))
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def _check_gdrive_connectivity(self) -> ConnectivityStatus:
        """
        Check Google Drive API connectivity.
        
        Returns:
            Connectivity status
        """
        try:
            scanner = StatementScanner()
            # Try to authenticate
            if scanner.service:
                return ConnectivityStatus.CONNECTED
            else:
                return ConnectivityStatus.DISCONNECTED
                
        except Exception as e:
            logger.error("gdrive_connectivity_check_failed", error=str(e))
            return ConnectivityStatus.ERROR
    
    def _check_email_connectivity(self) -> ConnectivityStatus:
        """
        Check email server connectivity.
        
        Returns:
            Connectivity status
        """
        try:
            distributor = EmailDistributor()
            if distributor.test_connection():
                return ConnectivityStatus.CONNECTED
            else:
                return ConnectivityStatus.DISCONNECTED
                
        except Exception as e:
            logger.error("email_connectivity_check_failed", error=str(e))
            return ConnectivityStatus.ERROR
    
    def _check_db_connectivity(self) -> ConnectivityStatus:
        """
        Check database connectivity.
        
        Returns:
            Connectivity status
        """
        try:
            if db.test_connection():
                return ConnectivityStatus.CONNECTED
            else:
                return ConnectivityStatus.DISCONNECTED
                
        except Exception as e:
            logger.error("db_connectivity_check_failed", error=str(e))
            return ConnectivityStatus.ERROR
    
    def _get_pending_deliveries_count(self) -> int:
        """
        Get count of pending deliveries.
        
        Returns:
            Number of pending deliveries
        """
        try:
            with db.get_session() as session:
                count = session.query(DeliveryStatus).filter(
                    DeliveryStatus.status == ProcessingStatus.PENDING
                ).count()
                
                return count
                
        except Exception as e:
            logger.error("pending_deliveries_count_failed", error=str(e))
            return 0
    
    def _get_failed_deliveries_count(self) -> int:
        """
        Get count of failed deliveries in last 24 hours.
        
        Returns:
            Number of failed deliveries
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            with db.get_session() as session:
                count = session.query(DeliveryStatus).filter(
                    DeliveryStatus.status == ProcessingStatus.PENDING,
                    DeliveryStatus.updated_at >= cutoff_time
                ).count()
                
                return count
                
        except Exception as e:
            logger.error("failed_deliveries_count_failed", error=str(e))
            return 0
    
    def _get_last_execution_timestamp(self) -> str:
        """
        Get timestamp of last successful execution.
        
        Returns:
            ISO 8601 timestamp string or None
        """
        try:
            with db.get_session() as session:
                health = session.query(SystemHealth).first()
                
                if health and health.last_execution_timestamp:
                    return health.last_execution_timestamp.isoformat()
                
                return None
                
        except Exception as e:
            logger.error("last_execution_timestamp_failed", error=str(e))
            return None
    
    def _update_system_health(self, health_data: Dict) -> None:
        """
        Update system health table.
        
        Args:
            health_data: Health status data
        """
        try:
            with db.get_session() as session:
                health = session.query(SystemHealth).first()
                
                if not health:
                    health = SystemHealth()
                    session.add(health)
                
                # Update fields
                connectivity = health_data.get('connectivity', {})
                deliveries = health_data.get('deliveries', {})
                
                health.gdrive_connectivity = ConnectivityStatus(connectivity.get('google_drive'))
                health.email_connectivity = ConnectivityStatus(connectivity.get('email_server'))
                health.db_connectivity = ConnectivityStatus(connectivity.get('database'))
                health.pending_deliveries_count = deliveries.get('pending', 0)
                health.failed_deliveries_count = deliveries.get('failed_last_24h', 0)
                health.updated_at = datetime.utcnow()
                
        except Exception as e:
            logger.error("system_health_update_failed", error=str(e))


# Flask routes
health_service = HealthCheckService()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    health_status = health_service.get_health_status()
    
    status_code = 200 if health_status.get('status') == 'healthy' else 503
    
    return jsonify(health_status), status_code


def start_health_check_server():
    """Start health check HTTP server."""
    port = config.health_check_port
    
    logger.info("starting_health_check_server", port=port)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
