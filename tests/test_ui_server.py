"""Local UI server — story + prove-bugs API (stdlib HTTP)."""
from __future__ import annotations

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from conjecture_behaviour_runner.ui_server import _make_handler


def test_ui_story_and_prove_bugs() -> None:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _make_handler())
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/story") as resp:
            story = json.load(resp)
        assert "plot" in story
        assert len(story.get("turns") or []) >= 1

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/prove-bugs", method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            report = json.load(resp)
        assert report.get("helpful") is True
        assert report.get("clean_passes") is True
    finally:
        httpd.shutdown()
