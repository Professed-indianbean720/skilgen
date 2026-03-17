from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from skilgen.core.requirements import load_requirements


class RequirementsTests(unittest.TestCase):
    def test_markdown_requirements_detect_domains(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "requirements.md"
            path.write_text("Backend API endpoints\nFrontend React components\n", encoding="utf-8")
            context = load_requirements(path)
            self.assertTrue(context.domains["backend"])
            self.assertTrue(context.domains["frontend"])
            self.assertTrue(context.summary)


if __name__ == "__main__":
    unittest.main()
