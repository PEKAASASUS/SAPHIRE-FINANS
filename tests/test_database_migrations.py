import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.migrations.migration_manager import (
    current_schema_version,
    run_migrations,
)

EXPECTED_TABLES = {
    "users",
    "app_settings",
    "categories",
    "accounts",
    "cards",
    "transactions",
    "commitments",
    "goals",
    "investments",
    "notifications",
    "schema_migrations",
}


class TestDatabaseMigrations(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def tearDown(self):
        self.conn.close()

    def test_migrations_create_all_expected_tables(self):
        run_migrations(self.conn)
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        table_names = {row[0] for row in cursor.fetchall()}
        self.assertTrue(EXPECTED_TABLES.issubset(table_names))

    def test_schema_version_after_migration(self):
        run_migrations(self.conn)
        self.assertEqual(current_schema_version(self.conn), 1)

    def test_running_migrations_twice_is_idempotent(self):
        first_run = run_migrations(self.conn)
        second_run = run_migrations(self.conn)
        self.assertEqual(first_run, [1])
        self.assertEqual(second_run, [])  # nada pendente na segunda execução

    def test_foreign_keys_are_enforced(self):
        run_migrations(self.conn)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO accounts (user_id, name) VALUES (999, 'Conta Fantasma')"
            )
            self.conn.commit()


if __name__ == "__main__":
    unittest.main()
