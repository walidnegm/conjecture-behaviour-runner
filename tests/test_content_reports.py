"""The console's Content view reads content-eval reports from one folder, safely (0.1.7)."""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from conjecture_behaviour_runner.content_reports import get_report, list_reports
from conjecture_behaviour_runner.ui_server import _html_page, _make_handler

REPORT = {
    "suite": "glossary", "stages": ["retrieve", "select", "answer"], "ran_at": "2026-11-12T17:00:00",
    "model_calls": 17, "passed": 1, "cases": 2,
    "rates": {"top1": 0.5, "forbidden_selection": 0.5},
    "results": [{"case": "a", "passed": True, "judged": {"faithfulness": {"score": 1.0, "reason": "ok"}}}],
}


@pytest.fixture()
def reports(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setenv("CONJECTURE_CONTENT_REPORTS_DIR", str(tmp_path))
    (tmp_path / "glossary-1.json").write_text(json.dumps(REPORT))
    (tmp_path / "broken.json").write_text("{not json")
    (tmp_path.parent / "secret.json").write_text(json.dumps({"secret": True}))
    return tmp_path


def test_list_and_get(reports: Path) -> None:
    listed = list_reports()
    names = {i["file"]: i for i in listed["items"]}
    assert names["glossary-1.json"]["passed"] == 1
    assert names["broken.json"]["error"] == "unreadable"
    assert get_report("glossary-1.json")["model_calls"] == 17


def test_only_bare_json_names_in_the_folder(reports: Path) -> None:
    for name in ("../secret.json", "..%2Fsecret.json", "/etc/passwd", ".hidden.json", "glossary-1.txt", ""):
        assert get_report(name) is None, name


def test_routes_and_the_view(reports: Path) -> None:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _make_handler())
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        base = f"http://127.0.0.1:{port}"
        with urllib.request.urlopen(f"{base}/api/content-reports") as r:
            assert json.loads(r.read())["count"] == 2
        with urllib.request.urlopen(f"{base}/api/content-reports/glossary-1.json") as r:
            assert json.loads(r.read())["suite"] == "glossary"
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(f"{base}/api/content-reports/..%2Fsecret.json")
        assert e.value.code == 404
    finally:
        httpd.shutdown()
    page = _html_page().decode("utf-8")
    assert 'data-view="content"' in page and "loadContentReports" in page
