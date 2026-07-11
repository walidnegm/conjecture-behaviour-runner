"""Cognition modes for Conjecture runs."""
from __future__ import annotations

from enum import Enum


class LlmMode(str, Enum):
    """How cognition (labels / router enums) is supplied per turn.

    * ``stub`` — pin on the turn; no model calls (default, CI-safe).
    * ``freeze`` — load a recorded pin JSON by key.
    * ``record`` — capture live labels into freeze files (host provides recorder).
    * ``local`` — host routes a real bounded classifier (private/local endpoint).
    * ``cloud`` — host routes cloud cognition (soak only; not default CI).
    """

    STUB = "stub"
    FREEZE = "freeze"
    RECORD = "record"
    LOCAL = "local"
    CLOUD = "cloud"
