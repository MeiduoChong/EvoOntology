"""Read-only ontology visualization: one ontology version -> one standalone HTML.

Pipeline::

    ontology version
        -> build_content_elements / build_schema_view /
           build_tool_view / load_evolution_metadata
        -> render_html (template.html + vendored cytoscape.min.js)
        -> <workspace>/visualizations/<version>.html

The module is strictly read-only: records are loaded through ``SemanticStore``
and the only write is the generated HTML. ``active.json``, versions,
trajectories, and evolution records are never modified.
"""

from __future__ import annotations

import dataclasses
import json
import re
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..ontology.models import Constraint, Evidence, Mapping, Relation, Term
from ..ontology.store import SemanticStore
from ..runtime.tools import TOOLS
from ..runtime.runtime import SemanticLayer
from ..workspace import PathLike, resolve_workspace

ACTIVE = "active"
VISUALIZATIONS_DIRNAME = "visualizations"
CYTOSCAPE_VERSION = "3.30.2"

#: The five controlled relation values defined by ``semantic-schema.md``.
RELATION_TYPES = (
    "association",
    "hierarchy",
    "composition",
    "equivalence",
    "derivation",
)

_RUN_DIR_RE = re.compile(r"^run_(\d+)$")
_PACKAGE_DIR = Path(__file__).resolve().parent

_SCHEMA_OBJECTS = (
    ("Term", Term, "Reusable analytical concept: business concept, metric, entity, dimension, or category."),
    ("Mapping", Mapping, "Grounds a Term to physical structures in the underlying data environment."),
    ("Constraint", Constraint, "Conditions required for correct interpretation and usage of semantic objects."),
    ("Evidence", Evidence, "Reproducible observations from the data environment that support semantic claims."),
)

_RELATION_SEMANTICS = {
    "association": "Concept-level relatedness that does not fit a stronger relation type.",
    "hierarchy": "Directed broader/narrower (parent/child) structure between Terms.",
    "composition": "Directed part-of relationship between Terms.",
    "equivalence": "Symmetric same-meaning relationship between Terms.",
    "derivation": "Directed relationship where one Term is computed from another.",
}

_REFERENCE_RULES = (
    ("grounded_by", "Term", "Mapping", "A Mapping grounds its Term to database structures (table, column, path)."),
    ("constrained_by", "Term / Mapping", "Constraint", "A Constraint governs how its target object must be interpreted."),
    ("supported_by", "Term / Mapping / Relation", "Evidence", "Evidence supports the semantic claim of the object it is attached to."),
)


# ---- public API -------------------------------------------------------------


def visualize(
    workspace: Optional[PathLike] = None,
    version: str = ACTIVE,
    open_browser: bool = True,
) -> Path:
    """Render one ontology version to a standalone HTML file and return its path.

    ``version="active"`` follows ``active.json``; an explicit version is
    rendered without touching ``active.json``. The HTML is written to
    ``<workspace>/visualizations/<version>.html`` (overwriting any previous
    render of the same version).
    """
    root = resolve_workspace(workspace)
    if not root.is_dir():
        raise FileNotFoundError("EvoOntology workspace not initialized.")
    selected = resolve_version(root, version)
    store = load_ontology(root, selected)

    active_version: Optional[str] = None
    try:
        active_version = SemanticStore.active_version(root)
    except (FileNotFoundError, ValueError):
        active_version = None

    content = build_content_elements(store)
    data = {
        "meta": {
            "version": selected,
            "active": selected == active_version,
            "counts": store.counts(),
            "warnings": content["warnings"],
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        },
        "content": {"nodes": content["nodes"], "edges": content["edges"]},
        "schema": build_schema_view(),
        "tools": build_tool_view(store),
        "evolution": load_evolution_metadata(root, selected),
    }

    out_dir = root / VISUALIZATIONS_DIRNAME
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{selected}.html"
    out_path.write_text(render_html(data), encoding="utf-8")

    if open_browser:
        try:
            webbrowser.open(out_path.resolve().as_uri())
        except Exception:
            pass  # visualization output stays valid without a browser
    return out_path


