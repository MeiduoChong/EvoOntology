"""Core store tests: save / load / active version / candidate publish / rollback."""

import json

import pytest

from evoontology import SemanticStore, ensure_workspace

SAMPLE = {
    "terms": [{"id": "t1", "name": "net_income", "type": "metric", "definition": "net income"}],
    "mappings": [{"id": "m1", "term_id": "t1", "table": "financials", "column": "net_income"}],
    "relations": [],
    "constraints": [{"id": "c1", "target": "t1", "severity": "warn", "description": "exclude refunds"}],
    "evidence": [{"id": "e1", "source": "schema", "query": "PRAGMA table_info(financials)"}],
}


def _write_v0(root):
    SemanticStore.save_version(str(root), "semantic_v0", SAMPLE)
    SemanticStore.set_active(str(root), "semantic_v0")


def test_save_load_roundtrip(tmp_path):
    ensure_workspace(str(tmp_path))
    _write_v0(tmp_path)
    store = SemanticStore.load(str(tmp_path))
    assert store.version == "semantic_v0"
    assert store.counts() == {
        "terms": 1, "mappings": 1, "relations": 0, "constraints": 1, "evidence": 1,
    }
    assert store.terms["t1"].name == "net_income"
    assert store.mappings["m1"].table == "financials"


def test_active_version(tmp_path):
    ensure_workspace(str(tmp_path))
    _write_v0(tmp_path)
    assert SemanticStore.active_version(str(tmp_path)) == "semantic_v0"


def test_legacy_version_field(tmp_path):
    ensure_workspace(str(tmp_path))
    _write_v0(tmp_path)
    # rewrite active.json using the legacy "version" field
    (tmp_path / "active.json").write_text(json.dumps({"version": "semantic_v0"}), encoding="utf-8")
    assert SemanticStore.active_version(str(tmp_path)) == "semantic_v0"


def test_candidate_publish_and_promote(tmp_path):
    ensure_workspace(str(tmp_path))
    _write_v0(tmp_path)

    candidate = {k: v for k, v in SAMPLE.items()}
    candidate["terms"] = SAMPLE["terms"] + [{"id": "t2", "name": "gross_margin", "type": "metric"}]
    SemanticStore.save_version(str(tmp_path), "v0-c1", candidate)

    # before promote, active is still parent
    assert SemanticStore.active_version(str(tmp_path)) == "semantic_v0"

    new_version = SemanticStore.promote(str(tmp_path), "v0-c1", "semantic_v1")
    assert new_version == "semantic_v1"
    assert SemanticStore.active_version(str(tmp_path)) == "semantic_v1"
    store = SemanticStore.load(str(tmp_path))
    assert "t2" in store.terms


def test_rollback_keeps_parent(tmp_path):
    ensure_workspace(str(tmp_path))
    _write_v0(tmp_path)

    candidate = {k: v for k, v in SAMPLE.items()}
    candidate["terms"] = SAMPLE["terms"] + [{"id": "t3", "name": "bad", "type": "metric"}]
    SemanticStore.save_version(str(tmp_path), "v0-c1", candidate)

    # reject = simply do not promote; active.json stays at parent
    assert SemanticStore.active_version(str(tmp_path)) == "semantic_v0"
    store = SemanticStore.load(str(tmp_path))
    assert "t3" not in store.terms


def test_list_versions(tmp_path):
    ensure_workspace(str(tmp_path))
    _write_v0(tmp_path)
    SemanticStore.save_version(str(tmp_path), "v0-c1", SAMPLE)
    assert SemanticStore.list_versions(str(tmp_path)) == ["semantic_v0", "v0-c1"]


def test_missing_active_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        SemanticStore.load(str(tmp_path))
