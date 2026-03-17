from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from skilgen.delivery import run_delivery


class DeliveryTests(unittest.TestCase):
    def test_run_delivery_works_with_requirements_only(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            requirements = root / "requirements.md"
            requirements.write_text("Backend endpoints\nFrontend routes\nRoadmap phases\n", encoding="utf-8")

            generated = run_delivery(requirements, root)

            self.assertTrue((root / "ANALYSIS.md").exists())
            self.assertTrue((root / "FEATURES.md").exists())
            self.assertTrue((root / "skills" / "MANIFEST.md").exists())
            self.assertTrue((root / "skills" / "requirements" / "SKILL.md").exists())
            self.assertTrue((root / "skills" / "roadmap" / "SKILL.md").exists())
            self.assertGreaterEqual(len(generated), 4)

    def test_run_delivery_generates_docs_and_skills(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            requirements = root / "requirements.md"
            (root / "api" / "routes").mkdir(parents=True)
            (root / "api" / "routes" / "users.py").write_text("def handler():\n    return {}\n", encoding="utf-8")
            (root / "services").mkdir(parents=True)
            (root / "services" / "users_service.py").write_text("def run():\n    return True\n", encoding="utf-8")
            (root / "src" / "routes").mkdir(parents=True)
            (root / "src" / "routes" / "dashboard.tsx").write_text("export default function Dashboard() { return null; }\n", encoding="utf-8")
            (root / "src" / "components").mkdir(parents=True)
            (root / "src" / "components" / "SkillCard.tsx").write_text("export function SkillCard() { return null; }\n", encoding="utf-8")
            requirements.write_text("Backend endpoints\nFrontend routes\n", encoding="utf-8")

            generated = run_delivery(requirements, root)

            self.assertTrue((root / "ANALYSIS.md").exists())
            self.assertTrue((root / "FEATURES.md").exists())
            self.assertTrue((root / "REPORT.md").exists())
            self.assertTrue((root / "TRACEABILITY.md").exists())
            self.assertTrue((root / "skills" / "MANIFEST.md").exists())
            self.assertTrue((root / "skills" / "GRAPH.md").exists())
            self.assertTrue((root / "skills" / "backend" / "SKILL.md").exists())
            self.assertTrue((root / "skills" / "backend" / "routes" / "SKILL.md").exists())
            self.assertTrue((root / "skills" / "backend" / "services" / "SKILL.md").exists())
            self.assertTrue((root / "skills" / "backend" / "SUMMARY.md").exists())
            self.assertTrue((root / "skills" / "frontend" / "SKILL.md").exists())
            self.assertTrue((root / "skills" / "frontend" / "routes" / "SKILL.md").exists())
            self.assertTrue((root / "skills" / "frontend" / "SUMMARY.md").exists())
            self.assertTrue((root / "skills" / "frontend" / "components" / "SUMMARY.md").exists())
            self.assertGreaterEqual(len(generated), 4)

    def test_run_delivery_can_limit_to_backend_skills(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            requirements = root / "requirements.md"
            (root / "api" / "routes").mkdir(parents=True)
            (root / "api" / "routes" / "users.py").write_text("def handler():\n    return {}\n", encoding="utf-8")
            (root / "src" / "routes").mkdir(parents=True)
            (root / "src" / "routes" / "dashboard.tsx").write_text("export default function Dashboard() { return null; }\n", encoding="utf-8")
            requirements.write_text("Backend endpoints\nFrontend routes\n", encoding="utf-8")

            run_delivery(requirements, root, targets=("skills",), domains=("backend",))

            self.assertTrue((root / "skills" / "backend" / "SKILL.md").exists())
            self.assertFalse((root / "skills" / "frontend" / "SKILL.md").exists())
            self.assertFalse((root / "ANALYSIS.md").exists())

    def test_run_delivery_works_with_codebase_only(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "api" / "routes").mkdir(parents=True)
            (root / "api" / "routes" / "users.py").write_text("def handler():\n    return {}\n", encoding="utf-8")
            (root / "services").mkdir(parents=True)
            (root / "services" / "users_service.py").write_text("def run():\n    return True\n", encoding="utf-8")
            (root / "src" / "components").mkdir(parents=True)
            (root / "src" / "components" / "SkillCard.tsx").write_text("export function SkillCard() { return null; }\n", encoding="utf-8")

            generated = run_delivery(None, root)

            self.assertTrue((root / "ANALYSIS.md").exists())
            self.assertTrue((root / "FEATURES.md").exists())
            self.assertTrue((root / "skills" / "MANIFEST.md").exists())
            self.assertTrue((root / "skills" / "backend" / "SKILL.md").exists())
            self.assertGreaterEqual(len(generated), 4)


if __name__ == "__main__":
    unittest.main()
