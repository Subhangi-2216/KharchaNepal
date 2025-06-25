"""
Encryption utilities for securely storing OAuth credentials.
"""
import base64
import json
import logging
from typing import Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from config import settings

logger = logging.getLogger(__name__)


class CredentialEncryption:
    """Handles encryption and decryption of OAuth credentials."""
    
    def __init__(self):
        self.encryption_key = self._get_or_generate_key()
        self.fernet = Fernet(self.encryption_key)
    
    def _get_or_generate_key(self) -> bytes:
        """
        Get encryption key from settings or generate a new one.

        Returns:
            Encryption key as base64-encoded bytes for Fernet
        """
        if settings.ENCRYPTION_KEY:
            # Use existing key from settings (should be base64 encoded)
            try:
                return settings.ENCRYPTION_KEY.encode()
            except Exception as e:
                logger.error(f"Error encoding encryption key: {e}")
                raise
        else:
            # Generate a new key (for development only)
            logger.warning("No encryption key found in settings. Generating a new one for development.")
            key = Fernet.generate_key()
            logger.info(f"Generated encryption key (save this to ENCRYPTION_KEY in .env): {key.decode()}")
            return key
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """
        Encrypt OAuth credentials for storage.
        
        Args:
            credentials: Dictionary containing OAuth credentials
            
        Returns:
            Encrypted credentials as base64 string
        """
        try:
            # Convert credentials to JSON string
            credentials_json = json.dumps(credentials)
            
            # Encrypt the JSON string
            encrypted_data = self.fernet.encrypt(credentials_json.encode())
            
            # Return as base64 string for database storage
            return base64.urlsafe_b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f"Error encrypting credentials: {e}")
            raise
    
    def decrypt_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """
        Decrypt OAuth credentials from storage.
        
        Args:
            encrypted_credentials: Base64 encoded encrypted credentials
            
        Returns:
            Decrypted credentials dictionary
        """
        try:
            # Decode from base64
            encrypted_data = base64.urlsafe_b64decode(encrypted_credentials.encode())
            
            # Decrypt the data
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            # Parse JSON and return
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            logger.error(f"Error decrypting credentials: {e}")
            raise


# Global instance
credential_encryption = CredentialEncryption()
