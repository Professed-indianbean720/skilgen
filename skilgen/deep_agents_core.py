from __future__ import annotations

import asyncio
import json
import os
from typing import Callable

from pathlib import Path

from skilgen.agents.model_registry import resolve_model_settings
from skilgen.core.config import DEFAULT_CONFIG, load_config

try:
    from deepagents import create_deep_agent
    from langchain.chat_models import init_chat_model
except ImportError:  # pragma: no cover
    create_deep_agent = None
    init_chat_model = None


def deep_agents_unavailable_reason() -> str | None:
    settings = resolve_model_settings(load_config(Path.cwd()))
    if create_deep_agent is None or init_chat_model is None:
        return (
            "Model-backed runtime dependencies are not installed in this Python environment. "
            "Use Python 3.11+ for model-backed runtime support, or reinstall after upgrading Python."
        )
    key_env = settings.api_key_env or "OPENAI_API_KEY"
    if not os.getenv(key_env):
        return f"Missing model credential environment variable: {key_env}"
    return None


def _close_model(model: object) -> None:
    close = getattr(model, "close", None)
    if not callable(close):
        return
    try:
        result = close()
        if asyncio.iscoroutine(result):
            asyncio.run(result)
    except Exception:
        pass


def _model_name() -> str:
    settings = resolve_model_settings(load_config(Path.cwd()))
    provider = settings.provider or "openai"
    model = settings.model or DEFAULT_CONFIG.model or os.getenv("SKILGEN_MODEL", "gpt-4.1-mini")
    return f"{provider}:{model}"


def deep_agents_available() -> bool:
    return deep_agents_unavailable_reason() is None


def current_runtime_mode() -> str:
    return "model_backed" if deep_agents_available() else "local_fallback"


def _build_chat_model():
    if init_chat_model is None:
        raise RuntimeError("Chat model initialization is unavailable")
    settings = resolve_model_settings(load_config(Path.cwd()))
    model_name = _model_name()
    kwargs: dict[str, object] = {}
    if settings.temperature is not None:
        kwargs["temperature"] = settings.temperature
    if settings.max_tokens is not None:
        kwargs["max_tokens"] = settings.max_tokens
    return init_chat_model(model_name, **kwargs)


def _extract_json(text: str) -> dict[str, object]:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return json.loads(stripped)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        return json.loads(stripped[start : end + 1])
    raise ValueError("No JSON object found in model-backed response")


def _normalize_json_with_model(task: str, raw_text: str) -> dict[str, object]:
    if init_chat_model is None:
        raise RuntimeError("Chat model is unavailable for JSON normalization")
    model = _build_chat_model()
    try:
        response = model.invoke(
            [
                (
                    "system",
                    (
                        "You normalize agent outputs into strict JSON for Skilgen. "
                        "Return exactly one valid JSON object, with no markdown fences, commentary, or prose. "
                        "If the source text is partially structured, preserve all useful fields and discard filler."
                    ),
                ),
                (
                    "user",
                    (
                        f"Task: {task}\n\n"
                        "Normalize the following agent output into one valid JSON object matching the requested schema.\n\n"
                        f"{raw_text}"
                    ),
                ),
            ]
        )
        return _extract_json(_message_text(response))
    finally:
        _close_model(model)


def _message_text(message: object) -> str:
    if isinstance(message, dict):
        content = message.get("content", "")
    else:
        content = getattr(message, "content", "")
    if isinstance(content, list):
        return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content).strip()
    return str(content).strip()


def run_deep_json(task: str, prompt: str, fallback: Callable[[], dict[str, object]]) -> dict[str, object]:
    required = os.getenv("SKILGEN_DEEPAGENTS_REQUIRED") == "1"
    if not deep_agents_available():
        if required:
            raise RuntimeError(deep_agents_unavailable_reason() or "Model-backed runtime is required but unavailable")
        return fallback()

    model = _build_chat_model()
    agent = create_deep_agent(
        model=model,
        system_prompt=(
            "You are Skilgen's internal reasoning engine for requirements interpretation, planning, "
            "feature modeling, and skill guidance synthesis.\n"
            "Your job is to extract complete, implementation-relevant information from the provided "
            "requirements and code context without inventing unsupported details.\n"
            "Prioritize:\n"
            "1. completeness over brevity,\n"
            "2. grounded details from the provided input,\n"
            "3. stable output formatting,\n"
            "4. direct support for downstream automation.\n"
            "Output contract:\n"
            "- Return exactly one valid JSON object.\n"
            "- Do not wrap JSON in markdown fences.\n"
            "- Do not add explanation before or after the JSON.\n"
            "- Prefer short, concrete strings over vague summaries.\n"
            "- Include only fields supported by the requested shape."
        ),
    )
    try:
        result = agent.invoke({"messages": [{"role": "user", "content": f"Task: {task}\n\n{prompt}"}]})
        messages = result.get("messages", []) if isinstance(result, dict) else []
        if not messages:
            if required:
                raise RuntimeError("Model-backed runtime returned no messages")
            return fallback()
        collected = []
        for message in reversed(messages):
            text = _message_text(message)
            if not text:
                continue
            collected.append(text)
            try:
                return _extract_json(text)
            except Exception:
                continue
        normalized_source = "\n\n".join(reversed(collected))
        if normalized_source:
            return _normalize_json_with_model(task, normalized_source)
        raise ValueError("No usable agent text found for JSON normalization")
    except Exception:
        if required:
            raise
        return fallback()
    finally:
        _close_model(model)


def run_deep_text(task: str, prompt: str, fallback: Callable[[], str]) -> str:
    required = os.getenv("SKILGEN_DEEPAGENTS_REQUIRED") == "1"
    if not deep_agents_available():
        if required:
            raise RuntimeError(deep_agents_unavailable_reason() or "Model-backed runtime is required but unavailable")
        return fallback()

    model = _build_chat_model()
    agent = create_deep_agent(
        model=model,
        system_prompt=(
            "You are Skilgen's internal content synthesis engine.\n"
            "Write polished, structured project artifacts for Skilgen using the supplied requirements, "
            "code evidence, and plan context.\n"
            "Prioritize clarity, completeness, reuse guidance, and traceability to evidence.\n"
            "Output contract:\n"
            "- Return only the requested markdown text.\n"
            "- Do not add preambles like 'Here is the markdown'.\n"
            "- Preserve requested headings, tables, references, and file-oriented structure.\n"
            "- Prefer actionable guidance over abstract commentary."
        ),
    )
    try:
        result = agent.invoke({"messages": [{"role": "user", "content": f"Task: {task}\n\n{prompt}"}]})
        messages = result.get("messages", []) if isinstance(result, dict) else []
        if not messages:
            if required:
                raise RuntimeError("Model-backed runtime returned no messages")
            return fallback()
        return _message_text(messages[-1])
    except Exception:
        if required:
            raise
        return fallback()
    finally:
        _close_model(model)