# ---- pipeline steps ---------------------------------------------------------


def resolve_version(root: PathLike, version: Union[str, None]) -> str:
    """Resolve ``"active"`` through ``active.json``; check explicit versions."""
    requested = str(version or ACTIVE).strip() or ACTIVE
    root = Path(root)
    if requested == ACTIVE:
        try:
            return SemanticStore.active_version(root)
        except (FileNotFoundError, ValueError) as exc:
            raise FileNotFoundError("No active ontology version.") from exc
    if not (root / "versions" / requested).is_dir():
        raise FileNotFoundError(f"Ontology version '{requested}' not found.")
    return requested


def load_ontology(root: PathLike, version: str) -> SemanticStore:
    """Load one version read-only (never changes ``active.json``)."""
    return SemanticStore.load_version(root, version)


def build_content_elements(store: SemanticStore) -> Dict[str, Any]:
    """Convert the Content Layer into Cytoscape nodes/edges.

    Node families: Term / Mapping / Constraint / Evidence. Edge families:
    Semantic Relations (Relation records between Terms) and Structural
    References (grounded_by / constrained_by / supported_by). Broken
    references are reported as warnings; nothing is fabricated.
    """
    warnings: List[str] = []
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    used_ids: set = set()

    mappings_by_term: Dict[str, List[str]] = {}
    for mapping in store.mappings.values():
        if mapping.term_id:
            mappings_by_term.setdefault(mapping.term_id, []).append(mapping.id)
    relations_by_term: Dict[str, List[str]] = {}
    for relation in store.relations.values():
        for end in {relation.source, relation.target}:
            if end:
                relations_by_term.setdefault(end, []).append(relation.id)
    constraints_by_target: Dict[str, List[str]] = {}
    for constraint in store.constraints.values():
        if constraint.target:
            constraints_by_target.setdefault(constraint.target, []).append(constraint.id)
    term_names = {t.id: (t.name or t.id) for t in store.terms.values()}

    def _nid(family: str, record_id: str) -> str:
        # Prefix ids so record ids that collide with Object.prototype keys
        # (e.g. a Term named "constructor") cannot poison Cytoscape internals.
        return f"{family}:{record_id}"

    def _add_node(record_id: str, family: str, label: str, search: List[str],
                  detail: List[List[Any]], extra: Optional[Dict[str, Any]] = None) -> None:
        if record_id in used_ids:
            warnings.append(f"duplicate object id skipped: {record_id!r}")
            return
        used_ids.add(record_id)
        data = {
            "id": _nid(family, record_id),
            "record_id": record_id,
            "family": family,
            "label": label,
            "search": sorted({s.lower() for s in search if s}),
            "detail": detail,
        }
        if extra:
            data.update(extra)
        nodes.append({"data": data})

    def _add_edge(edge_id: str, family: str, source: str, target: str,
                  extra: Dict[str, Any]) -> None:
        data = {"id": edge_id, "family": family, "source": source, "target": target}
        data.update(extra)
        edges.append({"data": data})

    for term in store.terms.values():
        term_maps = mappings_by_term.get(term.id, [])
        sublabel = ""
        if term_maps:
            first = store.mappings.get(term_maps[0])
            grounding = ".".join(part for part in (first.table, first.column) if part) if first else ""
            if grounding:
                sublabel = grounding + (f" +{len(term_maps) - 1}" if len(term_maps) > 1 else "")
            else:
                sublabel = f"{len(term_maps)} mapping(s)"
        _add_node(term.id, "term", term.name or term.id,
                  [term.name, term.id, *term.aliases],
                  _pairs([
                      ("Name", term.name),
                      ("ID", term.id),
                      ("Type", term.type),
                      ("Definition", term.definition),
                      ("Scope", term.scope),
                      ("Aliases", term.aliases),
                      ("Mappings", sorted(mappings_by_term.get(term.id, []))),
                      ("Relations", sorted(relations_by_term.get(term.id, []))),
                      ("Constraints", sorted(constraints_by_target.get(term.id, []))),
                      ("Evidence", term.evidence_refs),
                      ("Lifecycle", term.lifecycle_state),
                  ]),
                  {"sublabel": sublabel, "definition": term.definition or ""})

    for mapping in store.mappings.values():
        grounding = ".".join(part for part in (mapping.table, mapping.column) if part)
        _add_node(mapping.id, "mapping", grounding or mapping.id,
                  [mapping.id, grounding, mapping.table, mapping.column,
                   term_names.get(mapping.term_id, "")],
                  _pairs([
                      ("ID", mapping.id),
                      ("Related Term", term_names.get(mapping.term_id, "") if mapping.term_id else ""),
                      ("Data source", mapping.database_source),
                      ("Table", mapping.table),
                      ("Column", mapping.column),
                      ("Semantic Filter", mapping.semantic_filter),
                      ("Aggregation", mapping.aggregation_semantics),
                      ("Grain", mapping.grain),
                      ("Validation", mapping.validation),
                      ("Confidence", mapping.confidence_level),
                      ("Evidence", mapping.evidence_refs),
                      ("Lifecycle", mapping.lifecycle_state),
                  ]))

    for constraint in store.constraints.values():
        _add_node(constraint.id, "constraint", constraint.constraint_type or constraint.id,
                  [constraint.id, constraint.constraint_type, constraint.description],
                  _pairs([
                      ("ID", constraint.id),
                      ("Target", constraint.target),
                      ("Type", constraint.constraint_type),
                      ("Trigger Keywords", constraint.trigger_keywords),
                      ("Severity", constraint.severity),
                      ("Scope", constraint.scope),
                      ("Confidence", constraint.confidence_level),
                      ("Description", constraint.description),
                      ("Evidence", constraint.evidence_refs),
                      ("Lifecycle", constraint.lifecycle_state),
                  ]))

    for evidence in store.evidence.values():
        _add_node(evidence.id, "evidence", evidence.id,
                  [evidence.id, evidence.source],
                  _pairs([
                      ("ID", evidence.id),
                      ("Source", evidence.source),
                      ("Query", evidence.query),
                      ("Result", evidence.result),
                      ("Validation Method", evidence.validation_method),
                      ("Timestamp", evidence.timestamp),
                  ]))

    # Semantic Relation edges: Relation records between Terms.
    for relation in store.relations.values():
        if relation.source in store.terms and relation.target in store.terms:
            relation_type = relation.relation_type or "association"
            _add_edge(f"rel:{relation.id}", "relation",
                      _nid("term", relation.source), _nid("term", relation.target), {
                "relation_type": relation_type,
                "record_id": relation.id,
                "label": relation_type,
                "detail": _pairs([
                    ("ID", relation.id),
                    ("Type", relation.relation_type),
                    ("Source", term_names.get(relation.source, relation.source)),
                    ("Target", term_names.get(relation.target, relation.target)),
                    ("Connection", relation.connection_condition),
                    ("Description", relation.description),
                    ("Evidence", relation.evidence_refs),
                    ("Lifecycle", relation.lifecycle_state),
                ]),
            })
        else:
            warnings.append(
                f"relation {relation.id}: unresolved term reference, edge skipped "
                f"(source={relation.source!r}, target={relation.target!r})"
            )

    # Implicit same-table Term links (visualization-level, derived from mapping
    # grounding) so attribute Terms never float disconnected in the Term view.
    explicit_pairs = {
        frozenset((rel.source, rel.target))
        for rel in store.relations.values()
        if rel.source in store.terms and rel.target in store.terms
    }
    relation_degree: Dict[str, int] = {}
    for rel in store.relations.values():
        relation_degree[rel.source] = relation_degree.get(rel.source, 0) + 1
        relation_degree[rel.target] = relation_degree.get(rel.target, 0) + 1
    terms_by_table: Dict[str, List[str]] = {}
    for term_id in store.terms:
        tables: List[str] = []
        for mid in mappings_by_term.get(term_id, []):
            mapping = store.mappings.get(mid)
            if mapping and mapping.table and mapping.table not in tables:
                tables.append(mapping.table)
        for table in tables:
            terms_by_table.setdefault(table, []).append(term_id)
    for table in sorted(terms_by_table):
        members = sorted(terms_by_table[table])
        if len(members) < 2:
            continue
        hub = members[0]
        for tid in members[1:]:
            if (relation_degree.get(tid, 0), len(mappings_by_term.get(tid, []))) > (
                relation_degree.get(hub, 0), len(mappings_by_term.get(hub, []))
            ):
                hub = tid
        for member in members:
            if member == hub or frozenset((hub, member)) in explicit_pairs:
                continue
            _add_edge(f"ref:same_table:{table}:{hub}:{member}", "reference",
                      _nid("term", hub), _nid("term", member), {
                "kind": "same_table",
                "label": table,
                "detail": _pairs([
                    ("Reference", "same_table"),
                    ("Table", table),
                    ("Terms", f"{term_names.get(hub, hub)} \u2194 {term_names.get(member, member)}"),
                ]),
            })

    # Structural Reference edges: induced by schema-defined object references.
    for mapping in store.mappings.values():
        if not mapping.term_id:
            continue
        if mapping.term_id in store.terms:
            _add_edge(f"ref:grounded_by:{mapping.term_id}:{mapping.id}", "reference",
                      _nid("term", mapping.term_id), _nid("mapping", mapping.id), {
                          "kind": "grounded_by",
                          "detail": _pairs([
                              ("Reference", "grounded_by"),
                              ("Term", term_names.get(mapping.term_id, mapping.term_id)),
                              ("Mapping", mapping.id),
                              ("Grounding", ".".join(p for p in (mapping.table, mapping.column) if p)),
                          ]),
                      })
        else:
            warnings.append(
                f"mapping {mapping.id}: unresolved term_id {mapping.term_id!r}, reference skipped"
            )

    for constraint in store.constraints.values():
        if not constraint.target:
            continue
        if constraint.target in store.terms or constraint.target in store.mappings:
            target_family = "term" if constraint.target in store.terms else "mapping"
            _add_edge(f"ref:constrained_by:{constraint.target}:{constraint.id}", "reference",
                      _nid(target_family, constraint.target), _nid("constraint", constraint.id), {
                          "kind": "constrained_by",
                          "detail": _pairs([
                              ("Reference", "constrained_by"),
                              ("Object", constraint.target),
                              ("Constraint", constraint.id),
                              ("Severity", constraint.severity),
                              ("Description", constraint.description),
                          ]),
                      })
        else:
            warnings.append(
                f"constraint {constraint.id}: unresolved target {constraint.target!r}, reference skipped"
            )

    evidence_ids = set(store.evidence)
    for owner in (*store.terms.values(), *store.mappings.values()):
        for ref in owner.evidence_refs:
            if ref in evidence_ids:
                owner_family = "term" if owner.id in store.terms else "mapping"
                _add_edge(f"ref:supported_by:{owner.id}:{ref}", "reference",
                          _nid(owner_family, owner.id), _nid("evidence", ref), {
                              "kind": "supported_by",
                              "detail": _pairs([
                                  ("Reference", "supported_by"),
                                  ("Object", owner.id),
                                  ("Evidence", ref),
                              ]),
                          })
            else:
                warnings.append(
                    f"{owner.id}: unresolved evidence reference {ref!r}, reference skipped"
                )

    return {"nodes": nodes, "edges": edges, "warnings": warnings}


