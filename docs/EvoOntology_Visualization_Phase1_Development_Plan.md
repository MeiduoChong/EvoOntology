# EvoOntology Visualization — Phase 1 Development Plan

## Goal

Add a lightweight, read-only ontology visualization capability to EvoOntology.

User-facing entry points:

```text
Claude Code: /evo-visualize
Codex:       $evo-visualize
```

The visualization must:

- reflect EvoOntology's three layers: **Content / Schema / Tool**;
- use **Cytoscape.js** for the Content graph;
- generate a local, standalone interactive HTML file;
- work offline;
- reuse the existing EvoOntology Core, workspace, store, schema, and plugin structure;
- not modify Build, Evolve, Runtime, ontology state, or evolution state.

Do not introduce React, Node/Vite, Web Server, Graph DB, or additional layout frameworks.

---

## 1. Architecture

Implement visualization as a read-only Core capability:

```text
Ontology Version
    ↓
visualization/renderer.py
    ↓
Content / Schema / Tool render data
    ↓
template.html
    ↓
Standalone HTML
```

Recommended Core structure:

```text
evoontology/
└── visualization/
    ├── __init__.py
    ├── renderer.py
    ├── template.html
    └── vendor/
        ├── cytoscape.min.js
        └── LICENSE.cytoscape.txt
```

Adapt the path to the existing package layout. Do not create a parallel Core package.

Output:

```text
.evoontology/
└── visualizations/
    └── semantic_vN.html
```

Regenerating the same version overwrites the existing HTML.

---

## 2. Core API

Expose one shared API:

```python
visualize(
    workspace=None,
    version="active",
    open_browser=True
) -> Path
```

Behavior:

```text
resolve workspace
→ resolve ontology version
→ load ontology state
→ build visualization data
→ render standalone HTML
→ save HTML
→ optionally open browser
→ return output path
```

Version rules:

- `version="active"`: read the version referenced by `active.json`.
- Explicit `semantic_vN`: render that version without changing `active.json`.

Claude Code and Codex must call this same API.

---

## 3. Content View

Content is the primary visualization and uses Cytoscape.js.

The graph must reflect the current EvoOntology Content Layer:

### Node families

- Term
- Mapping
- Constraint
- Evidence

### Edge families

- Semantic Relation
- Structural Reference

Do not create new ontology object types such as DataElement, TableNode, or ColumnNode.

### Rendering rules

```text
Term
→ primary Cytoscape node

Mapping
→ secondary Cytoscape node

Constraint
→ lightweight Cytoscape node

Evidence
→ lightweight Cytoscape node

Relation record
→ Semantic Relation edge between Terms

schema-defined object references
→ Structural Reference edges
```

Grounding information such as tables, columns, files, and linking paths remains inside Mapping details; it must not be converted into new ontology nodes.

All references must be derived from the current schema/store representation. Do not infer nonexistent edges.

---

## 4. Content Visual Style

Use a restrained, product-style visual design.

### Nodes

**Term**
- largest node;
- rounded rectangle;
- soft blue styling.

**Mapping**
- medium node;
- rounded rectangle;
- soft green/teal styling.

**Constraint**
- smaller node;
- soft orange styling.

**Evidence**
- smaller node;
- soft purple/gray styling.

Use low-saturation colors, readable text, thin borders, and no gradients/glow/3D effects.

### Semantic Relations

Support the relation types defined by the current schema, including:

```text
association
hierarchy
composition
equivalence
derivation
```

Use a consistent color family and distinguish relation types mainly with line style, arrow style where semantically valid, and labels.

Do not assume every relation is directed; follow the actual schema/record semantics.

### Structural References

Use thin gray lines with lower visual weight than Semantic Relations.

Reference labels may remain hidden by default and appear when selected.

---

## 5. Layout

Use Cytoscape.js built-in `cose` layout only.

Recommended behavior:

```text
name: cose
animate: false
fit after initial render
use reasonable padding
```

Do not add fCoSE, ELK, Dagre, or other layout extensions in Phase 1.

---

## 6. Page Layout

