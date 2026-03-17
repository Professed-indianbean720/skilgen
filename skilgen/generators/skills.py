from __future__ import annotations

from datetime import date
from pathlib import Path

from skilgen.agents.codebase_signals import analyze_codebase
from skilgen.agents.requirements_parser import parse_project_intent
from skilgen.agents.roadmap_planner import build_roadmap_plan
from skilgen.deep_agents_core import run_deep_text
from skilgen.core.config import load_config
from skilgen.core.models import CodebaseSignals, RequirementsContext, SkillSpec


TODAY = date.today().isoformat()


def _signal_bullets(items: list[str], fallback: str, limit: int = 5) -> list[str]:
    if not items:
        return [fallback]
    bullets = [f"Detected: `{item}`" for item in items[:limit]]
    if len(items) > limit:
        bullets.append(f"Detected {len(items) - limit} more matching files elsewhere in the repo.")
    return bullets


def build_skill_specs(domains: dict[str, bool], output_dir: Path, requirements_path: Path | None) -> list[SkillSpec]:
    project_root = output_dir.parent
    signals = analyze_codebase(project_root)
    specs = [
        SkillSpec(
            path="requirements/SKILL.md",
            name="requirements",
            domain="requirements",
            sub_domain="planning",
            overview="Start here when the repo is being shaped from a PRD, spec, or feature brief.",
            checks=["{{project_root}}/docs/", "{{project_root}}/skills/", "{{project_root}}/scripts/", "{{requirements_path}}"],
            patterns=[
                (
                    "Requirements-first generation",
                    [
                        "Extract domains, endpoints, flows, and constraints before creating implementation guidance.",
                        "Keep the skill tree aligned to the product intent, then refine it as real code appears.",
                    ],
                ),
                (
                    "Dynamic pathing",
                    [
                        "Use `{{project_root}}` and `{{skill_dir}}` placeholders instead of machine-specific paths.",
                        "Keep references relative to the current `SKILL.md` file.",
                    ],
                ),
            ],
            how_to=[
                "Read the latest requirements source.",
                "List major implementation domains.",
                "Create or update parent and child skills.",
                "Refresh the manifest so agents can discover the tree.",
            ],
            references=["../backend/SKILL.md", "../frontend/SKILL.md", "../roadmap/SKILL.md"],
        )
    ]

    if domains.get("backend"):
        specs.extend(
            [
                SkillSpec(
                    path="backend/SKILL.md",
                    name="backend",
                    domain="backend",
                    sub_domain="platform",
                    overview="Parent skill for server-side work, with an emphasis on scalable service boundaries.",
                    checks=["{{project_root}}/backend/", "{{project_root}}/server/", "{{project_root}}/api/"],
                    patterns=[
                        (
                            "Scalable backend structure",
                            [
                                "Keep handlers thin and push business logic into services or use-case modules.",
                                "Separate transport, domain logic, and persistence so growth stays manageable.",
                            ],
                        ),
                        (
                            "Endpoint quality gate",
                            [
                                "Every new backend feature must test all affected endpoints.",
                                "Cover success and failure paths for each touched route.",
                            ],
                        ),
                    ],
                    how_to=[
                        "Confirm the feature in the requirements skill.",
                        "Identify endpoints, services, data changes, and integrations.",
                        "Implement the smallest backend slice that satisfies the requirement.",
                        "Add endpoint coverage before marking the feature complete.",
                    ],
                    references=[
                        "../requirements/SKILL.md",
                        "./api/SKILL.md",
                        "./testing/SKILL.md",
                        *(["./routes/SKILL.md"] if signals.backend_routes else []),
                        *(["./services/SKILL.md"] if signals.services else []),
                        "../roadmap/SKILL.md",
                    ],
                ),
                SkillSpec(
                    path="backend/api/SKILL.md",
                    name="backend-api",
                    domain="backend",
                    sub_domain="api",
                    overview="Focused guidance for defining or changing API endpoints.",
                    checks=["{{project_root}}/backend/api/", "{{project_root}}/server/routes/", "{{project_root}}/tests/"],
                    patterns=[
                        (
                            "Endpoint lifecycle",
                            [
                                "Define the request contract, validate inputs, delegate to services, and map stable responses.",
                                "Keep endpoint behavior easy to test and document.",
                            ],
                        )
                    ],
                    how_to=[
                        "List all endpoints created or changed by the feature.",
                        "Define request and response contracts.",
                        "Implement the route or controller layer.",
                        "Add tests for every impacted endpoint.",
                    ],
                    references=[
                        "../SKILL.md",
                        "../testing/SKILL.md",
                        *(["../routes/SKILL.md"] if signals.backend_routes else []),
                        *(["../services/SKILL.md"] if signals.services else []),
                        "../../requirements/SKILL.md",
                    ],
                ),
                SkillSpec(
                    path="backend/testing/SKILL.md",
                    name="backend-testing",
                    domain="backend",
                    sub_domain="testing",
                    overview="Verification rules for backend work, especially endpoint coverage.",
                    checks=["{{project_root}}/tests/", "{{project_root}}/backend/tests/", "{{project_root}}/server/tests/"],
                    patterns=[
                        (
                            "Endpoint-first verification",
                            [
                                "Build a checklist from changed routes, not only changed files.",
                                "Test happy paths and failure modes for each impacted endpoint.",
                            ],
                        )
                    ],
                    how_to=[
                        "Enumerate every endpoint touched by the feature.",
                        "Add or update tests for success and failure cases.",
                        "Run the relevant test suite before closing the work.",
                    ],
                    references=[
                        "../SKILL.md",
                        "../api/SKILL.md",
                        *(["../routes/SKILL.md"] if signals.backend_routes else []),
                        *(["../services/SKILL.md"] if signals.services else []),
                    ],
                ),
            ]
        )
        if signals.backend_routes:
            specs.append(
                SkillSpec(
                    path="backend/routes/SKILL.md",
                    name="backend-routes",
                    domain="backend",
                    sub_domain="routes",
                    overview="Code-aware guidance for backend routes and handlers already present in the scanned project.",
                    checks=["{{project_root}}/backend/", "{{project_root}}/server/", "{{project_root}}/api/"],
                    patterns=[
                        ("Detected route files", _signal_bullets(signals.backend_routes, "No backend route files were detected.")),
                        (
                            "Route extension pattern",
                            [
                                "Extend the closest existing route or controller area before creating a new top-level folder.",
                                "Keep request parsing at the edge and move business logic into services.",
                            ],
                        ),
                    ],
                    how_to=[
                        "Start with the closest existing route file from the detected list.",
                        "Trace the handler to the service or use-case layer before making changes.",
                        "Add endpoint tests for every touched success and failure path.",
                    ],
                    references=[
                        "../SKILL.md",
                        "../api/SKILL.md",
                        "../testing/SKILL.md",
                        *(["../services/SKILL.md"] if signals.services else []),
                        "../../requirements/SKILL.md",
                    ],
                )
            )
        if signals.services:
            specs.append(
                SkillSpec(
                    path="backend/services/SKILL.md",
                    name="backend-services",
                    domain="backend",
                    sub_domain="services",
                    overview="Code-aware guidance for service and use-case modules already present in the scanned project.",
                    checks=["{{project_root}}/backend/services/", "{{project_root}}/services/", "{{project_root}}/src/services/"],
                    patterns=[
                        ("Detected service files", _signal_bullets(signals.services, "No service files were detected.")),
                        (
                            "Service boundary pattern",
                            [
                                "Keep orchestration, validation, and transport concerns separate from business logic.",
                                "Extend the nearest existing service module before creating another service namespace.",
                            ],
                        ),
                    ],
                    how_to=[
                        "Start from the closest service file in the detected list.",
                        "Reuse the current service naming and return-shape conventions.",
                        "Add endpoint or unit coverage for the service path you change.",
                    ],
                    references=[
                        "../SKILL.md",
                        "../api/SKILL.md",
                        "../testing/SKILL.md",
                        *(["../routes/SKILL.md"] if signals.backend_routes else []),
                        "../../requirements/SKILL.md",
                    ],
                )
            )

    if domains.get("frontend"):
        specs.extend(
            [
                SkillSpec(
                    path="frontend/SKILL.md",
                    name="frontend",
                    domain="frontend",
                    sub_domain="platform",
                    overview="Parent skill for user-facing work, routes, flows, and scalable UI structure.",
                    checks=["{{project_root}}/frontend/", "{{project_root}}/web/", "{{project_root}}/src/"],
                    patterns=[
                        (
                            "Scalable frontend structure",
                            [
                                "Group UI by feature or route domain once the app grows.",
                                "Keep shared components distinct from route-specific composition.",
                            ],
                        ),
                        ("Requirements traceability", ["Map screens and flows back to the requirements skill before implementation."]),
                    ],
                    how_to=[
                        "Start from the relevant requirement or user flow.",
                        "Identify the route, page, components, and data dependencies.",
                        "Update child skills when a reusable UI pattern appears.",
                    ],
                    references=[
                        "../requirements/SKILL.md",
                        "./components/SKILL.md",
                        *(["./routes/SKILL.md"] if signals.frontend_routes else []),
                        "../roadmap/SKILL.md",
                    ],
                ),
                SkillSpec(
                    path="frontend/components/SKILL.md",
                    name="frontend-components",
                    domain="frontend",
                    sub_domain="components",
                    overview="Guidance for reusable components and UI composition.",
                    checks=[
                        "{{project_root}}/frontend/components/",
                        "{{project_root}}/src/components/",
                        "{{project_root}}/app/components/",
                    ],
                    patterns=[
                        (
                            "Dynamic location awareness",
                            [
                                "Resolve the nearest existing component folder before creating a new one.",
                                "Avoid hard-coded paths copied from another repo.",
                            ],
                        ),
                        ("Detected component files", _signal_bullets(signals.components, "No reusable component files were detected.")),
                    ],
                    how_to=[
                        "Find the nearest existing feature or shared component folder.",
                        "Match naming and export conventions for that area.",
                        "Add tests or story coverage if the project uses them.",
                    ],
                    references=[
                        "../SKILL.md",
                        *(["../routes/SKILL.md"] if signals.frontend_routes else []),
                        "../../requirements/SKILL.md",
                    ],
                ),
            ]
        )
        if signals.frontend_routes:
            specs.append(
                SkillSpec(
                    path="frontend/routes/SKILL.md",
                    name="frontend-routes",
                    domain="frontend",
                    sub_domain="routes",
                    overview="Code-aware guidance for pages, screens, and route modules already present in the scanned project.",
                    checks=["{{project_root}}/frontend/", "{{project_root}}/src/", "{{project_root}}/app/"],
                    patterns=[
                        ("Detected route files", _signal_bullets(signals.frontend_routes, "No frontend route files were detected.")),
                        (
                            "Route composition",
                            [
                                "Prefer extending the nearest existing route or page folder before creating another top-level navigation area.",
                                "Keep route-level data orchestration close to the page and move reusable UI into components.",
                            ],
                        ),
                    ],
                    how_to=[
                        "Start with the closest existing route or page file from the detected list.",
                        "Reuse nearby components and shared state patterns before introducing new abstractions.",
                        "Update tests or route smoke checks if the project already has them.",
                    ],
                    references=["../SKILL.md", "../components/SKILL.md", "../../requirements/SKILL.md"],
                )
            )

    plan = build_roadmap_plan(load_config(project_root), parse_project_intent(project_root, requirements_path))
    phase_paths: list[str] = []
    seen_phases: set[str] = set()
    for step in plan.steps:
        phase_dir = f"roadmap/{step.phase}"
        if step.phase in seen_phases:
            continue
        seen_phases.add(step.phase)
        phase_paths.append(f"./{step.phase}/SKILL.md")
        specs.append(
            SkillSpec(
                path=f"{phase_dir}/SKILL.md",
                name=f"roadmap-{step.phase}",
                domain="roadmap",
                sub_domain=step.phase,
                overview=f"Roadmap guidance for {step.title}.",
                checks=["{{project_root}}/README.md", "{{project_root}}/FEATURES.md", "{{project_root}}/skills/roadmap/"],
                patterns=[
                    ("Roadmap step", [step.description]),
                    ("Status tracking", [f"Current status: {step.status}."]),
                ],
                how_to=[
                    "Read the current step description.",
                    "Use the phase status to decide whether the work is in progress or pending.",
                    "Reflect completed work back into the roadmap tree.",
                ],
                references=["../SKILL.md", "../../requirements/SKILL.md"],
            )
        )

    specs.append(
        SkillSpec(
            path="roadmap/SKILL.md",
            name="roadmap",
            domain="roadmap",
            sub_domain="plan",
            overview="Parent roadmap skill for the product phases and implementation sequence.",
            checks=["{{project_root}}/README.md", "{{project_root}}/FEATURES.md", "{{project_root}}/skills/roadmap/"],
            patterns=[
                ("Phase-based delivery", ["Organize work by roadmap phase and keep each phase discoverable as a child skill."]),
                ("Plan persistence", ["Persist the roadmap as generated skills, not only as transient CLI output."]),
            ],
            how_to=[
                "Start here to understand the overall implementation sequence.",
                "Open the child phase skills for current and upcoming work.",
                "Update statuses as the roadmap advances.",
            ],
            references=["../requirements/SKILL.md", *phase_paths],
        )
    )
    return specs


