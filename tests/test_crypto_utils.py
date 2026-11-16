import pytest

from fileforge.crypto_utils import (
    aes_decrypt, aes_encrypt, generate_aes_key, generate_iv, url_decode, url_encode,
)


@pytest.mark.parametrize("component", [False, True])
def test_url_round_trip(component):
    value = "https://example.com/a path?q=hello world&x=✓"
    assert url_decode(url_encode(value, component=component)) == value


def test_url_decode_keeps_plus():
    assert url_decode("a+b%20c") == "a+b c"


@pytest.mark.parametrize("mode", ["GCM", "CBC"])
def test_aes_round_trip(mode):
    key = generate_aes_key(256, "Base64")
    iv = generate_iv(mode, "Hex")
    encrypted, used_iv = aes_encrypt("FileForge ✓", key, mode=mode, iv=iv)
    assert used_iv == iv
    assert aes_decrypt(encrypted, key, mode=mode, iv=iv) == "FileForge ✓"


def test_gcm_rejects_tampered_ciphertext():
    key = generate_aes_key()
    iv = generate_iv()
    encrypted, _ = aes_encrypt("secret", key, iv=iv)
    raw = bytearray(__import__("base64").b64decode(encrypted))
    raw[0] ^= 1
    tampered = __import__("base64").b64encode(raw).decode()
    with pytest.raises(Exception):
        aes_decrypt(tampered, key, iv=iv)
