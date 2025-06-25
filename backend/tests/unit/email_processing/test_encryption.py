"""
Unit tests for credential encryption utilities.
"""
import pytest
import json
from unittest.mock import patch

from src.email_processing.encryption import CredentialEncryption


class TestCredentialEncryption:
    """Test credential encryption and decryption."""
    
    @pytest.fixture
    def encryption_service(self):
        """Create encryption service instance."""
        # Create encryption service with a direct Fernet key for testing
        from cryptography.fernet import Fernet
        test_key = Fernet.generate_key()

        with patch('src.email_processing.encryption.settings') as mock_settings:
            mock_settings.ENCRYPTION_KEY = test_key.decode()
            return CredentialEncryption()
    
    def test_encrypt_decrypt_credentials(self, encryption_service):
        """Test encrypting and decrypting credentials."""
        test_credentials = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
        }
        
        # Encrypt credentials
        encrypted = encryption_service.encrypt_credentials(test_credentials)
        
        # Verify encrypted data is a string
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0
        
        # Decrypt credentials
        decrypted = encryption_service.decrypt_credentials(encrypted)
        
        # Verify decrypted data matches original
        assert decrypted == test_credentials
        assert decrypted["access_token"] == "test_access_token"
        assert decrypted["refresh_token"] == "test_refresh_token"
    
    def test_encrypt_empty_credentials(self, encryption_service):
        """Test encrypting empty credentials."""
        empty_credentials = {}
        
        encrypted = encryption_service.encrypt_credentials(empty_credentials)
        decrypted = encryption_service.decrypt_credentials(encrypted)
        
        assert decrypted == empty_credentials
    
    def test_encrypt_complex_credentials(self, encryption_service):
        """Test encrypting complex credential structures."""
        complex_credentials = {
            "access_token": "test_token",
            "metadata": {
                "user_info": {
                    "email": "test@example.com",
                    "verified": True
                },
                "scopes": ["scope1", "scope2"]
            },
            "expiry": "2024-12-31T23:59:59Z"
        }
        
        encrypted = encryption_service.encrypt_credentials(complex_credentials)
        decrypted = encryption_service.decrypt_credentials(encrypted)
        
        assert decrypted == complex_credentials
        assert decrypted["metadata"]["user_info"]["email"] == "test@example.com"
        assert decrypted["metadata"]["scopes"] == ["scope1", "scope2"]
    
    def test_decrypt_invalid_data(self, encryption_service):
        """Test decrypting invalid data raises exception."""
        with pytest.raises(Exception):
            encryption_service.decrypt_credentials("invalid_encrypted_data")
    
    def test_encrypt_non_serializable_data(self, encryption_service):
        """Test encrypting non-JSON-serializable data raises exception."""
        import datetime
        
        non_serializable = {
            "date": datetime.datetime.now(),  # datetime objects are not JSON serializable
            "token": "test_token"
        }
        
        with pytest.raises(Exception):
            encryption_service.encrypt_credentials(non_serializable)