def _render_skill_native(spec: SkillSpec, source_hash: str) -> str:
    depth = len(Path(spec.path).parts)
    traceability_ref = "/".join([".."] * depth + ["TRACEABILITY.md"])
    pattern_sections = []
    for title, bullets in spec.patterns:
        block = [f"### {title}"]
        block.extend(f"- {item}" for item in bullets)
        pattern_sections.append("\n".join(block))

    sections = [
        "---",
        f"name: {spec.name}",
        "version: 0.1.0",
        f"domain: {spec.domain}",
        f"sub_domain: {spec.sub_domain}",
        f"last_updated: {TODAY}",
        "triggered_by: requirements_pipeline",
        f"source_hash: {source_hash}",
        "references:",
        *[f"  - {item}" for item in spec.references],
        "status: active",
        "---",
        "",
        f"# {spec.name.replace('-', ' ').title()} Skill",
        "",
        "## Overview",
        spec.overview,
        "",
        "## Check These Paths First",
        *[f"- {item}" for item in spec.checks],
        "",
        "## Patterns",
        "\n".join(pattern_sections),
        "",
        "## How-To",
        *[f"{index}. {step}" for index, step in enumerate(spec.how_to, start=1)],
        "",
        "## Traceability",
        f"- Generated from requirements source hash: `{source_hash}`",
        f"- Domain path: `{spec.domain}/{spec.sub_domain}`",
        f"- Read `{traceability_ref}` for full requirement-to-output mapping.",
        "- Use the detected file patterns in this skill before creating new structure.",
        "",
        "## References",
        *[f"- {item}" for item in spec.references],
        "",
    ]
    return "\n".join(sections)


