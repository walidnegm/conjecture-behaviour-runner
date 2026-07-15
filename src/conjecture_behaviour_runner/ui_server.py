"""Local browser UI for Conjecture demos (stdlib only — no Flask/FastAPI).

  conjecture ui
  # open http://127.0.0.1:8765

Shows the path-faithful sole-continue story, run results, planted-bug proof,
and host-authored **candidate Scenarios** (precursor to Scripts) when a
candidates directory is discoverable.

For contributors who want a visual before reading the SPEC.
"""
from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional
from urllib.parse import parse_qs, unquote, urlparse


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
  <title>Conjecture — local console</title>
  <style>
    :root { font-family: ui-sans-serif, system-ui, sans-serif; color: #18181b; }
    body { margin: 0; background: #fafafa; }
    main { max-width: 56rem; margin: 0 auto; padding: 1.5rem; }
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
    .open { background: #fff7ed; color: #c2410c; }
    .partial { background: #eff6ff; color: #1d4ed8; }
    .reg { background: #f4f4f5; color: #3f3f46; }
    .turn { border: 1px solid #e4e4e7; border-radius: .6rem; padding: .75rem; margin: .6rem 0; }
    .turn.ok { border-color: #a7f3d0; background: #f0fdf4; }
    .turn.bad { border-color: #fecaca; background: #fef2f2; }
    .cand { cursor: pointer; }
    .cand:hover { border-color: #a1a1aa; }
    .cand.active { border-color: #3b82f6; background: #eff6ff; }
    .cand a { color: #1d4ed8; text-decoration: none; font-weight: 600; }
    .cand a:hover { text-decoration: underline; }
    .cand-tab.active { background: #18181b; color: #fff; border-color: #18181b; }
    .deep-link { font-size: .8rem; padding: .25rem .5rem; border: 1px solid #d4d4d8;
      border-radius: .35rem; background: #fafafa; color: #1d4ed8; text-decoration: none; }
    .deep-link:hover { background: #eff6ff; }
    code, .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .75rem; }
    ul { margin: .35rem 0; padding-left: 1.2rem; }
    pre { background: #18181b; color: #f4f4f5; padding: .75rem; border-radius: .5rem;
          overflow: auto; font-size: .7rem; max-height: 18rem; }
    select, input[type=search] { font: inherit; font-size: .85rem; padding: .4rem .55rem;
      border: 1px solid #d4d4d8; border-radius: .4rem; background: #fff; }
    .grid2 { display: grid; gap: .75rem; }
    @media (min-width: 640px) { .grid2 { grid-template-columns: 1fr 1fr; } }
    /* Pipeline tracker — same contract as product Prose → Draft IR → Save */
    .pipe { display: flex; flex-wrap: wrap; align-items: center; gap: .35rem;
            margin: .5rem 0 .85rem; font-size: .7rem; }
    .pipe-stage { border-radius: .35rem; padding: .2rem .45rem; border: 1px solid #e4e4e7;
                  background: #fff; color: #71717a; white-space: nowrap; }
    .pipe-stage.current { border-color: #a5b4fc; background: #e0e7ff; color: #312e81;
                          font-weight: 700; }
    .pipe-stage.complete { background: #fafafa; color: #a1a1aa; text-decoration: line-through; }
    .pipe-stage.upcoming { color: #71717a; }
    .pipe-arrow { color: #d4d4d8; }
    .pipe-caption { font-size: .72rem; color: #71717a; margin: 0 0 .35rem; }
  </style>
</head>
<body>
<main>
  <h1>Conjecture local console</h1>
  <p class="muted">
    Catch state-law breaks that still look fine in chat. The model may
    <em>propose</em> continue / detour / new task; your coded ledger and handoff
    rules must <em>enforce</em> who owns the turn, which record stays locked, and
    when ownership may yield. <strong>Owner/kind strings are host-defined</strong>
    (this demo uses <code>cost_out</code> + <code>workflow_id</code> as stand-ins—
    your ledger might use any mid-flight type and pin keys). If the seal is soft,
    a label can steal or hijack while the reply still sounds helpful. Conjecture
    tests the enforce half under pin/freeze—not classifier correctness. This UI
    runs the mini-app’s real <code>handle()</code>. Ledger store (DB, LangGraph,
    Temporal, …) does not matter if Act projects owner and pins for a verdict.
  </p>

  <div class="card">
    <div class="row" style="margin-bottom:.75rem">
      <strong>Five concepts only (start here)</strong>
    </div>
    <p class="muted" style="margin:0">
      <strong>Script</strong> · <strong>Turn</strong> · <strong>Driver</strong> ·
      <strong>Observation</strong> · <strong>Invariant</strong>.
      <strong>Scenario</strong> = flexible description of twists (precursor to Script).
      See docs/SPEC.md.
    </p>
  </div>

  <div class="card" id="candidatesCard">
    <div class="row" style="justify-content:space-between">
      <strong>Candidate scenarios / incidents</strong>
      <span class="muted mono" id="candMeta"></span>
    </div>
    <p class="pipe-caption">Discovery path — same tracker idea as Prose → Draft IR → Staffed IR → Save</p>
    <div class="pipe" id="discoveryPipe" role="list" aria-label="Discovery path">
      <span class="pipe-stage complete" role="listitem" title="kinds · surfaces · stealers">✓ Host vocab</span>
      <span class="pipe-arrow" aria-hidden>→</span>
      <span class="pipe-stage complete" role="listitem" title="surface × act × stealer">✓ Invent</span>
      <span class="pipe-arrow" aria-hidden>→</span>
      <span class="pipe-stage complete" role="listitem" title="kind × foreign leaf">✓ Expand</span>
      <span class="pipe-arrow" aria-hidden>→</span>
      <span class="pipe-stage current" role="listitem" title="candidate YAML">● Scenario</span>
      <span class="pipe-arrow" aria-hidden>→</span>
      <span class="pipe-stage upcoming" role="listitem" title="CI golden">○ Script</span>
      <span class="pipe-arrow" aria-hidden>→</span>
      <span class="pipe-stage upcoming" role="listitem" title="forever regression">○ Sealed</span>
    </div>
    <details class="card" style="margin:.5rem 0 1rem; padding:.75rem 1rem; box-shadow:none; border:1px solid #e4e4e7">
      <summary style="cursor:pointer; font-weight:600">Help — working taxonomy (not FMEA reinvention)</summary>
      <p class="muted" style="margin:.5rem 0">
        Small layered map so discovery, classification, and validation stay consistent.
        <em>Not</em> a full FMEA product — only enough structure to connect failure laws,
        incidents, trajectories, executable tests, and evidence.
      </p>
      <table class="muted" style="width:100%; border-collapse:collapse; font-size:.85rem; margin:.5rem 0">
        <thead>
          <tr style="text-align:left; border-bottom:1px solid #d4d4d8">
            <th style="padding:.3rem .4rem">Layer</th>
            <th style="padding:.3rem .4rem">What it is</th>
            <th style="padding:.3rem .4rem">Example</th>
          </tr>
        </thead>
        <tbody>
          <tr style="border-bottom:1px solid #e4e4e7">
            <td style="padding:.4rem; vertical-align:top"><strong>Failure mode</strong><br/><span class="mono">id / slug</span></td>
            <td style="padding:.4rem">Named class of prohibited/incorrect behavior in CAQ-FM /
              <span class="mono">registry.yaml</span>. Slug = Conjecture’s unique id for the
              <em>class</em>, not one occurrence.</td>
            <td style="padding:.4rem" class="mono">owner_steal, hollow_open, packaging_steal</td>
          </tr>
          <tr style="border-bottom:1px solid #e4e4e7">
            <td style="padding:.4rem; vertical-align:top"><strong>Incident</strong></td>
            <td style="padding:.4rem">One observed production, soak, eval, or test occurrence of a mode.
              Many incidents → one mode.</td>
            <td style="padding:.4rem">“Glossary stole ownership mid-claim on C-1042 on 2026-07-01.”</td>
          </tr>
          <tr style="border-bottom:1px solid #e4e4e7">
            <td style="padding:.4rem; vertical-align:top"><strong>Candidate scenario</strong></td>
            <td style="padding:.4rem">One authored multi-turn trajectory that can expose or stress a mode.
              Inventory rows are trajectories, not modes. Many scenarios → one mode.</td>
            <td style="padding:.4rem" class="mono">invent_…_glossary_concept, matrix.hollow_open.…</td>
          </tr>
          <tr style="border-bottom:1px solid #e4e4e7">
            <td style="padding:.4rem; vertical-align:top"><strong>Script / sealed pattern</strong></td>
            <td style="padding:.4rem">Deterministic CI-runnable form of a scenario (setup, turns, asserts).
              Linked via <span class="mono">patterns/&lt;portable_seed&gt;/</span> and registry
              <span class="mono">portable_seed</span>.</td>
            <td style="padding:.4rem" class="mono">patterns/owner_steal_mid_continue/</td>
          </tr>
          <tr>
            <td style="padding:.4rem; vertical-align:top"><strong>Execution evidence</strong></td>
            <td style="padding:.4rem">Trace, assertions, artifacts, and verdict from running a sealed pattern —
              proof the law held or broke under that trajectory.</td>
            <td style="padding:.4rem">Trace: claims agent stayed authoritative; C-1042 stayed pinned.</td>
          </tr>
        </tbody>
      </table>
      <p class="muted" style="margin:.65rem 0 .35rem"><strong>Core relationships</strong> (not strictly 1:1)</p>
      <ul class="muted" style="margin:0; font-size:.85rem">
        <li>Failure mode = reusable behavioral class · Incident = one occurrence</li>
        <li>Candidate scenario = one trajectory · Sealed pattern = repeatable test · Evidence = run verdict</li>
        <li>Many incidents/scenarios → one mode · one scenario may expose multiple modes</li>
        <li>One pattern → many execution results across models, versions, configs</li>
      </ul>
      <p class="muted" style="margin:.65rem 0 .35rem"><strong>Supporting metadata</strong> (not separate layers)</p>
      <p class="muted" style="margin:0; font-size:.85rem">
        Trigger/context · Effect · Cause/insufficiency hypothesis · Invariant/law violated ·
        Detection signal · Mitigation/guardrail — attach to mode, incident, or scenario as needed.
      </p>
      <p class="muted" style="margin:.65rem 0 .35rem"><strong>Discovery workflow</strong></p>
      <p class="muted" style="margin:0; font-size:.85rem">
        <strong>Invent</strong>: surface × act × stealer ·
        <strong>Expand</strong>: sole×foreign · matrix · residual ·
        Maturation: <strong>Open trajectory → Candidate scenario → Sealed pattern → Execution evidence</strong>
      </p>
      <p class="muted" style="margin:.65rem 0 0; font-size:.85rem">
        <strong>Guardrails:</strong> mode slug ≠ incident id ≠ scenario id.
        Portable seed links registry → pattern. Script = runnable artifact. Proof = evidence + verdict.
      </p>
    </details>
    <div id="candTaxonomy" class="muted" style="margin:0 0 .75rem; font-size:.9rem"></div>
    <div id="candInventRun" class="muted" style="margin:0 0 .75rem; display:none"></div>
    <div class="row" style="margin-bottom:.75rem">
      <select id="candSeal" title="seal status">
        <option value="">all seals</option>
        <option value="open">open</option>
        <option value="partial">partial</option>
        <option value="regression_check">regression_check</option>
      </select>
      <select id="candPri" title="priority">
        <option value="">all priority</option>
        <option value="high">high</option>
        <option value="medium">medium</option>
        <option value="low">low</option>
      </select>
      <select id="candSrc" title="family / source">
        <option value="">all families</option>
        <option value="invention">Invention only</option>
        <option value="expansion">Expansion only</option>
        <option value="incident">Incident seeds</option>
        <option value="sole_continue_x_foreign">expand (sole×foreign)</option>
        <option value="matrix_queue">matrix</option>
        <option value="residual_heuristic">residual</option>
        <option value="host_incident">incident source</option>
      </select>
      <input type="search" id="candQ" placeholder="filter id / failure class…" style="min-width:10rem" />
      <button type="button" class="secondary" id="btnCandReload">Reload</button>
    </div>
    <div id="candList" class="muted">Loading candidates…</div>
    <div id="candDetail" style="display:none; margin-top:1rem">
      <div class="row" style="justify-content:space-between; margin-bottom:.5rem">
        <div>
          <a href="#/" class="muted" id="candBack" style="text-decoration:none">← all candidates</a>
          <div class="row" style="margin-top:.35rem">
            <strong id="candDetailTitle">—</strong>
            <span class="badge" id="candDetailSeal"></span>
          </div>
          <p class="muted mono" id="candDetailPath" style="margin:.25rem 0"></p>
        </div>
      </div>
      <div class="row" id="candTabs" style="margin-bottom:.75rem">
        <button type="button" class="secondary cand-tab" data-tab="trajectory">Trajectory</button>
        <button type="button" class="secondary cand-tab" data-tab="scenario">Scenario</button>
        <button type="button" class="secondary cand-tab" data-tab="script">Script</button>
      </div>
      <div class="row" id="candDeepLinks" style="margin-bottom:.75rem"></div>
      <div id="candPanelTrajectory" class="cand-panel"></div>
      <div id="candPanelScenario" class="cand-panel" style="display:none"></div>
      <div id="candPanelScript" class="cand-panel" style="display:none"></div>
    </div>
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
function sealBadge(s) {
  if (s === 'open') return 'open';
  if (s === 'partial') return 'partial';
  return 'reg';
}
function escapeHtml(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function parseHash() {
  // #/candidate/<id>[/trajectory|scenario|script]
  const h = (location.hash || '').replace(/^#/, '');
  const parts = h.split('/').filter(Boolean);
  if (parts[0] === 'candidate' && parts[1]) {
    return { id: decodeURIComponent(parts[1]), tab: parts[2] || 'trajectory' };
  }
  return { id: null, tab: 'trajectory' };
}
function setHash(id, tab) {
  const t = tab || 'trajectory';
  location.hash = id ? ('/candidate/' + encodeURIComponent(id) + '/' + t) : '/';
}
function showTab(tab) {
  ['trajectory','scenario','script'].forEach(name => {
    const panel = document.getElementById('candPanel' + name.charAt(0).toUpperCase() + name.slice(1));
    if (panel) panel.style.display = name === tab ? 'block' : 'none';
  });
  document.querySelectorAll('.cand-tab').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tab);
  });
}
function renderTrajectory(traj) {
  const steps = (traj && traj.steps) || [];
  const goals = (traj && traj.goal_state) || [];
  const initH = (traj && traj.initial_state_human) || [];
  const initM = (traj && traj.initial_state_machine) || (traj && traj.initial_state) || [];
  const exp = (traj && traj.expected_invariant) || {};
  const detect = (traj && traj.mode_detection) || (traj && traj.failure_oracle) || [];
  const geo = (traj && traj.geometry) || {};
  let html = '<p class="muted"><strong>Trajectory</strong> — '
    + '<em>user trajectory</em> (story) → <em>geometry</em> (adversarial conditions) → '
    + '<em>failure-mode mapping</em> (slug) → <em>mode detection</em> (observable evidence). '
    + 'Setup twists are harness preconditions, not end-user chat.</p>';
  if (traj.failure_mode) {
    html += '<div style="margin:.5rem 0"><strong>Failure mode stressed:</strong> '
      + '<span class="mono">' + escapeHtml(traj.failure_mode) + '</span></div>';
  }
  if (traj.scenario_purpose) {
    html += '<div class="muted" style="margin:.5rem 0"><strong>Purpose:</strong> '
      + escapeHtml(traj.scenario_purpose) + '</div>';
  }
  if (traj.user_trajectory) {
    html += '<div class="turn" style="background:#f8fafc"><strong>User trajectory</strong><p style="margin:.35rem 0 0">'
      + escapeHtml(traj.user_trajectory) + '</p></div>';
  }
  if (initH.length) {
    html += '<div class="muted" style="margin:.5rem 0"><strong>Initial state (human):</strong><ul>'
      + initH.map(x => '<li>' + escapeHtml(x) + '</li>').join('') + '</ul></div>';
  }
  if (initM.length) {
    html += '<div class="muted mono" style="margin:.35rem 0"><strong>Machine:</strong> '
      + initM.map(escapeHtml).join(' · ') + '</div>';
  }
  if (exp.prose) {
    html += '<div class="muted" style="margin:.5rem 0"><strong>Expected invariant:</strong> '
      + escapeHtml(exp.prose) + '</div>';
  } else if (goals.length) {
    html += '<div class="muted" style="margin:.5rem 0"><strong>Must hold:</strong> '
      + goals.map(escapeHtml).join(' · ') + '</div>';
  }
  html += steps.map(st => {
    const inv = (st.invariants || []).map(x =>
      (x.kind || '') + '=' + JSON.stringify(x.expected)).join(', ');
    const isSetup = st.role === 'setup' || st.setup_only;
    const head = isSetup
      ? 'Twist ' + st.index + ' — Establish active interaction (test setup)'
      : 'Twist ' + st.index + ' — User behavior';
    const body = isSetup
      ? '<div class="muted">' + escapeHtml(st.user_behavior || st.user_text || 'Harness setup') + '</div>'
      : '<div><strong>User:</strong> “' + escapeHtml(st.user_behavior || st.user_text) + '”</div>'
        + (st.competing_interpretation
          ? '<div class="muted">Competing interpretation: ' + escapeHtml(st.competing_interpretation) + '</div>'
          : '');
    return `<div class="turn ${isSetup ? '' : 'ok'}">
      <div class="mono">${escapeHtml(head)}</div>
      <div class="muted mono">${escapeHtml(st.id)} · ${escapeHtml(st.maneuver)}</div>
      ${body}
      <div class="muted mono">geometry pin=${escapeHtml(JSON.stringify(st.pin || {}))}</div>
      <div class="muted mono">invariants: ${escapeHtml(inv || '—')}</div>
      ${(st.postconditions || []).length
        ? '<div class="muted">must hold after: ' + st.postconditions.map(escapeHtml).join('; ') + '</div>'
        : ''}
    </div>`;
  }).join('') || '<p class="muted">No twists</p>';
  if (detect.length) {
    html += '<div class="turn bad" style="margin-top:.75rem"><strong>Mode detection</strong> '
      + '<span class="muted">(observable evidence the mode materialized)</span><ul>'
      + detect.map(x => '<li>' + escapeHtml(x) + '</li>').join('') + '</ul></div>';
  }
  if (geo.surface || geo.stealer || geo.mode) {
    html += '<div class="muted mono" style="margin-top:.75rem"><strong>Scenario geometry:</strong> '
      + 'surface=' + escapeHtml(geo.surface || '—')
      + ' · act=' + escapeHtml(geo.act || '—')
      + ' · stealer=' + escapeHtml(geo.stealer || '—')
      + ' · mode=' + escapeHtml(geo.mode || '—') + '</div>';
  }
  document.getElementById('candPanelTrajectory').innerHTML = html;
}
function renderScenarioPanel(data) {
  const sc = data.scenario || {};
  const scope = sc.scope || {};
  let html = '<p class="muted"><strong>Conjecture Scenario</strong> — human-first description (precursor to Script).</p>';
  html += `<div class="muted mono">scenario_id=${escapeHtml(sc.scenario_id || data.scenario_id)} · failure_mode=${escapeHtml(sc.failure_mode || '')} · class=${escapeHtml(sc.scenario_class || '')}</div>`;
  if (sc.scenario_purpose) {
    html += '<div class="muted" style="margin:.5rem 0"><strong>Purpose:</strong> ' + escapeHtml(sc.scenario_purpose) + '</div>';
  }
  if (sc.user_trajectory) {
    html += '<div class="muted" style="margin:.5rem 0"><strong>User trajectory:</strong> ' + escapeHtml(sc.user_trajectory) + '</div>';
  }
  if ((scope.expected_refusal || []).length) {
    html += '<div class="muted" style="margin:.5rem 0"><strong>expected_refusal:</strong><ul>'
      + scope.expected_refusal.map(x => '<li>' + escapeHtml(x) + '</li>').join('')
      + '</ul></div>';
  }
  html += '<pre style="margin-top:.75rem">' + escapeHtml(data.yaml || '') + '</pre>';
  document.getElementById('candPanelScenario').innerHTML = html;
}
function renderScriptPanel(data) {
  const sv = data.script_view || {};
  let html = '<p class="muted"><strong>Conjecture Script</strong> — play-back form (compiled from Scenario when possible).</p>';
  if (sv.ok === false && sv.error) {
    html += '<div class="turn bad"><div class="muted">Compile note (payload fallback used if turns shown):</div>'
      + '<div class="mono">' + escapeHtml(sv.error) + '</div></div>';
  }
  html += `<div class="muted mono">script_id=${escapeHtml(sv.script_id || '')} · turns=${(sv.turns||[]).length}</div>`;
  html += (sv.turns || []).map(t => {
    const inv = (t.invariants || []).map(x =>
      (x.kind || '') + '=' + JSON.stringify(x.expected)).join(', ');
    return `<div class="turn">
      <div class="mono">turn ${t.index}${t.freeze_key ? ' · freeze=' + escapeHtml(t.freeze_key) : ''}</div>
      <div><strong>User:</strong> “${escapeHtml(t.user_text)}”</div>
      <div class="muted mono">pin=${escapeHtml(JSON.stringify(t.pin || {}))}</div>
      <div class="muted mono">invariants: ${escapeHtml(inv || '—')}</div>
    </div>`;
  }).join('') || '<p class="muted">No script turns</p>';
  if (sv.script) {
    html += '<pre style="margin-top:.75rem">' + escapeHtml(JSON.stringify(sv.script, null, 2)) + '</pre>';
  }
  document.getElementById('candPanelScript').innerHTML = html;
}
function renderCandRow(s, active) {
  const id = s.scenario_id;
  const href = '#/candidate/' + encodeURIComponent(id) + '/trajectory';
  const fc = s.failure_class || '';
  return `<div class="turn cand ${active === id ? 'active' : ''}" data-id="${escapeHtml(id)}">
    <div class="row">
      <a href="${href}">${escapeHtml(id)}</a>
      <span class="badge ${sealBadge(s.seal_status)}">${escapeHtml(s.seal_status || '?')}</span>
      <span class="muted">${escapeHtml(s.priority || '')}</span>
      <span class="muted mono">${escapeHtml(s.family || s.source || '')}</span>
    </div>
    <div class="muted mono">${escapeHtml(fc ? 'failure_mode=' + fc + ' · ' : '')}${escapeHtml(s.path_id || '')}</div>
    <div class="row" style="margin-top:.35rem">
      <a class="deep-link" href="#/candidate/${encodeURIComponent(id)}/trajectory">Trajectory</a>
      <a class="deep-link" href="#/candidate/${encodeURIComponent(id)}/scenario">Scenario</a>
      <a class="deep-link" href="#/candidate/${encodeURIComponent(id)}/script">Script</a>
    </div>
  </div>`;
}
async function loadCandidates() {
  const seal = document.getElementById('candSeal').value;
  const pri = document.getElementById('candPri').value;
  const src = document.getElementById('candSrc').value;
  const q = document.getElementById('candQ').value.trim();
  const params = new URLSearchParams();
  if (seal) params.set('seal', seal);
  if (pri) params.set('priority', pri);
  if (src) params.set('source', src);
  if (q) params.set('q', q);
  params.set('limit', '200');
  const r = await fetch('/api/candidates?' + params.toString());
  const data = await r.json();
  const meta = document.getElementById('candMeta');
  const list = document.getElementById('candList');
  const tax = document.getElementById('candTaxonomy');
  const invEl = document.getElementById('candInventRun');
  if (!data.dir) {
    meta.textContent = 'none';
    list.innerHTML = '<p class="muted">' + (data.hint || 'No candidates dir') + '</p>';
    tax.textContent = '';
    invEl.style.display = 'none';
    return;
  }
  const bf = data.by_family || {};
  meta.textContent = (data.count || 0) + '/' + (data.total_in_manifest || 0)
    + ' scenarios · invent=' + (bf.invention || 0)
    + ' expand=' + (bf.expansion || 0)
    + (bf.incident ? ' incident=' + bf.incident : '');
  tax.textContent = data.taxonomy_note || '';
  // Last invent / author run
  const ir = data.invent_run;
  if (ir && !ir.error) {
    invEl.style.display = 'block';
    const n = ir.invention_count != null ? ir.invention_count
      : (ir.scenarios || ir.invention_scenarios || []).length;
    const when = ir.generated_at || '';
    const rows = ir.scenarios || ir.invention_scenarios || [];
    let html = '<strong>Last author run</strong> '
      + '<span class="mono">' + escapeHtml(when) + '</span>'
      + ' · invention scenarios generated: <strong>' + n + '</strong>';
    if (rows.length) {
      html += '<ul style="margin:.35rem 0 0; padding-left:1.2rem">';
      rows.slice(0, 24).forEach(row => {
        const sid = row.scenario_id || '';
        html += '<li class="mono"><a href="#/candidate/'
          + encodeURIComponent(sid) + '/trajectory">' + escapeHtml(sid) + '</a>'
          + (row.failure_class ? ' · mode=' + escapeHtml(row.failure_class) : '')
          + '</li>';
      });
      if (rows.length > 24) html += '<li class="muted">… +' + (rows.length - 24) + ' more</li>';
      html += '</ul>';
    }
    invEl.innerHTML = html;
  } else {
    invEl.style.display = 'none';
  }
  if (!(data.scenarios || []).length) {
    list.innerHTML = '<p class="muted">No scenarios match filters.</p>';
    return;
  }
  const active = parseHash().id;
  const groups = data.groups || {};
  const order = ['invention', 'expansion', 'incident', 'other'];
  const labels = {
    invention: 'Invention scenarios (geometry — not cross-product expand)',
    expansion: 'Expansion scenarios (sole×foreign · matrix · residual)',
    incident: 'Incident-seeded scenarios',
    other: 'Other scenarios',
  };
  let html = '';
  let usedGrouped = false;
  order.forEach(fam => {
    const rows = groups[fam] || [];
    if (!rows.length) return;
    usedGrouped = true;
    html += '<div style="margin:1rem 0 .35rem"><strong>' + escapeHtml(labels[fam] || fam)
      + '</strong> <span class="muted">(' + rows.length + ')</span></div>';
    html += rows.map(s => renderCandRow(s, active)).join('');
  });
  if (!usedGrouped) {
    html = (data.scenarios || []).map(s => renderCandRow(s, active)).join('');
  }
  list.innerHTML = html;
}
async function openCandidate(id, tab) {
  tab = tab || 'trajectory';
  const r = await fetch('/api/candidates/' + encodeURIComponent(id));
  const data = await r.json();
  if (!data.ok) {
    document.getElementById('status').textContent = data.error || 'load failed';
    return;
  }
  document.getElementById('candList').style.display = 'none';
  document.getElementById('candDetail').style.display = 'block';
  document.getElementById('candDetailTitle').textContent = data.scenario_id;
  const seal = (data.meta && data.meta.seal_status) || '';
  const b = document.getElementById('candDetailSeal');
  b.textContent = seal || 'candidate';
  b.className = 'badge ' + sealBadge(seal);
  const meta = data.meta || {};
  const fc = meta.failure_class || '';
  document.getElementById('candDetailPath').textContent =
    (fc ? 'failure_mode=' + fc + ' · ' : '')
    + (meta.family || meta.source || '') + ' · ' + (data.path || '');
  const links = data.links || {};
  document.getElementById('candDeepLinks').innerHTML = `
    <a class="deep-link" href="${escapeHtml(links.trajectory || '#')}"># trajectory</a>
    <a class="deep-link" href="${escapeHtml(links.scenario || '#')}"># scenario</a>
    <a class="deep-link" href="${escapeHtml(links.script || '#')}"># script</a>
    <a class="deep-link" href="${escapeHtml(links.api || '#')}" target="_blank" rel="noopener">API JSON</a>
  `;
  renderTrajectory(data.trajectory || {});
  renderScenarioPanel(data);
  renderScriptPanel(data);
  showTab(tab);
  window._candData = data;
}
function routeFromHash() {
  const { id, tab } = parseHash();
  if (id) {
    openCandidate(id, tab);
  } else {
    document.getElementById('candDetail').style.display = 'none';
    document.getElementById('candList').style.display = 'block';
    loadCandidates();
  }
}
document.getElementById('btnCandReload').onclick = () => loadCandidates();
document.getElementById('candBack').onclick = (e) => {
  e.preventDefault();
  setHash(null);
};
document.querySelectorAll('.cand-tab').forEach(btn => {
  btn.onclick = () => {
    const tab = btn.getAttribute('data-tab');
    const { id } = parseHash();
    if (id) setHash(id, tab);
    else showTab(tab);
  };
});
['candSeal','candPri','candSrc'].forEach(id => {
  document.getElementById(id).onchange = () => loadCandidates();
});
document.getElementById('candQ').oninput = () => {
  clearTimeout(window._candT);
  window._candT = setTimeout(loadCandidates, 200);
};
window.addEventListener('hashchange', routeFromHash);
loadStory();
routeFromHash();
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
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query or "")
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
            if path == "/api/candidates":
                from conjecture_behaviour_runner.candidates_ui import list_candidates

                def _one(key: str) -> Optional[str]:
                    vals = qs.get(key) or []
                    return vals[0] if vals else None

                limit_raw = _one("limit") or "200"
                try:
                    limit = int(limit_raw)
                except ValueError:
                    limit = 200
                _json_response(
                    self,
                    200,
                    list_candidates(
                        seal=_one("seal"),
                        priority=_one("priority"),
                        source=_one("source"),
                        q=_one("q"),
                        limit=limit,
                    ),
                )
                return
            if path.startswith("/api/candidates/"):
                from conjecture_behaviour_runner.candidates_ui import get_candidate

                sid = unquote(path[len("/api/candidates/") :].strip("/"))
                payload = get_candidate(sid)
                _json_response(self, 200 if payload.get("ok") else 404, payload)
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
    print(f"Conjecture local console → {url}")
    print("  Candidate Scenarios · healthy story · prove planted bugs")
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
