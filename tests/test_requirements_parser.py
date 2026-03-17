from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from skilgen.agents.requirements_parser import parse_requirements_file


class RequirementsParserTests(unittest.TestCase):
    def test_parse_requirements_file_extracts_project_intent(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "requirements.md"
            path.write_text(
                "\n".join(
                    [
                        "Feature: Auto-update engine",
                        "Backend API endpoint for skills scan",
                        "Frontend dashboard flow for skill tracking",
                        "Entity: SkillVersion",
                        "Domain: backend",
                    ]
                ),
                encoding="utf-8",
            )
            intent = parse_requirements_file(path)
            self.assertTrue(intent.features)
            self.assertTrue(intent.endpoints)
            self.assertTrue(intent.ui_flows)
            self.assertTrue(intent.entities)


if __name__ == "__main__":
    unittest.main()
