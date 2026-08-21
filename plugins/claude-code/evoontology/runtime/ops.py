"""Deterministic build/evolve/visualize operations served by the MCP server.

These wrap the core's validate, visualize, trigger, store, and evolution-session
capabilities. They exist so a plugin-only installation (no repo clone, no
``pip install evoontology``) can still drive the full build and evolve loop:
the MCP server boots from the plugin root where the bundled core lives, and the
agent calls these tools with an explicit workspace path.
"""

from __future__ import annotations

from typing import Any, Dict

from ..evolution.session import EvolutionSession
from ..ontology.store import SemanticStore
from ..trigger.trigger import EvolutionTrigger
from ..validate import validate
from ..visualization import visualize as _visualize
from ..workspace import resolve_workspace


def _workspace(arguments: Dict[str, Any]):
    raw = str(arguments.get("workspace") or "").strip()
    if not raw:
        raise ValueError(
            "workspace is required: pass the absolute path to the .evoontology/ directory"
        )
    return resolve_workspace(raw)


def _version(arguments: Dict[str, Any]) -> str | None:
    raw = str(arguments.get("version") or "").strip()
    return raw or None


def validate_semantics(arguments: Dict[str, Any]) -> Dict[str, Any]:
    return validate(str(_workspace(arguments)), version=_version(arguments))


def visualize_semantics(arguments: Dict[str, Any]) -> Dict[str, Any]:
    workspace = _workspace(arguments)
    path = _visualize(
        workspace=str(workspace),
        version=_version(arguments) or "active",
        open_browser=False,
    )
    return {"status": "ok", "html_path": str(path)}


def evolution_status(arguments: Dict[str, Any]) -> Dict[str, Any]:
    trigger = EvolutionTrigger(str(_workspace(arguments)))
    state = trigger.initialize()
    return {"status": "ok", "state": state, "check": trigger.check()}


def list_versions(arguments: Dict[str, Any]) -> Dict[str, Any]:
    workspace = _workspace(arguments)
    active_version: str | None = None
    try:
        active_version = SemanticStore.active_version(str(workspace))
    except (FileNotFoundError, ValueError):
        active_version = None
    return {
        "status": "ok",
        "active_version": active_version,
        "versions": SemanticStore.list_versions(str(workspace)),
    }


def save_version(arguments: Dict[str, Any]) -> Dict[str, Any]:
    version = str(arguments.get("version") or "").strip()
    records = arguments.get("records")
    if not version:
        raise ValueError("version is required")
    if not isinstance(records, dict):
        raise ValueError("records must be an object with the five record families")
    path = SemanticStore.save_version(str(_workspace(arguments)), version, records)
    return {"status": "ok", "version": version, "path": path}


def set_active_version(arguments: Dict[str, Any]) -> Dict[str, Any]:
    version = str(arguments.get("version") or "").strip()
    if not version:
        raise ValueError("version is required")
    SemanticStore.set_active(str(_workspace(arguments)), version)
    return {"status": "ok", "active_version": version}


def start_evolution_run(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    return session.start_run(
        str(arguments.get("parent_version") or "").strip(),
        adapter=str(arguments.get("adapter") or ""),
        max_rounds=arguments.get("max_rounds"),
        acceptance=arguments.get("acceptance"),
    )


def resume_evolution_run(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    run_id = str(arguments.get("run_id") or "").strip() or None
    return session.resume(run_id)


def evolution_run_status(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    run = session.latest_run()
    return {"status": "ok", "run": run}


def begin_evolution_round(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    round_number = session.begin_round(
        str(arguments.get("hypothesis") or ""),
        str(arguments.get("candidate_version") or ""),
    )
    return {"status": "ok", "round": round_number}


def record_evolution_round(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    return session.record_round(
        decision=str(arguments.get("decision") or ""),
        metrics=arguments.get("metrics"),
        artifact_refs=arguments.get("artifact_refs"),
        notes=str(arguments.get("notes") or ""),
    )


def record_evolution_evaluation(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    path = session.record_evaluation(
        str(arguments.get("subject") or ""),
        arguments.get("result") or {},
        role=str(arguments.get("role") or ""),
    )
    return {"status": "ok", "path": str(path)}


def confirm_trajectory_sources(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    sources = arguments.get("sources")
    if not isinstance(sources, list):
        raise ValueError("sources must be a list of {path, scope, purpose} objects")
    path = session.confirm_trajectory_sources(sources)
    return {"status": "ok", "path": str(path)}


def accept_evolution(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    new_version = str(arguments.get("new_version") or "").strip() or None
    published = session.accept(new_version)
    return {"status": "ok", "accepted_version": published}


def mark_evolution_incomplete(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    return session.mark_incomplete(str(arguments.get("reason") or ""))


def extend_evolution_budget(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    max_rounds = arguments.get("max_rounds")
    if max_rounds is None:
        raise ValueError("max_rounds is required")
    return session.extend_budget(int(max_rounds))


def finalize_evolution_run(arguments: Dict[str, Any]) -> Dict[str, Any]:
    session = EvolutionSession(str(_workspace(arguments)))
    return session.finalize()


_HANDLERS = {
    "validate_semantics": validate_semantics,
    "visualize_semantics": visualize_semantics,
    "evolution_status": evolution_status,
    "list_versions": list_versions,
    "save_version": save_version,
    "set_active_version": set_active_version,
    "start_evolution_run": start_evolution_run,
    "resume_evolution_run": resume_evolution_run,
    "evolution_run_status": evolution_run_status,
    "begin_evolution_round": begin_evolution_round,
    "record_evolution_round": record_evolution_round,
    "record_evolution_evaluation": record_evolution_evaluation,
    "confirm_trajectory_sources": confirm_trajectory_sources,
    "accept_evolution": accept_evolution,
    "mark_evolution_incomplete": mark_evolution_incomplete,
    "extend_evolution_budget": extend_evolution_budget,
    "finalize_evolution_run": finalize_evolution_run,
}


def execute(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    handler = _HANDLERS.get(name)
    if handler is None:
        raise ValueError(f"Unknown operation: {name}")
    return handler(arguments or {})
