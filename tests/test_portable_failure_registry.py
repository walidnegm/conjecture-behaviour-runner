"""Public portable failure-mode registry stays join-consistent with patterns/."""
from __future__ import annotations

import unittest
from pathlib import Path

import yaml

_PKG = Path(__file__).resolve().parents[1]
_REGISTRY = _PKG / "incidents" / "registry.yaml"
_PATTERNS = _PKG / "incidents" / "patterns"
_CONTROL_DOC = _PKG / "docs" / "conversational-authority-quality.md"
_CATALOG = _PKG / "incidents" / "CATALOG.md"

# Optional: host monorepo registry when this tree is nested (path built without
# monorepo path literals so public leak-scan stays clean).
def _optional_host_registry() -> Path | None:
    # extract/conjecture-behaviour-runner → repo root → docs / epics / …
    root = _PKG.parents[1]
    cand = root.joinpath("docs", "epics", "failure-mode-registry.yaml")
    return cand if cand.is_file() else None


class PortableFailureRegistryTests(unittest.TestCase):
    def test_registry_and_control_doc_exist(self) -> None:
        self.assertTrue(_REGISTRY.is_file(), _REGISTRY)
        self.assertTrue(_CONTROL_DOC.is_file(), _CONTROL_DOC)
        self.assertTrue(_CATALOG.is_file(), _CATALOG)
        text = _CONTROL_DOC.read_text(encoding="utf-8")
        self.assertIn("LLM proposes", text)
        self.assertIn("code enforces", text)
        self.assertIn("registry.yaml", text)
        # Engineering-first: worked example + why not pytest + portable
        self.assertIn("Observation", text)
        self.assertIn("Pinned cognition", text)
        self.assertIn("Worked example", text)
        self.assertIn("Why not just pytest", text)
        self.assertIn("portable", text.lower())
        self.assertIn("not integration-free", text)
        self.assertIn("correctly decline", text)

    def test_runnable_seeds_have_pattern_folders(self) -> None:
        data = yaml.safe_load(_REGISTRY.read_text(encoding="utf-8"))
        entries = data["entries"]
        ids = [e["id"] for e in entries]
        self.assertEqual(len(ids), len(set(ids)), "duplicate registry ids")

        for e in entries:
            if e.get("seed_status") != "runnable":
                continue
            seed = e.get("portable_seed")
            self.assertTrue(seed, f"{e['id']}: runnable needs portable_seed")
            folder = _PATTERNS / str(seed)
            self.assertTrue(
                folder.is_dir(),
                f"{e['id']}: missing patterns/{seed}/",
            )
            self.assertTrue(
                (folder / "script.json").is_file(),
                f"patterns/{seed}/script.json missing",
            )
            self.assertTrue(
                (folder / "INCIDENT.md").is_file(),
                f"patterns/{seed}/INCIDENT.md missing",
            )

    def test_pattern_folders_are_registered_runnable(self) -> None:
        data = yaml.safe_load(_REGISTRY.read_text(encoding="utf-8"))
        runnable_seeds = {
            str(e["portable_seed"])
            for e in data["entries"]
            if e.get("seed_status") == "runnable" and e.get("portable_seed")
        }
        on_disk = {
            p.name
            for p in _PATTERNS.iterdir()
            if p.is_dir() and not p.name.startswith("_")
        }
        self.assertEqual(
            on_disk,
            runnable_seeds,
            f"patterns/ folders must match runnable portable_seed set: "
            f"disk={sorted(on_disk)} registry={sorted(runnable_seeds)}",
        )

    def test_owner_steal_seed_maps_to_owner_steal_id(self) -> None:
        data = yaml.safe_load(_REGISTRY.read_text(encoding="utf-8"))
        by_seed = {
            str(e.get("portable_seed")): e
            for e in data["entries"]
            if e.get("portable_seed")
        }
        self.assertIn("owner_steal_mid_continue", by_seed)
        self.assertEqual(by_seed["owner_steal_mid_continue"]["id"], "owner_steal")

    def test_catalog_mentions_registry_and_control_doc(self) -> None:
        text = _CATALOG.read_text(encoding="utf-8")
        self.assertIn("registry.yaml", text)
        self.assertIn("conversational-authority-quality.md", text)
        self.assertIn("Full mode list", text)
        self.assertIn("owner_steal", text)
        self.assertIn("owner_steal_mid_continue", text)
        self.assertIn("named_item_misresolve", text)
        self.assertIn("compound_act_loss", text)
        self.assertIn("success_payload_rewrite", text)
        self.assertIn("host_only", text)

    def test_registry_lists_full_mode_namespace(self) -> None:
        """Catalog companion registry covers the full CAQ-FM mode set (18)."""
        data = yaml.safe_load(_REGISTRY.read_text(encoding="utf-8"))
        ids = {e["id"] for e in data["entries"]}
        # Core portable + documented + host_only map
        for mid in (
            "owner_steal",
            "hollow_open",
            "compound_act_loss",
            "domain_pick_misbound",
            "success_payload_rewrite",
            "false_save_claim",
        ):
            self.assertIn(mid, ids)
        self.assertGreaterEqual(len(ids), 18)

    def test_host_portable_modes_align_when_present(self) -> None:
        """When nested in a monorepo with a host CAQ-FM registry, ids align."""
        host_path = _optional_host_registry()
        if host_path is None:
            self.skipTest("host monorepo registry not present")
        host = yaml.safe_load(host_path.read_text(encoding="utf-8"))
        host_ids = {e["id"] for e in host["entries"]}
        pub = yaml.safe_load(_REGISTRY.read_text(encoding="utf-8"))
        for e in pub["entries"]:
            if e.get("seed_status") != "runnable":
                continue
            self.assertIn(
                e["id"],
                host_ids,
                f"public runnable id {e['id']} missing from host registry",
            )


if __name__ == "__main__":
    unittest.main()
