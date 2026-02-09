"""
Cryptography utilities for encrypting sensitive credentials
"""
from cryptography.fernet import Fernet
import base64
import os
from typing import Optional

from .config import settings


class CredentialEncryption:
    """Handles encryption/decryption of sensitive credentials"""
    
    def __init__(self, key: Optional[str] = None):
        """
        Initialize with encryption key
        If no key provided, uses CONFIG_ENCRYPTION_KEY from settings
        """
        encryption_key = key or settings.CONFIG_ENCRYPTION_KEY
        
        if not encryption_key:
            raise ValueError(
                "CONFIG_ENCRYPTION_KEY not configured. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        
        # Ensure key is proper format
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        self.cipher = Fernet(encryption_key)
    
    def encrypt(self, value: str) -> str:
        """
        Encrypt a string value
        Returns base64-encoded encrypted string
        """
        if not value:
            return ""
        encrypted = self.cipher.encrypt(value.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_value: str) -> str:
        """
        Decrypt an encrypted string
        """
        if not encrypted_value:
            return ""
        decrypted = self.cipher.decrypt(encrypted_value.encode())
        return decrypted.decode()
    
    def encrypt_bytes(self, value: bytes) -> bytes:
        """Encrypt bytes directly"""
        return self.cipher.encrypt(value)
    
    def decrypt_bytes(self, encrypted_value: bytes) -> bytes:
        """Decrypt bytes directly"""
        return self.cipher.decrypt(encrypted_value)


def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key"""
    return Fernet.generate_key().decode()


# Singleton instance (lazy loaded)
_crypto_instance: CredentialEncryption | None = None


def get_crypto() -> CredentialEncryption:
    """Get or create the crypto singleton"""
    global _crypto_instance
    if _crypto_instance is None:
        _crypto_instance = CredentialEncryption()
    return _crypto_instance
