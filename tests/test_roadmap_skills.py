from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from skilgen.core.requirements import load_requirements
from skilgen.generators.skills import write_skills


class RoadmapSkillsTests(unittest.TestCase):
    def test_write_skills_generates_roadmap_tree(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            requirements = root / "requirements.md"
            requirements.write_text("Backend endpoint\nFrontend flow\n", encoding="utf-8")
            context = load_requirements(requirements)
            write_skills(context, root / "skills")
            self.assertTrue((root / "skills" / "roadmap" / "SKILL.md").exists())
            self.assertTrue((root / "skills" / "roadmap" / "phase-0" / "SKILL.md").exists())
            self.assertTrue((root / "skills" / "GRAPH.md").exists())
            manifest = (root / "skills" / "MANIFEST.md").read_text(encoding="utf-8")
            self.assertIn("roadmap/SKILL.md", manifest)
            skill_text = (root / "skills" / "roadmap" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("## Traceability", skill_text)


if __name__ == "__main__":
    unittest.main()
