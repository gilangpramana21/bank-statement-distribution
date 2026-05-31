"""
Configuration management module for Bank Statement Distribution System.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration manager for the system."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
        self._load_env_vars()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)
    
    def _load_env_vars(self) -> None:
        """Load sensitive configuration from environment variables."""
        self._config['encryption_key'] = os.getenv('ENCRYPTION_KEY')
        self._config['db_user'] = os.getenv('DB_USER')
        self._config['db_password'] = os.getenv('DB_PASSWORD')
        self._config['email_user'] = os.getenv('EMAIL_USER')
        self._config['email_password'] = os.getenv('EMAIL_PASSWORD')
        self._config['admin_emails'] = os.getenv('ADMIN_EMAILS', '').split(',')
        self._config['environment'] = os.getenv('ENVIRONMENT', 'development')
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'database.host')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    @property
    def google_drive_credentials_file(self) -> str:
        """Get Google Drive credentials file path."""
        return self.get('google_drive.credentials_file')
    
    @property
    def bank_groups(self) -> List[str]:
        """Get list of bank group folders."""
        return self.get('google_drive.bank_groups', [])
    
    @property
    def max_depth(self) -> int:
        """Get maximum folder traversal depth."""
        return self.get('google_drive.max_depth', 10)
    
    @property
    def smtp_host(self) -> str:
        """Get SMTP server host."""
        return self.get('email.smtp_host')
    
    @property
    def smtp_port(self) -> int:
        """Get SMTP server port."""
        return self.get('email.smtp_port', 587)
    
    @property
    def use_tls(self) -> bool:
        """Check if TLS should be used for email."""
        return self.get('email.use_tls', True)
    
    @property
    def sender_address(self) -> str:
        """Get email sender address."""
        return self.get('email.sender_address')
    
    @property
    def max_attachment_size_mb(self) -> int:
        """Get maximum email attachment size in MB."""
        return self.get('email.max_attachment_size_mb', 25)
    
    @property
    def max_attachment_size_bytes(self) -> int:
        """Get maximum email attachment size in bytes."""
        return self.max_attachment_size_mb * 1024 * 1024
    
    @property
    def db_host(self) -> str:
        """Get database host."""
        return self.get('database.host', 'localhost')
    
    @property
    def db_port(self) -> int:
        """Get database port."""
        return self.get('database.port', 5432)
    
    @property
    def db_name(self) -> str:
        """Get database name."""
        return self.get('database.database', 'bank_statements')
    
    @property
    def db_user(self) -> str:
        """Get database user."""
        return self._config.get('db_user')
    
    @property
    def db_password(self) -> str:
        """Get database password."""
        return self._config.get('db_password')
    
    @property
    def encryption_key(self) -> str:
        """Get encryption key."""
        return self._config.get('encryption_key')
    
    @property
    def email_user(self) -> str:
        """Get email username."""
        return self._config.get('email_user')
    
    @property
    def email_password(self) -> str:
        """Get email password."""
        return self._config.get('email_password')
    
    @property
    def admin_emails(self) -> List[str]:
        """Get admin email addresses."""
        return [email.strip() for email in self._config.get('admin_emails', []) if email.strip()]
    
    @property
    def batch_size(self) -> int:
        """Get processing batch size."""
        return self.get('processing.batch_size', 100)
    
    @property
    def max_split_parts(self) -> int:
        """Get maximum number of split parts for archives."""
        return self.get('processing.max_split_parts', 10)
    
    @property
    def execution_timeout_minutes(self) -> int:
        """Get execution timeout in minutes."""
        return self.get('processing.execution_timeout_minutes', 60)
    
    @property
    def warning_timeout_minutes(self) -> int:
        """Get warning timeout in minutes."""
        return self.get('processing.warning_timeout_minutes', 30)
    
    @property
    def max_retry_attempts(self) -> int:
        """Get maximum retry attempts."""
        return self.get('retry.max_attempts', 3)
    
    @property
    def initial_backoff_seconds(self) -> int:
        """Get initial backoff time in seconds."""
        return self.get('retry.initial_backoff_seconds', 1)
    
    @property
    def max_backoff_seconds(self) -> int:
        """Get maximum backoff time in seconds."""
        return self.get('retry.max_backoff_seconds', 60)
    
    @property
    def gdrive_rate_limit(self) -> int:
        """Get Google Drive API rate limit (requests per second)."""
        return self.get('google_drive.rate_limit_per_second', 10)
    
    @property
    def email_rate_limit(self) -> int:
        """Get email rate limit (emails per minute)."""
        return self.get('email.rate_limit_per_minute', 10)
    
    @property
    def rate_limit_threshold(self) -> float:
        """Get rate limit threshold (0.0 to 1.0)."""
        return self.get('google_drive.rate_limit_threshold', 0.8)
    
    @property
    def normal_pause_seconds(self) -> int:
        """Get normal pause duration in seconds."""
        return self.get('cooldown.normal_pause_seconds', 60)
    
    @property
    def quota_exceeded_pause_seconds(self) -> int:
        """Get quota exceeded pause duration in seconds."""
        return self.get('cooldown.quota_exceeded_pause_seconds', 300)
    
    @property
    def audit_retention_months(self) -> int:
        """Get audit log retention period in months."""
        return self.get('audit.retention_months', 24)
    
    @property
    def health_check_port(self) -> int:
        """Get health check server port."""
        return self.get('health.port', 8080)
    
    @property
    def health_check_endpoint(self) -> str:
        """Get health check endpoint path."""
        return self.get('health.endpoint', '/health')
    
    @property
    def health_check_timeout(self) -> int:
        """Get health check timeout in seconds."""
        return self.get('health.timeout_seconds', 5)
    
    def validate(self) -> List[str]:
        """
        Validate configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required environment variables
        if not self.encryption_key:
            errors.append("ENCRYPTION_KEY environment variable is not set")
        
        if not self.db_user:
            errors.append("DB_USER environment variable is not set")
        
        if not self.db_password:
            errors.append("DB_PASSWORD environment variable is not set")
        
        if not self.email_user:
            errors.append("EMAIL_USER environment variable is not set")
        
        if not self.email_password:
            errors.append("EMAIL_PASSWORD environment variable is not set")
        
        # Check required configuration values
        if not self.bank_groups:
            errors.append("No bank groups configured in config.yaml")
        
        if not self.smtp_host:
            errors.append("SMTP host not configured in config.yaml")
        
        if not self.sender_address:
            errors.append("Sender address not configured in config.yaml")
        
        if not self.admin_emails:
            errors.append("No admin emails configured in ADMIN_EMAILS environment variable")
        
        return errors


# Global configuration instance
config = Config()
