"""Minimal Conjecture script against the null adapter."""
from __future__ import annotations

from conjecture_behaviour_runner import (
    CognitionPin,
    ConjectureScript,
    DialogueTurn,
    InvariantSpec,
    LlmMode,
    NullControlPlaneAdapter,
    run_script,
)


def main() -> None:
    script = ConjectureScript(
        script_id="minimal",
        description="smoke: pin present + always_true invariant",
        conversation_id="conv_minimal",
        turns=[
            DialogueTurn(
                user_text="continue",
                pin=CognitionPin(task_intent="continue", reason="example"),
                invariants=[InvariantSpec(kind="always_true")],
            ),
        ],
    )
    result = run_script(
        script, adapter=NullControlPlaneAdapter(), llm_mode=LlmMode.STUB
    )
    print("passed:", result.passed)
    if not result.passed:
        print("failures:", result.failures)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
