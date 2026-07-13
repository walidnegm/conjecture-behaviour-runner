"""Incident → pattern library: playbook + portable seed scripts load."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from conjecture_behaviour_runner import LlmMode, load_script_json, run_script
from conjecture_behaviour_runner.path_faithful import MiniAppAdapter, MiniChatApp

ROOT = Path(__file__).resolve().parents[1]
INCIDENTS = ROOT / "incidents"
PATTERNS = INCIDENTS / "patterns"

# Every portable seed that must pass healthy mini-app + have a CATALOG row.
PORTABLE_SEEDS: tuple[tuple[str, str | None], ...] = (
    ("owner_steal_mid_continue", "owner_steal"),
    ("drop_pin_mid_continue", "drop_pin"),
    ("illegal_restart_mid_continue", "illegal_restart"),
    ("pin_without_open", "pin_without_open"),
    ("cold_system_suggest_miss", "cold_system_suggest_miss"),
    ("hollow_async_advance", "hollow_async_advance"),
)


class IncidentLibraryTests(unittest.TestCase):
    def test_playbook_and_catalog_exist(self) -> None:
        self.assertTrue((INCIDENTS / "README.md").is_file())
        self.assertTrue((INCIDENTS / "CATALOG.md").is_file())
        self.assertTrue((INCIDENTS / "_template" / "script.json").is_file())
        self.assertTrue((INCIDENTS / "_template" / "INCIDENT.md").is_file())
        readme = (INCIDENTS / "README.md").read_text(encoding="utf-8")
        self.assertIn("Conjecture-type", readme)
        self.assertIn("Scenario", readme)
        self.assertIn("script.json", readme)
        self.assertIn("CATALOG", readme)
        self.assertIn("patterns inventory", readme.lower())
        catalog = (INCIDENTS / "CATALOG.md").read_text(encoding="utf-8")
        # Must not pretend four seeds are the only known classes.
        self.assertIn("Broader failure modes", catalog)
        # Plain failure modes (not only snake_case slugs as “the mode”)
        self.assertIn("Packaging steal", catalog)
        self.assertIn("Missing session leaf", catalog)
        self.assertIn("Hollow open", catalog)
        self.assertIn("packaging_too_wide", catalog)  # slug still listed as id

    def test_catalog_lists_every_pattern_folder(self) -> None:
        catalog = (INCIDENTS / "CATALOG.md").read_text(encoding="utf-8")
        folders = sorted(
            p.name for p in PATTERNS.iterdir() if p.is_dir() and not p.name.startswith("_")
        )
        self.assertTrue(folders, "expected at least one patterns/<slug>/ folder")
        for slug in folders:
            self.assertIn(slug, catalog, f"CATALOG.md missing slug {slug}")
            self.assertTrue(
                (PATTERNS / slug / "INCIDENT.md").is_file(),
                f"missing INCIDENT.md for {slug}",
            )
            self.assertTrue(
                (PATTERNS / slug / "script.json").is_file(),
                f"missing script.json for {slug}",
            )

    def test_catalog_table_slugs_have_folders(self) -> None:
        catalog = (INCIDENTS / "CATALOG.md").read_text(encoding="utf-8")
        # Rows like | `slug` | ...
        found = re.findall(r"\|\s*`([a-z0-9_]+)`\s*\|", catalog)
        # Filter to known pattern-like ids (skip code ticks in prose if any)
        for slug in found:
            if slug in {"script_id", "workflow_id", "cost_out"}:
                continue
            if (PATTERNS / slug).is_dir():
                continue
            # Allow non-folder backticks only if not in index section — require folder
            if (
                slug.endswith("_continue")
                or slug in (
                    "pin_without_open",
                    "cold_system_suggest_miss",
                    "hollow_async_advance",
                )
            ):
                self.fail(f"CATALOG lists `{slug}` but patterns/{slug}/ missing")

    def test_portable_seeds_pass_on_healthy_app(self) -> None:
        for slug, _bug in PORTABLE_SEEDS:
            path = PATTERNS / slug / "script.json"
            self.assertTrue(path.is_file(), path)
            script = load_script_json(str(path))
            result = run_script(
                script,
                adapter=MiniAppAdapter(MiniChatApp()),
                llm_mode=LlmMode.STUB,
            )
            self.assertTrue(
                result.passed,
                f"{slug} should PASS healthy: {result.failures}",
            )

    def test_portable_seeds_fail_on_planted_bug(self) -> None:
        for slug, bug in PORTABLE_SEEDS:
            if not bug:
                continue
            path = PATTERNS / slug / "script.json"
            script = load_script_json(str(path))
            result = run_script(
                script,
                adapter=MiniAppAdapter(MiniChatApp(bug=bug)),
                llm_mode=LlmMode.STUB,
            )
            self.assertFalse(
                result.passed,
                f"{slug} should FAIL on bug={bug}",
            )

    def test_pin_without_open_failure_mentions_blocks(self) -> None:
        path = PATTERNS / "pin_without_open" / "script.json"
        script = load_script_json(str(path))
        result = run_script(
            script,
            adapter=MiniAppAdapter(MiniChatApp(bug="pin_without_open")),
            llm_mode=LlmMode.STUB,
        )
        self.assertFalse(result.passed)
        joined = " ".join(result.failures)
        self.assertTrue(
            "blocks_resolve" in joined or "extra_true" in joined or "extra" in joined,
            result.failures,
        )


if __name__ == "__main__":
    unittest.main()
