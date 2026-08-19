"""Canonical EvoOntology workspace resolution and project context storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

PathLike = Union[str, Path]
WORKSPACE_DIRNAME = ".evoontology"
PROJECT_SCHEMA_VERSION = 1
PROJECT_MODES = {"fixed_split", "rolling_trajectory"}


def resolve_workspace(
    workspace: Optional[PathLike] = None,
    *,
    project_root: Optional[PathLike] = None,
) -> Path:
    """Return an absolute workspace path.

    An explicit ``workspace`` takes precedence. Otherwise the default is
    ``<project_root>/.evoontology`` and ``project_root`` defaults to the
    current working directory.
    """
    if workspace is not None:
        return Path(workspace).expanduser().resolve()
    root = Path(project_root) if project_root is not None else Path.cwd()
    return (root.expanduser().resolve() / WORKSPACE_DIRNAME)


def ensure_workspace(
    workspace: Optional[PathLike] = None,
    *,
    project_root: Optional[PathLike] = None,
) -> Path:
    """Create the idempotent workspace directory skeleton.

    State-bearing JSON files are written only when their corresponding
    lifecycle step completes: Step 0 writes ``project.json``; publication
    writes ``active.json`` and initializes ``state.json``.
    """
    root = resolve_workspace(workspace, project_root=project_root)
    for directory in ("versions", "trajectories", "evolution"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    return root


def load_project(
    workspace: Optional[PathLike] = None,
    *,
    project_root: Optional[PathLike] = None,
) -> Dict[str, Any]:
    """Load and minimally validate ``<workspace>/project.json``."""
    root = resolve_workspace(workspace, project_root=project_root)
    path = root / "project.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing EvoOntology project context: {path}")
    try:
        project = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid project.json: {exc}") from exc
    return _validate_project(project)


def save_project(
    project: Dict[str, Any],
    workspace: Optional[PathLike] = None,
    *,
    project_root: Optional[PathLike] = None,
) -> Path:
    """Validate and atomically persist ``project.json``."""
    normalized = _validate_project(project)
    root = ensure_workspace(workspace, project_root=project_root)
    path = root / "project.json"
    temporary = root / "project.json.tmp"
    temporary.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)
    return path


def _validate_project(project: Any) -> Dict[str, Any]:
    if not isinstance(project, dict):
        raise ValueError("project.json must contain a JSON object")
    schema_version = project.get("schema_version", project.get("version"))
    if schema_version != PROJECT_SCHEMA_VERSION:
        raise ValueError(
            f"project.json schema_version must be {PROJECT_SCHEMA_VERSION}"
        )
    mode = project.get("mode")
    if mode not in PROJECT_MODES:
        raise ValueError(f"project.json mode must be one of {sorted(PROJECT_MODES)}")
    for field in ("data_source", "workload_source", "evaluation", "boundary"):
        if field not in project:
            raise ValueError(f"project.json is missing required field: {field}")
    for field in ("evaluation", "boundary"):
        if not isinstance(project[field], dict):
            raise ValueError(f"project.json field {field!r} must be an object")
    normalized = dict(project)
    normalized.pop("version", None)
    normalized["schema_version"] = PROJECT_SCHEMA_VERSION
    return normalized
