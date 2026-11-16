"""Local URL and AES helpers used by FileForge's encoding workspace."""
from __future__ import annotations

import base64
import binascii
import secrets
import string
from urllib.parse import quote, unquote

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


_FORMATS = {"UTF-8", "HEX", "BASE-64"}


def url_encode(value: str, component: bool = False) -> str:
    """Encode UTF-8 text using RFC 3986 URL or component semantics."""
    safe = "-_.~" if component else ":/?#[]@!$&'()*+,;=%"
    return quote(value, safe=safe, encoding="utf-8", errors="strict")


def url_decode(value: str) -> str:
    """Decode percent-encoded UTF-8 without treating '+' as a space."""
    return unquote(value, encoding="utf-8", errors="strict")


def _decode_bytes(value: str, fmt: str, field: str) -> bytes:
    try:
        normalized = fmt.upper()
        if normalized in ("HEX", "HEX"):
            return bytes.fromhex(value.strip())
        if normalized in ("BASE-64", "BASE64"):
            return base64.b64decode(value.strip(), validate=True)
        if normalized in ("UTF-8", "PLAIN TEXT"):
            return value.encode("utf-8")
        raise ValueError(f"Định dạng {fmt} không được hỗ trợ.")
    except (ValueError, binascii.Error) as exc:
        raise ValueError(f"{field} không đúng định dạng {fmt}.") from exc


def _encode_bytes(value: bytes, fmt: str) -> str:
    normalized = fmt.upper()
    if normalized in ("HEX",):
        return value.hex()
    if normalized in ("BASE-64", "BASE64"):
        return base64.b64encode(value).decode("ascii")
    if normalized in ("UTF-8", "PLAIN TEXT"):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Dữ liệu giải mã không phải UTF-8 hợp lệ.") from exc
    raise ValueError(f"Định dạng {fmt} không được hỗ trợ.")