Use one standalone page:

```text
┌─────────────────────────────────────────────────────┐
│ EvoOntology · semantic_vN · Active                 │
│ Parent · Last Evolution Dimension        Search    │
├─────────────────────────────────────────────────────┤
│ [ Content ]   [ Schema ]   [ Tool ]                │
├──────────────────────────────────┬──────────────────┤
│                                  │                  │
│        Content Graph             │  Detail Panel    │
│                                  │                  │
└──────────────────────────────────┴──────────────────┘
│ Filters                     Fit · Reset · Export    │
└─────────────────────────────────────────────────────┘
```

Default tab: `Content`.

Use plain HTML/CSS/Vanilla JS for the page shell.

---

## 7. Content Interactions

Implement only the following:

### Search

Search Term and Mapping by:

- label/name;
- identifier.

On match:

```text
select
→ center
→ highlight
```

### Node click

- select the node;
- highlight first-degree neighbors;
- reduce opacity of unrelated elements;
- show object details in the right panel.

### Edge click

Show relation/reference details in the right panel.

### Reset

Clear selection and restore the full graph.

### Fit

Fit the full graph into the viewport.

### Native graph interaction

Keep Cytoscape's normal:

- zoom;
- pan;
- drag.

### Filters

Provide simple checkboxes:

```text
Objects
[x] Terms
[x] Mappings
[x] Constraints
[x] Evidence

Relations
[x] Association
[x] Hierarchy
[x] Composition
[x] Equivalence
[x] Derivation
```

Do not add a complex filter sidebar.

### Export PNG

Use Cytoscape.js PNG export to export the full graph.

---

## 8. Detail Panel

Render actual schema-defined fields only.

Do not define a second visualization-specific ontology schema.

Examples:

### Term

```text
Name
ID
Definition
Aliases
Mappings
Relations
Constraints
Evidence
```

### Mapping

```text
ID
Related Term
Grounding
Data source
Field/path information
Scope/conditions
Evidence
```

The exact fields must come from the current `semantic-schema.md` / Core model.

Hide fields that are absent.

---

## 9. Schema View

Schema View uses normal HTML, not a force graph.

Display the current Schema Layer as:

```text
Object Types
[Term] [Mapping] [Constraint] [Evidence]

Relation Types
association
hierarchy
composition
equivalence
derivation

Reference Rules
<actual schema-defined reference patterns>
```

Clicking an object type should show its current schema fields in the Detail Panel.

If the current product does not persist Schema as a separate versioned artifact, read the current schema definition used by Core. Do not add new schema persistence only for visualization.

---

## 10. Tool View

Tool View also uses normal HTML.

Display the current Tool Layer from the actual runtime/tool registry.

At minimum, if present in the current implementation, show:

```text
Manifest
browse / browse_semantics
resolve / resolve_semantics
```

Use the real tool names and descriptions from the current implementation.

Do not hard-code tools that do not exist.

The view should allow future tools to appear through the same metadata structure without redesigning the page.

---

## 11. Evolution Metadata

Show lightweight evolution context at the top of the page when available:

```text
Current Version
Parent Version
Target Dimension
Decision
Changed Components
```

Read from the current evolution record, using the existing fields such as:

```text
target_dimension
changed_components
decision
parent_version
```

For the initial ontology with no evolution record, display:

```text
Initial Build
```

Do not implement version-diff graphs, animations, or performance dashboards in Phase 1.

---

## 12. Renderer Responsibilities

Keep `renderer.py` small and deterministic.

Suggested functions:

```python
resolve_version()
load_ontology()
build_content_elements()
build_schema_view()
build_tool_view()
load_evolution_metadata()
render_html()
```

Render-time data may use a simple dictionary:

```python
{
    "content": {
        "nodes": [],
        "edges": []
    },
    "schema": {},
    "tools": [],
    "evolution": {}
}
```

Do not persist this render model back into the ontology store.

---

## 13. Cytoscape.js Packaging

Use a stable, pinned Cytoscape.js version.

Requirements:

