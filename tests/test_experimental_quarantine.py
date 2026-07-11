"""Fix #3 + #5: scenario/trajectory quarantined; PyYAML declared optional."""
from __future__ import annotations

import importlib
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "src" / "conjecture_behaviour_runner"


class ExperimentalQuarantineTests(unittest.TestCase):
    def test_not_on_package_root(self) -> None:
        for name in ("scenario_models.py", "trajectory.py", "schema.json"):
            self.assertFalse(
                (PKG / name).exists(),
                msg=f"{name} must not live on the stable package root",
            )

    def test_under_experimental(self) -> None:
        exp = PKG / "experimental"
        for name in ("scenario_models.py", "trajectory.py", "schema.json", "__init__.py"):
            self.assertTrue((exp / name).is_file(), msg=name)

    def test_import_path(self) -> None:
        mod = importlib.import_module(
            "conjecture_behaviour_runner.experimental.scenario_models"
        )
        self.assertTrue(hasattr(mod, "Scenario"))
        self.assertTrue(hasattr(mod, "load_scenario_from_yaml"))
        traj = importlib.import_module(
            "conjecture_behaviour_runner.experimental.trajectory"
        )
        self.assertTrue(hasattr(traj, "Trajectory"))

    def test_not_exported_from_package_root(self) -> None:
        import conjecture_behaviour_runner as cbr

        self.assertFalse(hasattr(cbr, "Scenario"))
        self.assertFalse(hasattr(cbr, "Trajectory"))
        self.assertFalse(hasattr(cbr, "load_scenario_from_yaml"))

    def test_yaml_loader_mentions_scenarios_extra(self) -> None:
        from conjecture_behaviour_runner.experimental import scenario_models as sm

        src = Path(sm.__file__).read_text(encoding="utf-8")
        self.assertIn("conjecture-behaviour-runner[scenarios]", src)
        self.assertIn("PyYAML", src)


class PyYamlOptionalDeclared(unittest.TestCase):
    def test_pyproject_declares_scenarios_extra(self) -> None:
        text = (PKG.parents[1] / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("scenarios", text)
        self.assertIn("PyYAML", text)


if __name__ == "__main__":
    unittest.main()