def generate_aes_key(bits: int = 256, fmt: str = "BASE-64") -> str:
    if bits not in (128, 192, 256):
        raise ValueError("AES key phải có độ dài 128, 192 hoặc 256 bit.")
    raw = secrets.token_bytes(bits // 8)
    if fmt.upper() in ("UTF-8", "PLAIN TEXT"):
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(bits // 8))
    return _encode_bytes(raw, fmt)


def generate_iv(mode: str = "GCM", fmt: str = "HEX") -> str:
    normalized = mode.upper()
    if normalized == "ECB":
        return ""
    if normalized not in ("GCM", "CBC", "CTR"):
        raise ValueError("Chế độ AES không được hỗ trợ.")
    size = 12 if normalized == "GCM" else 16
    raw = secrets.token_bytes(size)
    if fmt.upper() in ("UTF-8", "PLAIN TEXT"):
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(size))
    return _encode_bytes(raw, fmt)


def _validate_key(key: str, key_format: str) -> bytes:
    key_bytes = _decode_bytes(key, key_format, "Key")
    if len(key_bytes) not in (16, 24, 32):
        raise ValueError("AES key phải có độ dài 16, 24 hoặc 32 byte.")
    return key_bytes


def _prepare_plaintext(data: bytes, mode: str, padding_name: str) -> bytes:
    if mode in ("GCM", "CTR"):
        if padding_name != "NoPadding":
            raise ValueError(f"AES-{mode} chỉ hỗ trợ NoPadding.")
        return data
    if padding_name == "PKCS5Padding":
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        return padder.update(data) + padder.finalize()
    if padding_name == "NoPadding":
        if len(data) % algorithms.AES.block_size:
            raise ValueError("NoPadding yêu cầu plaintext có độ dài bội số 16 byte.")
        return data
    raise ValueError("Padding không được hỗ trợ.")


def _remove_padding(data: bytes, mode: str, padding_name: str) -> bytes:
    if mode in ("GCM", "CTR") or padding_name == "NoPadding":
        return data
    if padding_name == "PKCS5Padding":
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        try:
            return unpadder.update(data) + unpadder.finalize()
        except ValueError as exc:
            raise ValueError("Sai key/IV hoặc dữ liệu không có PKCS5Padding hợp lệ.") from exc
    raise ValueError("Padding không được hỗ trợ.")


def _mode_instance(mode: str, iv_bytes: bytes):
    if mode == "CBC":
        if len(iv_bytes) != 16:
            raise ValueError("IV của AES-CBC phải dài 16 byte.")
        return modes.CBC(iv_bytes)
    if mode == "CTR":
        if len(iv_bytes) != 16:
            raise ValueError("IV/counter của AES-CTR phải dài 16 byte.")
        return modes.CTR(iv_bytes)
    if mode == "ECB":
        return modes.ECB()
    raise ValueError("Cipher mode không được hỗ trợ.")


def aes_encrypt(plaintext: str, key: str, key_format: str = "BASE-64",
                mode: str = "GCM", iv: str = "", output_format: str = "BASE-64",
                iv_format: str = "HEX", padding_name: str = "NoPadding") -> tuple[str, str]:
    key_bytes = _validate_key(key, key_format)
    normalized_mode = mode.upper()
    if normalized_mode not in ("CBC", "GCM", "CTR", "ECB"):
        raise ValueError("Cipher mode phải là CBC, GCM, CTR hoặc ECB.")

    if normalized_mode == "ECB":
        iv_bytes = b""
        used_iv = ""
    else:
        iv_bytes = _decode_bytes(iv, iv_format, "IV") if iv.strip() else secrets.token_bytes(
            12 if normalized_mode == "GCM" else 16
        )
        used_iv = _encode_bytes(iv_bytes, iv_format)

    data = _prepare_plaintext(plaintext.encode("utf-8"), normalized_mode, padding_name)
    if normalized_mode == "GCM":
        if padding_name != "NoPadding":
            raise ValueError("AES-GCM chỉ hỗ trợ NoPadding.")
        if len(iv_bytes) != 12:
            raise ValueError("IV của AES-GCM nên dài 12 byte.")
        encrypted = AESGCM(key_bytes).encrypt(iv_bytes, data, None)
    else:
        encryptor = Cipher(
            algorithms.AES(key_bytes), _mode_instance(normalized_mode, iv_bytes)
        ).encryptor()
        encrypted = encryptor.update(data) + encryptor.finalize()

    return _encode_bytes(encrypted, output_format), used_iv


def aes_decrypt(ciphertext: str, key: str, key_format: str = "BASE-64",
                mode: str = "GCM", iv: str = "", input_format: str = "BASE-64",
                iv_format: str = "HEX", padding_name: str = "NoPadding",
                output_format: str = "UTF-8") -> str:
    key_bytes = _validate_key(key, key_format)
    normalized_mode = mode.upper()
    if normalized_mode not in ("CBC", "GCM", "CTR", "ECB"):
        raise ValueError("Cipher mode phải là CBC, GCM, CTR hoặc ECB.")
    if normalized_mode == "ECB":
        iv_bytes = b""
    else:
        if not iv.strip():
            raise ValueError("Cần nhập IV để giải mã.")
        iv_bytes = _decode_bytes(iv, iv_format, "IV")

    encrypted = _decode_bytes(ciphertext, input_format, "Ciphertext")
    if normalized_mode == "GCM":
        if padding_name != "NoPadding":
            raise ValueError("AES-GCM chỉ hỗ trợ NoPadding.")
        if len(iv_bytes) != 12:
            raise ValueError("IV của AES-GCM nên dài 12 byte.")
        try:
            plaintext = AESGCM(key_bytes).decrypt(iv_bytes, encrypted, None)
        except InvalidTag as exc:
            raise ValueError("Xác thực GCM thất bại: sai key/IV hoặc ciphertext đã bị thay đổi.") from exc
    else:
        decryptor = Cipher(
            algorithms.AES(key_bytes), _mode_instance(normalized_mode, iv_bytes)
        ).decryptor()
        decrypted = decryptor.update(encrypted) + decryptor.finalize()
        plaintext = _remove_padding(decrypted, normalized_mode, padding_name)

    return _encode_bytes(plaintext, output_format)
