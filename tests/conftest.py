"""Test bootstrap.

Public clones install the companion runtime via the ``[control-plane]`` extra.
When this tree sits next to a ``conversation-control-plane`` checkout (local
staging layout), put that package ``src/`` on ``sys.path`` so adapter tests run
without a prior install. Bare public clones without the extra skip those tests.
"""
from __future__ import annotations

import pathlib
import sys

# tests/ → package root; optional sibling: ../conversation-control-plane/src
_repo_root = pathlib.Path(__file__).resolve().parents[1]
_ccp_src = _repo_root.parent / "conversation-control-plane" / "src"
if _ccp_src.is_dir() and str(_ccp_src) not in sys.path:
    sys.path.insert(0, str(_ccp_src))
