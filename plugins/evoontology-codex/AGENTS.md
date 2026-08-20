# EvoOntology — Codex Instructions

This project uses EvoOntology: a versioned, self-evolving ontology layer between
natural-language questions and the underlying data. The deterministic core lives
in the `evoontology` Python package; the Build/Evolve method lives in the shared
skills bundled in this plugin's `skills/` directory.

## Entry points

- **Build** — when the user asks to "build the ontology" or runs `/evo-build`,
  execute the `build-semantic-layer` skill (see
  `skills/build-semantic-layer/SKILL.md`). Default workspace
  is `<project-root>/.evoontology`, resolved and initialized through EvoOntology
  Core. Save `semantic_v0`, validate it with `python -m evoontology.validate
  --root <workspace> --version semantic_v0`, then activate it and initialize
  the trigger checkpoint.
- **Evolve** — when the user asks to "evolve the ontology" or runs `/evo-evolve`,
  execute the `evolve-semantic-layer` skill (see
  `skills/evolve-semantic-layer/SKILL.md`) following
  Diagnose → Attribute → Patch → Evaluate/Gate. Drive the loop through an
  `EvolutionSession` from the shared core: resume an existing session when one
  is running, confirm the round budget with the user only when creating a new
  run, and evaluate Candidates on independent versions without switching
  `active.json`. Only an accepted Candidate is published as the next
  `semantic_vN`, switches `active.json`, and advances the checkpoint; an
  Incomplete run changes neither.

## Semantic MCP tools

The `evo-semantic` MCP server exposes two bounded navigation tools plus a
session manifest resource:

- `browse_semantics(query, kind, limit)` — discover concepts relevant to a need;
- `resolve_semantics(mentions, context)` — resolve concepts to grounded
  mappings, relations, constraints, and evidence.

Use them to ground analytical concepts before querying real data with native
tools. They are guidance, not final answers.

## Evolution reminder

Before a session, check whether evolution is due:

```bash
python -c "from evoontology import EvolutionTrigger; import json; t=EvolutionTrigger(); t.initialize(); print(json.dumps(t.check()))"
```

If `evolution_due` is true, remind the user that `/evo-evolve` is available.
Never start evolution automatically.
