"""Conjecture Behaviour Runner — public package surface.

Portable multi-turn behaviour eval: script model, cognition modes,
adapter protocol, and scenario/trajectory contracts. Hosts bind a
``ControlPlaneAdapter`` to their control plane or ledger.
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
    "TurnObservation",
    "check_standard_invariant",
    "run_script",
    "__version__",
]
