---
name: build-semantic-layer
description: Build an initial ontology-inspired semantic layer by analyzing workload requirements, exploring data-environment evidence, and generating schema-conformant semantic objects.
---

# Build Semantic Layer

Construct the first version of a semantic layer for a target workload.

The goal is to discover reusable, evidence-grounded analytical knowledge
from questions and data-environment exploration.

The semantic schema defines the structure of the semantic layer.
The Builder Agent discovers and populates semantic content under this
schema.

---

# Before Starting

Read:

- references/semantic-schema.md
- references/semantic-interaction-protocol.md
- references/semantic-layer-data-boundary.md

The generated semantic layer MUST follow semantic-schema.md.

The semantic interaction assumptions MUST follow
semantic-interaction-protocol.md.

Do not create alternative semantic object structures.

All dataset access, split usage, freezing, and evaluation boundaries MUST
follow semantic-layer-data-boundary.md.

---

# Builder Workflow

## Step 1 — Workload-Guided Probing

### Understand workload requirements

Read only the analytical questions in the frozen construction split.

Identify:

- recurring analytical dimensions;
- concepts and metrics required for reasoning;
- relationships needed between concepts;
- evidence required to answer questions reliably.

Create a workload coverage map.

The coverage map is a construction artifact, not part of the semantic
layer. Its purpose is to ensure important analytical requirements are not
lost during semantic layer construction.

Do not start from data structures. Start from analytical requirements.

### Design semantic requirements

Translate workload requirements into semantic objects defined by
semantic-schema.md.

Determine:

- required Terms;
- required Mappings;
- useful Relations using one of the five controlled `relation_type` values
  defined in semantic-schema.md: association / hierarchy / composition /
  equivalence / derivation;
- necessary Constraints.

For each Relation, classify the relationship type using the decision
priority defined in semantic-schema.md. Do not use free-text types such as
`affects` or `belongs_to`.

Keep the semantic layer minimal and reusable. Do not create objects without
a clear workload purpose.

### Explore data-environment evidence

Use available read-only tools to inspect the target data environment,
including databases, structured files, documents, metadata, and other
supported data sources.

For each semantic requirement:

- identify plausible candidate data sources, structures, and elements based
  on structural metadata, relationships, workload terms, and representative
  content;
- inspect and compare candidates' granularity, identifiers, fields,
  relationships, metadata, and representative content;
- do not stop at the first plausible match when multiple candidates remain
  semantically possible;
- stop candidate expansion when remaining candidates lack support from the
  workload, data structure, metadata, representative values, or observed
  content;
- verify the selected grounding's meaning, scope, and granularity;
- record supporting evidence, including why competing candidates were not
  selected when the distinction is analytically important.

Semantic objects must be grounded in reproducible observations from the
target data environment. Do not infer unsupported concepts from external
knowledge.

When multiple data sources or elements are plausible groundings for the same
analytical concept, document their distinct semantic roles, granularity,
scope, and applicability conditions.

Use Mapping to connect analytical concepts to concrete data sources,
structures, or elements. Use Constraint to record data-grounded applicability
conditions, value interpretations, and business rules. Use Relation to record
semantic connections between Terms. Use Evidence to record the reproducible
observations supporting these semantic claims.

**Stage Output:** Candidate semantic objects and their data-grounded evidence.

---

## Step 2 — Evidence-Grounded Commitment

### Generate semantic layer

Create semantic objects according to semantic-schema.md:

- Term;
- Mapping;
- Relation;
- Constraint;
- Evidence.

Every active semantic object must be traceable to:

- a workload requirement;
- data-environment evidence.

The semantic layer should preserve the workload coverage map while storing
only validated semantic knowledge.

Semantic objects MUST contain only the fields defined in
semantic-schema.md. Do not add query-generation instructions, SQL templates,
procedural reasoning steps, or task-specific solution strategies. Do not
encode such prohibited content inside schema-defined free-text fields as a
workaround.

Relation objects MUST use one of the five controlled `relation_type` values.
Describe the connection semantically rather than as a query template.

Constraint objects MUST include suitable `trigger_keywords` so that relevant
constraints can be discovered at runtime.

### Validate semantic layer

Validate that:

- each important analytical dimension in the workload coverage map is
  represented by grounded semantic objects where valid grounding exists;
- Mappings correspond to real data structures;
- Relations and Constraints make required semantic relationships,
  applicability conditions, value interpretations, or business definitions
  explicit;
- Evidence can be reproduced;
- semantic objects can be accessed through the semantic interaction protocol;
- semantic objects contain only schema-defined fields.

Coverage validation confirms semantic availability and grounding; it does
not by itself guarantee successful task execution.

If no valid grounding exists, record a coverage gap or known limitation. Do
not fabricate semantic objects.

Revise unsupported, ambiguous, incomplete, or schema-invalid objects.

### Publish

Create a versioned semantic layer containing:

- semantic objects;
- evidence records;
- build metadata, including rejected-candidate rationale where analytically
  significant;
- construction split identifier;
- validation results;
- known limitations.

This version becomes the initial semantic layer and the starting point for
future evolution.

After the validated version is published, initialize its evolution trigger:

```bash
python -c "from evoontology import EvolutionTrigger; EvolutionTrigger(r'<workspace>').initialize()"
```

This operation is idempotent. It starts the time-based reminder from the
initial publication without resetting existing trajectories or user-defined
thresholds.

**Stage Output:** A validated and versioned initial semantic layer.
