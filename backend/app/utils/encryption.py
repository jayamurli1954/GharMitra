"""
Encryption utility for sensitive data fields
Uses Fernet (symmetric encryption) for encrypting storage locations and verification notes
"""
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # Note: Use PBKDF2HMAC, not PBKDF2
import base64
from app.config import settings


class EncryptionManager:
    def __init__(self):
        # Get encryption key from environment variable or settings
        key_string = os.getenv('ENCRYPTION_KEY') or getattr(settings, 'ENCRYPTION_KEY', None)
        
        if not key_string:
            raise ValueError("ENCRYPTION_KEY environment variable not set. Please set it in .env file")
        
        # Derive a proper Fernet key from the string
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'gharmitra_salt_2024',  # Use a fixed salt (or store securely)
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_string.encode()))
        self.cipher = Fernet(key)
    
    def encrypt(self, text: str) -> str:
        """Encrypt a string and return base64-encoded result."""
        if not text:
            return ""
        
        try:
            encrypted = self.cipher.encrypt(text.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            print(f"Encryption error: {e}")
            raise
    
    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt a base64-encoded encrypted string."""
        if not encrypted_text:
            return ""
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            raise


# Singleton instance
_encryption_manager = None


def get_encryption_manager() -> EncryptionManager:
    """Get or create the encryption manager singleton"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def encrypt(text: str) -> str:
    """Encrypt a string using the encryption manager"""
    return get_encryption_manager().encrypt(text)


def decrypt(encrypted_text: str) -> str:
    """Decrypt an encrypted string using the encryption manager"""
    return get_encryption_manager().decrypt(encrypted_text)

