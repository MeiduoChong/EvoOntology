---
name: evo-visualize
description: Visualize the current EvoOntology ontology state as an interactive local graph.
---

# Visualize Ontology

Render one ontology version as a standalone, offline, single-file interactive
HTML graph (Content / Schema / Tool views). The operation is strictly
read-only.

## Workflow

1. Resolve the workspace: default is the current project's `.evoontology/`
   (Core `resolve_workspace()`); use an explicit path when the user provides one.
2. Resolve the requested version: default `active` (the version referenced by
   `active.json`). An explicit `semantic_vN` is rendered without changing
   `active.json`.
3. Call the `evo-semantic` MCP tool `visualize_semantics` (the single rendering
   entry point), passing `workspace` (the absolute `.evoontology/` path) and
   optionally `version`. Do not run `python -m evoontology.visualization`.

4. Return the generated path `<workspace>/visualizations/<version>.html`.
   The MCP tool writes the file without opening a browser.

## Boundaries

- Do not implement HTML generation inside this skill; all rendering lives in
  EvoOntology Core (`evoontology.visualization`).
- Never modify Build, Evolve, Runtime, `active.json`, `versions/`, or any
  other ontology/evolution state.
- Errors stay explicit: workspace not initialized, no active version, or the
  requested version does not exist. Broken references only produce warnings;
  graph objects are never fabricated.
