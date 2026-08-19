"""Benchmark-independent semantic runtime.

``SemanticLayer`` exposes the two paper-defined operations over a loaded
:class:`SemanticStore`: ``browse_semantics`` and ``resolve_semantics``, plus a
``manifest`` describing the active version and how to use the tools.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from ..ontology.store import SemanticStore

_ACTIVE_STATES = {"validated", "active"}
_DEFAULT_TOOLS = ["browse_semantics", "resolve_semantics"]
_MAX_BROWSE_ITEMS = 6
_MAX_RESOLVE = 5


def _tokens(text: str) -> set:
    return set(re.findall(r"\w+", str(text).lower(), flags=re.UNICODE))


def _is_active(item: Any) -> bool:
    return getattr(item, "lifecycle_state", "active") in _ACTIVE_STATES


class SemanticLayer:
    """Read-only view of the active semantic version."""

    def __init__(self, store: SemanticStore):
        self.store = store

    @classmethod
    def load(cls, store_path: str) -> "SemanticLayer":
        try:
            store = SemanticStore.load(store_path)
        except FileNotFoundError:
            store = cls._empty_store()
        return cls(store)

    @staticmethod
    def _empty_store() -> SemanticStore:
        return SemanticStore(
            version="uninitialized",
            terms={},
            relations={},
            mappings={},
            constraints={},
            evidence={},
            root_dir="",
        )

    @property
    def version(self) -> str:
        return self.store.version

    # ---- manifest ----------------------------------------------------------

    def manifest(self, exposed_tools: Optional[List[str]] = None) -> str:
        if self.store.version == "uninitialized":
            return (
                "Semantic layer: uninitialized.\n\n"
                "No ontology has been built for this workspace yet. Run "
                "/evo-build to create the initial semantic version."
            )
        counts = self.store.counts()
        active_constraints = [
            c for c in self.store.constraints.values() if _is_active(c)
        ]
        by_severity: Dict[str, int] = {}
        for c in active_constraints:
            by_severity[c.severity] = by_severity.get(c.severity, 0) + 1
        severity_summary = ", ".join(
            f"{sev}={count}" for sev, count in sorted(by_severity.items())
        )

        exposed = set(exposed_tools or _DEFAULT_TOOLS)
        tool_lines = []
        if "browse_semantics" in exposed:
            tool_lines.append(
                "- **browse_semantics**(query, kind, limit) — find up to 6 catalog "
                "items relevant to a specific analytical need."
            )
        if "resolve_semantics" in exposed:
            tool_lines.append(
                "- **resolve_semantics**(mentions, context) — resolve up to 5 concepts "
                "to grounded mappings, relations, constraints, and evidence."
            )

        lines = [
            f"Semantic layer version: {self.version}",
            f"Objects: {counts['terms']} terms, {counts['mappings']} mappings, "
            f"{counts['relations']} relations, {counts['constraints']} constraints, "
            f"{counts['evidence']} evidence records.",
            f"Active constraints: {len(active_constraints)}"
            + (f" ({severity_summary})" if severity_summary else ""),
            "",
            "## Semantic MCP Tools",
            f"Semantic Tools ({len(tool_lines)} available)",
            "",
            "These tools are bounded navigation aids. Use them to ground analytical "
            "concepts before querying the underlying data.",
            "",
            *tool_lines,
            "",
            "### When to use semantic tools",
            "- Call resolve_semantics with the concepts you plan to use; it returns the "
            "corresponding tables, columns, constraints, and supporting evidence.",
            "- Use browse_semantics only when you need to discover what concepts are "
            "available.",
            "- Resolved mappings are guidance, not final answers — always validate "
            "against the actual data with your native query tools.",
        ]
        return "\n".join(lines)

    # ---- browse_semantics --------------------------------------------------

    def browse(self, query: str = "", kind: str = "term", limit: int = 6) -> Dict[str, Any]:
        query = str(query or "").strip().lower()
        kind = str(kind).lower()
        if kind not in ("term", "mapping", "relation", "constraint", "all"):
            kind = "term"
        limit = max(1, min(int(limit or _MAX_BROWSE_ITEMS), _MAX_BROWSE_ITEMS))

        items: List[Dict[str, Any]] = []
        if kind in ("term", "all"):
            items.extend(
                self._browse_view(item, "term")
                for item in self.store.terms.values() if _is_active(item)
            )
        if kind in ("mapping", "all"):
            items.extend(
                self._browse_view(item, "mapping")
                for item in self.store.mappings.values() if _is_active(item)
            )
        if kind in ("relation", "all"):
            items.extend(
                self._browse_view(item, "relation")
                for item in self.store.relations.values() if _is_active(item)
            )
        if kind in ("constraint", "all"):
            items.extend(
                self._browse_view(item, "constraint")
                for item in self.store.constraints.values() if _is_active(item)
            )

        catalog_total = len(items)
        if not query:
            return {
                "status": "needs_query",
                "items": [],
                "catalog_total": catalog_total,
                "version": self.version,
                "note": "Provide a specific query. Full-catalog enumeration is disabled.",
            }

        query_tokens = _tokens(query)
        ranked = []
        for item in items:
            search_text = item.pop("_search_text", "")
            overlap = sorted(query_tokens & _tokens(search_text))
            phrase_match = query in search_text.lower()
            if not overlap and not phrase_match:
                continue
            score = (2 if phrase_match else 0) + len(overlap)
            item["match_rationale"] = {
                "phrase_match": phrase_match,
                "overlap_tokens": overlap,
            }
            ranked.append((score, item))
        ranked.sort(key=lambda pair: (-pair[0], pair[1]["id"]))

        return {
            "status": "ok",
            "items": [item for _, item in ranked[:limit]],
            "matched_total": len(ranked),
            "catalog_total": catalog_total,
            "version": self.version,
            "note": "Only query-relevant items are returned; this is not an analysis checklist.",
        }

    @staticmethod
    def _browse_view(item: Any, kind: str) -> dict:
        name = getattr(item, "name", "") or ""
        if not name and kind == "mapping":
            name = f"{getattr(item, 'term_id', '')} -> {getattr(item, 'table', '')}"
        return {
            "id": item.id,
            "name": name,
            "type": getattr(item, "type", kind),
            "scope": getattr(item, "scope", ""),
            "availability": getattr(item, "lifecycle_state", "active"),
            "_search_text": " ".join(
                filter(
                    None,
                    [
                        name,
                        str(getattr(item, "definition", "") or ""),
                        " ".join(getattr(item, "aliases", []) or []),
                        str(getattr(item, "term_id", "") or ""),
                    ],
                )
            ),
        }

    # ---- resolve_semantics -------------------------------------------------

    def resolve(self, mentions: Optional[List[str]] = None,
                context: Optional[str] = None) -> Dict[str, Any]:
        mentions = [str(m).strip().lower() for m in (mentions or []) if str(m).strip()]
        accepted = mentions[:_MAX_RESOLVE]
        skipped = mentions[_MAX_RESOLVE:]

        results = []
        for mention in accepted:
            candidates = self._match_mention(mention)
            if not candidates:
                results.append({
                    "query": mention,
                    "query_type": "mention",
                    "status": "unresolved",
                    "match_rationale": f"No active term matching '{mention}'. Inspect the data directly.",
                    "candidates": [],
                })
            elif len(candidates) == 1:
                item, rationale = candidates[0]
                results.append(self._build_resolve_result(mention, item, rationale, "resolved"))
            else:
                results.append({
                    "query": mention,
                    "query_type": "mention",
                    "status": "ambiguous",
                    "match_rationale": f"{len(candidates)} terms match '{mention}'",
                    "candidates": [
                        self._build_resolve_result(mention, item, rationale, "ambiguous")
                        for item, rationale in candidates
                    ],
                })

        for result in results:
            if result.get("status") == "unresolved":
                result["coverage_status"] = "unavailable"
            elif result.get("status") == "ambiguous":
                result["coverage_status"] = "partial"
            elif result.get("mappings") or result.get("relations") or result.get("constraints"):
                result["coverage_status"] = "supported"
            else:
                result["coverage_status"] = "partial"

        return {
            "status": "partial" if skipped else "ok",
            "results": results,
            "requested_count": len(mentions),
            "processed_count": len(accepted),
            "skipped": [{"query_type": "mention", "query": value} for value in skipped],
            "version": self.version,
            "note": (
                "Resolve is limited to 5 relevant concepts."
                if skipped else "Use these mappings only for the current analysis need."
            ),
        }

    def _match_mention(self, mention: str) -> List[tuple]:
        exact_name: List[tuple] = []
        exact_alias: List[tuple] = []
        substring: List[tuple] = []

        for term in self.store.terms.values():
            if not _is_active(term):
                continue
            name_lower = term.name.lower()
            if mention == name_lower:
                exact_name.append((term, f"exact name match: '{term.name}'"))
            elif any(mention == a.lower() for a in (term.aliases or [])):
                exact_alias.append((term, f"exact alias match: term '{term.name}'"))
            elif mention in name_lower or any(mention in a.lower() for a in (term.aliases or [])):
                substring.append((term, f"substring match: term '{term.name}'"))

        if exact_name:
            return exact_name
        if exact_alias:
            return exact_alias
        return substring

    def _build_resolve_result(self, query: str, item: Any, rationale: str,
                              status: str) -> dict:
        term_id = item.id
        result: Dict[str, Any] = {
            "query": query,
            "query_type": "mention",
            "status": status,
            "match_rationale": rationale,
            "term": {
                "id": item.id,
                "type": getattr(item, "type", ""),
                "name": getattr(item, "name", ""),
                "aliases": list(getattr(item, "aliases", [])),
                "definition": getattr(item, "definition", ""),
                "scope": getattr(item, "scope", ""),
                "evidence_refs": list(getattr(item, "evidence_refs", [])),
            },
        }

        mappings = [
            {
                "id": m.id,
                "term_id": m.term_id,
                "table": m.table,
                "column": m.column,
                "semantic_filter": m.semantic_filter,
                "aggregation_semantics": m.aggregation_semantics,
                "grain": m.grain,
                "evidence_refs": list(m.evidence_refs),
            }
            for m in self.store.mappings.values()
            if _is_active(m) and m.term_id == term_id
        ]
        if mappings:
            result["mappings"] = mappings

        relations = [
            {
                "id": r.id,
                "relation_type": r.relation_type,
                "source": r.source,
                "target": r.target,
                "connection_condition": r.connection_condition or "",
                "evidence_refs": list(r.evidence_refs),
            }
            for r in self.store.relations.values()
            if _is_active(r) and (r.source == term_id or r.target == term_id)
        ]
        if relations:
            result["relations"] = relations

        constraints = [
            {
                "id": c.id,
                "severity": c.severity,
                "description": c.description or "",
                "evidence_refs": list(c.evidence_refs),
            }
            for c in self.store.constraints.values()
            if _is_active(c) and c.target == term_id
        ]
        if constraints:
            result["constraints"] = constraints

        return result

    # ---- dispatch ----------------------------------------------------------

    def execute(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "browse_semantics":
            return self.browse(
                query=arguments.get("query", ""),
                kind=arguments.get("kind", "term"),
                limit=arguments.get("limit", _MAX_BROWSE_ITEMS),
            )
        if name == "resolve_semantics":
            return self.resolve(
                mentions=arguments.get("mentions"),
                context=arguments.get("context"),
            )
        raise ValueError(f"Unknown semantic tool: {name}")
