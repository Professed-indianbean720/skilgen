from __future__ import annotations

from pathlib import Path

from skilgen.agents.codebase_signals import analyze_codebase
from skilgen.agents.framework_fingerprint import fingerprint_project
from skilgen.core.models import CodebaseContext, DomainRecord, RequirementsContext, SkillTreeNode


def _build_file_tree(project_root: Path) -> list[str]:
    return sorted(
        path.relative_to(project_root).as_posix()
        for path in project_root.rglob("*")
        if path.is_file() and ".git/" not in path.as_posix()
    )


def _domain_records(requirements: RequirementsContext) -> list[DomainRecord]:
    records: list[DomainRecord] = [
        DomainRecord(
            name="requirements",
            confidence=0.99,
            key_files=[requirements.requirements_path.name],
            key_patterns=["requirements-first generation", "skill scaffolding"],
            sub_domains=["planning"],
        )
    ]
    if requirements.domains.get("backend"):
        records.append(
            DomainRecord(
                name="backend",
                confidence=0.8,
                key_files=["skilgen/api/server.py", "skills/backend/SKILL.md"],
                key_patterns=["endpoint quality gate", "service boundaries"],
                sub_domains=["api", "testing"],
            )
        )
    if requirements.domains.get("frontend"):
        records.append(
            DomainRecord(
                name="frontend",
                confidence=0.8,
                key_files=["skills/frontend/SKILL.md"],
                key_patterns=["route-driven structure", "shared components"],
                sub_domains=["components"],
            )
        )
    records.append(
        DomainRecord(
            name="roadmap",
            confidence=0.8,
            key_files=["skills/roadmap/SKILL.md"],
            key_patterns=["phase-based delivery", "plan persistence"],
            sub_domains=["phase-0", "phase-1", "phase-2", "phase-3"],
        )
    )
    return records


def _skill_tree(project_root: Path) -> list[SkillTreeNode]:
    signals = analyze_codebase(project_root)
    backend_children = ["skills/backend/api/SKILL.md", "skills/backend/testing/SKILL.md"]
    if signals.backend_routes:
        backend_children.append("skills/backend/routes/SKILL.md")
    if signals.services:
        backend_children.append("skills/backend/services/SKILL.md")

    frontend_children = ["skills/frontend/components/SKILL.md"]
    if signals.frontend_routes:
        frontend_children.append("skills/frontend/routes/SKILL.md")

    return [
        SkillTreeNode(
            path="skills/requirements/SKILL.md",
            domain="requirements",
            parent_skill=None,
            child_skills=[],
            cross_references=["skills/backend/SKILL.md", "skills/frontend/SKILL.md", "skills/roadmap/SKILL.md"],
        ),
        SkillTreeNode(
            path="skills/backend/SKILL.md",
            domain="backend",
            parent_skill=None,
            child_skills=backend_children,
            cross_references=["skills/requirements/SKILL.md", "skills/roadmap/SKILL.md"],
        ),
        SkillTreeNode(
            path="skills/frontend/SKILL.md",
            domain="frontend",
            parent_skill=None,
            child_skills=frontend_children,
            cross_references=["skills/requirements/SKILL.md", "skills/roadmap/SKILL.md"],
        ),
        SkillTreeNode(
            path="skills/roadmap/SKILL.md",
            domain="roadmap",
            parent_skill=None,
            child_skills=[],
            cross_references=["skills/requirements/SKILL.md"],
        ),
    ]


def build_codebase_context(project_root: Path, requirements: RequirementsContext) -> CodebaseContext:
    return CodebaseContext(
        project_root=project_root.resolve(),
        file_tree=_build_file_tree(project_root.resolve()),
        detected_domains=_domain_records(requirements),
        dependency_map={"skills": ["requirements", "backend", "frontend", "roadmap"]},
        framework_fingerprint=fingerprint_project(project_root.resolve()),
        skill_tree=_skill_tree(project_root.resolve()),
    )
