"""Local browser UI for Conjecture demos (stdlib only — no Flask/FastAPI).

  conjecture ui
  # open http://127.0.0.1:8765

Shows the path-faithful sole-continue story, run results, and planted-bug proof
in plain English. For contributors who want a visual before reading the SPEC.
"""
from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional
from urllib.parse import urlparse


def _json_response(handler: BaseHTTPRequestHandler, code: int, payload: Any) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _html_page() -> bytes:
    # Single-file UI — keep dependencies at zero.
    html = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Conjecture — local runner</title>
  <style>
    :root { font-family: ui-sans-serif, system-ui, sans-serif; color: #18181b; }
    body { margin: 0; background: #fafafa; }
    main { max-width: 52rem; margin: 0 auto; padding: 1.5rem; }
    h1 { font-size: 1.5rem; margin: 0 0 .5rem; }
    .muted { color: #52525b; font-size: .9rem; line-height: 1.5; }
    .card { background: #fff; border: 1px solid #e4e4e7; border-radius: .75rem;
            padding: 1rem; margin: 1rem 0; box-shadow: 0 1px 2px rgb(0 0 0 / 4%); }
    .row { display: flex; flex-wrap: wrap; gap: .5rem; align-items: center; }
    button { background: #18181b; color: #fff; border: 0; border-radius: .4rem;
             padding: .55rem 1rem; font-size: .875rem; cursor: pointer; }
    button.secondary { background: #fff; color: #18181b; border: 1px solid #d4d4d8; }
    button:disabled { opacity: .5; cursor: wait; }
    .badge { font-size: .7rem; font-weight: 700; border-radius: 999px; padding: .15rem .5rem; }
    .pass { background: #ecfdf5; color: #047857; }
    .fail { background: #fef2f2; color: #b91c1c; }
    .turn { border: 1px solid #e4e4e7; border-radius: .6rem; padding: .75rem; margin: .6rem 0; }
    .turn.ok { border-color: #a7f3d0; background: #f0fdf4; }
    .turn.bad { border-color: #fecaca; background: #fef2f2; }
    code, .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .75rem; }
    ul { margin: .35rem 0; padding-left: 1.2rem; }
    pre { background: #18181b; color: #f4f4f5; padding: .75rem; border-radius: .5rem;
          overflow: auto; font-size: .7rem; max-height: 18rem; }
    .grid2 { display: grid; gap: .75rem; }
    @media (min-width: 640px) { .grid2 { grid-template-columns: 1fr 1fr; } }
  </style>
</head>
<body>
<main>
  <h1>Conjecture local runner</h1>
  <p class="muted">
    Catch agent bugs that still look fine in chat. This UI runs the built-in
    path-faithful mini-app: a tiny real <code>handle()</code>, frozen cognition,
    and state-law checks (owner · pin · mid-flight). Not a chat quality grader.
  </p>

  <div class="card">
    <div class="row" style="margin-bottom:.75rem">
      <strong>Five concepts only (start here)</strong>
    </div>
    <p class="muted" style="margin:0">
      <strong>Script</strong> · <strong>Turn</strong> · <strong>Driver</strong> ·
      <strong>Observation</strong> · <strong>Invariant</strong>.
      Everything else (Scenario, ODD, multi-runner, Verdict) is advanced — see docs/SPEC.md.
    </p>
  </div>

  <div class="card">
    <div class="row" style="justify-content:space-between">
      <strong>Actions</strong>
      <span class="muted mono" id="status"></span>
    </div>
    <div class="row" style="margin-top:.75rem">
      <button id="btnHealthy" type="button">Run healthy story</button>
      <button id="btnProve" class="secondary" type="button">Prove planted bugs</button>
    </div>
  </div>

  <div class="card" id="storyCard">
    <strong id="storyTitle">Loading story…</strong>
    <p class="muted" id="storyWhy"></p>
    <p class="muted" id="storyPlot"></p>
    <p class="muted" id="storyGreen"></p>
    <div id="plannedTurns"></div>
  </div>

  <div class="card" id="resultCard" style="display:none">
    <div class="row">
      <strong>What just ran</strong>
      <span id="resultBadge" class="badge"></span>
      <span class="muted mono" id="resultMeta"></span>
    </div>
    <div id="resultTurns"></div>
  </div>

  <div class="card" id="proveCard" style="display:none">
    <div class="row">
      <strong>Planted-bug proof</strong>
      <span id="proveBadge" class="badge"></span>
    </div>
    <p class="muted">Same story four ways: clean must PASS; three deliberate state bugs must FAIL.</p>
    <div class="grid2" id="proveGrid"></div>
  </div>

  <div class="card">
    <strong>Contributor first code</strong>
    <pre id="snippet">from conjecture_behaviour_runner import (
    ConjectureScript, DialogueTurn, InvariantSpec, CognitionPin,
    run_script, LlmMode,
)
from conjecture_behaviour_runner.path_faithful import MiniAppAdapter, MiniChatApp

script = ConjectureScript(
    script_id="demo",
    description="continue keeps owner and pin",
    conversation_id="conv_1",
    turns=[
        DialogueTurn(
            user_text="cost out the onboarding workflow",
            pin=CognitionPin(task_intent="new_task", read_kind="cost_out"),
            invariants=[
                InvariantSpec(kind="exclusive_owner", expected="cost_out"),
                InvariantSpec(kind="pin_present", expected="workflow_id"),
            ],
        ),
        DialogueTurn(
            user_text="make the volume 10k",
            pin=CognitionPin(task_intent="continue"),
            invariants=[
                InvariantSpec(kind="exclusive_owner", expected="cost_out"),
                InvariantSpec(kind="pin_equals",
                              expected={"key": "workflow_id", "value": "wf_1"}),
            ],
        ),
    ],
)
result = run_script(script, adapter=MiniAppAdapter(MiniChatApp()), llm_mode=LlmMode.STUB)
assert result.passed</pre>
  </div>
</main>
<script>
async function api(path) {
  const r = await fetch(path, { method: 'POST' });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
function badge(el, ok) {
  el.textContent = ok ? 'PASS' : 'FAIL';
  el.className = 'badge ' + (ok ? 'pass' : 'fail');
}
function renderPlanned(story) {
  document.getElementById('storyTitle').textContent = story.title || 'Story';
  document.getElementById('storyWhy').textContent = story.why || '';
  document.getElementById('storyPlot').innerHTML = '<strong>The story:</strong> ' + (story.plot || '');
  document.getElementById('storyGreen').innerHTML = '<strong>Green means:</strong> ' + (story.what_green_means || '');
  const box = document.getElementById('plannedTurns');
  box.innerHTML = (story.turns || []).map(t => `
    <div class="turn">
      <div class="mono">t${t.index}</div>
      <div>${t.story || ''}</div>
      <div class="muted">User: “${t.user_says || ''}”</div>
      <ul>${(t.must_hold || []).map(m => `<li>${m}</li>`).join('')}</ul>
    </div>`).join('');
}
function renderResult(data) {
  const card = document.getElementById('resultCard');
  card.style.display = 'block';
  badge(document.getElementById('resultBadge'), !!data.passed);
  document.getElementById('resultMeta').textContent =
    (data.script_id || '') + (data.bug ? ' · bug=' + data.bug : '');
  const turns = data.turns || [];
  document.getElementById('resultTurns').innerHTML = turns.map(t => `
    <div class="turn ${t.passed ? 'ok' : 'bad'}">
      <div class="row">
        <span class="mono">turn ${t.index}</span>
        <span class="badge ${t.passed ? 'pass' : 'fail'}">${t.passed ? 'PASS' : 'FAIL'}</span>
      </div>
      <div>${t.story || ''}</div>
      <div class="muted">User: “${t.user_text || ''}”</div>
      <div class="grid2" style="margin-top:.5rem">
        <div>
          <div class="muted"><strong>Must hold</strong></div>
          <ul>${(t.must_hold || []).map(m => `<li>${m}</li>`).join('') || '<li>—</li>'}</ul>
        </div>
        <div>
          <div class="muted"><strong>Measured</strong></div>
          <div class="mono">owner=${t.exclusive_owner ?? '—'} · kind=${t.active_kind ?? '—'}</div>
          <div class="mono">pins=${JSON.stringify(t.pins || {})}</div>
          ${(t.failures || []).map(f => `<div style="color:#b91c1c">${f}</div>`).join('')}
        </div>
      </div>
    </div>`).join('');
}
function renderProve(data) {
  document.getElementById('proveCard').style.display = 'block';
  badge(document.getElementById('proveBadge'), !!data.helpful);
  const items = [
    ['clean_passes', 'Healthy PASS'],
    ['owner_steal_caught', 'Owner steal → FAIL'],
    ['drop_pin_caught', 'Drop pin → FAIL'],
    ['illegal_restart_caught', 'Illegal restart → FAIL'],
  ];
  document.getElementById('proveGrid').innerHTML = items.map(([k, label]) => `
    <div class="turn ${data[k] ? 'ok' : 'bad'}">
      <div class="muted">${label}</div>
      <span class="badge ${data[k] ? 'pass' : 'fail'}">${data[k] ? 'yes' : 'no'}</span>
    </div>`).join('');
  if (data.details && data.details.clean) renderResult(data.details.clean);
}
async function loadStory() {
  const r = await fetch('/api/story');
  renderPlanned(await r.json());
}
document.getElementById('btnHealthy').onclick = async () => {
  const st = document.getElementById('status');
  const b1 = document.getElementById('btnHealthy');
  const b2 = document.getElementById('btnProve');
  b1.disabled = b2.disabled = true; st.textContent = 'running…';
  try {
    const data = await api('/api/run-healthy');
    renderResult(data);
    document.getElementById('proveCard').style.display = 'none';
    st.textContent = data.passed ? 'healthy PASS' : 'healthy FAIL';
  } catch (e) { st.textContent = String(e); }
  finally { b1.disabled = b2.disabled = false; }
};
document.getElementById('btnProve').onclick = async () => {
  const st = document.getElementById('status');
  const b1 = document.getElementById('btnHealthy');
  const b2 = document.getElementById('btnProve');
  b1.disabled = b2.disabled = true; st.textContent = 'proving…';
  try {
    const data = await api('/api/prove-bugs');
    renderProve(data);
    st.textContent = data.helpful ? 'prove-bugs helpful' : 'prove-bugs unexpected';
  } catch (e) { st.textContent = String(e); }
  finally { b1.disabled = b2.disabled = false; }
};
loadStory();
</script>
</body>
</html>
"""
    return html.encode("utf-8")


def _make_handler() -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:  # quieter default
            if "/api/" in (args[0] if args else ""):
                super().log_message(fmt, *args)

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path in ("/", "/index.html"):
                body = _html_page()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if path == "/api/story":
                from conjecture_behaviour_runner.path_faithful import sole_continue_story

                _json_response(self, 200, sole_continue_story())
                return
            _json_response(self, 404, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            try:
                if path == "/api/run-healthy":
                    from conjecture_behaviour_runner.path_faithful import (
                        run_path_faithful_demo,
                    )

                    _json_response(self, 200, run_path_faithful_demo(bug=None))
                    return
                if path == "/api/prove-bugs":
                    from conjecture_behaviour_runner.path_faithful import (
                        prove_planted_bugs,
                    )

                    _json_response(self, 200, prove_planted_bugs())
                    return
            except Exception as exc:  # noqa: BLE001
                _json_response(self, 500, {"error": str(exc)})
                return
            _json_response(self, 404, {"error": "not_found"})

    return Handler


def serve_ui(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
) -> None:
    """Block and serve the local Conjecture UI."""
    handler = _make_handler()
    httpd = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{port}/"
    print(f"Conjecture UI → {url}")
    print("  Run healthy story · Prove planted bugs · story timeline")
    print("Ctrl+C to stop.")
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()


def main(argv: Optional[list[str]] = None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="conjecture ui")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-browser", action="store_true")
    args = p.parse_args(argv)
    serve_ui(host=args.host, port=args.port, open_browser=not args.no_browser)
    return 0
