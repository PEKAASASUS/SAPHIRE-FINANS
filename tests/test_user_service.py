import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.migrations.migration_manager import run_migrations
from app.security.password_manager import hash_password
from app.services import user_service


class TestUserService(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        run_migrations(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_has_user_returns_false_on_empty_db(self):
        self.assertFalse(user_service.has_user(self.conn))

    def test_create_user_persists_and_returns_user(self):
        ph = hash_password("minha-senha", iterations=1000)
        user = user_service.create_user(self.conn, "Maria", ph)
        self.assertEqual(user.name, "Maria")
        self.assertEqual(user.password_algorithm, "pbkdf2_sha256")
        # Senha nunca é armazenada em texto puro
        self.assertNotEqual(user.password_hash, "minha-senha")

    def test_has_user_returns_true_after_creation(self):
        ph = hash_password("minha-senha", iterations=1000)
        user_service.create_user(self.conn, "João", ph)
        self.assertTrue(user_service.has_user(self.conn))

    def test_get_primary_user_returns_none_when_empty(self):
        self.assertIsNone(user_service.get_primary_user(self.conn))

    def test_get_primary_user_returns_first_user(self):
        ph = hash_password("senha123", iterations=1000)
        user_service.create_user(self.conn, "Primeiro", ph)
        found = user_service.get_primary_user(self.conn)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Primeiro")

    def test_update_password_changes_hash(self):
        ph_old = hash_password("senha-velha", iterations=1000)
        user = user_service.create_user(self.conn, "Teste", ph_old)
        old_hash = user.password_hash

        ph_new = hash_password("senha-nova", iterations=1000)
        user_service.update_password(self.conn, user.id, ph_new)

        updated = user_service.get_primary_user(self.conn)
        self.assertNotEqual(updated.password_hash, old_hash)


if __name__ == "__main__":
    unittest.main()