def render_skill(spec: SkillSpec, source_hash: str) -> str:
    if spec.path.count("/") >= 2:
        return _render_skill_native(spec, source_hash)
    return run_deep_text(
        "skill guidance synthesis",
        (
            "Write a markdown SKILL.md file with YAML frontmatter for Skilgen. "
            "Use the provided skill spec to generate higher-level reusable guidance while preserving references and traceability.\n\n"
            f"Skill spec JSON:\n{spec}"
            f"\nSource hash: {source_hash}"
        ),
        lambda: _render_skill_native(spec, source_hash),
    )


def render_manifest(specs: list[SkillSpec], source_hash: str) -> str:
    unique_specs: list[SkillSpec] = []
    seen_paths: set[str] = set()
    for spec in specs:
        if spec.path in seen_paths:
            continue
        seen_paths.add(spec.path)
        unique_specs.append(spec)
    lines = [
        "# Skill Manifest",
        "",
        "This manifest is the entry point for agents discovering the skill tree.",
        "",
        "| Skill Path | Version | Domain | Last Updated | Triggered By | Source Hash |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for spec in unique_specs:
        lines.append(
            f"| `{spec.path}` | `0.1.0` | `{spec.domain}` | `{TODAY}` | `requirements_pipeline` | `{source_hash}` |"
        )
    lines.append("")
    return "\n".join(lines)


def render_graph(specs: list[SkillSpec]) -> str:
    unique_specs: list[SkillSpec] = []
    seen_paths: set[str] = set()
    for spec in specs:
        if spec.path in seen_paths:
            continue
        seen_paths.add(spec.path)
        unique_specs.append(spec)

    lines = [
        "# Skill Graph",
        "",
        "This file summarizes the generated skill tree and cross references.",
        "",
    ]
    for spec in unique_specs:
        lines.append(f"## {spec.path}")
        lines.append(f"- domain: `{spec.domain}`")
        lines.append(f"- sub_domain: `{spec.sub_domain}`")
        if spec.references:
            lines.append("- references:")
            lines.extend(f"  - `{reference}`" for reference in spec.references)
        else:
            lines.append("- references: none")
        lines.append("")
    return "\n".join(lines)


def render_summary(context: RequirementsContext) -> str:
    lines = ["# Requirements Summary", ""]
    if context.summary:
        lines.extend(f"- {line}" for line in context.summary)
    else:
        lines.append("- No major summary lines were extracted.")
    lines.append("")
    return "\n".join(lines)


def render_domain_summary(title: str, sections: list[tuple[str, list[str]]]) -> str:
    lines = [f"# {title}", ""]
    for heading, items in sections:
        lines.append(f"## {heading}")
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append("- No matching files detected.")
        lines.append("")
    return "\n".join(lines)


def _select_specs(specs: list[SkillSpec], selected_domains: set[str]) -> list[SkillSpec]:
    if not selected_domains:
        return specs
    return [spec for spec in specs if spec.domain in selected_domains]


def planned_skill_paths(context: RequirementsContext, output_dir: Path, selected_domains: set[str] | None = None) -> list[Path]:
    selected = selected_domains or set()
    requirements_path = context.requirements_path if context.requirements_path.exists() else None
    specs = _select_specs(build_skill_specs(context.domains, output_dir, requirements_path), selected)
    planned = [output_dir / spec.path for spec in specs]
    planned.append(output_dir / "MANIFEST.md")
    planned.append(output_dir / "GRAPH.md")
    if not selected or "requirements" in selected:
        planned.append(output_dir / "requirements" / "SUMMARY.md")
    if not selected or "backend" in selected:
        planned.append(output_dir / "backend" / "SUMMARY.md")
        planned.append(output_dir / "backend" / "services" / "SUMMARY.md")
    if not selected or "frontend" in selected:
        planned.append(output_dir / "frontend" / "SUMMARY.md")
        planned.append(output_dir / "frontend" / "components" / "SUMMARY.md")
    unique_paths: list[Path] = []
    seen: set[Path] = set()
    for path in planned:
        if path in seen:
            continue
        seen.add(path)
        unique_paths.append(path)
    return unique_paths


def write_skills(context: RequirementsContext, output_dir: Path, selected_domains: set[str] | None = None) -> list[Path]:
    selected = selected_domains or set()
    requirements_path = context.requirements_path if context.requirements_path.exists() else None
    specs = _select_specs(build_skill_specs(context.domains, output_dir, requirements_path), selected)
    signals = analyze_codebase(output_dir.parent)
    written: list[Path] = []
    for spec in specs:
        target = output_dir / spec.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_skill(spec, context.source_hash), encoding="utf-8")
        written.append(target)

    manifest = output_dir / "MANIFEST.md"
    manifest.write_text(render_manifest(specs, context.source_hash), encoding="utf-8")
    written.append(manifest)

    graph = output_dir / "GRAPH.md"
    graph.write_text(render_graph(specs), encoding="utf-8")
    written.append(graph)

    if not selected or "requirements" in selected:
        summary = output_dir / "requirements" / "SUMMARY.md"
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(render_summary(context), encoding="utf-8")
        written.append(summary)

    if context.domains.get("backend") and (not selected or "backend" in selected):
        backend_summary = output_dir / "backend" / "SUMMARY.md"
        backend_summary.write_text(
            render_domain_summary(
                "Backend Summary",
                [
                    ("Detected Route Files", signals.backend_routes),
                    ("Detected Service Files", signals.services),
                    ("Detected Test Files", signals.tests),
                ],
            ),
            encoding="utf-8",
        )
        written.append(backend_summary)

    if context.domains.get("frontend") and (not selected or "frontend" in selected):
        frontend_summary = output_dir / "frontend" / "SUMMARY.md"
        frontend_summary.write_text(
            render_domain_summary(
                "Frontend Summary",
                [
                    ("Detected Route Files", signals.frontend_routes),
                    ("Detected Component Files", signals.components),
                    ("Detected Test Files", signals.tests),
                ],
            ),
            encoding="utf-8",
        )
        written.append(frontend_summary)

        component_summary = output_dir / "frontend" / "components" / "SUMMARY.md"
        component_summary.parent.mkdir(parents=True, exist_ok=True)
        component_summary.write_text(
            render_domain_summary("Frontend Components Summary", [("Detected Component Files", signals.components)]),
            encoding="utf-8",
        )
        written.append(component_summary)

    if context.domains.get("backend") and signals.services and (not selected or "backend" in selected):
        service_summary = output_dir / "backend" / "services" / "SUMMARY.md"
        service_summary.parent.mkdir(parents=True, exist_ok=True)
        service_summary.write_text(
            render_domain_summary("Backend Services Summary", [("Detected Service Files", signals.services)]),
            encoding="utf-8",
        )
        written.append(service_summary)
    return written
