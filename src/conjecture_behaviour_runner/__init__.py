"""Conjecture Behaviour Runner — public package surface.

Portable multi-turn behaviour eval: script model, cognition providers,
invariant + trajectory oracles, adapter protocol. Hosts bind a
``ControlPlaneAdapter`` (or path-faithful driver) to their system.
"""
from __future__ import annotations

from conjecture_behaviour_runner.cognition import (
    CognitionDecision,
    CognitionProvider,
    FreezeArtifact,
    FreezeCognitionProvider,
    FreezeStore,
    RecordCognitionProvider,
    StubCognitionProvider,
    provider_for_mode,
)
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
from conjecture_behaviour_runner.temporal import (
    TRAJECTORY_INVARIANT_KINDS,
    check_trajectory_invariant,
)

__version__ = "0.1.1"

__all__ = [
    "STANDARD_INVARIANT_KINDS",
    "TRAJECTORY_INVARIANT_KINDS",
    "BaseControlPlaneAdapter",
    "CognitionDecision",
    "CognitionPin",
    "CognitionProvider",
    "ConjectureScript",
    "ControlPlaneAdapter",
    "DialogueTurn",
    "FreezeArtifact",
    "FreezeCognitionProvider",
    "FreezeStore",
    "InvariantSpec",
    "LedgerEffect",
    "LlmMode",
    "NullControlPlaneAdapter",
    "RecordCognitionProvider",
    "RunResult",
    "ScriptScope",
    "StubCognitionProvider",
    "TurnObservation",
    "check_standard_invariant",
    "check_trajectory_invariant",
    "load_script_json",
    "load_script_yaml",
    "provider_for_mode",
    "run_script",
    "script_from_dict",
    "__version__",
]
