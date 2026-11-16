"""Local URL and AES helpers used by FileForge's encoding workspace."""
from __future__ import annotations

import base64
import binascii
import secrets
import string
from urllib.parse import quote, unquote

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def url_encode(value: str, component: bool = False) -> str:
    """Encode UTF-8 text using RFC 3986 URL or component semantics."""
    safe = "-_.~" if component else ":/?#[]@!$&'()*+,;=%"
    return quote(value, safe=safe, encoding="utf-8", errors="strict")


def url_decode(value: str) -> str:
    """Decode percent-encoded UTF-8 without treating '+' as a space."""
    return unquote(value, encoding="utf-8", errors="strict")


def _decode_bytes(value: str, fmt: str, field: str) -> bytes:
    try:
        if fmt == "Hex":
            return bytes.fromhex(value.strip())
        if fmt == "Base64":
            return base64.b64decode(value.strip(), validate=True)
        return value.encode("utf-8")
    except (ValueError, binascii.Error) as exc:
        raise ValueError(f"{field} không đúng định dạng {fmt}.") from exc


def _encode_bytes(value: bytes, fmt: str) -> str:
    if fmt == "Hex":
        return value.hex()
    return base64.b64encode(value).decode("ascii")


def generate_aes_key(bits: int = 256, fmt: str = "Base64") -> str:
    if bits not in (128, 192, 256):
        raise ValueError("AES key phải có độ dài 128, 192 hoặc 256 bit.")
    raw = secrets.token_bytes(bits // 8)
    if fmt == "Plain Text":
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(bits // 8))
    return _encode_bytes(raw, fmt)


def generate_iv(mode: str = "GCM", fmt: str = "Hex") -> str:
    if mode not in ("GCM", "CBC"):
        raise ValueError("Chế độ AES không được hỗ trợ.")
    return _encode_bytes(secrets.token_bytes(12 if mode == "GCM" else 16), fmt)


def aes_encrypt(plaintext: str, key: str, key_format: str = "Base64",
                mode: str = "GCM", iv: str = "", output_format: str = "Base64") -> tuple[str, str]:
    key_bytes = _decode_bytes(key, key_format, "Key")
    if len(key_bytes) not in (16, 24, 32):
        raise ValueError("AES key phải có độ dài 16, 24 hoặc 32 byte.")
    iv_bytes = _decode_bytes(iv, "Hex", "IV") if iv.strip() else secrets.token_bytes(12 if mode == "GCM" else 16)
    data = plaintext.encode("utf-8")
    if mode == "GCM":
        if len(iv_bytes) != 12:
            raise ValueError("IV của AES-GCM phải dài 12 byte (24 ký tự Hex).")
        encrypted = AESGCM(key_bytes).encrypt(iv_bytes, data, None)
    elif mode == "CBC":
        if len(iv_bytes) != 16:
            raise ValueError("IV của AES-CBC phải dài 16 byte (32 ký tự Hex).")
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded = padder.update(data) + padder.finalize()
        encryptor = Cipher(algorithms.AES(key_bytes), modes.CBC(iv_bytes)).encryptor()
        encrypted = encryptor.update(padded) + encryptor.finalize()
    else:
        raise ValueError("Chỉ hỗ trợ AES-GCM và AES-CBC.")
    return _encode_bytes(encrypted, output_format), iv_bytes.hex()


def aes_decrypt(ciphertext: str, key: str, key_format: str = "Base64",
                mode: str = "GCM", iv: str = "", output_format: str = "Base64") -> str:
    key_bytes = _decode_bytes(key, key_format, "Key")
    if len(key_bytes) not in (16, 24, 32):
        raise ValueError("AES key phải có độ dài 16, 24 hoặc 32 byte.")
    if not iv.strip():
        raise ValueError("Cần nhập IV để giải mã.")
    iv_bytes = _decode_bytes(iv, "Hex", "IV")
    encrypted = _decode_bytes(ciphertext, output_format, "Ciphertext")
    if mode == "GCM":
        if len(iv_bytes) != 12:
            raise ValueError("IV của AES-GCM phải dài 12 byte (24 ký tự Hex).")
        # AESGCM verifies the authentication tag and raises InvalidTag on tampering.
        plaintext = AESGCM(key_bytes).decrypt(iv_bytes, encrypted, None)
    elif mode == "CBC":
        if len(iv_bytes) != 16:
            raise ValueError("IV của AES-CBC phải dài 16 byte (32 ký tự Hex).")
        decryptor = Cipher(algorithms.AES(key_bytes), modes.CBC(iv_bytes)).decryptor()
        padded = decryptor.update(encrypted) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        plaintext = unpadder.update(padded) + unpadder.finalize()
    else:
        raise ValueError("Chỉ hỗ trợ AES-GCM và AES-CBC.")
    return plaintext.decode("utf-8")
