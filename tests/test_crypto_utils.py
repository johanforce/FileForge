import base64
import unittest

from fileforge.crypto_utils import (
    aes_decrypt, aes_encrypt, generate_aes_key, generate_iv, url_decode, url_encode,
)


class CryptoUtilsTests(unittest.TestCase):
    def test_url_round_trip(self):
        value = "https://example.com/a path?q=hello world&x=✓"
        for component in (False, True):
            with self.subTest(component=component):
                self.assertEqual(url_decode(url_encode(value, component)), value)

    def test_url_decode_keeps_plus(self):
        self.assertEqual(url_decode("a+b%20c"), "a+b c")

    def test_aes_modes_round_trip(self):
        cases = [
            ("CBC", "PKCS5Padding", "CBC compatibility"),
            ("GCM", "NoPadding", "FileForge ✓"),
            ("CTR", "NoPadding", "CTR stream mode"),
            ("ECB", "PKCS5Padding", "ECB legacy"),
        ]
        for mode, padding_name, plaintext in cases:
            with self.subTest(mode=mode):
                key = generate_aes_key(256, "BASE-64")
                iv = "" if mode == "ECB" else generate_iv(mode, "HEX")
                encrypted, used_iv = aes_encrypt(
                    plaintext, key, "BASE-64", mode, iv, "Base64", "HEX", padding_name
                )
                self.assertEqual(used_iv, iv)
                decrypted = aes_decrypt(
                    encrypted, key, "BASE-64", mode, used_iv, "Base64", "HEX",
                    padding_name, "UTF-8",
                )
                self.assertEqual(decrypted, plaintext)

    def test_aes_key_and_iv_formats(self):
        for key_format in ("UTF-8", "HEX", "BASE-64"):
            with self.subTest(key_format=key_format):
                key = generate_aes_key(128, key_format)
                iv = generate_iv("CBC", key_format)
                encrypted, _ = aes_encrypt(
                    "format test", key, key_format, "CBC", iv, "Hex", key_format,
                    "PKCS5Padding",
                )
                decoded = aes_decrypt(
                    encrypted, key, key_format, "CBC", iv, "Hex", key_format,
                    "PKCS5Padding", "BASE-64",
                )
                self.assertEqual(base64.b64decode(decoded), b"format test")

    def test_aes_gcm_authentication_rejects_tampering(self):
        key = generate_aes_key(256, "BASE-64")
        iv = generate_iv("GCM", "HEX")
        encrypted, _ = aes_encrypt("secret", key, mode="GCM", iv=iv, iv_format="HEX")
        raw = bytearray(base64.b64decode(encrypted))
        raw[0] ^= 1
        tampered = base64.b64encode(raw).decode("ascii")
        with self.assertRaisesRegex(ValueError, "Xác thực GCM thất bại"):
            aes_decrypt(tampered, key, mode="GCM", iv=iv)

    def test_block_modes_no_padding_require_full_blocks(self):
        key = generate_aes_key(128, "BASE-64")
        iv = generate_iv("CBC", "HEX")
        with self.assertRaisesRegex(ValueError, "bội số 16 byte"):
            aes_encrypt("short", key, mode="CBC", iv=iv, padding_name="NoPadding")

    def test_gcm_and_ctr_reject_pkcs5_padding(self):
        key = generate_aes_key(128, "BASE-64")
        for mode in ("GCM", "CTR"):
            with self.subTest(mode=mode):
                iv = generate_iv(mode, "HEX")
                with self.assertRaisesRegex(ValueError, "chỉ hỗ trợ NoPadding"):
                    aes_encrypt("data", key, mode=mode, iv=iv, padding_name="PKCS5Padding")


if __name__ == "__main__":
    unittest.main()
