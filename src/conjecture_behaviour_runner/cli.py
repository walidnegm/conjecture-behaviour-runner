"""Minimal CLI for the public package."""
from __future__ import annotations

import argparse
import json
import sys

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="conjecture",
        description="Conjecture Behaviour Runner (portable extract)",
    )
    parser.add_argument("--version", action="store_true")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the built-in smoke script against NullControlPlaneAdapter",
    )
    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    if args.demo:
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
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
