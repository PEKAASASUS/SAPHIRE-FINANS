import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.security.crypto_utils import (
    b64_to_bytes,
    bytes_to_b64,
    decrypt_data,
    derive_fernet_key_from_password,
    derive_key,
    encrypt_data,
    generate_salt,
)


class TestCryptoUtils(unittest.TestCase):
    def test_generate_salt_is_random(self):
        s1 = generate_salt()
        s2 = generate_salt()
        self.assertNotEqual(s1, s2)

    def test_generate_salt_has_correct_length(self):
        self.assertEqual(len(generate_salt(16)), 16)

    def test_derive_key_is_deterministic(self):
        salt = generate_salt()
        k1 = derive_key("senha", salt, iterations=1000)
        k2 = derive_key("senha", salt, iterations=1000)
        self.assertEqual(k1, k2)

    def test_different_passwords_produce_different_keys(self):
        salt = generate_salt()
        k1 = derive_key("senhaA", salt, iterations=1000)
        k2 = derive_key("senhaB", salt, iterations=1000)
        self.assertNotEqual(k1, k2)

    def test_different_salts_produce_different_keys(self):
        k1 = derive_key("senha", generate_salt(), iterations=1000)
        k2 = derive_key("senha", generate_salt(), iterations=1000)
        self.assertNotEqual(k1, k2)

    def test_b64_roundtrip(self):
        data = b"\x00\xFF\xAB\xCD"
        self.assertEqual(b64_to_bytes(bytes_to_b64(data)), data)

    def test_fernet_encrypt_decrypt_roundtrip(self):
        salt = generate_salt()
        key = derive_fernet_key_from_password("senha-super-secreta", salt, iterations=1000)
        original = b"Dado financeiro sensivel"
        encrypted = encrypt_data(original, key)
        self.assertNotEqual(encrypted, original)
        decrypted = decrypt_data(encrypted, key)
        self.assertEqual(decrypted, original)

    def test_wrong_key_cannot_decrypt(self):
        from cryptography.fernet import InvalidToken

        salt = generate_salt()
        key_correct = derive_fernet_key_from_password("correta", salt, iterations=1000)
        key_wrong = derive_fernet_key_from_password("errada", salt, iterations=1000)

        encrypted = encrypt_data(b"segredo", key_correct)
        with self.assertRaises((InvalidToken, Exception)):
            decrypt_data(encrypted, key_wrong)


if __name__ == "__main__":
    unittest.main()
