---
name: evolve-semantic-layer
description: This skill is triggered when the user requests to "self-evolve the current semantic layer system". Autonomously evolve a semantic-layer system through a four-step loop of diagnosis, attribution, patching, and Parent/Candidate evaluation until a reproducibly better version is obtained, or external conditions prevent trustworthy continuation.
---

# Self-Evolving Semantic Layer

Continuously improve the complete semantic-layer system until a credible and
reproducibly better version is obtained.

The evolution target may include semantic content, tools, and schema,
together with related prompts, interfaces, workflows, or runtime components
when they are part of the attributed mechanism. Evolution may correct
existing designs, add missing capabilities, or adjust system structures.

## Core Principles

* **Discover problems before designing optimization:** Do not only analyze failures that have already appeared. Actively identify analysis needs that the system does not cover, explore, or complete.
* **Evidence before attribution:** Use results, traces, representative tasks, and counterexamples. Do not determine root causes solely from final scores.
* **Determine mechanisms before selecting interventions:** First explain why the system is limited, then let the Agent determine how to optimize it.
* **One Candidate validates one primary hypothesis:** A Candidate may involve multiple components, but all changes must serve the same primary causal mechanism.
* **Validate capability changes before formal evaluation:** First confirm that the intervention truly changes the target capability or analysis behavior.
* **Only a better version counts as completion:** Evolution is successful only when the improvement is credible, reproducible, and has no unacceptable regression.

## Before Evolution

1. Read previous evolution records and accumulated knowledge if they exist.
2. Read the current semantic layer, tools, Builder, runtime flow, evaluation setup, and previous experiments.
3. Define optimization objectives, acceptance criteria, and unacceptable regressions.
4. Preserve a reproducible Parent before making changes.
5. Preserve the key objective, Parent version, and prior findings needed to continue the evolution process.

Do not rely only on current conversation context. Evolution must preserve
knowledge across iterations.

If objectives or acceptance criteria are materially unclear, confirm them
before expensive experiments.

**Stage Output:** A fixed optimization objective and a Parent that can be fairly compared.

## Evolution Loop

### Step 1 — Diagnose Problems from Historical Trajectories

Do not rely only on existing failure traces. Analyze both what the system has
done and what it should have done but did not.

1. Compare successful, failed, improved, and regressed cases to understand the analysis paths actually taken by the Agent.
2. Examine analysis coverage and identify important dimensions, metrics, concepts, relations, hypotheses, and analysis directions that were ignored, repeatedly missed, or never explored.
3. Examine capability coverage and determine whether the current tool system and its usage loop can support reasonable analysis needs.
4. Examine structural limitations and identify recurring issues showing that the current semantic layer limits exploration, expression, interaction, or evolution.
5. Use representative tasks, counterfactual questions, or exploratory tests to validate potential gaps not exposed in traces.
6. Organize discovered issues into a structured problem map, including:
   * Explicit execution failures;
   * Insufficient analysis coverage;
   * Tool or workflow limitations;
   * System-level structural constraints;
   * Potential gaps requiring further validation.

The problem map should preserve observed symptoms, evidence, causal
hypotheses, and unresolved uncertainty.

**Stage Output:** A problem map covering visible failures, missing capabilities, compensation paths, and potential system limitations.

### Step 2 — Attribute Causal Mechanisms

1. Select high-value problems.
   - Prioritize issues with large impact, repeated occurrence, upstream position, or high uncertainty reduction value.
   - Do not accept a causal explanation simply because a patch is easy to implement.

2. Analyze how each important problem affects the analysis process and final result.

3. Attribute causes to the most relevant part of the ontology layer:

   * **Content:** Whether semantic knowledge is incorrect, incomplete, improperly granular, or insufficiently covered.
   * **Tool:** Whether tool capabilities, interfaces, retrieval, ranking, returned information, or interaction patterns limit usage.
   * **Schema:** Whether the current object model or structural organization cannot reliably support requirements.

4. Determine the nature of each problem:

   * **Existing design error:** Current design produces incorrect behavior;
   * **Missing capability or coverage:** Required knowledge, capability, or coverage is absent;
   * **Structural mismatch:** Current design cannot reliably support analysis requirements.

Do not default to patching existing components. First determine whether the
system is doing something wrong, missing something necessary, or structurally
unsuitable. The optimization approach should follow from this diagnosis and
the available evidence.

5. Generate competing causal explanations and compare them using traces, successful cases, counterexamples, and targeted tests.
6. Separate independent root causes from downstream symptoms.
7. Prioritize causal issues according to expected impact, evidence strength, cross-case reproducibility, and testing value and cost.

