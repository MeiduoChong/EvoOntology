# EvoOntology — Codex Instructions

This project uses EvoOntology: a versioned, self-evolving ontology layer between
natural-language questions and the underlying data. The deterministic core lives
in the `evoontology` Python package; the Build/Evolve method lives in the shared
skills bundled in this plugin's `skills/` directory.

The `evo-semantic` MCP server is already running with the bundled core. Drive all
deterministic build/evolve/visualize operations through its tools with an explicit
`workspace` argument (the absolute path to `<project-root>/.evoontology`). Do not
run `python -m evoontology...` or `from evoontology import ...` from the user
project — the core is not installed there in a plugin-only setup.

## Entry points

- **Build** — when the user asks to "build the ontology" or runs `/evo-build`,
  execute the `evo-build` skill (see
  `skills/evo-build/SKILL.md`). Use the MCP tools `save_version`,
  `validate_semantics`, `set_active_version`, and `evolution_status` to publish
  `semantic_v0` and initialize the trigger checkpoint.
- **Evolve** — when the user asks to "evolve the ontology" or runs `/evo-evolve`,
  execute the `evo-evolve` skill (see
  `skills/evo-evolve/SKILL.md`) following
  Diagnose → Attribute → Patch → Evaluate/Gate. Drive the loop with the MCP
  tools `start_evolution_run` / `resume_evolution_run`, `begin_evolution_round`,
  `save_version`, `record_evolution_evaluation`, `record_evolution_round`,
  `accept_evolution`, and `mark_evolution_incomplete`. Resume an existing
  session when one is running, confirm the round budget with the user only when
  creating a new run, and evaluate Candidates on independent versions without
  switching `active.json`. Only an accepted Candidate is published as the next
  `semantic_vN`, switches `active.json`, and advances the checkpoint; an
  Incomplete run changes neither.

- **Visualize** — when the user asks to "visualize the ontology" or runs
  `/evo-visualize` (or `$evo-visualize`), execute the `evo-visualize` skill (see
  `skills/evo-visualize/SKILL.md`) and call the MCP tool `visualize_semantics`
  to render the active (or an explicitly requested) version as a standalone
  offline multi-version HTML at `<resolved-workspace>/visualizations/semantic-layer-explorer.html`,
  read-only. For this tool, a project root or `.evoontology` container may resolve
  to one nested database workspace; ambiguous candidates require an exact path.

For Codex, the slash-style phrases above are aliases that route to the matching
skills. The native Codex skill invocations are `$evo-build`, `$evo-evolve`, and
`$evo-visualize`.

## Semantic MCP tools

The `evo-semantic` MCP server exposes two bounded navigation tools plus a
session manifest resource:

- `browse_semantics(query, kind, limit)` — discover concepts relevant to a need;
- `resolve_semantics(mentions, context)` — resolve concepts to grounded
  mappings, relations, constraints, and evidence.

Use them to ground analytical concepts before querying real data with native
tools. They are guidance, not final answers.

The same server also exposes the deterministic build/evolve operations
(`validate_semantics`, `visualize_semantics`, `evolution_status`, version
helpers, and the evolution-session tools). Use those for the workflows above.

## Evolution reminder

Before a session, check whether evolution is due by calling the MCP tool
`evolution_status` with `workspace` set to `<project-root>/.evoontology`.

If `check.evolution_due` is true, remind the user that `/evo-evolve` is
available. Never start evolution automatically.
