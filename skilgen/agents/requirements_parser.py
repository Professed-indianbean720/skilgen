from __future__ import annotations

from pathlib import Path

from skilgen.agents.codebase_signals import analyze_codebase
from skilgen.deep_agents_core import run_deep_json
from skilgen.core.models import ProjectIntent
from skilgen.core.requirements import extract_project_intent, extract_text, normalize_lines


def parse_requirements_file_native(path: Path) -> ProjectIntent:
    return extract_project_intent(normalize_lines(extract_text(path)))


def parse_requirements_file(path: Path) -> ProjectIntent:
    resolved = path.resolve()
    text = extract_text(resolved)
    native_intent = extract_project_intent(normalize_lines(text))
    payload = run_deep_json(
        "requirements interpretation",
        (
            "Interpret the following requirements and return JSON with keys: "
            "features, domain_concepts, entities, endpoints, ui_flows. "
            "Each key must contain a short list of strings.\n\n"
        f"Requirements file: {resolved}\n"
            f"Content:\n{text}"
        ),
        lambda: {
            "features": native_intent.features,
            "domain_concepts": native_intent.domain_concepts,
            "entities": native_intent.entities,
            "endpoints": native_intent.endpoints,
            "ui_flows": native_intent.ui_flows,
        },
    )
    return ProjectIntent(
        features=[str(item) for item in payload.get("features", [])][:12],
        domain_concepts=[str(item) for item in payload.get("domain_concepts", [])][:12],
        entities=[str(item) for item in payload.get("entities", [])][:12],
        endpoints=[str(item) for item in payload.get("endpoints", [])][:12],
        ui_flows=[str(item) for item in payload.get("ui_flows", [])][:12],
    )


def parse_project_intent_native(project_root: Path, requirements_path: Path | None = None) -> ProjectIntent:
    if requirements_path is not None:
        return parse_requirements_file_native(requirements_path.resolve())
    signals = analyze_codebase(project_root.resolve())
    features = ["Codebase-only scan", "Generate skills from the current repository structure"]
    domain_concepts: list[str] = []
    entities: list[str] = []
    endpoints = [f"Detected route: {item}" for item in signals.backend_routes[:12]]
    ui_flows = [f"Detected route: {item}" for item in signals.frontend_routes[:12]]
    if signals.backend_routes or signals.services:
        domain_concepts.append("backend")
    if signals.frontend_routes or signals.components:
        domain_concepts.append("frontend")
    entities.extend(f"Service: {item}" for item in signals.services[:6])
    entities.extend(f"Component: {item}" for item in signals.components[:6])
    features.extend(f"Backend route: {item}" for item in signals.backend_routes[:6])
    features.extend(f"Frontend route: {item}" for item in signals.frontend_routes[:6])
    return ProjectIntent(
        features=features[:12],
        domain_concepts=domain_concepts[:12],
        entities=entities[:12],
        endpoints=endpoints[:12],
        ui_flows=ui_flows[:12],
    )


def parse_project_intent(project_root: Path, requirements_path: Path | None = None) -> ProjectIntent:
    if requirements_path is not None:
        return parse_requirements_file(requirements_path.resolve())
    resolved_root = project_root.resolve()
    native_intent = parse_project_intent_native(resolved_root, None)
    signals = analyze_codebase(resolved_root)
    payload = run_deep_json(
        "codebase intent interpretation",
        (
            "Interpret the repository structure and return JSON with keys: "
            "features, domain_concepts, entities, endpoints, ui_flows. "
            "Each key must contain a short list of strings grounded in the detected codebase.\n\n"
            f"Project root: {resolved_root}\n"
            f"Backend routes: {signals.backend_routes}\n"
            f"Frontend routes: {signals.frontend_routes}\n"
            f"Components: {signals.components}\n"
            f"Services: {signals.services}\n"
            f"Tests: {signals.tests}\n"
        ),
        lambda: {
            "features": native_intent.features,
            "domain_concepts": native_intent.domain_concepts,
            "entities": native_intent.entities,
            "endpoints": native_intent.endpoints,
            "ui_flows": native_intent.ui_flows,
        },
    )
    return ProjectIntent(
        features=[str(item) for item in payload.get("features", [])][:12],
        domain_concepts=[str(item) for item in payload.get("domain_concepts", [])][:12],
        entities=[str(item) for item in payload.get("entities", [])][:12],
        endpoints=[str(item) for item in payload.get("endpoints", [])][:12],
        ui_flows=[str(item) for item in payload.get("ui_flows", [])][:12],
    )
