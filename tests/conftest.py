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


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_stores(tmp_path_factory, monkeypatch):
    """Every test writes to its own backlog and reports folder — never the host's.

    Unset, ``resolve_backlog_dir`` walks up from the working directory and finds a host
    monorepo's real backlog, so a test run from inside one enqueued "demo_candidate"
    verdicts there: 20 of 32 "needs review" items on 11-12 were tests. A test that needs a
    specific folder still sets its own (monkeypatch after this fixture wins).
    """
    root = tmp_path_factory.mktemp("stores")
    monkeypatch.setenv("CONJECTURE_BACKLOG_DIR", str(root / "backlog"))
    monkeypatch.setenv("CONJECTURE_CONTENT_REPORTS_DIR", str(root / "content-reports"))
    yield
