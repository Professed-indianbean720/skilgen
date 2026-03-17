from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from skilgen.agents import fingerprint_project
from skilgen.core.config import load_config
from skilgen.core.context import build_codebase_context
from skilgen.core.requirements import load_project_context
from skilgen.generators.package import project_doc_paths, write_project_docs
from skilgen.generators.skills import planned_skill_paths, write_skills


ProgressCallback = Callable[[str], None]


def _emit(progress_callback: ProgressCallback | None, message: str) -> None:
    if progress_callback is not None:
        progress_callback(message)


def run_delivery(
    requirements_path: str | Path | None = None,
    project_root: str | Path = ".",
    *,
    targets: tuple[str, ...] = ("docs", "skills"),
    domains: tuple[str, ...] = (),
    dry_run: bool = False,
    progress_callback: ProgressCallback | None = None,
) -> list[Path]:
    root = Path(project_root).resolve()
    input_mode = "codebase and requirements" if requirements_path is not None else "codebase only"
    _emit(progress_callback, f"Reading your {input_mode} and loading the Skilgen project configuration.")
    load_config(root)
    _emit(progress_callback, "Building project context so agents can understand the repo structure and delivery scope.")
    context = load_project_context(root, Path(requirements_path).resolve() if requirements_path is not None else None)
    _emit(progress_callback, "Inspecting the codebase to identify frameworks, domains, and implementation patterns.")
    fingerprint_project(root)
    build_codebase_context(root, context)
    generated = []
    if "docs" in targets:
        if dry_run:
            _emit(progress_callback, "Previewing the generated project docs without writing files.")
            generated.extend(project_doc_paths(root))
        else:
            _emit(progress_callback, "Generating project docs so coding agents have clear context, traceability, and operating guidance.")
            generated.extend(write_project_docs(context, root))
    if "skills" in targets:
        if dry_run:
            _emit(progress_callback, "Previewing the skill tree that would be materialized for this repository.")
            generated.extend(planned_skill_paths(context, root / "skills", set(domains)))
        else:
            _emit(progress_callback, "Materializing backend, frontend, requirements, and roadmap skills for coding agents.")
            generated.extend(write_skills(context, root / "skills", set(domains)))
    _emit(progress_callback, f"Finished delivery. Generated or refreshed {len(generated)} files.")
    return generated


def watch_delivery(
    requirements_path: str | Path | None = None,
    project_root: str | Path = ".",
    *,
    targets: tuple[str, ...] = ("docs", "skills"),
    domains: tuple[str, ...] = (),
    interval_seconds: float = 2.0,
    cycles: int = 0,
    once: bool = False,
    progress_callback: ProgressCallback | None = None,
) -> list[list[Path]]:
    root = Path(project_root).resolve()

    def snapshot() -> dict[str, int]:
        tracked: dict[str, int] = {}
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            if relative.startswith((".git/", "skills/", "__pycache__/")):
                continue
            if path.name in {"ANALYSIS.md", "FEATURES.md", "REPORT.md"}:
                continue
            tracked[relative] = path.stat().st_mtime_ns
        return tracked

    results = [
        run_delivery(
            requirements_path,
            root,
            targets=targets,
            domains=domains,
            progress_callback=progress_callback,
        ),
    ]
    if once:
        return results

    previous = snapshot()
    completed_cycles = 0
    while cycles == 0 or completed_cycles < cycles:
        time.sleep(interval_seconds)
        current = snapshot()
        if current != previous:
            _emit(progress_callback, "Detected repository changes. Refreshing the generated docs and skills.")
            results.append(
                run_delivery(
                    requirements_path,
                    root,
                    targets=targets,
                    domains=domains,
                    progress_callback=progress_callback,
                )
            )
            previous = current
        completed_cycles += 1
    return results
