"""EvoOntology core — deterministic capabilities for the self-evolving ontology layer.

Layout follows the product design doc:

- ``ontology/``   — record models + versioned store (save / load / publish / rollback)
- ``runtime/``    — semantic runtime (browse / resolve / manifest) + MCP server
- ``trajectory/`` — tool-call-level task trajectory recording
- ``trigger/``    — evolution-due detection (new-task count + elapsed time)
- ``evaluation/`` — GT / LLM-Judge scheduling + aggregation gate

Build and Evolve intelligence lives in the plugin skills; this package provides
only deterministic capabilities.
"""

from .evaluation.evaluation import EvaluationGate
from .ontology.models import Constraint, Evidence, Mapping, Relation, Term
from .ontology.store import SemanticStore
from .runtime.runtime import SemanticLayer
from .trajectory.trajectory import TrajectoryStore, from_message_trace, truncate_result
from .trigger.trigger import EvolutionTrigger
from .workspace import ensure_workspace, load_project, resolve_workspace, save_project

__version__ = "1.0.0"

__all__ = [
    "SemanticStore",
    "SemanticLayer",
    "TrajectoryStore",
    "EvolutionTrigger",
    "EvaluationGate",
    "resolve_workspace",
    "ensure_workspace",
    "load_project",
    "save_project",
    "truncate_result",
    "from_message_trace",
    "Term",
    "Mapping",
    "Relation",
    "Constraint",
    "Evidence",
]
