#!/usr/bin/env python3
"""Standalone multi-turn chat host — ZERO Conjecture imports.

Portability proof: Conjecture must catch control-plane bugs in an application
that does not depend on the Conjecture package. Interaction is HTTP only.

POST /chat
  body: { "message": "...", "pin": { "task_intent": "new_task"|"continue"|... } }
  response: {
    "reply": "...",
    "debug": {
      "owner": "...",
      "kind": "...",
      "pins": {...},
      "outcome": "...",
      "extras": { "blocks_resolve": true|false }
    }
  }

Planted bugs (constructor / --bug):
  owner_steal      — continue reports front_door while task still active
  drop_pin         — continue clears workflow_id
  illegal_restart  — continue wipes the task

Note: owner_steal is *wrong exclusive owner* (steal), not two concurrent owners.
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional
from urllib.parse import urlparse


class Ledger:
    def __init__(self) -> None:
        self.exclusive_owner: Optional[str] = None
        self.active_kind: Optional[str] = None
        self.pins: dict[str, Any] = {}

    def clear(self) -> None:
        self.exclusive_owner = None
        self.active_kind = None
        self.pins.clear()


class ChatApp:
    """Naive mid-flight cost-out machine with optional planted bugs."""

    def __init__(self, *, bug: Optional[str] = None) -> None:
        # Accept legacy alias dual_owner → owner_steal
        if bug == "dual_owner":
            bug = "owner_steal"
        self.bug = bug
        self.ledger = Ledger()
        self.messages: list[str] = []

    def handle(self, message: str, pin: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        self.messages.append(message)
        intent = "continue"
        if isinstance(pin, dict):
            intent = str(pin.get("task_intent") or "continue").strip() or "continue"

        if intent == "detour":
            self.ledger.exclusive_owner = "front_door"
            self.ledger.active_kind = None
            self.ledger.pins.clear()
            return self._obs("detour_superseded", blocks_resolve=False)

        if intent == "new_task":
            self.ledger.active_kind = "cost_out"
            self.ledger.exclusive_owner = "cost_out"
            if "workflow_id" not in self.ledger.pins:
                self.ledger.pins["workflow_id"] = "wf_1"
            return self._obs("continue_owned", blocks_resolve=True)

        if self.ledger.active_kind and intent == "continue":
            if self.bug == "owner_steal":
                # Wrong exclusive owner while mid-flight (steal) — not two owners.
                self.ledger.exclusive_owner = "front_door"
                return self._obs("continue_owned", blocks_resolve=True)
            if self.bug == "drop_pin":
                self.ledger.pins.pop("workflow_id", None)
                self.ledger.exclusive_owner = "cost_out"
                return self._obs("continue_owned", blocks_resolve=True)
            if self.bug == "illegal_restart":
                self.ledger.clear()
                return self._obs("front_door", blocks_resolve=False)
            self.ledger.exclusive_owner = self.ledger.active_kind
            return self._obs("continue_owned", blocks_resolve=True)

        self.ledger.exclusive_owner = "front_door"
        return self._obs("front_door", blocks_resolve=False)

    def _obs(self, outcome: str, *, blocks_resolve: bool) -> dict[str, Any]:
        return {
            "reply": (
                f"[external app] owner={self.ledger.exclusive_owner} "
                f"kind={self.ledger.active_kind} pins={self.ledger.pins}"
            ),
            "debug": {
                "owner": self.ledger.exclusive_owner,
                "kind": self.ledger.active_kind,
                "pins": dict(self.ledger.pins),
                "outcome": outcome,
                "extras": {"blocks_resolve": blocks_resolve},
            },
        }


def make_handler(app: ChatApp) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            return

        def do_GET(self) -> None:  # noqa: N802
            if urlparse(self.path).path in ("/health", "/"):
                body = b'{"ok":true,"app":"external_http_app","conjecture_import":false}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_error(404)

        def do_POST(self) -> None:  # noqa: N802
            if urlparse(self.path).path not in ("/chat", "/"):
                self.send_error(404)
                return
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b"{}"
            try:
                body = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self.send_error(400, "invalid json")
                return
            if not isinstance(body, dict):
                self.send_error(400, "object required")
                return
            message = str(body.get("message") or body.get("user_text") or "")
            pin = body.get("pin") if isinstance(body.get("pin"), dict) else None
            payload = app.handle(message, pin=pin)
            data = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="External HTTP SUT (no Conjecture imports)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8790)
    p.add_argument(
        "--bug",
        choices=["owner_steal", "dual_owner", "drop_pin", "illegal_restart"],
        default=None,
        help="Plant a state-law bug (dual_owner is legacy alias for owner_steal)",
    )
    args = p.parse_args(argv)
    app = ChatApp(bug=args.bug)
    httpd = ThreadingHTTPServer((args.host, args.port), make_handler(app))
    print(
        f"external_http_app → http://{args.host}:{args.port}/chat  "
        f"bug={args.bug!r}  (no conjecture imports)"
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
