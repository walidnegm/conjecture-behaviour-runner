#!/usr/bin/env python3
"""Minimal HTTP host for Conjecture — proves the generic Driver without Bot0.

Serves MiniChatApp over POST /chat with a portable ``debug`` observation envelope:

  {
    "reply": "...",
    "debug": {
      "owner": "cost_out",
      "kind": "cost_out",
      "pins": {"workflow_id": "wf_1"},
      "outcome": "continue_owned",
      "extras": {"blocks_resolve": true}
    }
  }

Run (leave terminal open)::

  python examples/http_debug_app.py --port 8766 --bug owner_steal

Then in another shell::

  python examples/http_e2e.py --endpoint http://127.0.0.1:8766/chat

This is the activation path for apps that are *not* the Conversation Control Plane
package — any stack that can return owner/pins JSON works the same way.
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional
from urllib.parse import urlparse

from conjecture_behaviour_runner.pins import CognitionPin
from conjecture_behaviour_runner.path_faithful import MiniChatApp


def _pin_from_body(body: dict[str, Any]) -> Optional[CognitionPin]:
    raw = body.get("pin")
    if raw is None:
        return None
    if isinstance(raw, dict):
        return CognitionPin.from_dict(raw)
    return None


def make_handler(app: MiniChatApp) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            return  # quiet

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path not in ("/chat", "/"):
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
                self.send_error(400, "json object required")
                return
            message = str(body.get("message") or body.get("user_text") or "")
            pin = _pin_from_body(body)
            obs = app.handle(message, pin=pin)
            payload = {
                "reply": (
                    f"[http host] owner={obs.exclusive_owner} "
                    f"kind={obs.active_kind} pins={obs.pins}"
                ),
                "debug": {
                    "owner": obs.exclusive_owner,
                    "kind": obs.active_kind,
                    "pins": dict(obs.pins),
                    "outcome": obs.observed_outcome,
                    "extras": dict(obs.extras or {}),
                },
            }
            data = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
            if urlparse(self.path).path in ("/health", "/"):
                data = b'{"ok":true,"app":"conjecture-http-debug"}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            self.send_error(404)

    return Handler


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="HTTP debug host for Conjecture demos")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8766)
    p.add_argument(
        "--bug",
        choices=["owner_steal", "dual_owner", "drop_pin", "illegal_restart"],
        default=None,
        help="Plant a control-plane bug in the host",
    )
    args = p.parse_args(argv)
    app = MiniChatApp(bug=args.bug)
    httpd = ThreadingHTTPServer((args.host, args.port), make_handler(app))
    print(f"HTTP debug host → http://{args.host}:{args.port}/chat  bug={args.bug!r}")
    print("Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
