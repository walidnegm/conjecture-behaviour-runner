"""Conjecture CLI — discover and run scripts, path-faithful demo, reports."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from conjecture_behaviour_runner import (
    CognitionPin,
    ConjectureScript,
    DialogueTurn,
    InvariantSpec,
    LlmMode,
    NullControlPlaneAdapter,
    __version__,
    run_script,
)
from conjecture_behaviour_runner.discover import discover_scripts
from conjecture_behaviour_runner.report import (
    results_to_json_report,
    write_json_report,
    write_junit_report,
)


def _cmd_demo(_: argparse.Namespace) -> int:
    script = ConjectureScript(
        script_id="public_demo",
        description="null-adapter smoke",
        conversation_id="conv_public_demo",
        turns=[
            DialogueTurn(
                user_text="hello",
                pin=CognitionPin(task_intent="continue", reason="demo"),
                invariants=[InvariantSpec(kind="always_true")],
            ),
        ],
    )
    result = run_script(
        script, adapter=NullControlPlaneAdapter(), llm_mode=LlmMode.STUB
    )
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.passed else 1


def _cmd_path_faithful(args: argparse.Namespace) -> int:
    from conjecture_behaviour_runner.path_faithful import (
        prove_planted_bugs,
        run_path_faithful_demo,
    )

    if args.prove_bugs:
        report = prove_planted_bugs()
        print(json.dumps(report, indent=2))
        ok = (
            report["clean_passes"]
            and report["dual_owner_caught"]
            and report["drop_pin_caught"]
            and report["illegal_restart_caught"]
        )
        return 0 if ok else 1
    result = run_path_faithful_demo(bug=args.bug or None)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


def _cmd_run(args: argparse.Namespace) -> int:
    roots = args.paths or ["."]
    pairs = discover_scripts(
        roots,
        tags=args.tag or (),
        script_id_prefix=args.script_id or "",
    )
    if not pairs:
        print("No scripts discovered.", file=sys.stderr)
        return 2

    # Adapter selection
    adapter_name = args.adapter or "null"
    if adapter_name == "null":
        adapter = NullControlPlaneAdapter()
    elif adapter_name == "path-faithful":
        from conjecture_behaviour_runner.path_faithful import MiniAppAdapter, MiniChatApp

        adapter = MiniAppAdapter(MiniChatApp(bug=args.bug or None))
    elif adapter_name == "control-plane":
        try:
            from conjecture_behaviour_runner.contrib.control_plane import (
                ControlPlaneStreamAdapter,
            )

            adapter = ControlPlaneStreamAdapter()
        except ImportError as exc:
            print(f"control-plane adapter unavailable: {exc}", file=sys.stderr)
            return 2
    else:
        print(f"Unknown adapter {adapter_name!r}", file=sys.stderr)
        return 2

    freeze_dir = args.freeze_dir
    mode = args.mode or "stub"
    results = []
    for path, script in pairs:
        result = run_script(
            script,
            adapter=adapter,
            llm_mode=mode,
            freeze_dir=freeze_dir,
        )
        results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {script.script_id}  ({path.name})")
        if not result.passed:
            for f in result.failures:
                print(f"        {f}")

    report = results_to_json_report(results)
    if args.json_report:
        write_json_report(args.json_report, report)
        print(f"Wrote JSON report: {args.json_report}")
    if args.junit:
        write_junit_report(args.junit, results)
        print(f"Wrote JUnit report: {args.junit}")

    failed = sum(1 for r in results if not r.passed)
    print(f"\n{report['total']} scripts, {report['passed']} passed, {failed} failed")
    return 1 if failed else 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="conjecture",
        description=(
            "Conjecture Behaviour Runner — contract scripts for multi-turn "
            "control planes (discover, run, report)"
        ),
    )
    parser.add_argument("--version", action="store_true")

    sub = parser.add_subparsers(dest="command")

    p_demo = sub.add_parser("demo", help="Null-adapter smoke script")
    p_demo.set_defaults(func=_cmd_demo)

    p_run = sub.add_parser("run", help="Discover and run script JSON/YAML files")
    p_run.add_argument(
        "paths",
        nargs="*",
        help="Files or directories (default: .)",
    )
    p_run.add_argument(
        "--adapter",
        choices=["null", "path-faithful", "control-plane"],
        default="null",
        help="Host adapter binding",
    )
    p_run.add_argument("--mode", default="stub", help="stub|freeze|record")
    p_run.add_argument("--freeze-dir", default=None, help="Freeze artifact directory")
    p_run.add_argument("--tag", action="append", default=[], help="Require script tag")
    p_run.add_argument("--script-id", default="", help="script_id prefix filter")
    p_run.add_argument("--json-report", default=None, help="Write JSON report path")
    p_run.add_argument("--junit", default=None, help="Write JUnit XML path")
    p_run.add_argument(
        "--bug",
        default=None,
        help="path-faithful only: dual_owner|drop_pin|illegal_restart",
    )
    p_run.set_defaults(func=_cmd_run)

    p_pf = sub.add_parser(
        "path-faithful",
        help="Run mini-app vertical (Act through public handle)",
    )
    p_pf.add_argument(
        "--bug",
        choices=["dual_owner", "drop_pin", "illegal_restart"],
        default=None,
    )
    p_pf.add_argument(
        "--prove-bugs",
        action="store_true",
        help="Clean pass + three planted bugs must fail",
    )
    p_pf.set_defaults(func=_cmd_path_faithful)

    p_ui = sub.add_parser(
        "ui",
        help="Open local browser UI for path-faithful story + planted bugs",
    )
    p_ui.add_argument("--host", default="127.0.0.1")
    p_ui.add_argument("--port", type=int, default=8765)
    p_ui.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open a browser tab automatically",
    )

    def _cmd_ui(ns: argparse.Namespace) -> int:
        from conjecture_behaviour_runner.ui_server import serve_ui

        serve_ui(
            host=ns.host,
            port=ns.port,
            open_browser=not ns.no_browser,
        )
        return 0

    p_ui.set_defaults(func=_cmd_ui)

    # Back-compat: --demo / bare --version
    parser.add_argument(
        "--demo",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    if getattr(args, "demo", False) and not args.command:
        return _cmd_demo(args)
    if not args.command:
        parser.print_help()
        return 0
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
