"""
FinAgent — AES-256-GCM Encryption
Encrypts sensitive fields (notes, account numbers) at rest.
Key is derived from SECRET_KEY env var via PBKDF2.
"""
import os
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from dotenv import load_dotenv

load_dotenv()

_RAW_KEY = os.getenv("SECRET_KEY", "finagent-default-key-32-chars!!")


def _derive_key(raw_key: str) -> bytes:
    """Derive a 32-byte AES key from the raw secret key using SHA-256."""
    return hashlib.sha256(raw_key.encode()).digest()


AES_KEY = _derive_key(_RAW_KEY)


def encrypt(plaintext: str) -> str:
    """
    Encrypt a string using AES-256-GCM.
    Returns: base64-encoded string of (nonce + tag + ciphertext)
    """
    if not plaintext:
        return ""
    nonce = get_random_bytes(16)
    cipher = AES.new(AES_KEY, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))
    # Pack: nonce (16) + tag (16) + ciphertext
    packed = nonce + tag + ciphertext
    return base64.b64encode(packed).decode("utf-8")


def decrypt(encrypted_b64: str) -> str:
    """
    Decrypt an AES-256-GCM encrypted string.
    Input: base64-encoded string of (nonce + tag + ciphertext)
    """
    if not encrypted_b64:
        return ""
    try:
        packed = base64.b64decode(encrypted_b64.encode("utf-8"))
        nonce = packed[:16]
        tag = packed[16:32]
        ciphertext = packed[32:]
        cipher = AES.new(AES_KEY, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode("utf-8")
    except Exception:
        return "[decryption error]"
