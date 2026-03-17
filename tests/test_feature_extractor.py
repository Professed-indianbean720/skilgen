from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from skilgen.agents.feature_extractor import extract_features


class FeatureExtractorTests(unittest.TestCase):
    def test_extract_features_returns_inventory(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            requirements = root / "requirements.md"
            (root / "api" / "routes").mkdir(parents=True)
            (root / "api" / "routes" / "scan.py").write_text("def handler():\n    return {}\n", encoding="utf-8")
            (root / "src" / "components").mkdir(parents=True)
            (root / "src" / "components" / "Dashboard.tsx").write_text("export function Dashboard() { return null; }\n", encoding="utf-8")
            requirements.write_text(
                "\n".join(
                    [
                        "Feature: Auto-update engine",
                        "Backend API endpoint for scan",
                        "Frontend dashboard flow for skill tracking",
                    ]
                ),
                encoding="utf-8",
            )
            features = extract_features(requirements, root)
            self.assertTrue(features)
            domains = {feature.domain for feature in features}
            self.assertIn("requirements", domains)
            self.assertIn("backend", domains)
            self.assertIn("frontend", domains)
            names = {feature.name for feature in features}
            self.assertIn("Backend route: api/routes/scan.py", names)
            self.assertIn("Component: src/components/Dashboard.tsx", names)


if __name__ == "__main__":
    unittest.main()
