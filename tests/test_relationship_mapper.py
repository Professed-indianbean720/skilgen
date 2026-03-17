from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from skilgen.agents.relationship_mapper import build_import_graph


class RelationshipMapperTests(unittest.TestCase):
    def test_build_import_graph_collects_python_imports(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("import json\nfrom pathlib import Path\n", encoding="utf-8")
            graph = build_import_graph(root)
            self.assertIn("app.py", graph)
            self.assertIn("json", graph["app.py"])
            self.assertIn("pathlib", graph["app.py"])


if __name__ == "__main__":
    unittest.main()
