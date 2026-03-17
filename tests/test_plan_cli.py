import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


class PlanCliTests(unittest.TestCase):
    def test_plan_command_outputs_steps(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            requirements = root / "requirements.md"
            requirements.write_text(
                "\n".join(
                    [
                        "Feature: Skill generation",
                        "Backend API endpoint for project analysis",
                        "Frontend dashboard flow for repository review",
                    ]
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "skilgen.cli.main",
                    "plan",
                    "--requirements",
                    str(requirements),
                    "--project-root",
                    str(root),
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertIn("model", payload)
            self.assertTrue(payload["steps"])


if __name__ == "__main__":
    unittest.main()
