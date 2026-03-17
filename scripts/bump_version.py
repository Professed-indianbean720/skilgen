#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


def replace_version(path: Path, pattern: str, version: str) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, lambda match: f"{match.group(1)}{version}{match.group(3)}", text)
    if count != 1:
        raise SystemExit(f"Could not update version in {path}")
    path.write_text(updated, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bump Skilgen package version in tracked release files.")
    parser.add_argument("version", help="New version, for example 0.1.1")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    replace_version(root / "pyproject.toml", r'(version = ")([^"]+)(")', args.version)
    replace_version(root / "skilgen" / "__init__.py", r'(__version__ = ")([^"]+)(")', args.version)
    print(args.version)


if __name__ == "__main__":
    main()
