"""Runtime tests: browse / resolve / manifest, including the uninitialized case."""

from evoontology import SemanticLayer, SemanticStore, ensure_workspace

SAMPLE = {
    "terms": [
        {"id": "t1", "name": "net_income", "type": "metric", "definition": "net income", "aliases": ["profit"]},
        {"id": "t2", "name": "region", "type": "dimension", "definition": "sales region"},
    ],
    "mappings": [
        {"id": "m1", "term_id": "t1", "table": "financials", "column": "net_income"},
        {"id": "m2", "term_id": "t2", "table": "sales", "column": "region"},
    ],
    "relations": [{"id": "r1", "source": "t2", "target": "t1", "relation_type": "derivation"}],
    "constraints": [{"id": "c1", "target": "t1", "severity": "warn", "description": "exclude refunds"}],
    "evidence": [{"id": "e1", "source": "schema", "query": "PRAGMA table_info(financials)"}],
}


def _init(tmp_path):
    ensure_workspace(str(tmp_path))
    SemanticStore.save_version(str(tmp_path), "semantic_v0", SAMPLE)
    SemanticStore.set_active(str(tmp_path), "semantic_v0")


def test_manifest(tmp_path):
    _init(tmp_path)
    layer = SemanticLayer.load(str(tmp_path))
    manifest = layer.manifest()
    assert "semantic_v0" in manifest
    assert "browse_semantics" in manifest
    assert "resolve_semantics" in manifest


def test_browse(tmp_path):
    _init(tmp_path)
    layer = SemanticLayer.load(str(tmp_path))
    result = layer.browse(query="net income", kind="term")
    assert result["status"] == "ok"
    assert result["matched_total"] == 1
    assert result["items"][0]["name"] == "net_income"


def test_browse_needs_query(tmp_path):
    _init(tmp_path)
    layer = SemanticLayer.load(str(tmp_path))
    result = layer.browse(query="")
    assert result["status"] == "needs_query"


def test_resolve(tmp_path):
    _init(tmp_path)
    layer = SemanticLayer.load(str(tmp_path))
    result = layer.resolve(mentions=["net_income"])
    assert result["results"][0]["status"] == "resolved"
    resolved = result["results"][0]
    assert resolved["term"]["name"] == "net_income"
    assert len(resolved["mappings"]) == 1
    assert len(resolved["constraints"]) == 1


def test_resolve_unresolved(tmp_path):
    _init(tmp_path)
    layer = SemanticLayer.load(str(tmp_path))
    result = layer.resolve(mentions=["nonexistent"])
    assert result["results"][0]["status"] == "unresolved"


def test_uninitialized(tmp_path):
    layer = SemanticLayer.load(str(tmp_path))
    assert layer.version == "uninitialized"
    assert "uninitialized" in layer.manifest()
    assert layer.browse(query="x")["status"] == "ok"
    assert layer.browse(query="x")["items"] == []


def test_execute_dispatch(tmp_path):
    _init(tmp_path)
    layer = SemanticLayer.load(str(tmp_path))
    result = layer.execute("browse_semantics", {"query": "region", "kind": "term"})
    assert result["matched_total"] == 1
