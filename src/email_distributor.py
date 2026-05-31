"""
Email Distributor component for sending statement packages via email.
"""

import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.config import config
from src.database import db
from src.models import Financier, EntityMapping, DeliveryStatus, ProcessingStatus, ActiveStatus
from src.package_manager import Package
from src.security import decrypt_credential
from src.logger import get_logger
import re

logger = get_logger(__name__)


class EmailDistributor:
    """Sends statement packages as email attachments."""
    
    def __init__(self):
        """Initialize Email Distributor."""
        self.smtp_connection = None
        self.rate_limiter = EmailRateLimiter(
            max_emails_per_minute=config.email_rate_limit,
            threshold=config.rate_limit_threshold
        )
    
    def _connect_smtp(self) -> None:
        """Connect to SMTP server."""
        try:
            # Decrypt email credentials
            email_user = config.email_user
            email_password = decrypt_credential(config.email_password)
            
            # Create SMTP connection
            if config.use_tls:
                if config.smtp_port == 465:
                    # Implicit TLS
                    self.smtp_connection = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port)
                else:
                    # STARTTLS
                    self.smtp_connection = smtplib.SMTP(config.smtp_host, config.smtp_port)
                    self.smtp_connection.starttls()
            else:
                self.smtp_connection = smtplib.SMTP(config.smtp_host, config.smtp_port)
            
            # Authenticate
            self.smtp_connection.login(email_user, email_password)
            
            logger.info("smtp_connected", host=config.smtp_host)
            
        except Exception as e:
            logger.error("smtp_connection_failed", error=str(e))
            raise
    
    def _disconnect_smtp(self) -> None:
        """Disconnect from SMTP server."""
        if self.smtp_connection:
            try:
                self.smtp_connection.quit()
                logger.info("smtp_disconnected")
            except Exception as e:
                logger.warning("smtp_disconnect_failed", error=str(e))
            finally:
                self.smtp_connection = None
    
    def distribute_packages(self, packages: Dict[str, List[Package]]) -> Tuple[int, int]:
        """
        Distribute packages to authorized financiers.
        
        Args:
            packages: Dictionary mapping entity names to lists of Package objects
            
        Returns:
            Tuple of (successful_deliveries, failed_deliveries)
        """
        successful = 0
        failed = 0
        
        try:
            # Connect to SMTP
            self._connect_smtp()
            
            # Get financier-entity mappings
            financier_mappings = self._get_financier_mappings()
            
            if not financier_mappings:
                logger.error("no_financier_mappings_found")
                return 0, 0
            
            # Distribute packages
            for entity, entity_packages in packages.items():
                # Get authorized financiers for this entity
                authorized_financiers = financier_mappings.get(entity, [])
                
                if not authorized_financiers:
                    logger.warning("no_authorized_financiers", entity=entity)
                    continue
                
                # Send to each authorized financier
                for financier in authorized_financiers:
                    for package in entity_packages:
                        try:
                            # Rate limiting
                            self.rate_limiter.wait_if_needed()
                            
                            # Send email
                            self._send_email(financier, entity, package)
                            successful += 1
                            
                        except Exception as e:
                            logger.error("email_delivery_failed",
                                       financier_email=financier.email_address,
                                       entity=entity,
                                       error=str(e))
                            failed += 1
            
            logger.info("distribution_complete", 
                       successful=successful, 
                       failed=failed)
            
            return successful, failed
            
        finally:
            self._disconnect_smtp()
    
    def _get_financier_mappings(self) -> Dict[str, List[Financier]]:
        """
        Get financier-entity mappings from database.
        
        Returns:
            Dictionary mapping entity names to lists of Financier objects
        """
        try:
            with db.get_session() as session:
                # Query active financiers with their entity mappings
                financiers = session.query(Financier).filter(
                    Financier.active_status == ActiveStatus.ACTIVE
                ).all()
                
                # Build mapping
                entity_financiers = {}
                
                for financier in financiers:
                    for mapping in financier.entity_mappings:
                        entity = mapping.entity_name
                        
                        if entity not in entity_financiers:
                            entity_financiers[entity] = []
                        
                        entity_financiers[entity].append(financier)
                
                logger.info("financier_mappings_loaded", 
                          entity_count=len(entity_financiers),
                          financier_count=len(financiers))
                
                return entity_financiers
                
        except Exception as e:
            logger.error("financier_mappings_load_failed", error=str(e))
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=5, min=5, max=20),
        retry=retry_if_exception_type((smtplib.SMTPException, ConnectionError)),
        reraise=True
    )
    def _send_email(self, financier: Financier, entity: str, package: Package) -> None:
        """
        Send email with package attachment.
        
        Args:
            financier: Financier object
            entity: Entity name
            package: Package object
            
        Raises:
            ValueError: If email validation fails
            smtplib.SMTPException: If email sending fails
        """
        try:
            # Validate recipient email
            if not self._validate_email(financier.email_address):
                raise ValueError(f"Invalid email address: {financier.email_address}")
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = config.sender_address
            msg['To'] = financier.email_address
            msg['Subject'] = self._create_subject(entity)
            
            # Add body
            body = self._create_body(entity)
            msg.attach(MIMEText(body, 'plain'))
            
            # Add attachment
            self._add_attachment(msg, package)
            
            # Send email
            self.smtp_connection.send_message(msg)
            
            logger.info("email_sent",
                       financier_email=financier.email_address,
                       entity=entity,
                       package_name=package.get_filename())
            
            # Record delivery in database
            self._record_delivery(financier, entity, package)
            
        except Exception as e:
            logger.error("email_send_failed",
                       financier_email=financier.email_address,
                       entity=entity,
                       error=str(e))
            raise
    
    def _validate_email(self, email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not email or '@' not in email:
            return False
        
        parts = email.split('@')
        if len(parts) != 2:
            return False
        
        if not parts[0] or not parts[1]:
            return False
        
        return True
    
    def _create_subject(self, entity: str) -> str:
        """
        Create email subject line.
        
        Args:
            entity: Entity name
            
        Returns:
            Subject line string
        """
        date_str = datetime.now().strftime("%Y-%m")
        return f"Bank Statements - {entity} - {date_str}"
    
    def _create_body(self, entity: str) -> str:
        """
        Create email body text.
        
        Args:
            entity: Entity name
            
        Returns:
            Body text string
        """
        date_str = datetime.now().strftime("%Y-%m")
        iso_date = datetime.now().isoformat()
        
        body = f"""Dear Financier,

Please find attached the bank statements for {entity} for the period {date_str}.

Distribution Date: {iso_date}

Best regards,
Bank Statement Distribution System
"""
        return body
    
    def _add_attachment(self, msg: MIMEMultipart, package: Package) -> None:
        """
        Add package as email attachment.
        
        Args:
            msg: Email message object
            package: Package object
        """
        try:
            with open(package.file_path, 'rb') as f:
                part = MIMEBase('application', 'zip')
                part.set_payload(f.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={package.get_filename()}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.error("attachment_add_failed", 
                       package_path=package.file_path,
                       error=str(e))
            raise
    
    def _record_delivery(self, financier: Financier, entity: str, package: Package) -> None:
        """
        Record successful delivery in database.
        
        Args:
            financier: Financier object
            entity: Entity name
            package: Package object
        """
        try:
            with db.get_session() as session:
                # Update delivery status for all files in package
                for file in package.files:
                    delivery = session.query(DeliveryStatus).filter_by(
                        file_id=file.file_id,
                        financier_id=financier.financier_id
                    ).first()
                    
                    if delivery:
                        delivery.status = ProcessingStatus.DELIVERED
                        delivery.delivery_timestamp = datetime.utcnow()
                        delivery.retry_count = 0
                        delivery.last_error = None
                    else:
                        delivery = DeliveryStatus(
                            file_id=file.file_id,
                            financier_id=financier.financier_id,
                            status=ProcessingStatus.DELIVERED,
                            delivery_timestamp=datetime.utcnow()
                        )
                        session.add(delivery)
                
                logger.debug("delivery_recorded",
                           financier_id=financier.financier_id,
                           entity=entity,
                           file_count=len(package.files))
                
        except Exception as e:
            logger.error("delivery_record_failed", error=str(e))
            # Don't raise - delivery was successful even if recording failed
    
    def test_connection(self) -> bool:
        """
        Test SMTP connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self._connect_smtp()
            self._disconnect_smtp()
            return True
        except Exception as e:
            logger.error("smtp_connection_test_failed", error=str(e))
            return False


class EmailRateLimiter:
    """Rate limiter for email sending."""
    
    def __init__(self, max_emails_per_minute: int, threshold: float = 0.8):
        """
        Initialize email rate limiter.
        
        Args:
            max_emails_per_minute: Maximum emails per minute
            threshold: Threshold (0.0 to 1.0) at which to start pausing
        """
        self.max_emails = max_emails_per_minute
        self.threshold = threshold
        self.email_count = 0
        self.window_start = datetime.now()
    
    def wait_if_needed(self) -> None:
        """Wait if rate limit threshold is reached."""
        now = datetime.now()
        elapsed = (now - self.window_start).total_seconds()
        
        # Reset counter if window has passed (60 seconds)
        if elapsed >= 60.0:
            self.email_count = 0
            self.window_start = now
        
        # Check if threshold reached
        if self.email_count >= (self.max_emails * self.threshold):
            sleep_time = 60.0 - elapsed
            if sleep_time > 0:
                logger.info("email_rate_limit_pause", sleep_time=sleep_time)
                time.sleep(sleep_time)
                self.email_count = 0
                self.window_start = datetime.now()
        
        self.email_count += 1
