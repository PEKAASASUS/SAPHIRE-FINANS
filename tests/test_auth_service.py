import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.migrations.migration_manager import run_migrations
from app.security import auth_service


class TestAuthService(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        run_migrations(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_needs_setup_when_no_user_exists(self):
        self.assertTrue(auth_service.needs_master_password_setup(self.conn))

    def test_setup_creates_user_and_reports_success(self):
        result = auth_service.setup_master_password(self.conn, "senha@123", "senha@123")
        self.assertTrue(result.success)
        self.assertIsNotNone(result.user)

    def test_setup_fails_if_passwords_dont_match(self):
        result = auth_service.setup_master_password(self.conn, "senha@123", "diferente")
        self.assertFalse(result.success)
        self.assertIn("coincidem", result.error_message or "")

    def test_setup_fails_if_password_too_short(self):
        result = auth_service.setup_master_password(self.conn, "abc", "abc")
        self.assertFalse(result.success)

    def test_setup_cannot_be_done_twice(self):
        auth_service.setup_master_password(self.conn, "senha@123", "senha@123")
        result = auth_service.setup_master_password(self.conn, "nova@456", "nova@456")
        self.assertFalse(result.success)

    def test_login_with_correct_password_succeeds(self):
        auth_service.setup_master_password(self.conn, "senha@123", "senha@123")
        result = auth_service.login(self.conn, "senha@123")
        self.assertTrue(result.success)
        self.assertIsNotNone(result.user)

    def test_login_with_wrong_password_fails(self):
        auth_service.setup_master_password(self.conn, "senha@123", "senha@123")
        result = auth_service.login(self.conn, "senhaErrada")
        self.assertFalse(result.success)

    def test_change_password_requires_correct_current_password(self):
        auth_service.setup_master_password(self.conn, "senha@123", "senha@123")
        user = auth_service.login(self.conn, "senha@123").user
        result = auth_service.change_master_password(
            self.conn, user, "errada", "nova@456", "nova@456"
        )
        self.assertFalse(result.success)

    def test_change_password_works_correctly(self):
        auth_service.setup_master_password(self.conn, "senha@123", "senha@123")
        user = auth_service.login(self.conn, "senha@123").user
        result = auth_service.change_master_password(
            self.conn, user, "senha@123", "novaSenha@456", "novaSenha@456"
        )
        self.assertTrue(result.success)
        # Senha antiga não deve mais funcionar
        self.assertFalse(auth_service.login(self.conn, "senha@123").success)
        # Senha nova deve funcionar
        self.assertTrue(auth_service.login(self.conn, "novaSenha@456").success)


if __name__ == "__main__":
    unittest.main()
