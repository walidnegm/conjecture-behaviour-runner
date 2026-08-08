"""Review backlog — enqueue, classify, fix-close with patch documentation."""
from __future__ import annotations

import json
from pathlib import Path

from conjecture_behaviour_runner.review_backlog import (
    close_open_with_patch,
    close_with_patch,
    enqueue_review,
    get_backlog_item,
    list_backlog,
    update_backlog_item,
)


def test_close_with_patch_closes_open_and_documents_patch(tmp_path: Path) -> None:
    bdir = tmp_path / "backlog"
    item = enqueue_review(
        scenario_id="residual_draft_improve",
        evidence={
            "ok": True,
            "run": {
                "passed": False,
                "failures": ["exclusive_owner"],
                "thread_id": "conv_abc",
                "adapter": "Bot0HttpAdapter",
            },
            "product_path": True,
            "findings": {"headline": "improve stole to IR", "verdict": "FAIL"},
        },
        adapter="host",
        backlog_dir=bdir,
    )
    iid = item["id"]
    upd = update_backlog_item(
        iid,
        classification="product_bug",
        analysis={"prose": "Wrong leaf despite soft PASS path"},
        suggested_fixes=[
            {
                "priority": "P0",
                "title": "seal improve leaf",
                "files": ["conversation_control/draft_strengtheners_contract.py"],
                "action": "finite improve before IR",
            }
        ],
        backlog_dir=bdir,
    )
    assert upd["ok"]
    assert upd["item"]["status"] == "backlog_fix"
    assert upd["item"]["classification"] == "product_bug"

    closed = close_with_patch(
        iid,
        patch={
            "summary": "Seal open improve away from IR handoff",
            "files": [
                "conversation_control/draft_strengtheners_contract.py",
                "tests/test_draft_open_improve_not_ir.py",
            ],
            "commits": ["deadbeef"],
            "tests": ["test_draft_open_improve_not_ir.py"],
            "seal": "draft_open_improve_not_ir",
        },
        backlog_dir=bdir,
        reviewer="session_agent",
    )
    assert closed["ok"] is True
    assert closed["closed"] is True
    it = closed["item"]
    assert it["status"] == "closed"
    assert it["classification"] == "fixed"
    assert it["patch"]["summary"].startswith("Seal open improve")
    assert "conversation_control/draft_strengtheners_contract.py" in it["patch"]["files"]
    assert it["patch"]["commits"] == ["deadbeef"]
    assert it["patch"]["command"] == "fix"
    assert it["closed_at"]
    assert it["fix_notes"]

    # Durable on disk
    got = get_backlog_item(iid, backlog_dir=bdir)
    assert got["ok"]
    assert got["item"]["patch"]["tests"] == ["test_draft_open_improve_not_ir.py"]

    listing = list_backlog(status="closed", backlog_dir=bdir)
    assert listing["count"] >= 1
    assert any(r["id"] == iid for r in listing["items"])


def test_close_requires_patch_summary(tmp_path: Path) -> None:
    bdir = tmp_path / "backlog"
    item = enqueue_review(
        scenario_id="s_empty_patch",
        evidence={"run": {"passed": True, "failures": []}},
        backlog_dir=bdir,
    )
    res = close_with_patch(item["id"], patch={}, backlog_dir=bdir)
    assert res["ok"] is False
    assert res["error"] == "patch_required"


def test_close_open_with_patch_batch(tmp_path: Path) -> None:
    bdir = tmp_path / "backlog"
    a = enqueue_review(
        scenario_id="a_bug",
        evidence={"run": {"passed": False, "failures": ["x"]}},
        backlog_dir=bdir,
    )
    b = enqueue_review(
        scenario_id="b_bug",
        evidence={"run": {"passed": False, "failures": ["y"]}},
        backlog_dir=bdir,
    )
    update_backlog_item(
        a["id"], classification="product_bug", backlog_dir=bdir
    )
    update_backlog_item(
        b["id"], classification="product_bug", backlog_dir=bdir
    )
    # leave one needs_review without product_bug so batch default skips it
    c = enqueue_review(
        scenario_id="c_pending",
        evidence={"run": {"passed": True, "failures": []}},
        backlog_dir=bdir,
    )

    batch = close_open_with_patch(
        patch={
            "summary": "Batch seal for related steal incidents",
            "files": ["conversation_control/steal_incident.py"],
            "tests": ["test_control_plane_antipattern_ratchets.py"],
        },
        backlog_dir=bdir,
    )
    assert batch["ok"]
    assert batch["closed_count"] == 2
    closed_ids = {row["id"] for row in batch["closed"]}
    assert a["id"] in closed_ids
    assert b["id"] in closed_ids
    assert c["id"] not in closed_ids

    still = get_backlog_item(c["id"], backlog_dir=bdir)
    assert still["item"]["status"] == "needs_review"

    for iid in (a["id"], b["id"]):
        got = get_backlog_item(iid, backlog_dir=bdir)
        assert got["item"]["status"] == "closed"
        assert got["item"]["classification"] == "fixed"
        assert got["item"]["patch"]["summary"].startswith("Batch seal")

    handoff = (bdir / "HANDOFF.md").read_text(encoding="utf-8")
    assert "fix" in handoff
    assert "backlog_fix" in handoff


def test_close_with_string_patch(tmp_path: Path) -> None:
    bdir = tmp_path / "backlog"
    item = enqueue_review(
        scenario_id="string_patch",
        evidence={"run": {"passed": False, "failures": ["z"]}},
        backlog_dir=bdir,
    )
    update_backlog_item(item["id"], classification="product_bug", backlog_dir=bdir)
    res = close_with_patch(
        item["id"],
        patch="Hotfix: deictic apply + agentic tail",
        backlog_dir=bdir,
    )
    assert res["ok"]
    assert res["item"]["patch"]["summary"] == "Hotfix: deictic apply + agentic tail"
    raw = json.loads(
        (bdir / "items" / f"{item['id']}.json").read_text(encoding="utf-8")
    )
    assert raw["status"] == "closed"
    assert raw["patch"]["command"] == "fix"