- no CDN dependency;
- package `cytoscape.min.js` with EvoOntology;
- retain its license notice;
- ensure package assets are included by the project's existing Python build configuration;
- inline Cytoscape.js, CSS, visualization data, and interaction JS into the generated HTML.

The final `semantic_vN.html` must open offline as a single file.

---

## 14. Plugin Integration

### Claude Code

Add:

```text
/evo-visualize
```

Default:

```text
/evo-visualize
→ visualize active ontology
→ generate HTML
→ open browser when supported
→ return output path
```

Optional version:

```text
/evo-visualize semantic_v2
```

This renders `semantic_v2` without changing the active version.

The command must call Core `visualize()` and must not contain rendering logic.

### Codex

Add bundled Skill:

```text
skills/
└── evo-visualize/
    └── SKILL.md
```

Metadata:

```yaml
---
name: evo-visualize
description: Visualize the current EvoOntology ontology state as an interactive local graph.
---
```

Primary invocation:

```text
$evo-visualize
```

The Skill only:

```text
resolve workspace
→ resolve requested version
→ call Core visualize()
→ return generated path
→ open browser when supported
```

Do not implement HTML generation inside the Skill.

---

## 15. Error Behavior

Keep errors minimal and explicit:

```text
No workspace
→ EvoOntology workspace not initialized.

No active version
→ No active ontology version.

Requested version missing
→ Ontology version '<version>' not found.

Broken reference
→ report warning; do not fabricate graph objects.
```

Visualization failure must not modify project state.

---

## 16. Tests

Add focused tests only.

### Core

1. Minimal Content conversion:
   - Term;
   - Mapping;
   - Constraint;
   - Evidence;
   - Relation;
   - Structural References.

2. Relation records render as edges, not nodes.

3. Mapping grounding does not create virtual ontology nodes.

4. `version="active"` resolves `active.json`.

5. Explicit version renders without modifying `active.json`.

6. Generated HTML:
   - contains Cytoscape runtime;
   - contains visualization data;
   - has no CDN dependency.

7. Initial build without evolution history still renders.

8. Fixed-Split and Rolling-Trajectory projects both render; visualization must not depend on evaluator/GT/validation data.

### Plugin smoke test

Verify both:

```text
/evo-visualize
$evo-visualize
```

reach the same Core `visualize()` implementation.

---

## 17. Acceptance Criteria

Phase 1 is complete when:

- `/evo-visualize` works in Claude Code;
- `$evo-visualize` works in Codex;
- active or explicitly requested ontology versions can be rendered;
- output is written to `.evoontology/visualizations/semantic_vN.html`;
- HTML works offline;
- Content correctly visualizes Term / Mapping / Constraint / Evidence and both edge families;
- Schema and Tool views reflect the current implementation;
- Search, detail, neighbor highlight, filters, fit/reset, zoom/pan/drag, and PNG export work;
- evolution metadata is shown when available;
- visualization remains fully read-only;
- existing Build, Evolve, Runtime behavior is unchanged.

---

## 18. Implementation Procedure

Before coding, inspect the current repository and reuse the existing implementation for:

```text
Core package
SemanticStore
workspace resolver
active.json
versions/
semantic schema
relation/reference fields
MCP tools
Claude Code plugin
Codex plugin
```

If actual file names differ from this plan, adapt to the current structure rather than creating parallel implementations.

Implementation order:

```text
1. Add visualization package/assets
2. Implement ontology → Cytoscape element conversion
3. Implement standalone HTML renderer
4. Implement Content interactions
5. Implement Schema / Tool views
6. Add evolution metadata
7. Add Claude Code / Codex entry points
8. Add focused tests
9. Run existing + new tests
10. Smoke-test on a real .evoontology workspace
```

After completion, report only:

```text
- files added/modified
- implemented capabilities
- Cytoscape.js version
- test results
- generated HTML path
- any material mismatch found between the current Content / Schema / Tool implementation and the expected EvoOntology structure
```

Do not refactor Build, Evolve, Runtime, Store, or workspace architecture unless a change is strictly required for this visualization feature.
