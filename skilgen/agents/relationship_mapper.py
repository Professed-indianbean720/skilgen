from __future__ import annotations

import ast
import warnings
from pathlib import Path


def build_import_graph(project_root: Path) -> dict[str, list[str]]:
    root = project_root.resolve()
    graph: dict[str, list[str]] = {}
    for path in root.rglob("*.py"):
        if ".git/" in path.as_posix() or "__pycache__" in path.as_posix():
            continue
        rel = path.relative_to(root).as_posix()
        imports: list[str] = []
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            graph[rel] = imports
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        graph[rel] = sorted(set(imports))
    return graph
