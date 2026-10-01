import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.security.password_manager import (
    hash_password,
    is_password_strong_enough,
    verify_password,
)


class TestPasswordManager(unittest.TestCase):
    def test_correct_password_verifies(self):
        hashed = hash_password("senha-super-secreta", iterations=1000)
        self.assertTrue(verify_password("senha-super-secreta", hashed))

    def test_wrong_password_fails(self):
        hashed = hash_password("senha-super-secreta", iterations=1000)
        self.assertFalse(verify_password("senha-errada", hashed))

    def test_hash_never_equals_plaintext_password(self):
        hashed = hash_password("minha-senha-123", iterations=1000)
        self.assertNotEqual(hashed.hash_b64, "minha-senha-123")

    def test_two_hashes_of_same_password_use_different_salts(self):
        first = hash_password("mesma-senha", iterations=1000)
        second = hash_password("mesma-senha", iterations=1000)
        self.assertNotEqual(first.salt_b64, second.salt_b64)
        self.assertNotEqual(first.hash_b64, second.hash_b64)

    def test_password_strength_check(self):
        self.assertFalse(is_password_strong_enough("1234", minimum_length=8))
        self.assertTrue(is_password_strong_enough("12345678", minimum_length=8))

    def test_unsupported_algorithm_raises(self):
        hashed = hash_password("qualquer-senha", iterations=1000)
        tampered = hashed.__class__(
            algorithm="md5",
            salt_b64=hashed.salt_b64,
            hash_b64=hashed.hash_b64,
            iterations=hashed.iterations,
        )
        with self.assertRaises(ValueError):
            verify_password("qualquer-senha", tampered)


if __name__ == "__main__":
    unittest.main()