def build_schema_view() -> Dict[str, Any]:
    """Describe the current Schema Layer from the Core model definitions."""
    return {
        "object_types": [
            {"name": name, "description": description,
             "fields": [f.name for f in dataclasses.fields(model)]}
            for name, model, description in _SCHEMA_OBJECTS
        ],
        "relation_record": {
            "name": "Relation",
            "description": "Serialized form of a Semantic Relation edge between Terms.",
            "fields": [f.name for f in dataclasses.fields(Relation)],
        },
        "relation_types": [
            {"name": name, "directed": name in ("hierarchy", "composition", "derivation"),
             "description": _RELATION_SEMANTICS[name]}
            for name in RELATION_TYPES
        ],
        "reference_rules": [
            {"name": name, "from": source, "to": target, "description": description}
            for name, source, target, description in _REFERENCE_RULES
        ],
    }


def build_tool_view(store: SemanticStore) -> Dict[str, Any]:
    """Describe the current Tool Layer from the real runtime/tool registry."""
    layer = SemanticLayer(store)
    tools = []
    for spec in TOOLS:
        schema = spec.get("inputSchema", {})
        required = set(schema.get("required", []))
        tools.append({
            "name": spec.get("name", ""),
            "description": spec.get("description", ""),
            "parameters": [
                f"{name}{'*' if name in required else ''}"
                for name in schema.get("properties", {})
            ],
        })
    return {"manifest": layer.manifest(), "tools": tools}


