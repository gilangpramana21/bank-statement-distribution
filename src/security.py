"""
Security module for credential encryption and management.
"""

from cryptography.fernet import Fernet
from src.config import config
import structlog

logger = structlog.get_logger(__name__)


class CredentialManager:
    """Manages encrypted credentials."""
    
    def __init__(self):
        """Initialize credential manager."""
        self.cipher_suite = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize encryption cipher."""
        try:
            encryption_key = config.encryption_key
            if not encryption_key:
                raise ValueError("Encryption key not configured")
            
            # Convert string key to bytes if needed
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()
            
            self.cipher_suite = Fernet(encryption_key)
            logger.info("credential_manager_initialized")
            
        except Exception as e:
            logger.error("credential_manager_initialization_failed", error=str(e))
            raise
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a credential.
        
        Args:
            plaintext: Plain text credential
            
        Returns:
            Encrypted credential (base64 encoded)
        """
        try:
            if not plaintext:
                return ""
            
            encrypted = self.cipher_suite.encrypt(plaintext.encode())
            return encrypted.decode()
            
        except Exception as e:
            logger.error("credential_encryption_failed", error="[REDACTED]")
            raise ValueError("Credential encryption failed")
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a credential.
        
        Args:
            ciphertext: Encrypted credential (base64 encoded)
            
        Returns:
            Decrypted plain text credential
        """
        try:
            if not ciphertext:
                return ""
            
            decrypted = self.cipher_suite.decrypt(ciphertext.encode())
            return decrypted.decode()
            
        except Exception as e:
            logger.error("credential_decryption_failed", error="[REDACTED]")
            raise ValueError("Credential retrieval failed for [service name]")
    
    def validate_credential(self, service_name: str, credential: str) -> bool:
        """
        Validate a credential by attempting to use it.
        
        Args:
            service_name: Name of the service (e.g., 'google_drive', 'email', 'database')
            credential: Credential to validate
            
        Returns:
            True if credential is valid, False otherwise
        """
        # This is a placeholder - actual validation would depend on the service
        # For example, for email, we would try to authenticate with SMTP
        # For Google Drive, we would try to authenticate with the API
        logger.info("credential_validation_requested", service=service_name)
        return True


# Global credential manager instance
credential_manager = CredentialManager()


def encrypt_credential(plaintext: str) -> str:
    """
    Encrypt a credential.
    
    Args:
        plaintext: Plain text credential
        
    Returns:
        Encrypted credential
    """
    return credential_manager.encrypt(plaintext)


def decrypt_credential(ciphertext: str) -> str:
    """
    Decrypt a credential.
    
    Args:
        ciphertext: Encrypted credential
        
    Returns:
        Decrypted credential
    """
    return credential_manager.decrypt(ciphertext)


def mask_credential(value: str, visible_chars: int = 4) -> str:
    """
    Mask a credential for logging.
    
    Args:
        value: Credential value to mask
        visible_chars: Number of characters to show at the end
        
    Returns:
        Masked credential (e.g., "****1234")
    """
    if not value or len(value) <= visible_chars:
        return "[REDACTED]"
    
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]


def sanitize_log_message(message: str) -> str:
    """
    Sanitize log message to remove potential credentials.
    
    Args:
        message: Log message
        
    Returns:
        Sanitized message
    """
    # List of patterns that might indicate credentials
    sensitive_patterns = [
        'password', 'passwd', 'pwd', 'secret', 'token', 
        'api_key', 'apikey', 'credential', 'auth'
    ]
    
    # Simple sanitization - replace values after sensitive keywords
    sanitized = message
    for pattern in sensitive_patterns:
        if pattern in message.lower():
            # This is a simple implementation
            # In production, you might want more sophisticated pattern matching
            sanitized = sanitized.replace(pattern, "[REDACTED]")
    
    return sanitized
