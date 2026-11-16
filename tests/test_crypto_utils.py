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

    def test_aes_gcm_round_trip_and_authentication(self):
        key = generate_aes_key(256, "Base64")
        iv = generate_iv("GCM", "Hex")
        encrypted, used_iv = aes_encrypt("FileForge ✓", key, mode="GCM", iv=iv)
        self.assertEqual(used_iv, iv)
        self.assertEqual(aes_decrypt(encrypted, key, mode="GCM", iv=iv), "FileForge ✓")

        raw = bytearray(base64.b64decode(encrypted))
        raw[0] ^= 1
        tampered = base64.b64encode(raw).decode("ascii")
        with self.assertRaises(Exception):
            aes_decrypt(tampered, key, mode="GCM", iv=iv)

    def test_aes_cbc_round_trip(self):
        key = generate_aes_key(256, "Base64")
        iv = generate_iv("CBC", "Hex")
        encrypted, _ = aes_encrypt("CBC compatibility", key, mode="CBC", iv=iv)
        self.assertEqual(aes_decrypt(encrypted, key, mode="CBC", iv=iv), "CBC compatibility")


if __name__ == "__main__":
    unittest.main()
