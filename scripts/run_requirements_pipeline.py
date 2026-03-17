#!/usr/bin/env python3
"""Compatibility wrapper for the requirements-driven Skilgen delivery pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skilgen.delivery import run_delivery


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate docs and skills from a requirements document.")
    parser.add_argument("--requirements", required=True, help="Path to the requirements source.")
    parser.add_argument("--output", default="skills", help="Retained for compatibility; the project root receives the generated files.")
    parser.add_argument("--project-root", default=".", help="Project root where docs, package files, and skills should be written.")
    args = parser.parse_args()

    generated = run_delivery(Path(args.requirements), Path(args.project_root))
    print(
        json.dumps(
            {
                "project_root": str(Path(args.project_root).resolve()),
                "compat_output_arg": args.output,
                "generated_files": [str(path) for path in generated],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