def load_evolution_metadata(root: PathLike, version: str) -> Dict[str, Any]:
    """Read lightweight evolution context from the latest ``evolution/run_N``."""
    root = Path(root)
    runs: List[tuple] = []
    evolution_dir = root / "evolution"
    if evolution_dir.is_dir():
        for child in evolution_dir.iterdir():
            match = _RUN_DIR_RE.match(child.name)
            if match and (child / "run.json").is_file():
                runs.append((int(match.group(1)), child))
    if not runs:
        return {"initial_build": True, "label": "Initial Build", "current_version": version}

    runs.sort(key=lambda item: item[0])
    run_dir = runs[-1][1]
    try:
        run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"initial_build": True, "label": "Initial Build", "current_version": version}
    if not isinstance(run, dict):
        return {"initial_build": True, "label": "Initial Build", "current_version": version}

    target_dimension = str(run.get("target_dimension", "") or "")
    changed_components = list(run.get("changed_components", []) or [])

    # Rounds may carry the per-round dimension/components recorded by the skill.
    rounds_path = run_dir / "rounds.jsonl"
    if rounds_path.is_file():
        try:
            lines = rounds_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            lines = []
        for line in reversed(lines):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict):
                continue
            metrics = entry.get("metrics") if isinstance(entry.get("metrics"), dict) else {}
            if not target_dimension:
                target_dimension = str(
                    entry.get("target_dimension") or metrics.get("target_dimension") or ""
                )
            if not changed_components:
                components = entry.get("changed_components") or metrics.get("changed_components")
                if isinstance(components, list):
                    changed_components = [str(item) for item in components]
            if target_dimension and changed_components:
                break

    return {
        "initial_build": False,
        "label": f"Evolution {run.get('run_id', '')}".strip(),
        "current_version": version,
        "run_id": str(run.get("run_id", "")),
        "parent_version": str(run.get("parent_version", "") or ""),
        "decision": str(run.get("status", "") or ""),
        "accepted_version": str(run.get("accepted_version", "") or ""),
        "target_dimension": target_dimension,
        "changed_components": changed_components,
        "hypothesis": str(run.get("current_hypothesis", "") or ""),
        "updated_at": str(run.get("updated_at", "") or ""),
    }


def render_html(data: Dict[str, Any]) -> str:
    """Inline Cytoscape.js, CSS, data, and interaction JS into one HTML file."""
    template = _read_package_text("template.html")
    cytoscape_js = _read_package_text(Path("vendor") / "cytoscape.min.js")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/")  # keep </script> safe inside JSON
    title = f"EvoOntology · {data['meta']['version']}"
    return (
        template
        .replace("__TITLE__", title)
        .replace("__CYTOSCAPE_JS__", cytoscape_js)
        .replace("__DATA_JSON__", payload)
    )


# ---- internals --------------------------------------------------------------


def _pairs(items) -> List[List[Any]]:
    """Build detail-panel rows, hiding absent fields."""
    pairs: List[List[Any]] = []
    for key, value in items:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, (list, tuple)):
            if not value:
                continue
            value = [str(item) for item in value]
        pairs.append([key, value])
    return pairs


def _read_package_text(relative: Union[str, Path]) -> str:
    return (_PACKAGE_DIR / relative).read_text(encoding="utf-8")
