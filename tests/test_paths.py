import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import paths


class TestPaths(unittest.TestCase):
    def test_base_dir_is_project_root(self):
        # main.py deve existir dentro de BASE_DIR quando rodando via código-fonte.
        self.assertTrue((paths.BASE_DIR / "main.py").exists())

    def test_ensure_runtime_directories_creates_expected_folders(self):
        paths.ensure_runtime_directories()
        self.assertTrue(paths.DATA_DIR.exists())
        self.assertTrue(paths.CONFIG_DIR.exists())
        self.assertTrue(paths.LOGS_DIR.exists())

    def test_all_runtime_paths_are_inside_base_dir(self):
        paths.ensure_runtime_directories()
        self.assertTrue(paths.is_portable_safe())

    def test_database_file_is_inside_data_dir(self):
        self.assertEqual(paths.DATABASE_FILE.parent, paths.DATA_DIR)


if __name__ == "__main__":
    unittest.main()