Attribution may produce multiple causal explanations. Each should be
independently testable, but the next Candidate should normally target the
highest-priority mechanism.

**Stage Output:** A prioritized set of experimentally testable causal explanations with corresponding evidence and remaining uncertainty.

### Step 3 — Patch the Parent Ontology

1. Select the mechanism currently most valuable to validate.
2. Convert the mechanism into a clear, falsifiable hypothesis describing:
   * Current limitation;
   * Why it causes the observed problem;
   * Expected system behavior change if correct;
   * Evidence that supports or falsifies the hypothesis.
3. Design the intervention based on project structure, evidence, and problem characteristics.
   * Prefer solutions that directly test the hypothesis, have clear scope, and are reversible.
   * Do not expand changes unnecessarily or repeatedly apply low-value patches.
4. Keep the primary intervention localized to the attributed Content, Tool, or Schema level.
   * Multiple dependent components may be modified when all changes serve the same primary mechanism.
   * Improvements must not come from permanently disabling, removing, or bypassing the semantic layer.
   * Diagnostic ablation may serve as attribution evidence, not as the final successful solution.
5. Preserve the Parent and record Candidate changes, expected effects, and rollback methods.
6. Run representative cases, targeted replay, or low-cost exploratory experiments to verify that the Candidate changes the intended capability or behavior.
7. Check whether the Candidate introduces new limitations, reduces exploration space, or shifts problems elsewhere.

If the intervention is ineffective, redesign the Candidate. If the
intervention activates but the problem remains, update the attribution. If a
local capability improves without improving the overall process, inspect
integration, side effects, and remaining bottlenecks.

Only proceed to formal comparison after confirming that the target mechanism
has meaningfully changed.

**Stage Output:** One high-value Candidate and evidence showing whether the intended mechanism has activated.

### Step 4 — Evaluate and Gate the Candidate

Compare Parent and Candidate under a controlled and reproducible evaluation
protocol.

1. Keep inputs, data splits, models, Evaluator, budget, and runtime configuration consistent.
2. Analyze:
   * Whether target metrics improve;
   * Whether improvement covers the original problem;
   * Whether new regressions or limitations appear;
   * Whether improvement matches the proposed causal mechanism.
3. Determine the Candidate result:
   * Accept the Candidate when it provides reproducible improvement without unacceptable regression;
   * Revise the intervention or causal hypothesis when results are partial or mixed;
   * Reject and roll back the Candidate when it does not provide trustworthy improvement.

Do not accept a Candidate only because a final metric improves. Evaluation
should also deepen understanding of semantic-layer limitations and guide
future optimization.

After the decision:

1. Update the problem map and causal understanding.
2. Mark solved problems, remaining limitations, newly discovered issues, and disproven explanations.
3. Preserve the main validated mechanisms, rejected hypotheses, and unresolved uncertainty needed for later rounds.
4. If the Candidate is accepted, update the Parent and continue from the most relevant step when valuable problems remain.
5. If progress stagnates or similar patches repeat, read `references/exploration-guide.md`, broaden the problem search, and reconsider the current explanation.

Candidate failure, unknown attribution, no-op results, or temporary lack of
effective hypotheses do not indicate completion. They provide information for
the next evolution cycle.

**Stage Output:** A Parent/Candidate decision, updated evolution knowledge, and a clear next direction or rollback point.

## Completion Conditions

Only declare success when the final version satisfies:

* Target metrics improve;
* Results are reproducible and evidence-supported;
* No unacceptable regression exists;
* Final version can be activated and rerun.

If execution stops due to user interruption, exhausted budget, missing data
or permissions, or unreliable evaluation, mark status as `incomplete`.

Preserve the best current version, unresolved causal issues, remaining
hypotheses, and accurate recovery steps.

## Prohibited Actions

Do not improve results by modifying:

- Benchmark questions;
- Ground Truth;
- Labels;
- Evaluator;
- Data splits;
- Acceptance criteria.

Do not hard-code standard answers, task-specific correct values, or expected
Evaluator outputs.

Domain knowledge must be stored in traceable, versioned semantic artifacts
and must not be hidden inside Prompt, Builder code, or orchestration logic.

## Final Deliverable

Report:

* Starting Parent and final best version;
* Comparable experiment results;
* System problem map and prioritized causal mechanisms;
* Accepted and rejected hypotheses;
* Key improvements and regressions;
* Final causal explanation;
* Completion status;
* Reproduction or recovery instructions.

## Research Integrity

Preserve the validity of the benchmark and evaluation protocol. Do not modify benchmark questions, labels, Ground Truth, Evaluator logic, data splits, or acceptance criteria to improve results. Domain knowledge should remain in traceable semantic artifacts rather than being hidden in prompts or orchestration code.
