"""CLI surface — version integrity, path-faithful prove, subcommands."""
from __future__ import annotations

import io
import re
from contextlib import redirect_stdout
from pathlib import Path

import conjecture_behaviour_runner
from conjecture_behaviour_runner._version import __version__ as SRC_VERSION
from conjecture_behaviour_runner._version import get_version
from conjecture_behaviour_runner.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_source_version_locked() -> None:
    assert SRC_VERSION == "0.1.5"
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{SRC_VERSION}"' in text
    assert conjecture_behaviour_runner.__version__ == SRC_VERSION


def test_cli_version_prints_get_version() -> None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(["--version"])
    assert code == 0
    printed = buf.getvalue().strip()
    assert printed == get_version()
    assert re.match(r"^\d+\.\d+\.\d+", printed)


def test_cli_path_faithful_prove_bugs() -> None:
    assert main(["path-faithful", "--prove-bugs"]) == 0


def test_cli_demo() -> None:
    assert main(["demo"]) == 0


def test_cli_help_lists_ui_and_path_faithful() -> None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        try:
            main(["--help"])
        except SystemExit as exc:
            assert exc.code in (0, None)
    help_text = buf.getvalue()
    assert "path-faithful" in help_text
    assert "ui" in help_text
    assert "run" in help_text
