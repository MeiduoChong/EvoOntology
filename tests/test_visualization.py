"""Focused tests for the read-only visualization module (Phase 1 plan §16)."""

import json
from pathlib import Path

import pytest

from evoontology import SemanticStore, ensure_workspace, save_project
from evoontology.visualization import visualize
from evoontology.visualization.renderer import (
    build_content_elements,
    build_schema_view,
    build_tool_view,
    load_evolution_metadata,
    resolve_version,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _project(mode: str) -> dict:
    project = {
        "schema_version": 1,
        "mode": mode,
        "data_source": "financial_database",
        "workload_source": "seed_workload",
        "evaluation": {"type": "llm_judge"} if mode == "rolling_trajectory"
        else {"type": "external_evaluator", "adapter": "bird"},
        "boundary": {"strategy": "rolling_trajectory"} if mode == "rolling_trajectory"
        else {"direction": "A_to_B", "evolution_split": "ev", "validation_split": "val"},
    }
    return project


def _records(broken: bool = False) -> dict:
    records = {
        "terms": [
            {"id": "labor_cost", "name": "Labor Cost", "type": "metric",
             "definition": "Employee-related operating expenses",
             "aliases": ["labour cost"], "evidence": ["evidence_001"]},
            {"id": "operating_cost", "name": "Operating Cost", "type": "metric",
             "definition": "All operating expenses"},
        ],
        "mappings": [
            {"id": "mapping_labor_cost", "term_id": "labor_cost",
             "database_source": "financial_database", "table": "expense_statement",
             "column": "labor_expense", "aggregation_semantics": "sum of labor expenses",
             "grain": "annual", "evidence_refs": ["evidence_001"]},
        ],
        "relations": [
            {"id": "rel_cost_composition", "source": "operating_cost",
             "relation_type": "composition", "target": "labor_cost",
             "connection_condition": "labor expense is part of operating cost"},
        ],
        "constraints": [
            {"id": "constraint_annual", "target": "labor_cost",
             "constraint_type": "scope", "severity": "warning",
             "trigger_keywords": ["annual"], "description": "Use annual grain"},
        ],
        "evidence": [
            {"id": "evidence_001", "source": "financial_database",
             "query": "SELECT DISTINCT category FROM expenses",
             "result": "labor_expense exists", "validation_method": "schema verification"},
        ],
    }
    if broken:
        records["relations"].append(
            {"id": "rel_broken", "source": "labor_cost", "relation_type": "association",
             "target": "missing_term"}
        )
        records["mappings"].append(
            {"id": "mapping_orphan", "term_id": "missing_term", "table": "ghost_table"}
        )
        records["constraints"].append(
            {"id": "constraint_orphan", "target": "missing_term", "constraint_type": "unit"}
        )
        records["terms"][1]["evidence"] = ["missing_evidence"]
    return records


@pytest.fixture
def workspace(tmp_path):
    ws = ensure_workspace(tmp_path)
    save_project(_project("fixed_split"), ws)
    SemanticStore.save_version(ws, "semantic_v0", _records())
    SemanticStore.set_active(ws, "semantic_v0")
    return ws


# ---- 1. minimal Content conversion -----------------------------------------

def test_minimal_content_conversion(workspace):
    content = build_content_elements(SemanticStore.load(workspace))
    families = {node["data"]["family"] for node in content["nodes"]}
    assert families == {"term", "mapping", "constraint", "evidence"}

    edges = {edge["data"].get("kind") or edge["data"].get("relation_type")
             for edge in content["edges"]}
    assert {"composition", "grounded_by", "constrained_by", "supported_by"} <= edges
    assert not content["warnings"]


# ---- 2. Relation records render as edges, not nodes ------------------------

def test_relation_records_render_as_edges_not_nodes(workspace):
    store = SemanticStore.load(workspace)
    content = build_content_elements(store)
    node_ids = {node["data"]["id"] for node in content["nodes"]}
    for relation_id in store.relations:
        assert relation_id not in node_ids
    relation_edges = [edge["data"] for edge in content["edges"]
                       if edge["data"]["family"] == "relation"]
    assert [edge["record_id"] for edge in relation_edges] == list(store.relations)


# ---- 3. Mapping grounding creates no virtual nodes -------------------------

def test_mapping_grounding_creates_no_virtual_nodes(workspace):
    store = SemanticStore.load(workspace)
    content = build_content_elements(store)
    record_ids = set(store.terms) | set(store.mappings) | set(store.constraints) | set(store.evidence)
    for node in content["nodes"]:
        assert node["data"]["record_id"] in record_ids
    for virtual in ("expense_statement", "labor_expense", "financial_database"):
        assert virtual not in {node["data"]["record_id"] for node in content["nodes"]}


# ---- broken references: warn, never fabricate -------------------------------

def test_broken_references_warn_without_fabricating(tmp_path):
    ws = ensure_workspace(tmp_path)
    save_project(_project("fixed_split"), ws)
    SemanticStore.save_version(ws, "semantic_v0", _records(broken=True))
    SemanticStore.set_active(ws, "semantic_v0")

    content = build_content_elements(SemanticStore.load(ws))
    assert len(content["warnings"]) >= 4
    assert any("rel_broken" in warning for warning in content["warnings"])

    node_ids = {node["data"]["id"] for node in content["nodes"]}
    for edge in content["edges"]:
        assert edge["data"]["source"] in node_ids
        assert edge["data"]["target"] in node_ids
    assert "missing_term" not in node_ids


# ---- 4/5. version resolution ------------------------------------------------

def test_active_version_resolves_active_json(workspace):
    assert resolve_version(workspace, "active") == "semantic_v0"
    output = visualize(workspace=workspace, open_browser=False)
    assert output == workspace / "visualizations" / "semantic_v0.html"
    assert output.is_file()


def test_explicit_version_renders_without_changing_active(workspace):
    SemanticStore.save_version(workspace, "semantic_v1", _records())
    active_before = json.loads((workspace / "active.json").read_text(encoding="utf-8"))

    output = visualize(workspace=workspace, version="semantic_v1", open_browser=False)

    assert output.name == "semantic_v1.html"
    assert output.is_file()
    active_after = json.loads((workspace / "active.json").read_text(encoding="utf-8"))
    assert active_after == active_before == {"active_version": "semantic_v0"}


# ---- 6. generated HTML is offline and self-contained ------------------------

def test_generated_html_is_offline(workspace):
    html = visualize(workspace=workspace, open_browser=False).read_text(encoding="utf-8")
    assert "Copyright (c) 2016-2024, The Cytoscape Consortium." in html
    assert "3.30.2" in html
    assert "Labor Cost" in html and "mapping_labor_cost" in html
    assert "window.EVO_DATA" in html
    for marker in ("<script src", "cdn.jsdelivr", "unpkg.com", "cdnjs."):
        assert marker not in html


# ---- 7. initial build without evolution history -----------------------------

def test_initial_build_without_evolution_renders(workspace):
    metadata = load_evolution_metadata(workspace, "semantic_v0")
    assert metadata["initial_build"] is True
    assert metadata["label"] == "Initial Build"
    html = visualize(workspace=workspace, open_browser=False).read_text(encoding="utf-8")
    assert "Initial Build" in html


# ---- 8. both project modes render -------------------------------------------

def test_fixed_split_and_rolling_trajectory_both_render(tmp_path):
    for index, mode in enumerate(("fixed_split", "rolling_trajectory")):
        ws = ensure_workspace(tmp_path / mode)
        save_project(_project(mode), ws)
        SemanticStore.save_version(ws, "semantic_v0", _records())
        SemanticStore.set_active(ws, "semantic_v0")
        output = visualize(workspace=ws, open_browser=False)
        assert output.is_file(), f"{mode} failed to render"
        assert "Labor Cost" in output.read_text(encoding="utf-8")


# ---- evolution metadata ------------------------------------------------------

def test_evolution_metadata_from_run_records(workspace):
    run_dir = workspace / "evolution" / "run_1"
    run_dir.mkdir(parents=True)
    (run_dir / "run.json").write_text(json.dumps({
        "schema_version": 1, "run_id": "run_1", "status": "accepted",
        "parent_version": "semantic_v0", "accepted_version": "semantic_v1",
        "current_hypothesis": "improve cost composition coverage",
        "updated_at": "2026-08-01T00:00:00+00:00",
    }), encoding="utf-8")
    (run_dir / "rounds.jsonl").write_text(json.dumps({
        "round": 1, "decision": "reject", "target_dimension": "content",
        "changed_components": ["semantic content"], "metrics": {},
    }) + "\n", encoding="utf-8")

    metadata = load_evolution_metadata(workspace, "semantic_v1")
    assert metadata["initial_build"] is False
    assert metadata["parent_version"] == "semantic_v0"
    assert metadata["decision"] == "accepted"
    assert metadata["target_dimension"] == "content"
    assert metadata["changed_components"] == ["semantic content"]


# ---- schema / tool views ------------------------------------------------------

def test_schema_view_reflects_core_model():
    schema = build_schema_view()
    names = [object_type["name"] for object_type in schema["object_types"]]
    assert names == ["Term", "Mapping", "Constraint", "Evidence"]
    term_fields = next(t["fields"] for t in schema["object_types"] if t["name"] == "Term")
    assert {"id", "name", "type", "definition", "scope", "aliases"} <= set(term_fields)
    assert [r["name"] for r in schema["relation_types"]] == [
        "association", "hierarchy", "composition", "equivalence", "derivation"]
    assert {rule["name"] for rule in schema["reference_rules"]} == {
        "grounded_by", "constrained_by", "supported_by"}
    assert "source" in schema["relation_record"]["fields"]


def test_tool_view_uses_real_registry(workspace):
    tools = build_tool_view(SemanticStore.load(workspace))
    assert [tool["name"] for tool in tools["tools"]] == [
        "browse_semantics", "resolve_semantics"]
    assert all(tool["description"] for tool in tools["tools"])
    assert "Semantic layer version: semantic_v0" in tools["manifest"]


# ---- plugin smoke test ---------------------------------------------------------

def test_plugin_entry_points_call_same_core_api():
    claude_command = REPO_ROOT / "plugins" / "claude-code" / "commands" / "evo-visualize.md"
    codex_skill = (REPO_ROOT / "plugins" / "evoontology-codex" /
                   "skills" / "evo-visualize" / "SKILL.md")
    assert claude_command.is_file() and codex_skill.is_file()

    claude_text = claude_command.read_text(encoding="utf-8")
    codex_text = codex_skill.read_text(encoding="utf-8")
    invocation = "python -m evoontology.visualization"
    assert invocation in claude_text, "Claude command must call Core visualize()"
    assert invocation in codex_text, "Codex skill must call Core visualize()"
    assert "name: evo-visualize" in codex_text


# ---- read-only guarantee --------------------------------------------------------

def test_visualize_is_read_only(workspace):
    def snapshot():
        state = {}
        for path in sorted(workspace.rglob("*")):
            if path.is_file() and "visualizations" not in path.parts:
                state[path.relative_to(workspace).as_posix()] = path.read_bytes()
        return state

    before = snapshot()
    visualize(workspace=workspace, open_browser=False)
    visualize(workspace=workspace, version="semantic_v0", open_browser=False)
    assert snapshot() == before


# ---- error behavior --------------------------------------------------------------

def test_missing_workspace_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="workspace not initialized"):
        visualize(workspace=tmp_path / "nowhere", open_browser=False)


def test_missing_active_version_error(tmp_path):
    ws = ensure_workspace(tmp_path)
    save_project(_project("fixed_split"), ws)
    SemanticStore.save_version(ws, "semantic_v0", _records())
    with pytest.raises(FileNotFoundError, match="No active ontology version"):
        visualize(workspace=ws, open_browser=False)


def test_missing_explicit_version_error(workspace):
    with pytest.raises(FileNotFoundError, match="Ontology version 'semantic_v9' not found"):
        visualize(workspace=workspace, version="semantic_v9", open_browser=False)
    assert not (workspace / "visualizations" / "semantic_v9.html").exists()
