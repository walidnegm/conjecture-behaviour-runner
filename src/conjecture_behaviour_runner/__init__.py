"""Conjecture Behaviour Runner — public package surface.

Portable multi-turn behaviour eval: script model, cognition pins (generic),
invariant library, adapter protocol. Hosts bind a ``ControlPlaneAdapter`` to
their control plane or ledger.

Scenario YAML / trajectory models live under
``conjecture_behaviour_runner.experimental`` (not part of the stable 0.1 API).
"""
from __future__ import annotations

from conjecture_behaviour_runner.harness import run_script
from conjecture_behaviour_runner.invariants import (
    STANDARD_INVARIANT_KINDS,
    BaseControlPlaneAdapter,
    check_standard_invariant,
)
from conjecture_behaviour_runner.modes import LlmMode
from conjecture_behaviour_runner.pins import CognitionPin
from conjecture_behaviour_runner.protocol import (
    ControlPlaneAdapter,
    NullControlPlaneAdapter,
    TurnObservation,
)
from conjecture_behaviour_runner.script import (
    ConjectureScript,
    DialogueTurn,
    InvariantSpec,
    LedgerEffect,
    RunResult,
    ScriptScope,
    load_script_json,
    load_script_yaml,
    script_from_dict,
)

__version__ = "0.1.0"

__all__ = [
    "STANDARD_INVARIANT_KINDS",
    "BaseControlPlaneAdapter",
    "CognitionPin",
    "ConjectureScript",
    "ControlPlaneAdapter",
    "DialogueTurn",
    "InvariantSpec",
    "LedgerEffect",
    "LlmMode",
    "NullControlPlaneAdapter",
    "RunResult",
    "ScriptScope",
    "TurnObservation",
    "check_standard_invariant",
    "load_script_json",
    "load_script_yaml",
    "run_script",
    "script_from_dict",
    "__version__",
]
