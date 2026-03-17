from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from skilgen.agents.framework_fingerprint import fingerprint_project


class FrameworkFingerprintTests(unittest.TestCase):
    def test_detects_python_repo_signals(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
            (root / "main.py").write_text("import fastapi\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "test_app.py").write_text("import unittest\n", encoding="utf-8")
            result = fingerprint_project(root)
            self.assertIsNotNone(result.backend)
            self.assertEqual(result.backend.name, "fastapi")
            self.assertIsNotNone(result.test_framework)


if __name__ == "__main__":
    unittest.main()
