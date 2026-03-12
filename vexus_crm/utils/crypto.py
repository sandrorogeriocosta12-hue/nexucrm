"""
Encryption utilities for sensitive configuration fields.
Uses Fernet (symmetric encryption) to protect API keys, tokens, and webhooks.
"""

from cryptography.fernet import Fernet
import os
import base64
import hashlib
from typing import Optional

# Get or create encryption key from environment or config
def _get_encryption_key() -> bytes:
    """Get the master encryption key from environment or config."""
    # Allow override via environment for flexibility
    key_env = os.getenv("VEXUS_ENCRYPTION_KEY")
    if key_env:
        return key_env.encode()
    
    # Fallback: derive a key from a config file or use a default
    # In production, use a secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault)
    try:
        with open(".vexus_secret", "rb") as f:
            return f.read()
    except FileNotFoundError:
        # Generate a default key (NOT FOR PRODUCTION - use env var or secrets manager)
        default_key = Fernet.generate_key()
        # Optionally save it for local development
        # with open(".vexus_secret", "wb") as f:
        #     f.write(default_key)
        return default_key


_cipher = Fernet(_get_encryption_key())


def encrypt(plaintext: str) -> str:
    """Encrypt a string value (e.g., API key)."""
    if not plaintext:
        return plaintext
    encrypted = _cipher.encrypt(plaintext.encode())
    return encrypted.decode()  # Return as string


def decrypt(ciphertext: str) -> str:
    """Decrypt a string value."""
    if not ciphertext:
        return ciphertext
    try:
        decrypted = _cipher.decrypt(ciphertext.encode())
        return decrypted.decode()
    except Exception as e:
        # If decryption fails, return the value as-is or log error
        import logging
        logging.error(f"Decryption failed: {e}")
        return ciphertext


def is_encrypted(value: str) -> bool:
    """Check if a value looks encrypted (Fernet format)."""
    try:
        _cipher.decrypt(value.encode())
        return True
    except:
        return False
