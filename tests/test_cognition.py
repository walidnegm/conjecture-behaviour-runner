"""Cognition freeze / record / stub providers."""
from __future__ import annotations

from pathlib import Path

from conjecture_behaviour_runner import (
    CognitionPin,
    ConjectureScript,
    DialogueTurn,
    FreezeStore,
    InvariantSpec,
    LlmMode,
    NullControlPlaneAdapter,
    run_script,
)
from conjecture_behaviour_runner.cognition import (
    CognitionDecision,
    FreezeArtifact,
    FreezeCognitionProvider,
    RecordCognitionProvider,
    StubCognitionProvider,
    provider_for_mode,
)


def test_stub_provider_returns_turn_pin() -> None:
    pin = CognitionPin(task_intent="continue", reason="x")
    turn = DialogueTurn(user_text="hi", pin=pin)
    prov = StubCognitionProvider()
    dec = prov.resolve(turn, state={}, script_id="s", turn_index=0)
    assert dec.pin.task_intent == "continue"
    assert dec.source == "stub"


def test_freeze_roundtrip(tmp_path: Path) -> None:
    store = FreezeStore(tmp_path)
    pin = CognitionPin(task_intent="new_task", reason="freeze_me")
    dec = CognitionDecision(pin=pin, source="record", freeze_key="k1")
    store.save(FreezeArtifact(freeze_key="k1", decision=dec))
    loaded = store.load("k1")
    assert loaded.decision.pin.task_intent == "new_task"
    assert store.exists("k1")


def test_record_provider_writes_freeze(tmp_path: Path) -> None:
    store = FreezeStore(tmp_path)
    pin = CognitionPin(task_intent="continue", freeze_key="rec1", reason="r")
    turn = DialogueTurn(user_text="go", pin=pin, freeze_key="rec1")
    prov = RecordCognitionProvider(store)
    dec = prov.resolve(turn, state={}, script_id="s", turn_index=0)
    assert dec.pin.task_intent == "continue"
    assert store.exists("rec1")


def test_provider_for_mode_stub() -> None:
    p = provider_for_mode("stub")
    assert isinstance(p, StubCognitionProvider)


def test_run_script_freeze_mode(tmp_path: Path) -> None:
    pin = CognitionPin(task_intent="continue", freeze_key="run_freeze", reason="f")
    store = FreezeStore(tmp_path)
    store.save(
        FreezeArtifact(
            freeze_key="run_freeze",
            decision=CognitionDecision(pin=pin, source="record", freeze_key="run_freeze"),
        )
    )
    script = ConjectureScript(
        script_id="fz",
        description="freeze",
        conversation_id="c",
        turns=[
            DialogueTurn(
                user_text="x",
                freeze_key="run_freeze",
                invariants=[InvariantSpec(kind="always_true")],
            )
        ],
    )
    result = run_script(
        script,
        adapter=NullControlPlaneAdapter(),
        llm_mode=LlmMode.FREEZE,
        freeze_dir=tmp_path,
    )
    assert result.passed


def test_freeze_provider_fail_closed_missing(tmp_path: Path) -> None:
    prov = FreezeCognitionProvider(FreezeStore(tmp_path))
    turn = DialogueTurn(user_text="x", freeze_key="missing")
    try:
        prov.resolve(turn, state={}, script_id="s", turn_index=0)
        raise AssertionError("expected FileNotFoundError")
    except FileNotFoundError:
        pass
