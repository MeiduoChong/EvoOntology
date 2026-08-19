# Semantic Layer Data Boundary

Each benchmark is divided into two disjoint folds, A and B, for reciprocal evaluation.

For the A→B direction, 70% of fold A is used as the construction/evolution-training subset, and the remaining 30% is used as the evolution-validation subset. The selected semantic layer is frozen before final evaluation on fold B. The same procedure is then reversed for B→A, and the two held-out results are averaged.

The construction/evolution-training subset may be used to:

- analyze workload coverage;
- identify required semantic capabilities;
- explore the data environment;
- generate and validate evidence-grounded semantic objects;
- collect trajectories for diagnosis and Candidate design.

The evolution-validation subset is used only for Parent/Candidate comparison and acceptance. It must not be used for problem diagnosis or Candidate design.

The Builder and Evolver MUST NOT read or use:

- held-out test questions or identifiers;
- reference answers or ground truth from any split;
- evaluator feedback from the held-out test split;
- artifacts derived from the held-out test split;
- manually supplied benchmark-specific conclusions.

Before construction, freeze the fold assignment and the 70/30 split. All compared conditions should use the same split and evaluation protocol.

The held-out fold remains inaccessible until the semantic layer, evolution result, and evaluation protocol are frozen.
