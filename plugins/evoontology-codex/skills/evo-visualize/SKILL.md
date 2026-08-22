---
name: evo-visualize
description: Visualize the current EvoOntology ontology state as an interactive local graph.
---

# Visualize Ontology

Render all ontology versions as one standalone, offline, single-file interactive
HTML explorer (Content / Schema / Tool views), with in-page version switching
and side-by-side comparison across all three layers. Difference highlighting can
be toggled without changing the compared versions. The operation is strictly
read-only.

## Workflow

1. Resolve the workspace: default is the current project's `.evoontology/`
   (Core `resolve_workspace()`); use an explicit path when the user provides one.
2. Resolve the initially shown version: default `active` (the version referenced
   by `active.json`). An explicit `semantic_vN` changes only the initial page
   selection and never changes `active.json`; every available version is embedded.
3. Call the `evo-semantic` MCP tool `visualize_semantics` (the single rendering
   entry point), passing `workspace` (the absolute `.evoontology/` path) and
   optionally `version` and `open_browser`. Do not run
   `python -m evoontology.visualization`.

4. Return the generated path `<workspace>/visualizations/index.html`.
   The MCP tool writes the file and then opens it in the default browser
   exactly once (`open_browser` defaults to true). Pass `open_browser: false`
   only when the user explicitly does not want the browser to open. Never open
   the returned path a second time yourself (no `Start-Process` / `explorer` /
   `open`, no in-app browser): the tool has already opened the page, and a
   second open creates a duplicate tab.

## Boundaries

- Do not implement HTML generation inside this skill; all rendering lives in
  EvoOntology Core (`evoontology.visualization`).
- Never modify Build, Evolve, Runtime, `active.json`, `versions/`, or any
  other ontology/evolution state.
- Errors stay explicit: workspace not initialized, no active version, or the
  requested version does not exist. Broken references only produce warnings;
  graph objects are never fabricated.
- Content edges follow the semantic model: solid Semantic Relations connect
  Terms, while dotted Structural References attach Mapping, Constraint, and
  Evidence records according to schema reference rules.
