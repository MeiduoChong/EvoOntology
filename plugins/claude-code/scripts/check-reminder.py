#!/usr/bin/env python3
"""Session-start evolution reminder hook.

Checks ``<cwd>/.evoontology`` for an evolution-due condition and prints a
one-line reminder to stdout. Claude Code injects hook stdout into the session
context, so the agent sees the reminder without any user action.

Silently exits when no semantic layer is active or when evolution is not due.
For backward compatibility, an active legacy workspace without ``state.json``
is initialized automatically before checking its trajectories.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evoontology import EvolutionTrigger, resolve_workspace


def main() -> int:
    workspace = resolve_workspace()
    if not (workspace / "active.json").is_file():
        return 0

    trigger = EvolutionTrigger(str(workspace))
    trigger.initialize()
    result = trigger.check()
    if not result["evolution_due"]:
        return 0

    print(
        f"EvoOntology: evolution is due ({result['reason']}). "
        f"Run /evo-evolve to review and improve the semantic layer."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
