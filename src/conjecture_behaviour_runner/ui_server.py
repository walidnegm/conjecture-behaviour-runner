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
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
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


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    raw_len = handler.headers.get("Content-Length") or "0"
    try:
        n = max(0, min(int(raw_len), 2_000_000))
    except ValueError:
        n = 0
    if n <= 0:
        return {}
    raw = handler.rfile.read(n)
    try:
        data = json.loads(raw.decode("utf-8") or "{}")
    except Exception:  # noqa: BLE001
        return {}
    return data if isinstance(data, dict) else {}


def _html_page() -> bytes:
    # Single-file UI — keep dependencies at zero.
    html = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Conjecture · Conversational Agentic Quality</title>
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
  <link rel="alternate icon" href="/favicon.ico" />
  <link rel="apple-touch-icon" href="/static/bot0-logo.png" />
  <style>
    .brand-mark { width: 1.55rem; height: 1.55rem; border-radius: .4rem;
      vertical-align: middle; margin-right: .45rem; object-fit: contain;
      background: #2563eb; }
    h1 .brand-mark { position: relative; top: -1px; }
    :root { font-family: ui-sans-serif, system-ui, sans-serif; color: #18181b; }
    body { margin: 0; background: #f4f4f5; }
    .topbar { background: #fff; border-bottom: 1px solid #e4e4e7;
      position: sticky; top: 0; z-index: 20; }
    .topbar-inner { max-width: 64rem; margin: 0 auto; padding: .85rem 1.25rem .55rem; }
    h1 { font-size: 1.2rem; margin: 0 0 .1rem; line-height: 1.25; letter-spacing: -0.01em; }
    .brand-sub {
      display: flex; flex-wrap: wrap; gap: .35rem .55rem; align-items: center;
      margin: 0 0 .55rem;
    }
    .brand-badge {
      font-size: .68rem; font-weight: 800; text-transform: uppercase;
      letter-spacing: .05em; color: #3730a3; background: #eef2ff;
      border: 1px solid #c7d2fe; border-radius: .35rem; padding: .15rem .45rem;
    }
    .tagline { color: #52525b; font-size: .8rem; margin: 0; line-height: 1.4; flex: 1 1 14rem; }
    .app-nav { display: flex; flex-wrap: wrap; gap: .35rem; }
    .app-nav button { background: transparent; color: #3f3f46; border: 1px solid transparent;
      border-radius: .45rem; padding: .45rem .85rem; font-size: .875rem; cursor: pointer;
      font-weight: 600; }
    .app-nav button:hover { background: #f4f4f5; }
    .app-nav button.active { background: #18181b; color: #fff; border-color: #18181b; }
    .status-pill { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: .72rem; color: #71717a; margin-left: auto; padding: .35rem .5rem; }
    main { max-width: 64rem; margin: 0 auto; padding: 1rem 1.25rem 2.5rem; }
    .muted { color: #52525b; font-size: .9rem; line-height: 1.5; }
    .card { background: #fff; border: 1px solid #e4e4e7; border-radius: .75rem;
            padding: 1rem; margin: 0 0 1rem; box-shadow: 0 1px 2px rgb(0 0 0 / 4%); }
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
    /* Primary CTA to heat-map viz (same port /surface-map) — not a quiet text link */
    a.map-cta {
      display: inline-flex; align-items: center; gap: .35rem;
      background: #1d4ed8; color: #fff !important; border: 0; border-radius: .4rem;
      padding: .55rem 1rem; font-size: .875rem; font-weight: 700; text-decoration: none;
    }
    a.map-cta:hover { background: #1e40af; color: #fff !important; }
    a.map-cta.secondary {
      background: #fff; color: #1d4ed8 !important; border: 1px solid #93c5fd;
    }
    a.map-cta.secondary:hover { background: #eff6ff; }
    /* Home-page embedded heat map (not a buried link) */
    .viz-card {
      border: 2px solid #1d4ed8;
      background: #fff;
    }
    .viz-card .view-title {
      font-size: 1.05rem !important;
      letter-spacing: .02em;
    }
    .viz-badge {
      display: inline-block; font-size: .7rem; font-weight: 800;
      text-transform: uppercase; letter-spacing: .06em;
      background: #1d4ed8; color: #fff; border-radius: .3rem;
      padding: .2rem .5rem; margin-right: .4rem; vertical-align: middle;
    }
    .viz-frame-wrap {
      border: 1px solid #e4e4e7; border-radius: .5rem;
      overflow: hidden; background: #fafafa;
      min-height: 42rem;
    }
    .viz-frame {
      width: 100%; height: 48rem; border: 0; display: block;
      background: #fff;
    }
    .viz-chrome {
      display: flex; flex-wrap: wrap; gap: .45rem; align-items: center;
      background: #eff6ff !important; border-top: 1px solid #bfdbfe;
    }
    .laws-plane-pill.active-pill,
    button.laws-plane-pill.active-pill {
      background: #18181b !important; color: #fff !important; border-color: #18181b !important;
    }
    code, .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .75rem; }
    ul { margin: .35rem 0; padding-left: 1.2rem; }
    pre { background: #18181b; color: #f4f4f5; padding: .75rem; border-radius: .5rem;
          overflow: auto; font-size: .7rem; max-height: 18rem; }
    select, input[type=search] { font: inherit; font-size: .85rem; padding: .4rem .55rem;
      border: 1px solid #d4d4d8; border-radius: .4rem; background: #fff; }
    .grid2 { display: grid; gap: .75rem; }
    @media (min-width: 640px) { .grid2 { grid-template-columns: 1fr 1fr; } }
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
    .run-bar { background: #f8fafc; border: 1px solid #e4e4e7; border-radius: .6rem;
               padding: .75rem; margin: 0 0 .75rem; }
    .run-bar label { font-size: .85rem; color: #3f3f46; display: inline-flex;
                     align-items: center; gap: .35rem; cursor: pointer; }
    .report-card { border: 1px solid #e4e4e7; border-radius: .6rem; padding: .85rem;
                   margin: .75rem 0; background: #fff; }
    .report-card .sum { font-size: 1.05rem; font-weight: 700; }
    .chk { width: 1rem; height: 1rem; accent-color: #18181b; }
    .app-view { display: none; }
    .app-view.active { display: block; }
    .view-title { font-size: 1.05rem; font-weight: 700; margin: 0 0 .35rem; }
    .view-lead { color: #52525b; font-size: .88rem; margin: 0 0 1rem; line-height: 1.45; }
    .split { display: grid; gap: 1rem; }
    @media (min-width: 900px) {
      .split-run { grid-template-columns: 1fr 1.1fr; align-items: start; }
      .admin-grid { grid-template-columns: 1fr 1fr; }
    }
    .admin-grid { display: grid; gap: 1rem; }
    .kv { width: 100%; border-collapse: collapse; font-size: .85rem; }
    .kv th { text-align: left; padding: .35rem .5rem .35rem 0; color: #71717a;
      font-weight: 600; width: 38%; vertical-align: top; }
    .kv td { padding: .35rem 0; vertical-align: top; word-break: break-word; }
    .kv tr { border-top: 1px solid #f4f4f5; }
    .ok-dot { display: inline-block; width: .55rem; height: .55rem; border-radius: 999px;
      margin-right: .35rem; vertical-align: middle; }
    .ok-dot.on { background: #059669; }
    .ok-dot.off { background: #dc2626; }
    .ok-dot.warn { background: #d97706; }
    .warn-list { margin: .5rem 0 0; padding-left: 1.1rem; color: #b45309; font-size: .85rem; }
    details.help-block { margin: .5rem 0; padding: .75rem 1rem; border: 1px solid #e4e4e7;
      border-radius: .6rem; background: #fff; }
    details.scenario-result { border: 1px solid #e4e4e7; border-radius: .6rem;
      margin: .55rem 0; background: #fff; overflow: hidden; }
    details.scenario-result.ok { border-color: #a7f3d0; }
    details.scenario-result.bad { border-color: #fecaca; }
    details.scenario-result > summary { cursor: pointer; list-style: none; padding: .75rem .9rem;
      display: flex; flex-wrap: wrap; gap: .45rem; align-items: center;
      background: #fafafa; font-size: .9rem; }
    details.scenario-result > summary::-webkit-details-marker { display: none; }
    details.scenario-result > summary::before { content: '▸'; color: #71717a; font-size: .75rem; }
    details.scenario-result[open] > summary::before { content: '▾'; }
    details.scenario-result[open] > summary { border-bottom: 1px solid #e4e4e7; }
    .scenario-result-body { padding: .85rem 1rem 1rem; }
    .findings-block { border: 1px solid #c7d2fe; border-radius: .5rem; padding: .75rem;
      margin-top: .65rem; background: #f8fafc; }
    .findings-block h4 { margin: 0 0 .4rem; font-size: .9rem; }
    .turn-table { width: 100%; border-collapse: collapse; font-size: .82rem; margin: .35rem 0 .65rem; }
    .turn-table th { text-align: left; padding: .3rem .4rem; color: #71717a; font-weight: 600;
      border-bottom: 1px solid #e4e4e7; }
    .turn-table td { padding: .35rem .4rem; vertical-align: top; border-top: 1px solid #f4f4f5; }
    .turn-table .idx { width: 2rem; font-family: ui-monospace, monospace; color: #71717a; }
    .turn-table .role { width: 6.5rem; font-family: ui-monospace, monospace; font-size: .75rem; }
    .bl-section { margin: .85rem 0 .35rem; padding-top: .55rem; border-top: 1px solid #e4e4e7; }
    .bl-section:first-child { border-top: 0; padding-top: 0; margin-top: 0; }
    .bl-section h4 { margin: 0 0 .4rem; font-size: .88rem; color: #18181b; }
    .bl-empty { color: #a1a1aa; font-style: italic; font-size: .82rem; }
    .bl-prose { white-space: pre-wrap; font-size: .88rem; line-height: 1.45; margin: .25rem 0; }
    .bl-meta-grid { display: grid; gap: .35rem .75rem; grid-template-columns: 1fr; }
    @media (min-width: 720px) { .bl-meta-grid { grid-template-columns: 1fr 1fr; } }
    .mode-table { width: 100%; border-collapse: collapse; font-size: .8rem; }
    .mode-table th { text-align: left; padding: .35rem .4rem; color: #71717a; font-weight: 600;
      border-bottom: 1px solid #e4e4e7; position: sticky; top: 0; background: #fff; }
    .mode-table td { padding: .35rem .4rem; border-top: 1px solid #f4f4f5; vertical-align: top; }
    .mode-table tr:hover td { background: #fafafa; }
    .mode-table tr.selected td { background: #eff6ff; }
    .stat-cards { display: grid; gap: .55rem; grid-template-columns: repeat(auto-fill, minmax(8.5rem, 1fr));
      margin: 0 0 1rem; }
    .stat-card { border: 1px solid #e4e4e7; border-radius: .55rem; padding: .55rem .65rem; background: #fafafa; }
    .stat-card .n { font-size: 1.25rem; font-weight: 700; font-family: ui-monospace, monospace; }
    .stat-card .l { font-size: .72rem; color: #71717a; margin-top: .1rem; }
    .stack-box { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .72rem;
      background: #18181b; color: #e4e4e7; padding: .85rem 1rem; border-radius: .55rem;
      white-space: pre-wrap; line-height: 1.45; overflow: auto; }
    .chrome-bar { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .72rem;
      color: #52525b; margin: .35rem 0 .55rem; padding: .3rem .45rem; background: #f4f4f5;
      border-radius: .35rem; }
    .layer-pill { display: inline-block; font-size: .68rem; font-weight: 700; text-transform: uppercase;
      letter-spacing: .02em; padding: .1rem .4rem; border-radius: .3rem; background: #f4f4f5; color: #3f3f46; }
    .check-row { border: 1px solid #e4e4e7; border-radius: .45rem; padding: .5rem .65rem; margin: .35rem 0; font-size: .85rem; }
    .check-row.fail, .check-row.error { border-color: #fecaca; background: #fef2f2; }
    .check-row.pass { border-color: #a7f3d0; background: #f0fdf4; }
    .check-row.skip { opacity: .75; }
    .filter-row { display: flex; flex-wrap: wrap; gap: .45rem; align-items: center; margin: 0 0 .75rem; }
    /* Approach-aligned Quality Console */
    .patch-banner {
      border: 1px solid #fecaca; background: #fef2f2; color: #7f1d1d;
      border-radius: .55rem; padding: .65rem .85rem; margin: 0 0 .85rem;
      font-size: .78rem; line-height: 1.45;
    }
    .patch-banner strong { color: #991b1b; }
    .patch-banner .mono { color: #7f1d1d; font-size: .72rem; }
    .spine {
      display: flex; flex-wrap: wrap; gap: .35rem; align-items: stretch;
      margin: 0 0 1rem;
    }
    .spine-node {
      flex: 1 1 5.5rem; min-width: 5.2rem; border: 1px solid #e4e4e7;
      border-radius: .5rem; padding: .45rem .5rem; background: #fafafa;
      font-size: .72rem; line-height: 1.3;
    }
    .spine-node .k { font-weight: 800; font-size: .78rem; color: #18181b; display: block; }
    .spine-node .q { color: #71717a; margin-top: .15rem; display: block; }
    .spine-node.on { border-color: #a5b4fc; background: #eef2ff; }
    .spine-arrow { align-self: center; color: #a1a1aa; font-size: .85rem; flex: 0 0 auto; }
    .cat-grid {
      display: grid; gap: .55rem;
      grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr));
      margin: 0 0 .25rem;
    }
    .cat-card {
      border: 1px solid #e4e4e7; border-radius: .55rem; padding: .65rem .7rem;
      background: #fff; font-size: .8rem; line-height: 1.4;
    }
    .cat-card .cat-id {
      font-size: .65rem; font-weight: 800; text-transform: uppercase;
      letter-spacing: .04em; color: #6366f1; margin: 0 0 .2rem;
    }
    .cat-card .cat-name { font-weight: 700; font-size: .88rem; margin: 0 0 .35rem; }
    .cat-card .cat-q { color: #52525b; margin: 0 0 .4rem; }
    .cat-card .cat-meta { color: #71717a; font-size: .72rem; }
    .ladder {
      display: flex; flex-wrap: wrap; gap: .35rem; align-items: center;
      font-size: .78rem; margin: .35rem 0 .75rem;
    }
    .ladder-step {
      border: 1px solid #d4d4d8; border-radius: .4rem; padding: .3rem .5rem;
      background: #fff; font-weight: 600;
    }
    .ladder-step em { font-style: normal; color: #71717a; font-weight: 500; font-size: .72rem; }
    .nav-group {
      display: inline-flex; flex-wrap: wrap; gap: .3rem; align-items: center;
      margin-right: .55rem; padding-right: .55rem; border-right: 1px solid #e4e4e7;
    }
    .nav-group:last-of-type { border-right: 0; margin-right: 0; padding-right: 0; }
    .nav-group-label {
      font-size: .62rem; font-weight: 800; text-transform: uppercase;
      letter-spacing: .06em; color: #a1a1aa; padding: 0 .15rem;
    }
    .cov-bar {
      height: .55rem; border-radius: 999px; background: #e4e4e7; overflow: hidden;
      margin: .35rem 0 .15rem;
    }
    .cov-bar > i { display: block; height: 100%; background: #059669; }
    .cov-bar.warn > i { background: #d97706; }
    .cov-bar.bad > i { background: #dc2626; }
    .do-dont {
      display: grid; gap: .55rem; grid-template-columns: 1fr;
      margin: .5rem 0 0;
    }
    @media (min-width: 720px) { .do-dont { grid-template-columns: 1fr 1fr; } }
    .do-dont .col {
      border-radius: .5rem; padding: .55rem .7rem; font-size: .78rem; line-height: 1.4;
    }
    .do-dont .do { background: #ecfdf5; border: 1px solid #a7f3d0; color: #065f46; }
    .do-dont .dont { background: #fef2f2; border: 1px solid #fecaca; color: #7f1d1d; }
    .do-dont h4 { margin: 0 0 .35rem; font-size: .8rem; }
    .do-dont ul { margin: 0; padding-left: 1.05rem; }
    .job-cards {
      display: grid; gap: .45rem;
      grid-template-columns: repeat(auto-fill, minmax(11.5rem, 1fr));
    }
    .job-card {
      border: 1px solid #e4e4e7; border-radius: .5rem; padding: .55rem .6rem;
      background: #fafafa; font-size: .78rem;
    }
    .job-card .jid { font-weight: 800; font-size: .72rem; text-transform: uppercase;
      letter-spacing: .03em; color: #4338ca; }
    .job-card .jown { color: #71717a; font-size: .72rem; margin: .15rem 0; }
    .job-card .jq { color: #3f3f46; }
    .nav-rows { display: flex; flex-direction: column; gap: .4rem; }
    .nav-row { display: flex; flex-wrap: wrap; gap: .35rem; align-items: center; }
    .cat-card.clickable { cursor: pointer; transition: border-color .12s, box-shadow .12s; }
    .cat-card.clickable:hover { border-color: #818cf8; box-shadow: 0 0 0 2px #e0e7ff; }
    button.danger { background: #b91c1c; color: #fff; }
    button.danger:hover { background: #991b1b; }
    button.danger:disabled { opacity: .45; cursor: not-allowed; background: #b91c1c; }
    .prog-tools { display: flex; flex-wrap: wrap; gap: .4rem; margin: .5rem 0; }
    .gap-board { margin: 1rem 0 0; }
    .gap-board > .gb-head { margin: 0 0 .5rem; }
    .gap-board > .gb-head h3 { margin: 0 0 .25rem; font-size: .95rem; }
    .gap-class {
      border: 1px solid #e4e4e7; border-radius: .65rem; margin: 0 0 .75rem;
      background: #fff; overflow: hidden;
    }
    .gap-class.featured { border-color: #a5b4fc; box-shadow: 0 0 0 1px #e0e7ff; }
    .gap-class > summary {
      list-style: none; cursor: pointer; padding: .65rem .8rem;
      display: flex; flex-wrap: wrap; gap: .4rem; align-items: center;
      background: #fafafa; font-size: .85rem;
    }
    .gap-class > summary::-webkit-details-marker { display: none; }
    .gap-class[open] > summary { border-bottom: 1px solid #f4f4f5; }
    .gap-class .gc-id { font-family: ui-monospace, monospace; font-weight: 700; color: #3730a3; }
    .gap-class .gc-title { font-weight: 600; }
    .gap-class .gc-body { padding: .65rem .8rem .85rem; }
    .lens-grid {
      display: grid; gap: .55rem;
      grid-template-columns: 1fr;
    }
    @media (min-width: 900px) {
      .lens-grid { grid-template-columns: 1fr 1fr 1fr; }
    }
    .lens-card {
      border: 1px solid #e4e4e7; border-radius: .5rem; padding: .55rem .65rem;
      background: #fafafa; font-size: .78rem; min-height: 6rem;
    }
    .lens-card h4 {
      margin: 0 0 .35rem; font-size: .78rem; display: flex; flex-wrap: wrap;
      gap: .3rem; align-items: center;
    }
    .lens-card .lens-sum { color: #52525b; margin: 0 0 .45rem; line-height: 1.4; }
    .lens-card ul.compact { margin: 0; padding-left: 1rem; max-height: 9rem; overflow: auto; }
    .lens-card ul.compact li { margin: .15rem 0; line-height: 1.35; }
    .lens-card .empty-note { color: #a1a1aa; font-style: italic; }
    .prog-sot li { margin: .2rem 0; font-size: .82rem; }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <h1>
        <img class="brand-mark" src="/static/favicon.svg" width="24" height="24" alt="" />
        Conjecture · Conversational Agentic Quality
      </h1>
      <div class="brand-sub">
        <span class="brand-badge">Quality Console</span>
        <p class="tagline">
          Simple loop:
          <strong>categories</strong> → <strong>failure modes</strong> → <strong>incidents</strong>
          → <strong>mitigations in code</strong> → <strong>observation</strong>
          (when evidence still shows the burn).
          Doctrine unchanged — this console only navigates it.
        </p>
      </div>
      <nav class="app-nav nav-rows" id="appNav" aria-label="Console sections">
        <div class="nav-row">
          <span class="nav-group-label">Browse</span>
          <button type="button" class="active" data-view="home">Map</button>
          <button type="button" data-view="laws" title="All named failure modes (registry)">Failure modes</button>
          <button type="button" data-view="program-authority" title="Category: who may own the turn / pin / open">Authority</button>
          <button type="button" data-view="program-laundry" title="Category: free-text meaning / policy as laundry">Laundry</button>
          <button type="button" data-view="program-antipattern" title="Category: SDK construction anti-patterns A1–A19">Antipatterns</button>
          <button type="button" data-view="program-voice" title="Category: product voice / delivery feel">Voice</button>
          <button type="button" data-view="program-purity" title="Category: seal grade scoreboards">Purity</button>
          <button type="button" data-view="program-memory" title="Category: SoR · View · continuity">Memory</button>
          <button type="button" data-view="program-surface" title="Where each mode is still unproven on product surfaces">Where unproven</button>
        </div>
        <div class="nav-row">
          <span class="nav-group-label">Observe &amp; prove</span>
          <button type="button" data-view="techniques" title="How static vs multi-turn proof runs">How we run</button>
          <button type="button" data-view="seek" title="Observation battery — join / ratchets / live evidence">Observe</button>
          <button type="button" data-view="candidates" title="Author multi-turn scenarios from incidents">Author</button>
          <button type="button" data-view="run" title="Run multi-turn proof">Runner</button>
          <button type="button" data-view="backlog" title="Verdict / backlog from runs">Verdict</button>
          <span class="nav-group-label" style="margin-left:.35rem">Ops</span>
          <button type="button" data-view="demo">Demo</button>
          <button type="button" data-view="admin">Admin</button>
          <button type="button" data-view="help">Help</button>
          <span class="status-pill" id="status" title="Status"></span>
        </div>
      </nav>
      <div class="chrome-bar" id="seekChrome" title="Last observation battery summary">observation: loading…</div>
      <div class="chrome-bar viz-chrome" id="vizChrome">
        <strong style="color:#1d4ed8">WHERE UNPROVEN</strong>
        <span class="muted" style="font-size:.78rem">surfaces × failure modes — empty = still open</span>
        <a class="map-cta" href="#/home" id="btnJumpViz" style="margin-left:.35rem;padding:.35rem .75rem;font-size:.8rem">Show on Map ↓</a>
        <a class="map-cta secondary" href="/surface-map" target="_blank" rel="noopener"
           style="padding:.35rem .75rem;font-size:.8rem">Full page ↗</a>
      </div>
    </div>
  </header>
<main>

  <!-- ========== HOME / APPROACH MAP ========== -->
  <section class="app-view active" id="view-home" data-view="home">

  <!-- FIRST on home — above the fold (do not bury under programs) -->
  <div class="card viz-card" id="homeVizCard">
    <div class="view-title">
      <span class="viz-badge">Visualization</span>
      Surface area map · product surfaces × failure modes
    </div>
    <p class="view-lead" style="margin-bottom:.5rem">
      Coverage debt heat map (empty cells = red). Served at
      <span class="mono">/surface-map</span> on this same port — also embedded below.
    </p>
    <div class="row" style="margin:0 0 .55rem">
      <a class="map-cta" href="/surface-map" target="_blank" rel="noopener">Open full page ↗</a>
      <a class="map-cta secondary" href="#/program/memory_management">Memory program</a>
      <a class="map-cta secondary" href="#/program/surface_law_coverage">Surface×law program</a>
      <button type="button" class="secondary" id="btnReloadViz"
              title="Reload iframe">Reload visualization</button>
    </div>
    <div class="viz-frame-wrap">
      <iframe
        id="homeVizFrame"
        class="viz-frame"
        title="Surface area map visualization"
        src="/surface-map"
        loading="eager"
      ></iframe>
    </div>
  </div>

  <div class="patch-banner" id="homePatchBanner" role="note">
    <strong>Coding-agent patching note</strong> (mandatory on every diagnostic) —
    <span class="mono" id="homePatchShort">loading AGENTS.md banner…</span>
  </div>
  <div class="card">
    <div class="view-title">Map · what this console is for</div>
    <p class="view-lead">
      We name <strong>failure modes</strong> under a few <strong>categories</strong>
      (authority, laundry, antipatterns, voice, purity, memory).
      Each mode shows up as real <strong>incidents</strong> (<span class="mono">conv_*</span>).
      We put <strong>mitigations in code</strong> (contracts + ratchets), then
      <strong>observe</strong> whether evidence still shows the burn.
      This UI only makes that loop easy to follow — it does not invent new law.
    </p>
    <div class="spine" id="homeSpine" aria-label="Simple quality loop"></div>
    <div class="ladder" id="homeLadder" title="From live burn to seal">
      <span class="ladder-step">Incident</span><span class="spine-arrow">→</span>
      <span class="ladder-step">Failure mode</span><span class="spine-arrow">→</span>
      <span class="ladder-step">Category</span><span class="spine-arrow">→</span>
      <span class="ladder-step">Mitigation</span><span class="spine-arrow">→</span>
      <span class="ladder-step">Observe</span>
    </div>
    <div class="stat-cards" id="homeStats"></div>
    <div class="row" style="margin:0 0 .75rem">
      <button type="button" id="btnHomeRefresh">Refresh snapshot</button>
      <button type="button" class="secondary" id="btnHomeRunSeek">Observe (quick)</button>
      <a class="map-cta" href="#homeVizCard"
         title="Scroll to where-unproven map">Where unproven ↑</a>
      <button type="button" class="secondary" data-goto="program-surface"
              title="Where each mode is still unproven">Where unproven</button>
      <button type="button" class="secondary" data-goto="techniques">How we run</button>
      <button type="button" class="secondary" data-goto="laws">Failure modes</button>
      <button type="button" class="secondary" data-goto="seek">Observe</button>
      <button type="button" class="secondary" data-goto="candidates">Author</button>
      <button type="button" class="secondary" data-goto="help">Help</button>
    </div>
    <p class="muted mono" id="homeMeta" style="margin:0;font-size:.8rem"></p>
  </div>

  <div class="card">
    <div class="view-title" style="font-size:.95rem">Categories <span class="muted" style="font-weight:500">(pick one objective — do not merge)</span></div>
    <p class="view-lead" style="margin-bottom:.55rem" id="homeProgramLead">
      Start here when you know <em>what kind</em> of problem you are looking at.
      Each category groups related failure modes (and may point at the shared
      registry book). <strong>Where unproven</strong> is not a category of law —
      it is the map of mitigation/proof still missing on product surfaces.
    </p>
    <div class="cat-grid" id="homeCategories">Loading categories…</div>
  </div>
  <div class="card">
    <div class="view-title" style="font-size:.95rem">Jobs on the spine</div>
    <div class="job-cards" id="homeJobs">Loading jobs…</div>
    <p class="muted mono" id="homeStackSentence" style="margin:.65rem 0 0;font-size:.78rem"></p>
  </div>
  <div class="card" id="homeSurfaceCard">
    <div class="view-title" style="font-size:.95rem">Surface × law coverage (stats)</div>
    <p class="view-lead" style="margin-bottom:.4rem">
      Numbers from the latest snapshot. Full heat map is
      <strong>Where unproven</strong> above (not the Observe tab).
    </p>
    <div id="homeCoverage">—</div>
  </div>
  <div class="card">
    <div class="view-title" style="font-size:.95rem">When coding a seal</div>
    <div class="do-dont">
      <div class="col do">
        <h4>Required</h4>
        <ul>
          <li>Extend allow-table / enum / pin / phase</li>
          <li>Structural seal at earliest wrong layer</li>
          <li>Named path-faithful ratchet</li>
          <li>Keep cousin seals green</li>
        </ul>
      </div>
      <div class="col dont">
        <h4>Forbidden</h4>
        <ul>
          <li>Invent / hotfix / break-fix / shortcut</li>
          <li>Regex or wordlist as sole NL meaning</li>
          <li>Phrase laundry to green one soak</li>
          <li>Sibling “looks fine” script (fake-fixed)</li>
        </ul>
      </div>
    </div>
    <p class="muted" style="margin:.65rem 0 0;font-size:.8rem">
      Full note: taxonomy §2.4 · <span class="mono">agent_patching_note.py</span> · AGENTS.md banner.
    </p>
  </div>
  <div class="card">
    <strong>Open work (from last Coverage / Seek)</strong>
    <div id="homeOpenWork" class="muted" style="margin-top:.5rem">—</div>
  </div>
  </section>

  <!-- ========== PROGRAM DETAIL (Laundry / Antipatterns / Voice / Purity / Surface) ========== -->
  <section class="app-view" id="view-program" data-view="program">
  <div class="card">
    <div class="view-title" id="progTitle">Program</div>
    <p class="view-lead" id="progLead"></p>
    <div class="patch-banner" id="progPatch" style="display:none"></div>
    <div id="progBody"></div>
  </div>
  </section>

  <!-- ========== FAILURE MODES ========== -->
  <section class="app-view" id="view-laws" data-view="laws">
  <div class="card">
    <div class="view-title">Failure modes · named burns we track</div>
    <p class="view-lead">
      One row = one <strong>failure mode</strong> (shared registry id).
      Categories (Authority, Voice, …) are how you <em>enter</em> the problem;
      this table is the full book of modes. Each mode links to
      <strong>incidents</strong>, <strong>mitigations</strong> (ratchets), and
      <strong>observation</strong> (still red on surfaces?).
      Source: <span class="mono">failure-mode-registry.yaml</span>.
    </p>
    <p class="muted" style="font-size:.82rem;line-height:1.45;margin:.35rem 0 .5rem">
      <strong>How to read a row (simple):</strong>
      <em>named?</em> = mode is in the book ·
      <em>mitigations</em> = code ratchets ·
      <em>observe</em> = battery on that law ·
      <em>proven on surfaces / still open</em> = how widely the mitigation is path-proven
      (not “product broken %”).
      Named/sealed in the book does <strong>not</strong> mean every product surface is proven.
    </p>
    <p class="muted" style="font-size:.8rem;margin:0 0 .35rem">
      <strong>Category</strong> = how you enter the problem (authority, laundry, antipattern, voice, purity, memory).
      A mode can have several. <strong>Slice</strong> = where it breaks in the control plane (ownership, delivery, …).
    </p>
    <div id="lawsCategoryPills" class="row" style="margin:0 0 .4rem;gap:.35rem"></div>
    <div id="lawsPlanePills" class="row" style="margin:0 0 .55rem;gap:.35rem"></div>
    <div class="filter-row">
      <input type="search" id="lawsQ" placeholder="search mode id / name / category / incident…" style="min-width:12rem" />
      <select id="lawsCategory" title="Quality category (authority / laundry / …)">
        <option value="">all categories</option>
        <option value="authority">authority</option>
        <option value="laundry">laundry</option>
        <option value="antipattern">antipattern</option>
        <option value="voice">voice</option>
        <option value="purity">purity</option>
        <option value="memory">memory</option>
      </select>
      <select id="lawsPlane" title="Control-plane slice — not category">
        <option value="">all slices</option>
        <option value="memory">memory</option>
        <option value="ownership">ownership</option>
        <option value="delivery">delivery</option>
        <option value="packaging">packaging</option>
        <option value="cognition">cognition</option>
        <option value="substrate">substrate</option>
        <option value="authoring">authoring</option>
      </select>
      <select id="lawsLife" title="Is the mode named/sealed in the registry book?">
        <option value="">all named states</option>
        <option value="sealed">named+unit sealed</option>
        <option value="named">named</option>
        <option value="partial">partial</option>
        <option value="open">open</option>
      </select>
      <select id="lawsHealth" title="Observation battery for this mode">
        <option value="">all observe status</option>
        <option value="fail">observe fail</option>
        <option value="gap">gap</option>
        <option value="thin">thin</option>
        <option value="pass">observe✓</option>
        <option value="ok">join only</option>
      </select>
      <label style="font-size:.85rem"><input type="checkbox" id="lawsSoakOnly" /> needs soak</label>
      <label style="font-size:.85rem"><input type="checkbox" id="lawsSurfaceRed" /> still open on surfaces</label>
      <button type="button" class="secondary" id="btnLawsShowAll">Show all</button>
      <button type="button" class="secondary" id="btnLawsReload">Reload</button>
      <span class="muted mono" id="lawsMeta"></span>
    </div>
    <div style="overflow:auto;max-height:min(70vh, 40rem)">
      <table class="mode-table" id="lawsTable">
        <thead>
          <tr>
            <th title="Failure mode id (registry)">failure mode</th>
            <th title="Quality categories: authority · laundry · antipattern · voice · purity · memory">categories</th>
            <th title="Where in the control plane it breaks — not category">slice</th>
            <th title="In the book: named / unit sealed — not surface-wide proven">named?</th>
            <th title="Honest: unit-only / surface_proven / overclaim">honest status</th>
            <th title="Observation battery for this mode">observe</th>
            <th title="% of product surfaces with any proof for this mode">proven on surfaces</th>
            <th title="Surfaces still without path-faithful proof">still open</th>
            <th title="Multi-turn soak still wanted">soak</th>
            <th title="Matrix cells for this mode">matrix</th>
            <th title="Seek transition edges">edges</th>
            <th title="Code mitigations (ratchets)">mitigations</th>
            <th></th>
          </tr>
        </thead>
        <tbody id="lawsBody"></tbody>
      </table>
    </div>
  </div>
  <div class="card" id="lawDetailCard" style="display:none">
    <div class="row" style="justify-content:space-between">
      <strong id="lawDetailTitle">Mode</strong>
      <a class="deep-link" id="lawDetailSeekLink" href="#/seek">Seek</a>
    </div>
    <div id="lawDetailBody" class="muted" style="margin-top:.5rem"></div>
  </div>
  </section>

  <!-- ========== HOW WE RUN (techniques map) ========== -->
  <section class="app-view" id="view-techniques" data-view="techniques">
  <div class="card">
    <div class="view-title">How we run · proof techniques</div>
    <p class="view-lead">
      One place for <strong>static</strong> vs <strong>dynamic</strong> proof and
      <strong>how a run starts</strong> for each quality program.
      The multi-turn harness (portable package) implements path-faithful freezes;
      it is one tool under <em>Multi-turn proof</em> — not a second law book.
    </p>
  </div>
  <div class="card">
    <div class="view-title" style="font-size:.95rem">Two technique families</div>
    <div class="job-cards" style="margin-top:.5rem">
      <div class="job-card">
        <div class="jid">Static</div>
        <div class="jown">Code / inventory — no product chat turn required</div>
        <div class="jq">
          <strong>Ratchets</strong> — contracts + pytest (fail closed without soak).<br/>
          <strong>Daily FM seek</strong> — known ratchets + path sketch + optional LLM code hunt from the law.<br/>
          <strong>Coverage board</strong> — surface × FM cells (empty = red debt).<br/>
          <strong>Coverage battery join/ratchet</strong> — registry ↔ matrix ↔ files exist / pytest batch.
        </div>
      </div>
      <div class="job-card">
        <div class="jid">Dynamic</div>
        <div class="jown">Multi-turn path — chat looks fine while ledger may burn</div>
        <div class="jq">
          <strong>Transition edges</strong> — surface × SoR × finite act catalog.<br/>
          <strong>Author → Runner → Verdict</strong> — scenarios / freezes (geometry stub or host HTTP).<br/>
          <strong>Coverage battery scripts + live</strong> — freeze scripts + live SoR audit.<br/>
          <strong>Matrix neighbors</strong> — finite expansion core + neighbor cells.
        </div>
      </div>
    </div>
  </div>
  <div class="card">
    <div class="view-title" style="font-size:.95rem">Initiate runs by quality program</div>
    <p class="muted" style="font-size:.85rem;margin:0 0 .65rem">
      Classification programs name failure modes; <strong>Coverage</strong> is the runtime proof program that schedules static + dynamic work.
    </p>
    <div style="overflow:auto">
      <table class="mode-table">
        <thead>
          <tr>
            <th>Program</th>
            <th>Static entry</th>
            <th>Dynamic entry</th>
            <th>Console</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Authority</strong><br/><span class="muted">CAQ FM slugs</span></td>
            <td class="mono" style="font-size:.72rem">registry ratchets · daily_seek --registry-id … · surface×FM column</td>
            <td class="mono" style="font-size:.72rem">matrix cell · freeze script · Author residual · Runner host</td>
            <td><a class="deep-link" href="#/laws">Failure modes</a> · <a class="deep-link" href="#/program/cognitive_authority">Authority</a></td>
          </tr>
          <tr>
            <td><strong>Antipatterns</strong><br/><span class="muted">A1–A19</span></td>
            <td class="mono" style="font-size:.72rem">structural contracts · pre_decide · failsoft · antipattern ratchets</td>
            <td class="mono" style="font-size:.72rem">only when mapped CAQ FM needs soak (via Authority path)</td>
            <td><a class="deep-link" href="#/program/construction_antipattern">Antipatterns</a></td>
          </tr>
          <tr>
            <td><strong>Laundry</strong><br/><span class="muted">regex · if-else · phrase · A17–19</span></td>
            <td class="mono" style="font-size:.72rem">caq8 · no-vocabulary · failsoft · pre_decide tables</td>
            <td class="mono" style="font-size:.72rem">rare — laundry is construction; prove via unit + related FM soak</td>
            <td><a class="deep-link" href="#/program/code_poison_laundry">Laundry</a></td>
          </tr>
          <tr>
            <td><strong>Voice</strong><br/><span class="muted">DT / packaging</span></td>
            <td class="mono" style="font-size:.72rem">content_block · failsoft packaging · FE chip seals</td>
            <td class="mono" style="font-size:.72rem">path freezes that assert blocks/chips on open leaf</td>
            <td><a class="deep-link" href="#/program/product_voice">Voice</a></td>
          </tr>
          <tr>
            <td><strong>Purity</strong><br/><span class="muted">seal grade</span></td>
            <td class="mono" style="font-size:.72rem">scoreboard sweep tests · known_gap inventory</td>
            <td class="mono" style="font-size:.72rem">re-burn soaks pointed from purity rows</td>
            <td><a class="deep-link" href="#/program/purity_scoreboard">Purity</a></td>
          </tr>
          <tr>
            <td><strong>Coverage</strong><br/><span class="badge partial">runtime proof</span></td>
            <td class="mono" style="font-size:.72rem">surface_coverage · daily_seek --quick · law_seek join/ratchet</td>
            <td class="mono" style="font-size:.72rem">law_seek scripts/live · Author → Runner → Verdict · seek edges</td>
            <td><a class="deep-link" href="#/seek">Observe</a> · <a class="deep-link" href="#/program/surface_law_coverage">Where unproven</a> · <a class="deep-link" href="/surface-map" target="_blank" rel="noopener">Heat map ↗</a></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
  <div class="card">
    <div class="view-title" style="font-size:.95rem">CLI cheat sheet (host monorepo)</div>
    <pre class="stack-box" style="margin:0"># Static — everyday
python -m conjecture_host.expansion daily_seek --quick
python -m conjecture_host.expansion surface_coverage

# Coverage battery (static join + optional dynamic scripts/live)
python -m conjecture_host.expansion law_seek --quick
python -m conjecture_host.expansion law_seek --live --quick

# Dynamic multi-turn (Author → Runner)
python -m conjecture_host.expansion candidates --write --limit 30
# then Console: Author → select → Runner (geometry stub | host HTTP) → Verdict

# One FM static + optional LLM code hunt (Conjecture invent LLM env — not platform library)
python -m conjecture_host.expansion daily_seek --registry-id owner_steal --llm</pre>
    <p class="muted" style="margin:.65rem 0 0;font-size:.82rem">
      Artifacts: <span class="mono">artifacts/fm_daily_seek/</span> ·
      <span class="mono">artifacts/law_seek/</span> ·
      <span class="mono">artifacts/surface_coverage/</span> ·
      candidate evidence under the portable package.
    </p>
  </div>
  </section>

  <!-- ========== SEEK (law_seek battery) ========== -->
  <section class="app-view" id="view-seek" data-view="seek">
  <div class="card">
    <div class="view-title">Observe · evidence battery (law_seek)</div>
    <p class="view-lead" style="margin:0 0 .5rem;font-size:.88rem">
      After mitigations are in code, run observation here: joins, ratchets, multi-turn scripts,
      and live SoR. Failures mean “still seeing the burn,” not a new failure-mode taxonomy.
    </p>
    <p class="view-lead">
      <strong>Crawl coverage + live SoR</strong> — not a second law book.
      Join integrity · registry ratchets · transition edges · Conjecture scripts · optional live ledger.
      Artifacts: <span class="mono">host_artifacts/law_seek/</span> (MD export, not primary UX).
    </p>
    <div class="run-bar">
      <div class="row">
        <button type="button" id="btnSeekRunQuick">Run quick</button>
        <button type="button" class="secondary" id="btnSeekRunFull">Run full</button>
        <button type="button" class="secondary" id="btnSeekRunLive">Run quick + live</button>
        <button type="button" class="danger" id="btnSeekStop" disabled title="Stop the in-flight Coverage battery">Stop</button>
        <button type="button" class="secondary" id="btnSeekReload">Load latest</button>
        <label style="font-size:.85rem"><input type="checkbox" id="seekSkipScripts" /> skip scripts</label>
        <span class="muted mono" id="seekRunStatus"></span>
      </div>
      <p class="muted" style="margin:.45rem 0 0;font-size:.78rem">
        While running: use <strong>Stop</strong> (cancels between phases). Status shows
        <span class="mono">running…</span> until finish or stop.
      </p>
    </div>
    <div class="stat-cards" id="seekStats"></div>
    <p class="muted mono" id="seekMeta" style="font-size:.8rem;margin:0 0 .75rem"></p>
  </div>
  <div class="card">
    <strong>Mode board</strong>
    <p class="muted" style="font-size:.82rem;margin:.25rem 0 .5rem">
      Same table as <span class="mono">latest.md</span> — click registry_id → Laws.
    </p>
    <div style="overflow:auto;max-height:16rem">
      <table class="mode-table">
        <thead>
          <tr>
            <th>registry_id</th>
            <th>lifecycle</th>
            <th>soak</th>
            <th>matrix</th>
            <th>edges</th>
            <th>ratchets</th>
          </tr>
        </thead>
        <tbody id="seekModeBody"></tbody>
      </table>
    </div>
  </div>
  <div class="card">
    <div class="filter-row">
      <strong>Checks by layer</strong>
      <select id="seekLayer">
        <option value="">all layers</option>
        <option value="join">join</option>
        <option value="ratchet">ratchet</option>
        <option value="seek">seek</option>
        <option value="script">script</option>
        <option value="live">live</option>
      </select>
      <select id="seekStatus">
        <option value="">all status</option>
        <option value="fail">fail</option>
        <option value="error">error</option>
        <option value="pass">pass</option>
        <option value="skip">skip</option>
      </select>
      <input type="search" id="seekQ" placeholder="filter check_id / registry…" style="min-width:10rem" />
    </div>
    <div id="seekChecks"></div>
  </div>
  <div class="card">
    <strong>Open work queue</strong>
    <div id="seekOpenWork" class="muted" style="margin-top:.5rem">—</div>
  </div>
  <div class="card" id="seekLiveCard" style="display:none">
    <strong>Live ledger hits</strong>
    <div id="seekLiveHits" class="muted" style="margin-top:.5rem">—</div>
  </div>
  <details class="help-block">
    <summary style="cursor:pointer;font-weight:600">Markdown export (latest.md)</summary>
    <pre id="seekMarkdown" style="max-height:14rem"></pre>
  </details>
  </section>

  <!-- ========== CANDIDATES ========== -->
  <section class="app-view" id="view-candidates" data-view="candidates">
  <div class="card" id="candidatesCard">
    <div class="row" style="justify-content:space-between">
      <div>
        <div class="view-title">Candidates</div>
        <p class="view-lead" style="margin:0">
          Browse invent / expand / residual scenarios. Select rows →
          <strong>Runner</strong> executes · results enqueue to
          <strong>Verdict</strong> (session review backlog).
        </p>
      </div>
      <span class="muted mono" id="candMeta"></span>
    </div>
    <p class="pipe-caption">Console path — Candidates → Runner → Verdict</p>
    <div class="pipe" id="discoveryPipe" role="list" aria-label="Console path">
      <span class="pipe-stage current" role="listitem" title="invent / expand YAML">● Candidates</span>
      <span class="pipe-arrow" aria-hidden>→</span>
      <span class="pipe-stage upcoming" role="listitem" title="geometry or host HTTP">○ Runner</span>
      <span class="pipe-arrow" aria-hidden>→</span>
      <span class="pipe-stage upcoming" role="listitem" title="session review backlog">○ Verdict</span>
      <span class="pipe-arrow" aria-hidden>→</span>
      <span class="pipe-stage upcoming" role="listitem" title="CI golden">○ Sealed</span>
    </div>
    <p class="muted" style="margin:0 0 1rem; font-size:.85rem">
      Concepts under <strong>Help</strong>: taxonomy · harness plugs · agentic pipeline.
      After a run, open <strong>Verdict</strong> for session review (<span class="mono">review conjecture backlog</span>).
    </p>
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
      <button type="button" class="secondary" id="btnGoRunFromList">Run selected →</button>
    </div>
    <div id="candList" class="muted">Loading candidates…</div>
    <div id="candDetail" style="display:none; margin-top:1rem">
      <div class="row" style="justify-content:space-between; margin-bottom:.5rem">
        <div>
          <a href="#/candidates" class="muted" id="candBack" style="text-decoration:none">← all candidates</a>
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
        <button type="button" class="secondary cand-tab" data-tab="evidence">Evidence</button>
      </div>
      <div class="row" id="candDeepLinks" style="margin-bottom:.75rem"></div>
      <div class="row" style="margin-bottom:.75rem">
        <button type="button" id="btnCandRun">Run (geometry hold)</button>
        <button type="button" class="secondary" id="btnCandSteal">Run planted steal</button>
        <button type="button" class="secondary" id="btnCandRunHost">Run (host HTTP)</button>
        <button type="button" class="secondary" id="btnCandFindings">Author findings</button>
        <button type="button" class="secondary" id="btnOpenInRunTab">Open in Runner</button>
        <button type="button" class="secondary" id="btnOpenVerdict">Open Verdict</button>
        <span class="muted" style="font-size:.8rem">Evidence under <span class="mono">evidence/&lt;id&gt;/</span>. Geometry = stub; Host = product Act · Verdict = backlog review.</span>
      </div>
      <div id="candPanelTrajectory" class="cand-panel"></div>
      <div id="candPanelScenario" class="cand-panel" style="display:none"></div>
      <div id="candPanelScript" class="cand-panel" style="display:none"></div>
      <div id="candPanelEvidence" class="cand-panel" style="display:none"></div>
    </div>
  </div>
  </section>

  <!-- ========== RUNNER ========== -->
  <section class="app-view" id="view-run" data-view="run">
  <div class="card">
    <div class="view-title">Runner · multi-turn execute</div>
    <p class="view-lead" style="margin-bottom:.5rem">
      <strong>Dynamic</strong> technique only: execute authored scenarios
      (geometry stub or host product). Full map of static vs dynamic:
      <a class="deep-link" href="#/techniques">How we run</a>.
      Each finished run enqueues a <strong>Verdict</strong> item for session review.
    </p>
    <ol class="muted" style="margin:0 0 1rem; padding-left:1.25rem; font-size:.88rem; line-height:1.5">
      <li><strong>Candidates</strong> — tick rows (or filter → Select all visible).</li>
      <li><strong>Runner</strong> — Selected only · adapter · <strong>Run batch</strong>.</li>
      <li><strong>Verdict</strong> — session agent classifies · suggests fixes · <code>fix</code> closes with patch.</li>
    </ol>
    <p class="muted" style="margin:0 0 .75rem; font-size:.85rem">
      One scenario: open it on Candidates → <strong>Run (host HTTP)</strong> on the detail page.
    </p>
    <div class="row" style="margin-bottom:.75rem">
      <span class="muted mono" id="hostRunnerMeta">checking host driver…</span>
    </div>
    <div class="run-bar" id="candRunBar">
      <div class="row" style="margin-bottom:.5rem">
        <label><input type="radio" name="candSelMode" value="ids" id="candSelModeIds" checked /> Selected only</label>
        <label><input type="radio" name="candSelMode" value="all" id="candSelModeAll" /> All (filtered on Candidates)</label>
        <button type="button" class="secondary" id="btnCandSelectVisible" style="padding:.35rem .65rem">Select all visible</button>
        <button type="button" class="secondary" id="btnCandClearSel" style="padding:.35rem .65rem">Clear selection</button>
        <span class="muted" id="candSelCount" style="font-size:.8rem"></span>
      </div>
      <div id="runSelectedList" class="muted mono" style="font-size:.78rem; margin:0 0 .65rem; max-height:6rem; overflow:auto; border:1px solid #e4e4e7; border-radius:.4rem; padding:.5rem; background:#fff">
        No scenarios selected — go to Candidates and tick checkboxes.
      </div>
      <div class="row">
        <label>Adapter
          <select id="candAdapter" title="adapter">
            <option value="geometry">Geometry hold (stub — no product API)</option>
            <option value="host">Host HTTP (product E2E · burns LLM quota)</option>
          </select>
        </label>
        <label id="candStealLabel" style="display:none">
          <input type="checkbox" id="candBatchSteal" /> planted steal
        </label>
        <button type="button" id="btnCandBatchRun">Run batch</button>
        <button type="button" class="secondary" id="btnRunFailedOnly" style="display:none">Re-run last failures</button>
        <button type="button" class="secondary" id="btnGoCandidatesFromRun">← Candidates</button>
      </div>
      <p class="muted" style="margin:.5rem 0 0; font-size:.8rem">
        Host uses <span class="mono">CONJECTURE_HOST_EMAIL</span> /
        <span class="mono">CONJECTURE_HOST_BASE_URL</span> (env only — never baked into the package).
        Product LLM hourly caps often 429 large Host batches — run a few at a time, or use Geometry for stub checks.
      </p>
    </div>
    <div id="candBatchReport" class="report-card" style="display:none"></div>
    <div id="runSelectedHint" class="muted" style="margin-top:.75rem"></div>
  </div>
  </section>

  <!-- ========== VERDICT (session review queue = backlog in practice) ========== -->
  <section class="app-view" id="view-backlog" data-view="backlog">
  <div class="card">
    <div class="row" style="justify-content:space-between;align-items:flex-start">
      <div>
        <div class="view-title">Verdict</div>
        <p class="view-lead" style="margin:0">
          <strong>The practical backlog.</strong> After <strong>Runner</strong> finishes, each scenario
          lands here for the <strong>session agent</strong>
          (label: <span class="mono">__SESSION_AGENT_LABEL__</span> via
          <span class="mono">CONJECTURE_SESSION_AGENT_LABEL</span>).
          Classify <span class="mono">conjecture_caught</span> vs
          <span class="mono">product_bug</span> (or rate_limit / infra), write findings tables,
          then <strong>fix</strong> to close with a documented patch.
        </p>
      </div>
      <button type="button" class="secondary" id="btnBacklogRefresh">Refresh</button>
    </div>
    <p class="muted" style="margin:.75rem 0 0;font-size:.85rem">
      Pipeline: <strong>Candidates</strong> → <strong>Runner</strong> → <strong>Verdict</strong>.
      Session commands: <strong>review conjecture backlog</strong> → <strong>fix</strong>
      (open items close; patch documented on the closed item).
    </p>
    <p class="muted mono" id="backlogMeta" style="margin:.5rem 0 0;font-size:.78rem"></p>
  </div>
  <div id="backlogList" class="muted">Loading backlog…</div>
  <div id="backlogDetail" style="display:none" class="card"></div>
  </section>

  <!-- ========== ADMIN ========== -->
  <section class="app-view" id="view-admin" data-view="admin">
  <div class="card">
    <div class="row" style="justify-content:space-between; align-items:flex-start">
      <div>
        <div class="view-title">Admin</div>
        <p class="view-lead" style="margin:0">
          Environment settings, test account, LLM endpoints, host driver, and conversation cleanup.
          Secrets are never shown in full — only set / masked preview.
        </p>
      </div>
      <button type="button" class="secondary" id="btnAdminRefresh">Refresh</button>
    </div>
    <ul class="warn-list" id="adminWarnings" style="display:none"></ul>
  </div>

  <div class="admin-grid">
    <div class="card">
      <strong>Test account (host E2E)</strong>
      <p class="muted" style="margin:.35rem 0 .5rem; font-size:.82rem">Product runs and cleanup use this tenant account — not superadmin by default.</p>
      <table class="kv" id="adminAccountTable"><tbody>
        <tr><th>Loading…</th><td></td></tr>
      </tbody></table>
    </div>
    <div class="card">
      <strong>Host driver</strong>
      <p class="muted" style="margin:.35rem 0 .5rem; font-size:.82rem">Bot0 HTTP Adapter · product APIs only.</p>
      <table class="kv" id="adminHostTable"><tbody>
        <tr><th>Loading…</th><td></td></tr>
      </tbody></table>
    </div>
    <div class="card">
      <strong>Invent LLM</strong>
      <p class="muted" style="margin:.35rem 0 .5rem; font-size:.82rem">Scenario / geometry invent proposals.</p>
      <table class="kv" id="adminInventTable"><tbody>
        <tr><th>Loading…</th><td></td></tr>
      </tbody></table>
    </div>
    <div class="card">
      <strong>Findings reviewer</strong>
      <p class="muted" style="margin:.35rem 0 .5rem; font-size:.82rem">
        Who writes post-run verdicts. Default: <strong>session</strong> —
        coding agent + monorepo + Verdict (backlog) handoff.
      </p>
      <table class="kv" id="adminReviewerTable"><tbody>
        <tr><th>Loading…</th><td></td></tr>
      </tbody></table>
    </div>
    <div class="card">
      <strong>Remote findings LLM</strong>
      <p class="muted" style="margin:.35rem 0 .5rem; font-size:.82rem">
        Optional. Only when <span class="mono">CONJECTURE_FINDINGS_REVIEWER=openai</span>.
        Idle under default session mode.
      </p>
      <table class="kv" id="adminFindingsTable"><tbody>
        <tr><th>Loading…</th><td></td></tr>
      </tbody></table>
    </div>
    <div class="card">
      <strong>Candidates directory</strong>
      <table class="kv" id="adminCandTable"><tbody>
        <tr><th>Loading…</th><td></td></tr>
      </tbody></table>
    </div>
    <div class="card">
      <strong>Console process</strong>
      <table class="kv" id="adminConsoleTable"><tbody>
        <tr><th>Loading…</th><td></td></tr>
      </tbody></table>
    </div>
    <div class="card" style="grid-column: 1 / -1">
      <div class="row" style="justify-content:space-between;align-items:center">
        <div>
          <strong>Runner log</strong>
          <p class="muted" style="margin:.25rem 0 0;font-size:.82rem">
            In-process ring buffer (stderr also). Env:
            <span class="mono">CONJECTURE_LOG_LEVEL</span> ·
            <span class="mono">CONJECTURE_LOG_JSON=1</span>
          </p>
        </div>
        <button type="button" class="secondary" id="btnRunnerLogRefresh">Refresh log</button>
      </div>
      <pre id="adminRunnerLog" class="muted" style="margin:.65rem 0 0;max-height:14rem;font-size:.72rem;background:#fafafa;color:#18181b;border:1px solid #e4e4e7;padding:.65rem;border-radius:.4rem;overflow:auto">No events yet — run a candidate.</pre>
    </div>
    <div class="card" style="grid-column: 1 / -1">
      <strong id="adminLimitsTitle">Host product abuse controls (why empty shells / 429s)</strong>
      <p class="muted" style="margin:.35rem 0 .5rem; font-size:.82rem" id="adminLimitsLead">
        Portable categories (login · chat · LLM burst/hour · thread create · empty shells).
        Product-specific knobs are filled by host SPI when available.
        GeometryHold never calls product chat/login.
      </p>
      <table class="kv" id="adminLimitsTable"><tbody>
        <tr><th>Loading…</th><td></td></tr>
      </tbody></table>
      <p class="muted" style="margin:.5rem 0 0; font-size:.8rem" id="adminLimitsHint"></p>
    </div>
  </div>

  <div class="card">
    <strong>Conversation cleanup</strong>
    <p class="view-lead" style="margin:.35rem 0 .75rem">
      Archive Conjecture-owned product threads for the test account
      (<span class="mono">cbr-*</span> / <span class="mono">conjecture*</span>).
      Soft-delete via product API — not SQL. Does not touch real demo chats.
    </p>
    <div class="row">
      <button type="button" class="secondary" id="btnCleanupPreview">Preview cleanup</button>
      <button type="button" id="btnCleanupRun">Clean up Conjecture runs</button>
      <label title="Only archive threads with 0 messages">
        <input type="checkbox" id="cleanupEmptyOnly" checked /> empty shells only
      </label>
    </div>
    <p class="muted mono" id="adminCleanupMeta" style="margin:.5rem 0 0; font-size:.78rem"></p>
    <div id="candCleanupReport" class="report-card" style="display:none"></div>
  </div>
  </section>

  <!-- ========== DEMO ========== -->
  <section class="app-view" id="view-demo" data-view="demo">
  <div class="card">
    <div class="view-title">Path-faithful demo</div>
    <p class="view-lead">Mini-app sole-continue story (not host product E2E). Healthy PASS; planted bugs must FAIL.</p>
    <div class="row">
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
  </section>

  <!-- ========== HELP ========== -->
  <section class="app-view" id="view-help" data-view="help">
  <div class="card">
    <div class="view-title">Help</div>
    <p class="view-lead" style="margin:0">
      Three lenses on the same system: <strong>what we name</strong> (taxonomy),
      <strong>how we plug into a product</strong> (harness), and
      <strong>how we dedicate agents / LLM skills</strong> so discovery stays rigorous
      and hooked into the monorepo.
    </p>
    <p class="muted" style="margin:.65rem 0 0; font-size:.88rem">
      Core nouns: <strong>Script</strong> · <strong>Turn</strong> · <strong>Driver</strong> ·
      <strong>Observation</strong> · <strong>Invariant</strong>.
      Scenario = flexible description of twists (precursor to Script). See docs/SPEC.md.
    </p>
  </div>

  <details class="help-block" open>
    <summary style="cursor:pointer; font-weight:700; font-size:.95rem">
      0 · Approach map (do not merge quality jobs)
    </summary>
    <p class="muted" style="margin:.5rem 0">
      Epic: <span class="mono">docs/conjecture-control-plane-quality-console.md</span> ·
      Categories: <span class="mono">docs/quality-category-disambiguation.md</span> ·
      Diagnostics: taxonomy §2.4 patching note · AGENTS.md banner.
    </p>
    <div class="stack-box" style="margin:.5rem 0">Doctrine names · registry freezes the id · purity tracks seal grade
· ratchets enforce in code · multi-turn path-faithful proof
· coverage (join / live SoR) crawls · the Console navigates all of it.

Tabs (IA):
  Approach — spine · categories · surface×law · patching note · open work
  Laws     — CAQ failure-mode registry only (not laundry / purity merge)
  Coverage — law_seek battery (join / ratchet / seek / script / live)
  Author → Runner → Verdict — multi-turn prove-out pipeline
  Demo / Admin / Help — portable proof + env + doctrine

Categories (split forever):
  cognitive_authority · construction_antipattern · code_poison_laundry
  product_voice · purity_scoreboard · surface_law_coverage

Diagnostic ladder:
  User hit → FM slug → Root M/E/S/D → A# → earliest layer → seal + ratchet

Coding-agent note (every diagnostic):
  DO NOT invent · hotfix · break-fix · shortcut · regress
  FOLLOW LAWS · AGENTS.md · no laundry / regex as sole NL arbiter

CLI:
  python -m conjecture_host.expansion law_seek --quick
  python -m conjecture_host.expansion console_snapshot
  conjecture ui   # http://127.0.0.1:8765</div>
    <p class="muted" style="margin:.5rem 0 0; font-size:.85rem">
      Deep-links: <span class="mono">#/home</span> ·
      <span class="mono">#/laws/owner_steal</span> ·
      <span class="mono">#/seek?registry=finite_chip_rerun</span> ·
      <span class="mono">#/candidates?mode=owner_steal</span>.
      Purity v2–v4 stay scoreboards (not a duplicate Laws tab).
    </p>
  </details>

  <!-- 1. Taxonomy -->
  <details class="help-block">
    <summary style="cursor:pointer; font-weight:700; font-size:.95rem">
      1 · Working taxonomy (not FMEA reinvention)
    </summary>
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
            <span class="mono">registry.yaml</span>. Slug = unique id for the <em>class</em>, not one occurrence.</td>
          <td style="padding:.4rem" class="mono">owner_steal, hollow_open, draft_improve_to_ir</td>
        </tr>
        <tr style="border-bottom:1px solid #e4e4e7">
          <td style="padding:.4rem; vertical-align:top"><strong>Incident</strong></td>
          <td style="padding:.4rem">One observed production, soak, eval, or test occurrence of a mode.
            Many incidents → one mode.</td>
          <td style="padding:.4rem">conv_1732aa88 · open improve stole to IR</td>
        </tr>
        <tr style="border-bottom:1px solid #e4e4e7">
          <td style="padding:.4rem; vertical-align:top"><strong>Candidate scenario</strong></td>
          <td style="padding:.4rem">One authored multi-turn trajectory that can expose or stress a mode.
            Inventory rows are trajectories, not modes.</td>
          <td style="padding:.4rem" class="mono">invent_…_glossary_concept · residual…</td>
        </tr>
        <tr style="border-bottom:1px solid #e4e4e7">
          <td style="padding:.4rem; vertical-align:top"><strong>Script / sealed pattern</strong></td>
          <td style="padding:.4rem">CI-runnable form (setup, turns, asserts). Registry
            <span class="mono">portable_seed</span> → <span class="mono">patterns/&lt;seed&gt;/</span>.</td>
          <td style="padding:.4rem" class="mono">patterns/owner_steal_mid_continue/</td>
        </tr>
        <tr>
          <td style="padding:.4rem; vertical-align:top"><strong>Execution evidence</strong></td>
          <td style="padding:.4rem">Trace, assertions, artifacts, verdict from a run —
            proof the law held or broke under that trajectory.</td>
          <td style="padding:.4rem">evidence/…/latest.json · findings tables</td>
        </tr>
      </tbody>
    </table>
    <p class="muted" style="margin:.65rem 0 .35rem; font-size:.85rem"><strong>Discovery workflow</strong></p>
    <p class="muted" style="margin:0; font-size:.85rem">
      <strong>Invent</strong> surface × act × stealer ·
      <strong>Expand</strong> sole×foreign · matrix · residual ·
      Maturation: <strong>Open trajectory → Candidate scenario → Sealed pattern → Execution evidence</strong>
    </p>
    <p class="muted" style="margin:.65rem 0 0; font-size:.85rem">
      <strong>Guardrails:</strong> mode slug ≠ incident id ≠ scenario id.
      Script = runnable artifact. Proof = evidence + verdict (+ session review).
    </p>
  </details>

  <!-- 2. Harness plugs -->
  <details class="help-block" open>
    <summary style="cursor:pointer; font-weight:700; font-size:.95rem">
      2 · Harness plugs (pedantic; for seasoned testers)
    </summary>
    <p class="muted" style="margin:.5rem 0; font-size:.85rem">
      Conjecture is a <strong>test harness</strong>: it runs multi-turn scripts and must drive
      <em>some</em> product while staying product-agnostic. Everyday speech calls every interface
      an “API.” We split names so <strong>who calls whom</strong> is clear.
    </p>
    <pre class="muted" style="margin:.5rem 0; font-size:.72rem; background:#f4f4f5; color:#18181b; padding:.65rem; border-radius:.4rem; overflow:auto">YOU / CI / this console
       │  (1) How you invoke Conjecture  →  CLI · run_script() · this UI
       ▼
  ┌─────────────┐
  │  Conjecture │  testing tool
  └──────┬──────┘
         │  (2) How Conjecture invokes the product
         │      standardized plugin: observe_turn → Observation
         ▼
  ┌─────────────┐
  │ Adapter /   │  product-specific glue (implements the plugin)
  │ Driver      │
  └──────┬──────┘
         │  (3) How the product is actually called
         ▼
  ┌─────────────┐
  │ Product API │  chat / SSE / session / ledger (Bot0, or a third party)
  └─────────────┘</pre>
    <table class="muted" style="width:100%; border-collapse:collapse; font-size:.85rem; margin:.5rem 0">
      <thead>
        <tr style="text-align:left; border-bottom:1px solid #d4d4d8">
          <th style="padding:.3rem .4rem">Term</th>
          <th style="padding:.3rem .4rem">Meaning here</th>
        </tr>
      </thead>
      <tbody>
        <tr style="border-bottom:1px solid #e4e4e7">
          <td style="padding:.35rem .4rem; vertical-align:top"><strong>Contract</strong></td>
          <td style="padding:.35rem .4rem">Shared test language: Script · Turn · Observation (owner · pins) ·
            invariants · failure-mode slug · PASS healthy / FAIL planted.</td>
        </tr>
        <tr style="border-bottom:1px solid #e4e4e7">
          <td style="padding:.35rem .4rem; vertical-align:top"><strong>Plugin interface (SPI)</strong></td>
          <td style="padding:.35rem .4rem">Plug shape <em>Conjecture defines</em> and <em>calls</em>.
            Hosts implement <span class="mono">ControlPlaneAdapter</span>
            (<span class="mono">apply_effect</span> · <span class="mono">observe_turn</span>).</td>
        </tr>
        <tr style="border-bottom:1px solid #e4e4e7">
          <td style="padding:.35rem .4rem; vertical-align:top"><strong>Adapter / Driver</strong></td>
          <td style="padding:.35rem .4rem">One concrete plugin for one product.
            Portable: <span class="mono">GeometryHoldAdapter</span> (stub),
            <span class="mono">MiniAppAdapter</span>. Host products supply their own
            HTTP/driver via <span class="mono">CONJECTURE_HOST_RUNNER</span>.</td>
        </tr>
        <tr style="border-bottom:1px solid #e4e4e7">
          <td style="padding:.35rem .4rem; vertical-align:top"><strong>Product API</strong></td>
          <td style="padding:.35rem .4rem">How clients call the chatbot (auth, chat, SSE, control). Adapter uses these —
            not the same arrow as “how you start Conjecture.”</td>
        </tr>
        <tr>
          <td style="padding:.35rem .4rem; vertical-align:top"><strong>Hook</strong></td>
          <td style="padding:.35rem .4rem">Step inside the Adapter: arrange · act · wait · observe · evidence.
            Multi-turn E2E = sequence of hooks.</td>
        </tr>
      </tbody>
    </table>
    <p class="muted" style="margin:.5rem 0 0; font-size:.85rem">
      <strong>SPI ≠ product API:</strong> product API = callers come to the chatbot;
      SPI = Conjecture calls <em>your</em> Adapter and gets owner · pins · outcome.
      That is what keeps the harness product-agnostic. Host E2E uses product HTTP only
      (no harness SQL). Host identity is env-only
      (<span class="mono">CONJECTURE_HOST_EMAIL</span> / <span class="mono">BASE_URL</span> /
      <span class="mono">PASSWORD</span>).
    </p>
  </details>

  <!-- 3. Agentic architecture / pipeline -->
  <details class="help-block" open>
    <summary style="cursor:pointer; font-weight:700; font-size:.95rem">
      3 · Agentic architecture — author · runner · session reviewer · fix backlog
    </summary>
    <p class="muted" style="margin:.5rem 0; font-size:.85rem">
      Conjecture is a <strong>portable pipeline</strong>. Host products (Bot0 is one client)
      wire identity, adapters, and labels via <strong>environment variables</strong> —
      nothing product-specific is baked into the package defaults.
      Skills stay split so discovery is rigorous and hooked into <em>your</em> monorepo.
    </p>
    <pre class="muted" style="margin:.5rem 0; font-size:.72rem; background:#f4f4f5; color:#18181b; padding:.65rem; border-radius:.4rem; overflow:auto">1 AUTHOR (LLM skill)     invent / expand scenarios
   provider from CONJECTURE_INVENT_LLM_*   →  code laws + physics
              │
              ▼  candidate YAML
2 RUNNER (Python only)   execute Act · score envelopes
   GeometryHoldAdapter or Host runner (CONJECTURE_HOST_RUNNER)
              │  evidence + conversation_id
              ▼
3 SESSION REVIEWER       verdict on what just happened
   monorepo coding agent (label: CONJECTURE_SESSION_AGENT_LABEL)
   mode: CONJECTURE_FINDINGS_REVIEWER=session (default)
   classifies: conjecture_caught | product_bug | rate_limit | infra
              │  suggested_fixes[]
              ▼
4 VERDICT (backlog)      product_bug → backlog_fix
   same session can implement seals in-tree</pre>
    <table class="muted" style="width:100%; border-collapse:collapse; font-size:.85rem; margin:.5rem 0">
      <thead>
        <tr style="text-align:left; border-bottom:1px solid #d4d4d8">
          <th style="padding:.3rem .4rem">Skill</th>
          <th style="padding:.3rem .4rem">Who</th>
          <th style="padding:.3rem .4rem">Owns</th>
        </tr>
      </thead>
      <tbody>
        <tr style="border-bottom:1px solid #e4e4e7">
          <td style="padding:.4rem; vertical-align:top"><strong>Author</strong></td>
          <td style="padding:.4rem">Invent LLM (any OpenAI-compatible endpoint)</td>
          <td style="padding:.4rem">Propose scenarios / geometry. Code backs laws + physics.
            Env: <span class="mono">CONJECTURE_INVENT_LLM_BASE_URL</span> ·
            <span class="mono">_MODEL</span> · <span class="mono">_API_KEY</span>
            (or <span class="mono">OPENAI_API_KEY</span> fallback).</td>
        </tr>
        <tr style="border-bottom:1px solid #e4e4e7">
          <td style="padding:.4rem; vertical-align:top"><strong>Runner</strong></td>
          <td style="padding:.4rem">Python — no NL “meaning”</td>
          <td style="padding:.4rem">Drive stub or product Host adapter, evaluate invariants, write evidence.
            Soft PASS ≠ good product flow.
            Host: <span class="mono">CONJECTURE_HOST_RUNNER</span> +
            <span class="mono">CONJECTURE_HOST_EMAIL</span> /
            <span class="mono">_PASSWORD</span> / <span class="mono">_BASE_URL</span>.</td>
        </tr>
        <tr style="border-bottom:1px solid #e4e4e7">
          <td style="padding:.4rem; vertical-align:top"><strong>Session reviewer</strong></td>
          <td style="padding:.4rem">Monorepo coding agent<br/>
            <span class="muted">label now: <strong>__SESSION_AGENT_LABEL__</strong></span></td>
          <td style="padding:.4rem">Read <span class="mono">conversation_id</span>, ledger, code paths.
            Full findings tables + <strong>suggested fixes</strong>.
            Mode: <span class="mono">CONJECTURE_FINDINGS_REVIEWER=session</span> (default).
            Display name: <span class="mono">CONJECTURE_SESSION_AGENT_LABEL</span>
            (default <em>session coding agent</em>).</td>
        </tr>
        <tr>
          <td style="padding:.4rem; vertical-align:top"><strong>Fix backlog</strong></td>
          <td style="padding:.4rem">Human + session agent</td>
          <td style="padding:.4rem"><span class="mono">product_bug</span> stays on
            <strong>Verdict</strong> (backlog store). Same session seals contracts + ratchets.
            Close with <span class="mono">close_with_patch</span> after command <strong>fix</strong>.</td>
        </tr>
      </tbody>
    </table>
    <p class="muted" style="margin:.65rem 0 .35rem; font-size:.85rem"><strong>Env map (portable — set in host shell / .env, never commit secrets)</strong></p>
    <table class="muted" style="width:100%; border-collapse:collapse; font-size:.8rem; margin:.35rem 0">
      <thead>
        <tr style="text-align:left; border-bottom:1px solid #d4d4d8">
          <th style="padding:.3rem .4rem">Concern</th>
          <th style="padding:.3rem .4rem">Environment variables</th>
        </tr>
      </thead>
      <tbody>
        <tr style="border-bottom:1px solid #e4e4e7">
          <td style="padding:.35rem .4rem">Invent / author LLM</td>
          <td style="padding:.35rem .4rem" class="mono">CONJECTURE_INVENT_LLM_*</td>
        </tr>
        <tr style="border-bottom:1px solid #e4e4e7">
          <td style="padding:.35rem .4rem">Findings mode</td>
          <td style="padding:.35rem .4rem" class="mono">CONJECTURE_FINDINGS_REVIEWER=session|deterministic|openai</td>
        </tr>
        <tr style="border-bottom:1px solid #e4e4e7">
          <td style="padding:.35rem .4rem">Session agent display label</td>
          <td style="padding:.35rem .4rem" class="mono">CONJECTURE_SESSION_AGENT_LABEL</td>
        </tr>
        <tr style="border-bottom:1px solid #e4e4e7">
          <td style="padding:.35rem .4rem">Host product account + API</td>
          <td style="padding:.35rem .4rem" class="mono">CONJECTURE_HOST_EMAIL · _PASSWORD · _BASE_URL · _RUNNER</td>
        </tr>
        <tr style="border-bottom:1px solid #e4e4e7">
          <td style="padding:.35rem .4rem">Host rate-limit knobs (Admin card)</td>
          <td style="padding:.35rem .4rem" class="mono">CONJECTURE_HOST_LIMITS_PROVIDER · _LIMITS_JSON</td>
        </tr>
        <tr>
          <td style="padding:.35rem .4rem">Candidates / backlog dirs</td>
          <td style="padding:.35rem .4rem" class="mono">CONJECTURE_CANDIDATES_DIR · CONJECTURE_BACKLOG_DIR</td>
        </tr>
      </tbody>
    </table>
    <p class="muted" style="margin:.65rem 0 .35rem; font-size:.85rem"><strong>Why dedicate skills?</strong></p>
    <ul class="muted" style="margin:0; font-size:.85rem">
      <li><strong>Author</strong> invents coverage without writing product routing.</li>
      <li><strong>Runner</strong> is deterministic Act — no fake “understanding.”</li>
      <li><strong>Reviewer</strong> has monorepo context so “invariants passed but intent failed”
        becomes <span class="mono">product_bug</span>, not silence.</li>
      <li><strong>Verdict</strong> (backlog) prevents related product issues from being ignored.</li>
    </ul>
    <p class="muted" style="margin:.65rem 0 .35rem; font-size:.85rem"><strong>How the session agent is triggered</strong></p>
    <p class="muted" style="margin:0; font-size:.85rem">
      The console cannot auto-wake your IDE chat. After a run, items land in the host backlog dir.
      In <strong>this</strong> monorepo coding session (label: <strong>__SESSION_AGENT_LABEL__</strong>):
    </p>
    <ol class="muted" style="margin:.35rem 0 0; padding-left:1.25rem; font-size:.85rem">
      <li><strong>review conjecture backlog</strong> — develop findings, classify,
        <span class="mono">product_bug</span> → open <span class="mono">backlog_fix</span>.</li>
      <li><strong>fix</strong> — implement seals from <span class="mono">suggested_fixes</span>;
        open items are <strong>closed</strong>; the <strong>patch is documented on the closed item</strong>
        (summary, files, commits, tests).</li>
    </ol>
    <p class="muted" style="margin:.65rem 0 0; font-size:.85rem">
      Protocol: <span class="mono">prompts/session_reviewer.md</span>
      · host process doc (if any) under the product monorepo
      · console tabs <strong>Candidates</strong> · <strong>Runner</strong> · <strong>Verdict</strong> · <strong>Admin</strong>.
    </p>
  </details>

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
  </section>
</main>
<script>
/* ---- App shell: top-level views ---- */
const PROGRAM_NAV = {
  'program-authority': 'cognitive_authority',
  'program-laundry': 'code_poison_laundry',
  'program-antipattern': 'construction_antipattern',
  'program-voice': 'product_voice',
  'program-purity': 'purity_scoreboard',
  'program-memory': 'memory_management',
  'program-surface': 'surface_law_coverage',
};
function showAppView(view) {
  let v = view || 'home';
  // Program-* tabs share one section (data-view="program")
  let programId = null;
  if (PROGRAM_NAV[v]) {
    programId = PROGRAM_NAV[v];
    v = 'program';
  } else if (v === 'program' && window._programId) {
    programId = window._programId;
  }
  document.querySelectorAll('.app-view').forEach(el => {
    el.classList.toggle('active', el.getAttribute('data-view') === v);
  });
  document.querySelectorAll('#appNav button[data-view]').forEach(btn => {
    const bv = btn.getAttribute('data-view');
    let on = bv === view || bv === v;
    if (programId && PROGRAM_NAV[bv] === programId) on = true;
    if (v === 'program' && bv === 'program') on = false;
    btn.classList.toggle('active', on);
  });
  window._appView = view || v;
  if (v === 'run') updateRunSelectedHint();
  if (v === 'backlog') loadBacklog();
  if (v === 'admin') loadAdminStatus();
  if (v === 'home') loadHome();
  if (v === 'laws') loadLaws();
  if (v === 'seek') loadSeek();
  if (v === 'program' && programId) loadProgram(programId);
}
function healthBadge(h) {
  // Seek battery label only — never implies surface×law proof.
  // Display names avoid "pass" looking like "proven everywhere".
  const key = String(h || '');
  const m = {
    fail: 'fail', error: 'fail', gap: 'open',
    pass: 'pass',
    ok: 'reg', thin: 'partial', mixed: 'partial',
  };
  const labels = {
    pass: 'seek✓',
    ok: 'join',
    thin: 'thin',
    gap: 'gap',
    fail: 'seek✗',
    error: 'error',
    mixed: 'mixed',
  };
  const cls = m[key] || 'reg';
  const label = labels[key] || key || '—';
  const title = key === 'pass'
    ? 'Seek battery checks for this FM passed — not surface-wide proof'
    : (key === 'ok'
      ? 'Join/ratchet present; no per-mode Seek battery rows'
      : (key === 'thin'
        ? 'Needs generative soak / thin proof'
        : ''));
  return '<span class="badge ' + cls + '" title="' + escapeHtml(title) + '">'
    + escapeHtml(label) + '</span>';
}
function surfaceProofBadge(r) {
  const empty = r.surface_empty;
  const pct = r.surface_any_pct;
  if (empty == null && pct == null) {
    return '<span class="muted">—</span>';
  }
  const pctN = Number(pct || 0);
  const emptyN = Number(empty || 0);
  let cls = 'reg';
  if (emptyN > 0) cls = emptyN >= 20 ? 'fail' : 'open';
  if (pctN >= 40) cls = 'pass';
  else if (pctN >= 15) cls = 'partial';
  return '<span class="badge ' + cls + '" title="Surfaces with any sealed/partial proof for this FM">'
    + escapeHtml(String(pctN)) + '%</span>';
}
function inventoryBadge(r) {
  // Honest open-debt grade — never treat lifecycle:sealed as board-complete.
  const inv = String(r.inventory_status || '');
  const over = !!r.lifecycle_overclaim;
  const m = {
    open: 'fail',
    unit_only: 'fail',
    partial: 'partial',
    surface_proven: 'pass',
  };
  const labels = {
    open: 'open',
    unit_only: 'unit-only',
    partial: 'partial',
    surface_proven: 'surf✓',
  };
  let cls = m[inv] || 'reg';
  let label = labels[inv] || (inv || '—');
  if (over) {
    cls = 'fail';
    label = 'overclaim';
  }
  const title = over
    ? ('registry lifecycle=sealed but 0 surface-sealed cells — open debt'
      + (r.inventory_note ? (': ' + r.inventory_note) : ''))
    : (r.inventory_note || 'inventory_status from surface×law board');
  return '<span class="badge ' + cls + '" title="' + escapeHtml(title) + '">'
    + escapeHtml(label) + '</span>';
}
function setSeekChrome(text, passed) {
  const el = document.getElementById('seekChrome');
  if (!el) return;
  el.textContent = text || 'observation: —';
  el.style.color = passed === true ? '#047857' : (passed === false ? '#b91c1c' : '#52525b');
}
async function loadQualitySnapshot(opts) {
  opts = opts || {};
  const qs = new URLSearchParams();
  if (opts.rebuild) qs.set('rebuild', '1');
  if (opts.run_seek) qs.set('run_seek', '1');
  if (opts.live) qs.set('live', '1');
  if (opts.quick === false) qs.set('quick', '0');
  else qs.set('quick', '1');
  const r = await fetch('/api/quality-snapshot?' + qs.toString());
  const data = await r.json();
  if (data && data.snapshot) {
    window._qcSnapshot = data.snapshot;
    const chrome = (data.snapshot.nav || {}).chrome;
    const passed = (data.snapshot.summary || {}).law_seek_passed;
    if (chrome) setSeekChrome(chrome, passed);
  }
  return data;
}
function renderHomeSpine() {
  // Operator-facing loop (doctrine unchanged — console only navigates).
  const nodes = [
    ['Categories', 'authority · laundry · voice · …'],
    ['Failure modes', 'named burns (registry id)'],
    ['Incidents', 'conv_* soaks we track'],
    ['Mitigations', 'contracts · ratchets in code'],
    ['Observe', 'evidence · surfaces still red'],
  ];
  const el = document.getElementById('homeSpine');
  if (!el) return;
  el.innerHTML = nodes.map((n, i) => {
    const node = '<div class="spine-node' + (i === nodes.length - 1 ? ' on' : '') + '">'
      + '<span class="k">' + escapeHtml(n[0]) + '</span>'
      + '<span class="q">' + escapeHtml(n[1]) + '</span></div>';
    return i ? '<span class="spine-arrow" aria-hidden="true">→</span>' + node : node;
  }).join('');
}
function programHashForCat(id) {
  const map = {
    cognitive_authority: '#/program/cognitive_authority',
    code_poison_laundry: '#/program/code_poison_laundry',
    construction_antipattern: '#/program/construction_antipattern',
    product_voice: '#/program/product_voice',
    purity_scoreboard: '#/program/purity_scoreboard',
    memory_management: '#/program/memory_management',
    surface_law_coverage: '#/program/surface_law_coverage',
  };
  return map[id] || '#/home';
}
function renderHomeCategories(cats) {
  const el = document.getElementById('homeCategories');
  if (!el) return;
  const list = Array.isArray(cats) ? cats : [];
  if (!list.length) {
    el.innerHTML = '<p class="muted">No category map in snapshot — rebuild from monorepo '
      + '(<span class="mono">quality_category_map.yaml</span>).</p>';
    return;
  }
  el.innerHTML = list.map(c => {
    const kind = String(c.kind || '');
    const isRuntime = kind === 'runtime_proof_program';
    const fmLabel = c.fm_unit_label || c.unit || '';
    const badge = isRuntime
      ? '<span class="badge partial">runtime proof</span>'
      : '<span class="badge pass">FM class</span>';
    return '<div class="cat-card clickable" data-prog="' + escapeHtml(c.id || '') + '" role="link" tabindex="0">'
      + '<div class="cat-id">' + escapeHtml(c.short || c.id || '') + ' ' + badge + '</div>'
      + '<div class="cat-name">' + escapeHtml(c.name || c.id || '') + '</div>'
      + '<p class="cat-q">' + escapeHtml(c.question || '') + '</p>'
      + '<p class="cat-meta" style="margin:.25rem 0 .15rem"><strong>FM unit:</strong> '
      + escapeHtml(fmLabel || (isRuntime ? '— (not a taxonomy)' : '—')) + '</p>'
      + (c.overview
        ? '<p class="cat-meta" style="line-height:1.35">' + escapeHtml(String(c.overview).slice(0, 220))
          + (String(c.overview).length > 220 ? '…' : '') + '</p>'
        : '')
      + '<div class="cat-meta" style="margin-top:.35rem">open program →</div>'
      + '</div>';
  }).join('');
  el.querySelectorAll('.cat-card.clickable').forEach(card => {
    const go = () => { location.hash = programHashForCat(card.getAttribute('data-prog')); };
    card.onclick = go;
    card.onkeydown = (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } };
  });
}
function renderInventoryTables(invProg, catId) {
  if (!invProg) return '';
  let html = '';
  const native = invProg.native_rows || [];
  const related = invProg.related_failure_modes || [];
  html += '<p class="muted" style="font-size:.82rem;margin:0 0 .5rem">'
    + 'Unit: <span class="mono">' + escapeHtml(invProg.unit || '—') + '</span>'
    + ' · native rows: <strong>' + escapeHtml(String(invProg.native_count || 0)) + '</strong>'
    + ' · related FMs: <strong>' + escapeHtml(String(invProg.related_fm_count || 0)) + '</strong>'
    + (invProg.sot ? ' · SoT: <span class="mono">' + escapeHtml(invProg.sot) + '</span>' : '')
    + '</p>';
  if (invProg.notes) {
    html += '<p class="muted" style="font-size:.82rem">' + escapeHtml(invProg.notes) + '</p>';
  }
  // Native inventory (A#, laundry class, purity board, …)
  if (native.length) {
    const isA = catId === 'construction_antipattern';
    const col3 = isA ? 'root' : (catId === 'code_poison_laundry' ? 'ratchets' : 'status');
    html += '<p style="margin:.75rem 0 .35rem"><strong>Program inventory</strong> '
      + '<span class="muted">(not a second FM registry)</span>'
      + (catId === 'code_poison_laundry'
        ? ' · click a row → multi-lens gaps below'
        : '')
      + '</p>';
    html += '<div style="overflow:auto;max-height:18rem"><table class="mode-table"><thead><tr>'
      + '<th>id</th><th>title</th><th>' + escapeHtml(col3) + '</th><th>related FMs</th>'
      + '</tr></thead><tbody>';
    native.forEach(r => {
      const rel = (r.related_fms || []).slice(0, 6).map(id =>
        '<a class="deep-link" href="#/laws/' + encodeURIComponent(id) + '">' + escapeHtml(id) + '</a>'
      ).join(' ');
      let mid = '';
      if (isA) mid = escapeHtml(r.root || '');
      else if (catId === 'code_poison_laundry') mid = escapeHtml((r.ratchets || []).slice(0, 2).join(', ') || '—');
      else mid = escapeHtml(r.status || r.notes || '—').slice(0, 80);
      const rowId = r.id || '';
      const jump = catId === 'code_poison_laundry' && rowId
        ? ' data-gap-jump="' + escapeHtml(rowId) + '" style="cursor:pointer"'
        : '';
      html += '<tr' + jump + '><td class="mono">' + escapeHtml(rowId) + '</td>'
        + '<td>' + escapeHtml(r.title || '') + '</td>'
        + '<td class="mono" style="font-size:.72rem">' + mid + '</td>'
        + '<td style="font-size:.75rem">' + (rel || '—') + '</td></tr>';
    });
    html += '</tbody></table></div>';
  }
  // Related failure modes from collective registry
  if (related.length) {
    html += '<p style="margin:1rem 0 .35rem"><strong>Related failure modes</strong> '
      + '<span class="muted">(failure modes — click for detail)</span></p>';
    html += '<div style="overflow:auto;max-height:16rem"><table class="mode-table"><thead><tr>'
      + '<th>registry_id</th><th>title</th><th>plane</th><th>lifecycle</th><th></th>'
      + '</tr></thead><tbody>';
    related.forEach(r => {
      const orphan = r.in_registry === false;
      html += '<tr>'
        + '<td class="mono"><a href="#/laws/' + encodeURIComponent(r.id || '') + '">'
        + escapeHtml(r.id || '') + '</a></td>'
        + '<td>' + escapeHtml(r.title || '') + (orphan ? ' <span class="badge fail">orphan</span>' : '') + '</td>'
        + '<td class="mono">' + escapeHtml(r.plane || '—') + '</td>'
        + '<td>' + escapeHtml(r.lifecycle || '—') + '</td>'
        + '<td><a class="deep-link" href="#/laws/' + encodeURIComponent(r.id || '') + '">Mode</a></td>'
        + '</tr>';
    });
    html += '</tbody></table></div>';
  } else if (catId !== 'surface_law_coverage') {
    html += '<p class="muted">No related FM mapping yet for this program.</p>';
  }
  html += '<p class="muted" style="margin:.65rem 0 0;font-size:.8rem">'
    + '<a class="deep-link" href="#/laws">All failure modes</a> · '
    + 'collective SoT is only the registry — programs map onto it.</p>';
  return html;
}
function healthBadge(h) {
  const key = String(h || 'unknown');
  // ok is join-only — not full Seek pass (was mis-painted as green pass).
  const map = {
    ok: 'reg', thin: 'partial', pass: 'pass', sealed: 'pass',
    partial: 'partial', mixed: 'partial', n_a: 'reg',
    gap: 'open', fail: 'fail', error: 'fail', open: 'open',
    unknown: 'reg',
  };
  const cls = map[key] || 'reg';
  return '<span class="badge ' + cls + '">' + escapeHtml(key) + '</span>';
}
function renderVoiceProofBoard(board) {
  if (!board || board.error) {
    return '<div class="gap-board" id="voiceProofBoard"><p class="muted">'
      + escapeHtml((board && board.error) || 'Voice proof board unavailable')
      + '</p></div>';
  }
  const rows = board.rows || [];
  const sum = board.summary || {};
  let html = '<div class="gap-board" id="voiceProofBoard">';
  html += '<div class="gb-head"><h3>Voice · product shaping + proof flip</h3>';
  html += '<p class="muted" style="margin:0;font-size:.82rem;line-height:1.45">'
    + escapeHtml(board.doctrine || '')
    + '</p>';
  html += '<p class="muted" style="margin:.4rem 0 0;font-size:.78rem">'
    + 'Registry honesty: <span class="mono">' + escapeHtml(String(sum.registry_fm_count ?? '—'))
    + '</span> FMs · static gaps '
    + escapeHtml(String(sum.registry_static_gap ?? '—'))
    + ' · dynamic (soak) gaps '
    + escapeHtml(String(sum.registry_dynamic_gap ?? '—'))
    + ' · needs_soak '
    + escapeHtml(String(sum.registry_needs_soak ?? '—'))
    + ' · daily_seek modes cached '
    + escapeHtml(String(sum.seek_modes_cached ?? '—'))
    + '</p></div>';
  if (!rows.length) {
    html += '<p class="muted">No voice inventory rows.</p></div>';
    return html;
  }
  rows.forEach(row => {
    const open = (row.id === 'sparse_ceremony' || row.id === 'passive_non_advance'
      || (row.kind === 'product_shaping_lens' && String(row.id || '').includes('front_door')))
      ? ' open' : '';
    const feat = (row.id === 'sparse_ceremony' || row.id === 'passive_non_advance')
      ? ' featured' : '';
    html += '<details class="gap-class' + feat + '" id="voice-'
      + escapeHtml(row.id || '') + '"' + open + '>';
    html += '<summary>';
    html += '<span class="gc-id">' + escapeHtml(row.id || '') + '</span>';
    html += '<span class="gc-title">' + escapeHtml(row.title || '') + '</span>';
    html += healthBadge(row.overall_health);
    if (row.kind === 'product_shaping_lens') {
      html += '<span class="badge reg">shaping lens</span>';
    }
    html += '</summary><div class="gc-body">';
    if (row.notes) {
      html += '<p class="muted" style="margin:0 0 .55rem;font-size:.8rem">'
        + escapeHtml(row.notes) + '</p>';
    }
    const lenses = row.lenses || {};
    html += '<div class="lens-grid">';
    ['static', 'dynamic', 'llm_vector'].forEach(k => {
      const lens = lenses[k];
      if (!lens) return;
      html += '<div class="lens-card"><h4>' + escapeHtml(lens.label || k) + ' '
        + healthBadge(lens.health) + '</h4>';
      html += '<p class="lens-sum">' + escapeHtml(lens.summary || '') + '</p></div>';
    });
    html += '</div>';
    // Flip related FMs with proof
    const fps = row.fm_proofs || [];
    if (fps.length) {
      html += '<p style="margin:.65rem 0 .3rem;font-weight:600;font-size:.82rem">Related FMs (flip)</p>';
      html += '<div style="overflow:auto;max-height:12rem"><table class="mode-table"><thead><tr>'
        + '<th>registry_id</th><th>static</th><th>dynamic</th><th>LLM seek</th><th>lifecycle</th>'
        + '</tr></thead><tbody>';
      fps.forEach(fp => {
        const st = (fp.static || {});
        const dy = (fp.dynamic || {});
        const lv = (fp.llm_vector || {});
        html += '<tr>'
          + '<td class="mono"><a href="#/laws/' + encodeURIComponent(fp.registry_id || '') + '">'
          + escapeHtml(fp.registry_id || '') + '</a></td>'
          + '<td>' + healthBadge(st.health)
          + ' <span class="muted mono" style="font-size:.7rem">'
          + escapeHtml(String(st.count_ok ?? 0) + '/' + String(st.count_total ?? 0))
          + '</span></td>'
          + '<td>' + healthBadge(dy.health)
          + (dy.in_matrix ? ' <span class="badge pass">matrix</span>' : '')
          + (dy.portable_seed ? ' <span class="badge reg">seed</span>' : '')
          + '</td>'
          + '<td>' + healthBadge(lv.in_last_seek ? 'ok' : 'gap')
          + (lv.suspect_count ? ' <span class="muted">' + escapeHtml(String(lv.suspect_count)) + ' suspects</span>' : '')
          + '</td>'
          + '<td class="mono">' + escapeHtml(fp.lifecycle || '—') + '</td></tr>';
      });
      html += '</tbody></table></div>';
    }
    html += '</div></details>';
  });
  // Compact all-FM proof honesty table
  const allp = board.all_failure_mode_proof || [];
  if (allp.length) {
    html += '<p style="margin:1rem 0 .35rem"><strong>All CAQ modes — static vs dynamic proof</strong> '
      + '<span class="muted">(honest: not every FM has a multi-turn soak)</span></p>';
    html += '<div style="overflow:auto;max-height:16rem"><table class="mode-table"><thead><tr>'
      + '<th>registry_id</th><th>static</th><th>dynamic</th><th>soak?</th><th>plane</th>'
      + '</tr></thead><tbody>';
    allp.forEach(fp => {
      html += '<tr><td class="mono"><a href="#/laws/' + encodeURIComponent(fp.registry_id || '') + '">'
        + escapeHtml(fp.registry_id || '') + '</a></td>'
        + '<td>' + healthBadge((fp.static || {}).health) + '</td>'
        + '<td>' + healthBadge((fp.dynamic || {}).health) + '</td>'
        + '<td class="mono">' + (fp.needs_generative_soak ? 'yes' : 'no') + '</td>'
        + '<td class="mono">' + escapeHtml(fp.plane || '—') + '</td></tr>';
    });
    html += '</tbody></table></div>';
  }
  html += '<p class="muted" style="margin:.5rem 0 0;font-size:.78rem">'
    + 'LLM vector: <span class="mono">python -m conjecture_host.expansion daily_seek --llm --limit 8</span> '
    + '· Multi-turn: matrix.yaml + Conjecture freezes · Static: registry coverage.ratchets</p>';
  html += '</div>';
  return html;
}
function renderLensCard(lens) {
  if (!lens) return '';
  const counts = lens.counts || {};
  let body = '<div class="lens-card">';
  body += '<h4>' + escapeHtml(lens.label || lens.id || 'lens') + ' '
    + healthBadge(lens.health) + '</h4>';
  body += '<p class="lens-sum">' + escapeHtml(lens.summary || '') + '</p>';

  if (lens.id === 'static') {
    const rats = (lens.ratchets || []).slice(0, 8);
    const findings = (lens.findings || []).slice(0, 10);
    const probes = (lens.probes || []).slice(0, 8);
    if (rats.length) {
      body += '<p style="margin:0 0 .2rem;font-weight:600">Ratchets</p><ul class="compact">';
      rats.forEach(r => {
        body += '<li><span class="mono">' + escapeHtml(r.path || '') + '</span> '
          + (r.exists ? healthBadge('ok') : healthBadge('gap'))
          + ' <span class="muted">' + escapeHtml(r.kind || '') + '</span></li>';
      });
      body += '</ul>';
    }
    if (probes.length) {
      body += '<p style="margin:.4rem 0 .2rem;font-weight:600">Contract probes</p><ul class="compact">';
      probes.forEach(p => {
        body += '<li><span class="mono">' + escapeHtml(p.id || '') + '</span> '
          + healthBadge(p.health || (p.ok ? 'ok' : 'gap'))
          + ' — ' + escapeHtml((p.detail || '').slice(0, 120)) + '</li>';
      });
      body += '</ul>';
    }
    if (findings.length) {
      body += '<p style="margin:.4rem 0 .2rem;font-weight:600">Findings / signals</p><ul class="compact">';
      findings.forEach(f => {
        const loc = (f.path || '') + (f.line ? (':' + f.line) : '');
        body += '<li><span class="mono">' + escapeHtml(loc) + '</span> '
          + healthBadge(f.severity === 'high' ? 'gap' : 'partial')
          + ' <span class="muted">' + escapeHtml(f.pattern || '') + '</span>'
          + (f.snippet ? '<br><span class="muted">' + escapeHtml(f.snippet) + '</span>' : '')
          + '</li>';
      });
      body += '</ul>';
    } else if (!rats.length && !probes.length) {
      body += '<p class="empty-note">No static probes for this class yet.</p>';
    }
  } else if (lens.id === 'llm_vector') {
    const suspects = (lens.suspects || []).slice(0, 12);
    if (lens.how_to_refresh) {
      body += '<p class="muted" style="margin:0 0 .35rem;font-size:.72rem">'
        + 'Refresh: <span class="mono">' + escapeHtml(lens.how_to_refresh) + '</span></p>';
    }
    if (suspects.length) {
      body += '<ul class="compact">';
      suspects.forEach(s => {
        body += '<li><span class="mono">' + escapeHtml(s.path || '') + '</span> '
          + healthBadge(s.risk === 'high' ? 'gap' : (s.risk || 'partial'))
          + (s.already_ratcheted ? ' <span class="badge pass">ratcheted</span>' : '')
          + '<br><span class="muted">' + escapeHtml((s.why || '').slice(0, 140))
          + ' · ' + escapeHtml(s.source || '') + ' · ' + escapeHtml(s.registry_id || '')
          + '</span></li>';
      });
      body += '</ul>';
    } else {
      body += '<p class="empty-note">'
        + (counts.modes_covered
          ? 'No suspects for related FMs in last daily_seek.'
          : 'Related FMs not in last daily_seek scope — run daily_seek with those modes.')
        + '</p>';
    }
  } else if (lens.id === 'behaviour') {
    const fms = (lens.related_fms || []).slice(0, 10);
    const cells = (lens.surface_empty_cells || []).slice(0, 8);
    const sketches = (lens.path_sketches || []).slice(0, 3);
    if (fms.length) {
      body += '<p style="margin:0 0 .2rem;font-weight:600">Related FMs</p><ul class="compact">';
      fms.forEach(f => {
        body += '<li><a class="deep-link" href="#/laws/'
          + encodeURIComponent(f.registry_id || '') + '">'
          + escapeHtml(f.registry_id || '') + '</a> '
          + healthBadge(f.seek_health || f.lifecycle || 'unknown')
          + ' <span class="muted">' + escapeHtml(f.lifecycle || '') + '</span></li>';
      });
      body += '</ul>';
    }
    if (cells.length) {
      body += '<p style="margin:.4rem 0 .2rem;font-weight:600">Surface empty/partial (sample)</p><ul class="compact">';
      cells.forEach(c => {
        body += '<li><span class="mono">' + escapeHtml(c.surface || '') + '</span> × '
          + escapeHtml(c.registry_id || '') + ' '
          + healthBadge(c.status || 'empty') + '</li>';
      });
      body += '</ul>';
    }
    if (sketches.length) {
      body += '<p style="margin:.4rem 0 .2rem;font-weight:600">Path sketches</p><ul class="compact">';
      sketches.forEach(s => {
        body += '<li><span class="mono">' + escapeHtml(s.registry_id || '') + '</span><br>'
          + '<span class="muted">' + escapeHtml((s.path_sketch || '').slice(0, 220))
          + '</span></li>';
      });
      body += '</ul>';
    }
    if (!fms.length && !cells.length) {
      body += '<p class="empty-note">No behaviour join data yet.</p>';
    }
  }
  body += '</div>';
  return body;
}
function renderLaundryGapBoard(board) {
  if (!board || board.error) {
    return '<div class="gap-board"><p class="muted">'
      + escapeHtml((board && board.error) || 'Laundry gap board unavailable')
      + '</p></div>';
  }
  const classes = board.classes || [];
  let html = '<div class="gap-board" id="laundryGapBoard">';
  html += '<div class="gb-head"><h3>Multi-lens gap board</h3>';
  html += '<p class="muted" style="margin:0;font-size:.82rem;line-height:1.45">'
    + escapeHtml(board.doctrine || '')
    + ' · Featured: <span class="mono">if_else_policy_on_freetext</span> '
    + '(if-then-else poison)</p></div>';
  if (!classes.length) {
    html += '<p class="muted">No laundry classes in inventory.</p></div>';
    return html;
  }
  classes.forEach(cls => {
    const open = cls.featured || cls.id === 'if_else_policy_on_freetext' ? ' open' : '';
    const feat = cls.featured ? ' featured' : '';
    html += '<details class="gap-class' + feat + '" id="gap-'
      + escapeHtml(cls.id || '') + '"' + open + '>';
    html += '<summary>';
    html += '<span class="gc-id">' + escapeHtml(cls.id || '') + '</span>';
    html += '<span class="gc-title">' + escapeHtml(cls.title || '') + '</span>';
    html += healthBadge(cls.overall_health);
    html += '<span class="badge reg">score ' + escapeHtml(String(cls.gap_score ?? 0)) + '</span>';
    if (cls.a_numbers && cls.a_numbers.length) {
      html += '<span class="muted" style="font-size:.72rem">'
        + escapeHtml(cls.a_numbers.join(' · ')) + '</span>';
    }
    html += '</summary>';
    html += '<div class="gc-body">';
    if (cls.notes) {
      html += '<p class="muted" style="margin:0 0 .55rem;font-size:.8rem">'
        + escapeHtml(cls.notes) + '</p>';
    }
    const lenses = cls.lenses || {};
    html += '<div class="lens-grid">';
    html += renderLensCard(lenses.static);
    html += renderLensCard(lenses.llm_vector);
    html += renderLensCard(lenses.behaviour);
    html += '</div></div></details>';
  });
  html += '</div>';
  return html;
}
function bindLaundryGapJumps(root) {
  if (!root) return;
  root.querySelectorAll('[data-gap-jump]').forEach(tr => {
    tr.addEventListener('click', (ev) => {
      if (ev.target && ev.target.closest && ev.target.closest('a')) return;
      const id = tr.getAttribute('data-gap-jump');
      if (!id) return;
      const el = document.getElementById('gap-' + id);
      if (el) {
        el.open = true;
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}
async function loadProgram(catId) {
  window._programId = catId;
  const title = document.getElementById('progTitle');
  const lead = document.getElementById('progLead');
  const body = document.getElementById('progBody');
  const patch = document.getElementById('progPatch');
  try {
    let snap = window._qcSnapshot;
    if (!snap) {
      const data = await loadQualitySnapshot({});
      snap = (data && data.snapshot) || {};
    }
    const cats = snap.quality_categories || [];
    const c = cats.find(x => x && x.id === catId) || { id: catId, name: catId };
    const note = (snap.agent_patching_note || {}).short || '';
    const isRuntime = String(c.kind || '') === 'runtime_proof_program';
    if (title) {
      title.textContent = (c.short || 'program') + ' · ' + (c.name || catId)
        + (isRuntime ? ' (runtime proof)' : ' (FM classification)');
    }
    if (lead) {
      lead.innerHTML = '<strong>' + escapeHtml(c.question || 'Quality program') + '</strong>';
    }
    if (patch && note) {
      patch.style.display = 'block';
      patch.innerHTML = '<strong>Patch handoff</strong> — <span class="mono">'
        + escapeHtml(note) + '</span>';
    }
    const invRoot = snap.program_inventories || {};
    const invProg = (invRoot.programs || {})[catId] || null;
    let html = '';
    // Program overview narrative (from quality_category_map)
    html += '<div class="card" style="margin:0 0 .85rem;padding:.75rem .85rem;background:#fafafa">';
    html += '<p style="margin:0 0 .4rem;font-size:.8rem">'
      + (isRuntime
        ? '<span class="badge partial">runtime proof program</span> — not an FM taxonomy'
        : '<span class="badge pass">failure-mode classification</span> for this program\'s objective')
      + '</p>';
    if (c.fm_unit_label) {
      html += '<p style="margin:0 0 .45rem;font-size:.85rem"><strong>Definitive FM unit:</strong> '
        + escapeHtml(c.fm_unit_label) + '</p>';
    }
    if (c.overview) {
      html += '<p style="margin:0;font-size:.88rem;line-height:1.5;color:#3f3f46">'
        + escapeHtml(c.overview) + '</p>';
    }
    if (isRuntime && Array.isArray(c.runtime_layers) && c.runtime_layers.length) {
      html += '<p style="margin:.5rem 0 0;font-size:.8rem" class="muted">Runtime layers: '
        + '<span class="mono">' + escapeHtml(c.runtime_layers.join(' · ')) + '</span></p>';
    }
    html += '</div>';
    html += '<div class="prog-tools">';
    html += '<a class="deep-link" href="#/laws">All failure modes</a>';
    if (catId === 'cognitive_authority') {
      html += '<a class="deep-link" href="#/seek">Observe</a>';
    }
    if (catId === 'surface_law_coverage') {
      html += '<a class="deep-link" href="#/seek">Run Coverage battery</a>';
      html += '<a class="deep-link" href="/surface-map" target="_blank" rel="noopener">Surface area map ↗</a>';
      html += '<span class="badge reg">static · multi-turn · join/live</span>';
    }
    if (catId === 'code_poison_laundry') {
      html += '<span class="badge open">no laundry / regex as sole NL</span>';
      html += '<a class="deep-link" href="#gap-if_else_policy_on_freetext">If-else poison gaps ↓</a>';
    }
    if (catId === 'product_voice') {
      html += '<span class="badge partial">product shaping · voice FMs</span>';
      html += '<a class="deep-link" href="#voiceProofBoard">Proof board ↓</a>';
    }
    html += '</div>';
    if (catId === 'surface_law_coverage') {
      html += '<div id="progSurfaceEmbed"></div>';
    }
    html += renderInventoryTables(invProg, catId);
    if (catId === 'product_voice') {
      const vboard = snap.voice_proof_board
        || (invProg && invProg.proof_board)
        || null;
      html += renderVoiceProofBoard(vboard);
    }
    if (catId === 'code_poison_laundry') {
      const board = snap.laundry_gap_board
        || (invProg && invProg.gap_board)
        || null;
      html += renderLaundryGapBoard(board);
      html += '<div class="do-dont" style="margin-top:.75rem"><div class="col do"><h4>Seal shape</h4><ul>'
        + '<li>Classifier enums + allow-tables</li>'
        + '<li>Finite chip send_text</li>'
        + '<li>Named ratchet that fails without the seal</li>'
        + '</ul></div><div class="col dont"><h4>Forbidden</h4><ul>'
        + '<li>Growing phrase / synonym lists for meaning</li>'
        + '<li>Regex as sole NL arbiter</li>'
        + '<li>If-then-else policy ladders on free text</li>'
        + '<li>Fail-soft multi-option prose menus</li>'
        + '</ul></div></div>';
    }
    if (body) body.innerHTML = html;
    if (catId === 'code_poison_laundry') {
      bindLaundryGapJumps(body);
    }
    if (catId === 'surface_law_coverage') {
      const emb = document.getElementById('progSurfaceEmbed');
      if (emb) {
        const host = document.createElement('div');
        host.id = 'homeCoverage';
        emb.appendChild(host);
        renderHomeCoverage(snap);
        host.id = 'progSurfaceEmbedInner';
      }
    }
  } catch (e) {
    if (body) body.innerHTML = '<p class="muted">' + escapeHtml(String(e)) + '</p>';
  }
}
function renderHomeJobs(stck) {
  const el = document.getElementById('homeJobs');
  const sent = document.getElementById('homeStackSentence');
  if (sent) sent.textContent = (stck && stck.sentence) || '';
  if (!el) return;
  const jobs = (stck && stck.jobs) || [];
  if (!jobs.length) {
    el.innerHTML = '<p class="muted">No stack jobs in snapshot.</p>';
    return;
  }
  el.innerHTML = jobs.map(j =>
    '<div class="job-card">'
    + '<div class="jid">' + escapeHtml(j.id || '') + '</div>'
    + '<div class="jown">' + escapeHtml(j.owner || '') + '</div>'
    + '<div class="jq">' + escapeHtml(j.question || '') + '</div>'
    + '</div>'
  ).join('');
}
function renderHomeCoverage(snap) {
  const el = document.getElementById('homeCoverage');
  if (!el) return;
  const s = snap.summary || {};
  const sc = ((snap.surface_coverage || {}).summary) || {};
  const cells = sc.cells != null ? sc.cells : s.surface_coverage_cells;
  const empty = sc.empty != null ? sc.empty : s.surface_coverage_empty;
  const sealed = sc.sealed != null ? sc.sealed : s.surface_coverage_sealed;
  const partial = sc.partial != null ? sc.partial : s.surface_coverage_partial;
  const pct = sc.coverage_pct_any_proof != null
    ? sc.coverage_pct_any_proof
    : s.surface_coverage_pct_any;
  const pkgRed = s.package_path_red_count != null
    ? s.package_path_red_count
    : (sc.package_path_red || 0);
  if (cells == null && empty == null) {
    el.innerHTML = '<p class="muted">Surface coverage not in this snapshot.</p>';
    return;
  }
  const pctN = Number(pct || 0);
  const barCls = pctN < 10 ? 'bad' : (pctN < 40 ? 'warn' : '');
  const width = Math.max(0, Math.min(100, pctN));
  el.innerHTML =
    '<div class="stat-cards">'
    + '<div class="stat-card"><div class="n">' + escapeHtml(String(cells ?? '—')) + '</div><div class="l">surface×FM cells</div></div>'
    + '<div class="stat-card"><div class="n">' + escapeHtml(String(sealed ?? '—')) + '</div><div class="l">sealed cells</div></div>'
    + '<div class="stat-card"><div class="n">' + escapeHtml(String(partial ?? '—')) + '</div><div class="l">partial</div></div>'
    + '<div class="stat-card"><div class="n">' + escapeHtml(String(empty ?? '—')) + '</div><div class="l">empty (red debt)</div></div>'
    + '<div class="stat-card"><div class="n">' + escapeHtml(String(pctN)) + '%</div><div class="l">any-proof coverage</div></div>'
    + '<div class="stat-card"><div class="n">' + escapeHtml(String(pkgRed)) + '</div><div class="l">package-path red</div></div>'
    + '</div>'
    + '<div class="cov-bar ' + barCls + '" title="coverage_pct_any_proof"><i style="width:' + width + '%"></i></div>'
    + '<p class="muted" style="font-size:.78rem;margin:.5rem 0 0">'
    + 'Empty cells stay red until a path-faithful ratchet or Conjecture freeze joins the surface. '
    + '<a class="deep-link" href="/surface-map" target="_blank" rel="noopener">Heat map visualization ↗</a>'
    + ' · <a class="deep-link" href="#/program/surface_law_coverage">Program board</a>'
    + '</p>';
}
async function loadHome() {
  const st = document.getElementById('status');
  const stats = document.getElementById('homeStats');
  const meta = document.getElementById('homeMeta');
  const ow = document.getElementById('homeOpenWork');
  renderHomeSpine();
  try {
    const data = await loadQualitySnapshot({ rebuild: false });
    if (!data.ok && !data.available) {
      stats.innerHTML = '<p class="muted">' + escapeHtml(data.error || 'unavailable') + '</p>';
      const cats = document.getElementById('homeCategories');
      if (cats) cats.innerHTML = '<p class="muted">' + escapeHtml(data.hint || 'Host monorepo required.') + '</p>';
      return;
    }
    const snap = data.snapshot || {};
    const s = snap.summary || {};
    const note = snap.agent_patching_note || {};
    const patchEl = document.getElementById('homePatchShort');
    if (patchEl) {
      patchEl.textContent = note.short || note.full || 'AGENTS.md: do not invent · hotfix · break-fix · regress · follow laws · no laundry';
    }
    // lifecycle sealed ≠ surface proven — never collapse those grades
    const cards = [
      ['modes', s.modes_total, 'CAQ modes'],
      ['life', s.modes_lifecycle_sealed != null ? s.modes_lifecycle_sealed : s.modes_sealed, 'lifecycle sealed (unit/doctrine)'],
      ['surf', s.modes_surface_proven != null ? s.modes_surface_proven : '—', 'surface-proven FMs'],
      ['over', s.modes_lifecycle_overclaim != null ? s.modes_lifecycle_overclaim : '—', 'lifecycle overclaim (0 surface-sealed)'],
      ['unit', s.modes_unit_only != null ? s.modes_unit_only : '—', 'unit-only inventory'],
      ['gaps', s.modes_gap, 'open inventory / thin'],
      ['seek', s.law_seek_passed === true ? 'PASS' : (s.law_seek_passed === false ? 'FAIL' : '—'), 'seek battery'],
      ['critical', s.open_critical_count || 0, 'open critical'],
      ['empty', s.surface_coverage_empty != null ? s.surface_coverage_empty : '—', 'empty surface cells'],
      ['candidates', s.candidates_count || 0, 'author scenarios'],
    ];
    stats.innerHTML = cards.map(c =>
      '<div class="stat-card"><div class="n">' + escapeHtml(String(c[1])) + '</div>'
      + '<div class="l">' + escapeHtml(c[2]) + '</div></div>'
    ).join('');
    meta.textContent = (snap.generated_at || '') + ' · ' + ((snap.sources || {}).epic || '');
    renderHomeCategories(snap.quality_categories);
    renderHomeJobs(snap.stack || {});
    renderHomeCoverage(snap);
    const open = ((snap.seek || {}).open_work) || [];
    if (!open.length) {
      ow.innerHTML = '<p class="bl-empty">No open work in last Coverage report.</p>';
    } else {
      ow.innerHTML = '<ul style="margin:0;padding-left:1.1rem">' + open.slice(0, 20).map(w => {
        const rid = w.registry_id || w.check_id || '';
        const link = rid
          ? ' <a class="deep-link" href="#/laws/' + encodeURIComponent(rid) + '">' + escapeHtml(rid) + '</a>'
          : '';
        return '<li><span class="mono">' + escapeHtml(w.kind || '') + '</span>'
          + link + ' ' + escapeHtml(JSON.stringify(w).slice(0, 120)) + '</li>';
      }).join('') + '</ul>';
    }
    st.textContent = (s.law_seek_passed === true ? 'coverage PASS' : (s.law_seek_passed === false ? 'coverage FAIL' : 'snapshot ok'));
  } catch (e) {
    st.textContent = String(e);
    stats.innerHTML = '<p class="muted">' + escapeHtml(String(e)) + '</p>';
  }
}
async function loadLaws(focusId) {
  const st = document.getElementById('status');
  try {
    let snap = window._qcSnapshot;
    if (!snap) {
      const data = await loadQualitySnapshot({});
      snap = (data && data.snapshot) || null;
    }
    if (!snap) {
      document.getElementById('lawsBody').innerHTML =
        '<tr><td colspan="8" class="muted">Snapshot unavailable — run from monorepo.</td></tr>';
      return;
    }
    window._lawsAll = snap.laws || [];
    renderLawsTable(focusId || window._lawFocusId);
    st.textContent = 'laws registry ' + window._lawsAll.length
      + ' · lifecycle-sealed ' + ((snap.summary || {}).modes_lifecycle_sealed
        != null ? (snap.summary || {}).modes_lifecycle_sealed : (snap.summary || {}).modes_sealed || 0)
      + ' · surface-proven ' + ((snap.summary || {}).modes_surface_proven != null
        ? (snap.summary || {}).modes_surface_proven : '—')
      + ' · overclaim ' + ((snap.summary || {}).modes_lifecycle_overclaim != null
        ? (snap.summary || {}).modes_lifecycle_overclaim : '—');
  } catch (e) {
    st.textContent = String(e);
  }
}
function _lawCategories(r) {
  if (Array.isArray(r.categories) && r.categories.length) {
    return r.categories.map(String);
  }
  if (r.category) return [String(r.category)];
  return ['authority'];
}
function renderLawsCategoryPills() {
  const el = document.getElementById('lawsCategoryPills');
  if (!el) return;
  const all = window._lawsAll || [];
  const order = ['authority', 'laundry', 'antipattern', 'voice', 'purity', 'memory'];
  const counts = {};
  order.forEach(c => { counts[c] = 0; });
  all.forEach(r => {
    _lawCategories(r).forEach(c => {
      counts[c] = (counts[c] || 0) + 1;
    });
  });
  const catSel = document.getElementById('lawsCategory');
  const cur = catSel ? catSel.value : '';
  let html = '<span class="muted" style="font-size:.75rem;margin-right:.25rem">Category:</span>'
    + '<button type="button" class="secondary laws-cat-pill' + (!cur ? ' active-pill' : '')
    + '" data-cat="" style="font-size:.78rem" title="All failure modes">all ('
    + all.length + ')</button>';
  order.forEach(c => {
    const n = counts[c] || 0;
    if (!n && c !== 'authority') return;
    const on = cur === c ? ' active-pill' : '';
    html += '<button type="button" class="secondary laws-cat-pill' + on
      + '" data-cat="' + escapeHtml(c) + '" style="font-size:.78rem" title="Filter by category '
      + escapeHtml(c) + '">'
      + escapeHtml(c) + ' (' + n + ')</button>';
  });
  el.innerHTML = html;
  el.querySelectorAll('.laws-cat-pill').forEach(btn => {
    btn.onclick = () => {
      if (catSel) catSel.value = btn.getAttribute('data-cat') || '';
      renderLawsTable(window._lawFocusId);
    };
  });
}
function renderLawsPlanePills() {
  const el = document.getElementById('lawsPlanePills');
  if (!el) return;
  const all = window._lawsAll || [];
  const counts = {};
  all.forEach(r => {
    const p = String(r.plane || '—');
    counts[p] = (counts[p] || 0) + 1;
  });
  const planeSel = document.getElementById('lawsPlane');
  const cur = planeSel ? planeSel.value : '';
  const planes = Object.keys(counts).sort();
  let html = '<span class="muted" style="font-size:.75rem;margin-right:.25rem">Slice:</span>'
    + '<button type="button" class="secondary laws-plane-pill' + (!cur ? ' active-pill' : '')
    + '" data-plane="" style="font-size:.78rem" title="All slices">any slice</button>';
  planes.forEach(p => {
    const on = cur === p ? ' active-pill' : '';
    html += '<button type="button" class="secondary laws-plane-pill' + on
      + '" data-plane="' + escapeHtml(p) + '" style="font-size:.78rem" title="Control-plane slice: '
      + escapeHtml(p) + ' (not a quality category)">'
      + 'slice:' + escapeHtml(p) + ' (' + counts[p] + ')</button>';
  });
  el.innerHTML = html;
  el.querySelectorAll('.laws-plane-pill').forEach(btn => {
    btn.onclick = () => {
      if (planeSel) planeSel.value = btn.getAttribute('data-plane') || '';
      renderLawsTable(window._lawFocusId);
    };
  });
}
function renderLawsTable(focusId) {
  const q = (document.getElementById('lawsQ').value || '').toLowerCase();
  const life = document.getElementById('lawsLife').value;
  const cat = (document.getElementById('lawsCategory') || {}).value || '';
  const plane = (document.getElementById('lawsPlane') || {}).value || '';
  const health = document.getElementById('lawsHealth').value;
  const soakOnly = document.getElementById('lawsSoakOnly').checked;
  const surfaceRed = !!(document.getElementById('lawsSurfaceRed') || {}).checked;
  const all = window._lawsAll || [];
  const rows = all.filter(r => {
    const cats = _lawCategories(r);
    if (cat && cats.indexOf(cat) < 0) return false;
    if (plane && String(r.plane || '') !== plane) return false;
    if (life && String(r.lifecycle || '') !== life) return false;
    if (health && String(r.seek_health || '') !== health) return false;
    if (soakOnly && !r.needs_generative_soak) return false;
    if (surfaceRed && !r.surface_red && !(Number(r.surface_empty || 0) > 0)) return false;
    if (q) {
      const hay = (
        (r.registry_id || '') + ' ' + (r.failure_mode || '') + ' ' + (r.plane || '')
        + ' ' + (r.family || '') + ' ' + cats.join(' ')
        + ' ' + ((r.incidents || []).join(' '))
      ).toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
  // Prefer category then id when filtering; else slice then id
  rows.sort((a, b) => {
    if (cat) {
      return String(a.registry_id || '').localeCompare(String(b.registry_id || ''));
    }
    const pa = String(a.plane || ''), pb = String(b.plane || '');
    if (pa !== pb) return pa.localeCompare(pb);
    return String(a.registry_id || '').localeCompare(String(b.registry_id || ''));
  });
  const meta = document.getElementById('lawsMeta');
  if (meta) {
    meta.textContent = 'showing ' + rows.length + ' of ' + all.length
      + ' failure modes'
      + (cat ? ' · category=' + cat : '')
      + (plane ? ' · slice=' + plane : '');
  }
  renderLawsCategoryPills();
  renderLawsPlanePills();
  const body = document.getElementById('lawsBody');
  body.innerHTML = rows.map(r => {
    const rid = r.registry_id || '';
    const miss = (r.ratchets_missing || []).length;
    const sel = focusId && focusId === rid ? ' selected' : '';
    const emptyN = r.surface_empty != null ? String(r.surface_empty) : '—';
    const cats = _lawCategories(r);
    const catBadges = cats.map(c => {
      const cls = (c === 'laundry' || c === 'antipattern') ? 'open'
        : (c === 'memory' ? 'partial' : (c === 'voice' ? 'reg' : 'pass'));
      return '<span class="badge ' + cls + '" style="margin:0 2px 2px 0">' + escapeHtml(c) + '</span>';
    }).join('');
    const planeBadge = r.plane === 'memory'
      ? '<span class="badge partial">' + escapeHtml(r.plane) + '</span>'
      : '<span class="mono">' + escapeHtml(r.plane || '—') + '</span>';
    return '<tr class="' + sel + '" data-rid="' + escapeHtml(rid) + '">'
      + '<td class="mono"><a href="#/laws/' + encodeURIComponent(rid) + '">' + escapeHtml(rid) + '</a></td>'
      + '<td>' + (catBadges || '—') + '</td>'
      + '<td>' + planeBadge + '</td>'
      + '<td title="Doctrine/unit claim only — not surface board">' + escapeHtml(r.lifecycle || '') + '</td>'
      + '<td>' + inventoryBadge(r) + '</td>'
      + '<td>' + healthBadge(r.seek_health) + '</td>'
      + '<td>' + surfaceProofBadge(r) + '</td>'
      + '<td class="mono" title="Surfaces with no proof for this FM">' + escapeHtml(emptyN) + '</td>'
      + '<td>' + (r.needs_generative_soak ? 'yes' : 'no') + '</td>'
      + '<td class="mono">' + (r.matrix_modes || []).length + '</td>'
      + '<td class="mono">' + (r.seek_edges || []).length + '</td>'
      + '<td class="mono">' + (r.ratchet_count || 0)
      + (miss ? ' <span class="badge open">⚠' + miss + '</span>' : '') + '</td>'
      + '<td><a class="deep-link" href="#/seek?registry=' + encodeURIComponent(rid) + '">Observe</a></td>'
      + '</tr>';
  }).join('') || '<tr><td colspan="13" class="muted">No modes match filters — click <strong>Show all</strong> or clear category/slice.</td></tr>';
  body.querySelectorAll('tr[data-rid]').forEach(tr => {
    tr.onclick = (e) => {
      if (e.target.tagName === 'A') return;
      const rid = tr.getAttribute('data-rid');
      location.hash = '#/laws/' + encodeURIComponent(rid);
    };
  });
  if (focusId) showLawDetail(focusId);
}
function showLawDetail(rid) {
  window._lawFocusId = rid;
  const row = (window._lawsAll || []).find(r => r.registry_id === rid);
  const card = document.getElementById('lawDetailCard');
  if (!row) {
    card.style.display = 'none';
    return;
  }
  card.style.display = 'block';
  document.getElementById('lawDetailTitle').textContent = rid + ' — ' + (row.failure_mode || '');
  document.getElementById('lawDetailSeekLink').href = '#/seek?registry=' + encodeURIComponent(rid);
  let html = '<table class="kv">';
  const fields = [
    ['1. Failure mode', rid + ' — ' + (row.failure_mode || '')],
    ['2. Categories (browse)', (_lawCategories(row).join(', ') || 'authority')],
    ['3. Control-plane slice', row.plane || '—'],
    ['4. Incidents we track', (row.incidents || []).join(', ') || '—'],
    ['5. Mitigations in code (ratchets)', (row.ratchet_count != null ? row.ratchet_count : '—')
      + ((row.ratchets_missing || []).length
        ? ' · missing: ' + (row.ratchets_missing || []).join(', ')
        : '')],
    ['6. Named in book?', row.lifecycle || '—'],
    ['7. Honest status (after observation)', row.inventory_status || '—'],
    ['   overclaim?', row.lifecycle_overclaim
      ? 'YES — book says sealed but 0 surfaces proven'
      : 'no'],
    ['8. Observe battery', row.seek_health || '—'],
    ['   observe note', row.seek_health_note || '—'],
    ['9. Proven on product surfaces', row.surface_any_pct != null ? row.surface_any_pct + '%' : '—'],
    ['   still open (surfaces)', row.surface_empty != null ? row.surface_empty : '—'],
    ['   sealed / partial cells', (row.surface_sealed != null ? row.surface_sealed : '—')
      + ' / ' + (row.surface_partial != null ? row.surface_partial : '—')],
    ['Needs multi-turn soak?', row.needs_generative_soak ? 'yes' : 'no'],
    ['Matrix / edges', ((row.matrix_modes || []).join(', ') || '—')
      + ' · edges: ' + ((row.seek_edges || []).join(', ') || '—')],
  ];
  fields.forEach(f => {
    html += '<tr><th>' + escapeHtml(f[0]) + '</th><td class="mono">' + escapeHtml(String(f[1])) + '</td></tr>';
  });
  html += '</table>';
  const rel = row.related_checks || [];
  if (rel.length) {
    html += '<p style="margin:.65rem 0 .35rem"><strong>Observation checks</strong></p><ul>';
    rel.forEach(c => {
      html += '<li><span class="badge ' + (c.status === 'pass' ? 'pass' : (c.status === 'fail' || c.status === 'error' ? 'fail' : 'reg')) + '">'
        + escapeHtml(c.status) + '</span> <span class="layer-pill">' + escapeHtml(c.layer || '') + '</span> '
        + '<span class="mono">' + escapeHtml(c.check_id || '') + '</span> — ' + escapeHtml(c.title || '') + '</li>';
    });
    html += '</ul>';
  }
  html += '<p class="muted" style="margin:.5rem 0 0;font-size:.82rem">'
    + '<a class="deep-link" href="#/candidates?mode=' + encodeURIComponent(rid) + '">Author from this mode</a> · '
    + '<a class="deep-link" href="#/seek?registry=' + encodeURIComponent(rid) + '">Observe this mode</a></p>';
  const note = ((window._qcSnapshot || {}).agent_patching_note || {}).short
    || 'AGENTS.md: do not invent · hotfix · break-fix · regress · follow laws · no laundry';
  html += '<div class="patch-banner" style="margin-top:.75rem">'
    + '<strong>When mitigating</strong> — contract + ratchet + path-faithful proof; coding-agent note: '
    + '<span class="mono">' + escapeHtml(note) + '</span></div>';
  document.getElementById('lawDetailBody').innerHTML = html;
}
async function loadSeek(filterReg) {
  const st = document.getElementById('status');
  try {
    const r = await fetch('/api/law-seek');
    const data = await r.json();
    window._seekData = data;
    renderSeek(data, filterReg || window._seekFilterReg);
    if (data.passed === true) setSeekChrome('observation: PASS', true);
    else if (data.passed === false) setSeekChrome('observation: FAIL', false);
    st.textContent = data.ran ? 'seek ran' : (data.ok ? 'seek loaded' : (data.error || 'seek empty'));
  } catch (e) {
    st.textContent = String(e);
  }
}
function renderSeek(data, filterReg) {
  const report = (data && data.report) || {};
  const sum = report.summary || {};
  const stats = document.getElementById('seekStats');
  const passed = data && data.passed;
  const cards = [
    ['result', passed === true ? 'PASS' : (passed === false ? 'FAIL' : '—'), 'overall'],
    ['pass', sum.pass || 0, 'checks pass'],
    ['fail', sum.fail || 0, 'checks fail'],
    ['error', sum.error || 0, 'errors'],
    ['skip', sum.skip || 0, 'skipped'],
    ['ms', report.duration_ms || '—', 'duration ms'],
    ['modes', (report.mode_board || []).length, 'mode board'],
    ['open', (report.open_work || []).length, 'open work'],
  ];
  stats.innerHTML = cards.map(c =>
    '<div class="stat-card"><div class="n">' + escapeHtml(String(c[1])) + '</div>'
    + '<div class="l">' + escapeHtml(c[2]) + '</div></div>'
  ).join('');
  document.getElementById('seekMeta').textContent =
    (report.started_at || '') + ' → ' + (report.finished_at || '')
    + (data.artifact_dir ? ' · ' + data.artifact_dir : '');
  // Mode board
  const mb = report.mode_board || [];
  document.getElementById('seekModeBody').innerHTML = mb.map(r => {
    const rid = r.registry_id || '';
    const miss = (r.ratchets_missing || []).length;
    return '<tr><td class="mono"><a href="#/laws/' + encodeURIComponent(rid) + '">'
      + escapeHtml(rid) + '</a></td>'
      + '<td>' + escapeHtml(r.lifecycle || '') + '</td>'
      + '<td>' + (r.needs_generative_soak ? 'yes' : 'no') + '</td>'
      + '<td class="mono">' + (r.matrix_modes || []).length + '</td>'
      + '<td class="mono">' + (r.seek_edges || []).length + '</td>'
      + '<td class="mono">' + (r.ratchet_count || 0) + (miss ? ' ⚠' : '') + '</td></tr>';
  }).join('') || '<tr><td colspan="6" class="muted">No mode board — run Seek.</td></tr>';
  // Checks
  window._seekChecks = report.checks || [];
  window._seekFilterReg = filterReg || '';
  if (filterReg) {
    const sq = document.getElementById('seekQ');
    if (sq && !sq.value) sq.value = filterReg;
  }
  renderSeekChecks();
  // Open work
  const open = report.open_work || [];
  const ow = document.getElementById('seekOpenWork');
  if (!open.length) ow.innerHTML = '<p class="bl-empty">Empty queue.</p>';
  else {
    ow.innerHTML = '<ul style="margin:0;padding-left:1.1rem">' + open.slice(0, 40).map(w => {
      const rid = w.registry_id || '';
      return '<li><span class="mono">' + escapeHtml(w.kind || '') + '</span> '
        + (rid ? '<a class="deep-link" href="#/laws/' + encodeURIComponent(rid) + '">' + escapeHtml(rid) + '</a> ' : '')
        + escapeHtml(JSON.stringify(w).slice(0, 140)) + '</li>';
    }).join('') + '</ul>';
  }
  // Live
  const hits = (report.live_hits || []).filter(h =>
    h && h.probe_id !== 'audit_unavailable' && h.probe_id !== 'audit_error'
    && h.conversation_id && h.conversation_id !== '—');
  const liveCard = document.getElementById('seekLiveCard');
  if (hits.length) {
    liveCard.style.display = 'block';
    document.getElementById('seekLiveHits').innerHTML = '<ul style="margin:0;padding-left:1.1rem">'
      + hits.slice(0, 25).map(h =>
        '<li class="mono">' + escapeHtml(h.conversation_id || '') + ' · '
        + escapeHtml(h.probe_id || '') + ' · ' + escapeHtml(String(h.detail || '').slice(0, 100)) + '</li>'
      ).join('') + '</ul>';
  } else {
    liveCard.style.display = 'none';
  }
  document.getElementById('seekMarkdown').textContent = (data && data.markdown) || '(no markdown)';
}
function renderSeekChecks() {
  const layer = document.getElementById('seekLayer').value;
  const status = document.getElementById('seekStatus').value;
  const q = (document.getElementById('seekQ').value || '').toLowerCase();
  const rows = (window._seekChecks || []).filter(c => {
    if (layer && c.layer !== layer) return false;
    if (status && c.status !== status) return false;
    if (q) {
      const hay = ((c.check_id || '') + ' ' + (c.title || '') + ' ' + (c.registry_id || '') + ' ' + (c.detail || '')).toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
  const box = document.getElementById('seekChecks');
  if (!rows.length) {
    box.innerHTML = '<p class="bl-empty">No checks match (load latest or run battery).</p>';
    return;
  }
  box.innerHTML = rows.map(c => {
    const st = c.status || '';
    const rid = c.registry_id || '';
    return '<div class="check-row ' + escapeHtml(st) + '">'
      + '<span class="badge ' + (st === 'pass' ? 'pass' : (st === 'fail' || st === 'error' ? 'fail' : 'reg')) + '">'
      + escapeHtml(st) + '</span> '
      + '<span class="layer-pill">' + escapeHtml(c.layer || '') + '</span> '
      + '<span class="mono">' + escapeHtml(c.check_id || '') + '</span> — '
      + escapeHtml(c.title || '')
      + (rid ? ' · <a href="#/laws/' + encodeURIComponent(rid) + '">' + escapeHtml(rid) + '</a>' : '')
      + (c.detail ? '<div class="muted" style="margin-top:.25rem;font-size:.8rem">' + escapeHtml(String(c.detail).slice(0, 280)) + '</div>' : '')
      + '</div>';
  }).join('');
}
function setSeekRunningUi(running) {
  window._seekRunning = !!running;
  ['btnSeekRunQuick','btnSeekRunFull','btnSeekRunLive'].forEach(id => {
    const b = document.getElementById(id); if (b) b.disabled = !!running;
  });
  const stop = document.getElementById('btnSeekStop');
  if (stop) stop.disabled = !running;
}
function stopSeekBattery() {
  if (window._seekAbort) {
    try { window._seekAbort.abort(); } catch (e) { /* ignore */ }
  }
  // Best-effort server cancel (between phases when harness supports it)
  fetch('/api/law-seek/stop', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
    .catch(() => {});
  const rs = document.getElementById('seekRunStatus');
  const st = document.getElementById('status');
  if (rs) rs.textContent = 'stopping…';
  if (st) st.textContent = 'coverage stop requested';
}
async function runSeekBattery(opts) {
  opts = opts || {};
  if (window._seekRunning) return;
  const st = document.getElementById('status');
  const rs = document.getElementById('seekRunStatus');
  const skip = document.getElementById('seekSkipScripts').checked;
  if (rs) rs.textContent = 'running… (may take 30s–minutes) — use Stop to cancel';
  if (st) st.textContent = 'coverage running…';
  setSeekRunningUi(true);
  const ac = new AbortController();
  window._seekAbort = ac;
  try {
    const r = await fetch('/api/law-seek/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        quick: opts.quick !== false,
        live: !!opts.live,
        skip_scripts: skip,
      }),
      signal: ac.signal,
    });
    const data = await r.json();
    window._seekData = data;
    renderSeek(data, window._seekFilterReg);
    await loadQualitySnapshot({ rebuild: true });
    const cancelled = !!(data.cancelled || (data.report || {}).cancelled);
    if (cancelled) {
      if (rs) rs.textContent = 'STOPPED';
      if (st) st.textContent = 'coverage STOPPED';
      setSeekChrome('coverage battery: STOPPED · just now', false);
    } else {
      if (rs) rs.textContent = data.passed ? 'PASS' : (data.ok === false ? (data.error || 'fail') : 'FAIL');
      if (st) st.textContent = 'coverage ' + (data.passed ? 'PASS' : 'FAIL');
      setSeekChrome(
        'coverage battery: ' + (data.passed ? 'PASS' : 'FAIL') + ' · just now',
        !!data.passed,
      );
    }
  } catch (e) {
    const aborted = e && (e.name === 'AbortError' || String(e).includes('abort'));
    if (rs) rs.textContent = aborted ? 'STOPPED (client)' : String(e);
    if (st) st.textContent = aborted ? 'coverage STOPPED' : String(e);
    if (aborted) setSeekChrome('coverage battery: STOPPED · just now', false);
  } finally {
    window._seekAbort = null;
    setSeekRunningUi(false);
  }
}
function blEmpty(msg) {
  return '<p class="bl-empty">' + escapeHtml(msg || '— not filled yet') + '</p>';
}
function blKv(rows) {
  // rows: [[label, valueHtmlOrText, isHtml?], ...]
  let html = '<table class="kv">';
  rows.forEach(r => {
    const label = r[0];
    const val = r[1];
    const isHtml = r[2];
    const empty = val === null || val === undefined || val === ''
      || (Array.isArray(val) && !val.length);
    html += '<tr><th>' + escapeHtml(label) + '</th><td>';
    if (empty) html += '<span class="bl-empty">—</span>';
    else if (isHtml) html += val;
    else html += escapeHtml(String(val));
    html += '</td></tr>';
  });
  html += '</table>';
  return html;
}
function blSection(title, bodyHtml) {
  return '<div class="bl-section"><h4>' + escapeHtml(title) + '</h4>'
    + (bodyHtml || blEmpty()) + '</div>';
}
function renderAnalysisDetail(analysis) {
  if (!analysis) return blEmpty('No session analysis yet. Say: review conjecture backlog');
  if (typeof analysis === 'string') {
    return '<div class="bl-prose">' + escapeHtml(analysis) + '</div>';
  }
  const a = analysis;
  let html = '';
  if (a.prose) html += '<div class="bl-prose">' + escapeHtml(a.prose) + '</div>';
  const metaRows = [
    ['Classification (analysis)', a.classification || ''],
    ['Conversation', a.conversation_id || ''],
    ['Reviewed at', a.reviewed_at || ''],
    ['Reviewer', a.reviewer || ''],
    ['Layer trace', a.layer_trace || a.code_path || ''],
    ['Root cause', a.root_cause || a.root_cause_hypothesis || ''],
    ['Confidence', a.confidence != null && a.confidence !== '' ? String(a.confidence) : ''],
  ];
  // Extra string fields not already shown
  const skip = new Set([
    'prose', 'classification', 'conversation_id', 'reviewed_at', 'reviewer',
    'layer_trace', 'code_path', 'root_cause', 'root_cause_hypothesis', 'confidence',
    'suggested_fixes', 'related_scenarios', 'patch', 'expected_vs_observed',
    'what_should_have_happened', 'what_actually_happened',
  ]);
  Object.keys(a).forEach(k => {
    if (skip.has(k)) return;
    const v = a[k];
    if (v == null || v === '') return;
    if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') {
      metaRows.push([k, String(v)]);
    }
  });
  html += blKv(metaRows);
  if ((a.related_scenarios || []).length) {
    html += '<p class="muted" style="margin:.5rem 0 .2rem"><strong>Related scenarios</strong></p><ul>';
    a.related_scenarios.forEach(s => {
      html += '<li class="mono">' + escapeHtml(String(s)) + '</li>';
    });
    html += '</ul>';
  }
  if ((a.suggested_fixes || []).length) {
    html += renderFindingsBlock({
      headline: 'Suggested fixes (from analysis)',
      verdict: a.classification || '',
      suggested_fixes: a.suggested_fixes,
      source: a.reviewer || 'session_agent',
    });
  }
  if ((a.what_should_have_happened || []).length || (a.what_actually_happened || []).length
      || (a.expected_vs_observed || []).length) {
    html += renderFindingsBlock({
      headline: 'Tables embedded in analysis',
      verdict: a.classification || '',
      what_should_have_happened: a.what_should_have_happened,
      what_actually_happened: a.what_actually_happened,
      expected_vs_observed: a.expected_vs_observed,
      source: 'analysis',
    });
  }
  if (!a.prose && !html) {
    html += '<pre style="max-height:16rem">' + escapeHtml(JSON.stringify(a, null, 2)) + '</pre>';
  }
  return html;
}
function renderWahEnvelope(wah) {
  if (!wah || (typeof wah === 'object' && !Object.keys(wah).length)) {
    return blEmpty('No what_actually_happened envelope on this item');
  }
  if (Array.isArray(wah)) {
    return renderTurnTable(wah, 'What actually happened (turns)');
  }
  let html = blKv([
    ['Incident id', wah.incident_id || ''],
    ['Failure mode', wah.failure_mode || ''],
    ['Verdict', wah.verdict || ''],
    ['Adapter', wah.adapter || ''],
    ['Ledger', wah.ledger || ''],
    ['Code path', wah.code_path || ''],
    ['Root cause', wah.root_cause || ''],
    ['Planted steal', wah.planted_steal != null ? String(wah.planted_steal) : ''],
    ['Note', wah.note || ''],
  ]);
  const turns = wah.turns || wah.turn_table || [];
  if ((turns || []).length) {
    html += renderTurnTable(turns, 'Turn table');
  } else {
    html += blEmpty('No turn rows in envelope');
  }
  return html;
}
function renderRunTurns(turns) {
  if (!turns || !turns.length) return blEmpty('No run turn observations captured');
  let html = '<table class="turn-table"><thead><tr>'
    + '<th class="idx">#</th><th>User</th><th>Owner</th><th>Kind</th>'
    + '<th>Outcome</th><th>Agent</th><th>Failures</th></tr></thead><tbody>';
  turns.forEach(t => {
    const fails = (t.failures || []).join('; ');
    html += '<tr>'
      + '<td class="idx">' + escapeHtml(String(t.index ?? '')) + '</td>'
      + '<td>' + escapeHtml(t.user_text || '') + '</td>'
      + '<td class="mono">' + escapeHtml(t.owner || '—') + '</td>'
      + '<td class="mono">' + escapeHtml(t.active_kind || '—') + '</td>'
      + '<td class="mono">' + escapeHtml(t.outcome || '—') + '</td>'
      + '<td class="mono">' + escapeHtml(t.agent_type || '—') + '</td>'
      + '<td class="muted">' + escapeHtml(fails || '—') + '</td>'
      + '</tr>';
  });
  html += '</tbody></table>';
  return html;
}
function renderPatchDetail(p, it) {
  if (!p) return blEmpty('No patch yet — after fix, close_with_patch documents it here');
  let html = blKv([
    ['Summary', p.summary || ''],
    ['Seal', p.seal || ''],
    ['Notes', p.notes || ''],
    ['Closed at', p.closed_at || (it && it.closed_at) || ''],
    ['Closed by', p.closed_by || (it && it.reviewer) || ''],
    ['Command', p.command || 'fix'],
  ]);
  if ((p.files || []).length) {
    html += '<p class="muted" style="margin:.45rem 0 .15rem"><strong>Files</strong></p><ul>';
    p.files.forEach(f => { html += '<li class="mono">' + escapeHtml(f) + '</li>'; });
    html += '</ul>';
  }
  if ((p.commits || []).length) {
    html += '<p class="muted mono" style="font-size:.8rem">commits: '
      + escapeHtml(p.commits.join(', ')) + '</p>';
  }
  if ((p.tests || []).length) {
    html += '<p class="muted" style="margin:.45rem 0 .15rem"><strong>Tests / ratchets</strong></p><ul>';
    p.tests.forEach(t => { html += '<li class="mono">' + escapeHtml(t) + '</li>'; });
    html += '</ul>';
  }
  return html;
}
function renderBacklogItemDetail(it) {
  const st = it.status || '';
  const cl = it.classification || '';
  const fin = it.findings || it.findings_skeleton || {};
  let html = '';

  // 1. Identity + run
  html += blSection('Identity & run', blKv([
    ['Item id', it.id || ''],
    ['Scenario', it.scenario_id || ''],
    ['Headline', it.headline || fin.headline || ''],
    ['Status', st],
    ['Classification', cl],
    ['Failure mode', it.failure_mode || fin.failure_mode_slug || ''],
    ['Incident id', it.incident_id || ''],
    ['Reason enqueued', it.reason || ''],
    ['Adapter', it.adapter || ''],
    ['Product path', it.product_path != null ? String(it.product_path) : ''],
    ['Run ok', it.run_ok != null ? String(it.run_ok) : ''],
    ['Run passed', it.run_passed != null ? String(it.run_passed) : ''],
    ['Run error', it.run_error || ''],
    ['Account', it.account || ''],
    ['Conversation id', it.conversation_id || it.thread_id || ''],
    ['Thread id', it.thread_id || ''],
    ['Evidence path', it.evidence_path || ''],
    ['Reviewer', it.reviewer || ''],
    ['Created', it.created_at || ''],
    ['Updated', it.updated_at || ''],
    ['Closed at', it.closed_at || ''],
  ]));

  if (it.scenario_purpose) {
    html += blSection('Scenario purpose',
      '<div class="bl-prose">' + escapeHtml(it.scenario_purpose) + '</div>');
  }
  if (it.user_trajectory) {
    html += blSection('User trajectory',
      '<div class="bl-prose">' + escapeHtml(it.user_trajectory) + '</div>');
  }

  // Run failures
  const fails = it.run_failures || [];
  if (fails.length) {
    html += blSection('Invariant / run failures',
      '<ul>' + fails.map(f => '<li class="mono">' + escapeHtml(String(f)) + '</li>').join('')
      + '</ul>');
  } else if (it.run_passed === false) {
    html += blSection('Invariant / run failures',
      blEmpty('run_passed=false but no failure strings on item — check evidence_path or re-run host'));
  }

  // Conversation callout
  if (it.conversation_id || it.thread_id) {
    html += blSection('Product conversation',
      '<p>Open in product UI or admin: <span class="mono">'
      + escapeHtml(it.conversation_id || it.thread_id) + '</span></p>'
      + '<p class="muted" style="font-size:.82rem">Session reviewer should load transcript + '
      + 'route_data / control events (local Postgres or staging admin API).</p>');
  } else {
    html += blSection('Product conversation',
      blEmpty('No conversation_id — geometry stub, create-failed, or non-host adapter'));
  }

  // Session analysis
  html += blSection('Session analysis (' + (window._sessionAgentLabel || 'session coding agent') + ')',
    renderAnalysisDetail(it.analysis));

  // Findings (full tables)
  html += blSection('Findings tables', renderFindingsBlock(fin));

  // WAH envelope (execution)
  html += blSection('What actually happened (execution envelope)',
    renderWahEnvelope(it.what_actually_happened));

  // Run turn observations
  if ((it.run_turns || []).length) {
    html += blSection('Run turn observations (adapter)', renderRunTurns(it.run_turns));
  }

  // Suggested fixes (item-level, may duplicate findings)
  const sfx = it.suggested_fixes || [];
  if (sfx.length) {
    html += blSection('Suggested fixes (item)', renderFindingsBlock({
      headline: 'Suggested monorepo fixes',
      verdict: cl || st,
      suggested_fixes: sfx,
      source: it.reviewer || 'session_agent',
    }));
  } else if (st === 'backlog_fix' || cl === 'product_bug') {
    html += blSection('Suggested fixes (item)',
      blEmpty('None yet — session review should fill suggested_fixes[] before fix'));
  }

  // Patch on close
  html += blSection('Patch (documented on close)', renderPatchDetail(it.patch, it));

  if (it.fix_notes && !(it.patch && it.patch.summary === it.fix_notes)) {
    html += blSection('Fix notes',
      '<div class="bl-prose">' + escapeHtml(it.fix_notes) + '</div>');
  }

  // Checklist
  if ((it.review_checklist || []).length) {
    html += blSection('Review checklist',
      '<ol style="margin:0;padding-left:1.2rem;font-size:.85rem">'
      + it.review_checklist.map(c => '<li>' + escapeHtml(c) + '</li>').join('')
      + '</ol>');
  }

  // Taxonomy / split
  const tax = it.taxonomy || {};
  const split = it.candidate_split || {};
  if (Object.keys(tax).length || Object.keys(split).length) {
    const rows = [];
    Object.keys(tax).forEach(k => rows.push(['taxonomy.' + k, String(tax[k] ?? '')]));
    Object.keys(split).forEach(k => {
      const v = split[k];
      rows.push(['split.' + k, typeof v === 'object' ? JSON.stringify(v) : String(v ?? '')]);
    });
    html += blSection('Taxonomy & candidate split', blKv(rows));
  }

  // Related
  if ((it.related_item_ids || []).length) {
    html += blSection('Related items',
      '<ul>' + it.related_item_ids.map(x =>
        '<li class="mono">' + escapeHtml(String(x)) + '</li>').join('') + '</ul>');
  }

  // Next action
  if (st === 'needs_review') {
    html += blSection('Next action',
      '<p>In session: <code>review conjecture backlog</code> — fill analysis + findings tables '
      + '+ classification. <span class="mono">product_bug</span> → <span class="mono">backlog_fix</span>.</p>');
  } else if (st === 'backlog_fix') {
    html += blSection('Next action',
      '<p>In session: <code>fix</code> — implement seals from suggested_fixes, then '
      + '<span class="mono">close_with_patch</span> so this item is <strong>closed</strong> '
      + 'with the patch documented above.</p>');
  } else if (st === 'closed' && cl === 'fixed') {
    html += blSection('Next action',
      '<p class="muted">Closed as fixed. Re-run scenario to prove the seal if not already green.</p>');
  }

  // Raw JSON (power users)
  html += '<details class="help-block" style="margin-top:.75rem">'
    + '<summary style="cursor:pointer;font-weight:600;font-size:.85rem">'
    + 'Raw item JSON</summary>'
    + '<pre style="max-height:22rem">' + escapeHtml(JSON.stringify(it, null, 2)) + '</pre>'
    + '</details>';

  return html;
}
async function loadBacklog() {
  const list = document.getElementById('backlogList');
  const meta = document.getElementById('backlogMeta');
  const detail = document.getElementById('backlogDetail');
  if (detail) detail.style.display = 'none';
  try {
    const r = await fetch('/api/backlog?limit=100');
    const d = await r.json();
    window._backlog = d;
    if (meta) {
      meta.textContent = 'dir=' + (d.dir || '') + ' · n=' + (d.count || 0)
        + ' · needs_review=' + ((d.by_status || {}).needs_review || 0)
        + ' · backlog_fix=' + ((d.by_status || {}).backlog_fix || 0)
        + ' · closed=' + ((d.by_status || {}).closed || 0);
    }
    if (!list) return;
    const items = d.items || [];
    if (!items.length) {
      list.innerHTML = '<div class="card"><p class="muted">No backlog items yet. Run Host (or Geometry) tests — each run enqueues for session review.</p></div>';
      return;
    }
    let html = '';
    items.forEach(it => {
      const st = it.status || '';
      const cl = it.classification || '';
      const badgeCls = cl === 'product_bug' ? 'fail'
        : (cl === 'fixed' || cl === 'conjecture_caught' ? 'pass'
        : (cl === 'rate_limit' || cl === 'infra' ? 'open' : 'partial'));
      const closedCls = (st === 'closed' || cl === 'fixed') ? '' : (cl === 'product_bug' ? 'bad' : '');
      const hl = it.headline || (it.findings_skeleton && it.findings_skeleton.headline) || '';
      html += '<details class="scenario-result ' + closedCls + '">';
      html += '<summary>'
        + '<span class="badge ' + badgeCls + '">' + escapeHtml(cl || st) + '</span>'
        + '<span class="badge ' + (st === 'closed' ? 'pass' : (st === 'backlog_fix' ? 'fail' : 'partial')) + '">'
        + escapeHtml(st) + '</span>'
        + '<span class="mono">' + escapeHtml(it.scenario_id || '') + '</span>'
        + (it.failure_mode
          ? '<span class="badge open">' + escapeHtml(it.failure_mode) + '</span>' : '')
        + (it.conversation_id
          ? '<span class="muted mono">conv=' + escapeHtml(it.conversation_id) + '</span>'
          : '<span class="muted">no conv yet</span>')
        + (hl ? '<span class="muted" style="max-width:28rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
          + escapeHtml(hl) + '</span>' : '')
        + '</summary><div class="scenario-result-body">'
        + renderBacklogItemDetail(it)
        + '</div></details>';
    });
    list.innerHTML = html;
  } catch (e) {
    if (list) list.innerHTML = '<div class="turn bad">' + escapeHtml(String(e)) + '</div>';
  }
}
function updateRunSelectedHint() {
  const el = document.getElementById('runSelectedHint');
  const listEl = document.getElementById('runSelectedList');
  const n = (window._candSelected && window._candSelected.size) || 0;
  const vis = (window._candVisibleIds || []).length;
  const mode = (document.querySelector('input[name="candSelMode"]:checked') || {}).value || 'ids';
  const ids = Array.from(window._candSelected || []);
  if (listEl) {
    if (!ids.length) {
      listEl.innerHTML = 'No scenarios selected — go to <strong>Candidates</strong> and tick checkboxes, '
        + 'or choose <em>All (filtered)</em> to run everything matching filters.';
    } else {
      listEl.innerHTML = '<strong>' + ids.length + ' selected:</strong><br/>'
        + ids.slice(0, 40).map(id => escapeHtml(id)).join('<br/>')
        + (ids.length > 40 ? '<br/>… +' + (ids.length - 40) + ' more' : '');
    }
  }
  if (el) {
    el.innerHTML = '<strong>Mode:</strong> ' + (mode === 'all'
      ? 'All filtered (' + vis + ' on Candidates list)'
      : 'Selected only (' + n + ' checked)')
      + (window._candData && window._candData.scenario_id
        ? ' · detail open: <span class="mono">' + escapeHtml(window._candData.scenario_id) + '</span>'
        : '');
  }
  updateSelCount();
}
document.querySelectorAll('#appNav button[data-view]').forEach(btn => {
  btn.onclick = () => {
    const v = btn.getAttribute('data-view');
    if (v === 'home') location.hash = '#/home';
    else if (v === 'laws') location.hash = '#/laws';
    else if (v === 'techniques') location.hash = '#/techniques';
    else if (v === 'seek') location.hash = '#/seek';
    else if (v === 'candidates') location.hash = '#/candidates';
    else if (v === 'run') location.hash = '#/run';
    else if (v === 'backlog') location.hash = '#/verdict';
    else if (v === 'admin' || v === 'cleanup') location.hash = '#/admin';
    else if (v === 'demo') location.hash = '#/demo';
    else if (v === 'help') location.hash = '#/help';
    else if (v === 'program-authority') location.hash = '#/program/cognitive_authority';
    else if (v === 'program-laundry') location.hash = '#/program/code_poison_laundry';
    else if (v === 'program-antipattern') location.hash = '#/program/construction_antipattern';
    else if (v === 'program-voice') location.hash = '#/program/product_voice';
    else if (v === 'program-purity') location.hash = '#/program/purity_scoreboard';
    else if (v === 'program-memory') location.hash = '#/program/memory_management';
    else if (v === 'program-surface') location.hash = '#/program/surface_law_coverage';
  };
});
function dot(on, warn) {
  const cls = warn ? 'warn' : (on ? 'on' : 'off');
  return '<span class="ok-dot ' + cls + '"></span>';
}
function kvRows(pairs) {
  return pairs.map(([k, v]) =>
    '<tr><th>' + escapeHtml(k) + '</th><td>' + v + '</td></tr>'
  ).join('');
}
function renderAdminStatus(d) {
  if (!d || d.ok === false) {
    const err = (d && d.error) || 'failed to load admin status';
    ['adminAccountTable','adminHostTable','adminInventTable','adminReviewerTable','adminFindingsTable',
     'adminCandTable','adminConsoleTable'].forEach(id => {
      const t = document.getElementById(id);
      if (t) t.innerHTML = '<tr><th>Error</th><td class="mono">' + escapeHtml(err) + '</td></tr>';
    });
    return;
  }
  const acc = d.account || {};
  const host = d.host_driver || {};
  const inv = d.invent_llm || {};
  const fin = d.findings_llm || {};
  const cand = d.candidates || {};
  const con = d.console || {};
  const clean = d.cleanup || {};

  document.getElementById('adminAccountTable').innerHTML = kvRows([
    ['Email', acc.email_set
      ? ('<span class="mono">' + escapeHtml(acc.email || '') + '</span>')
      : (dot(false) + '<strong>not set</strong> — CONJECTURE_HOST_EMAIL')],
    ['Password', dot(!!acc.password_set)
      + (acc.password_set ? 'set (never shown)' : '<strong>not set</strong> — CONJECTURE_HOST_PASSWORD')],
    ['API base URL', acc.base_url_set
      ? ('<span class="mono">' + escapeHtml(acc.base_url || '') + '</span>')
      : (dot(false) + '<strong>not set</strong> — CONJECTURE_HOST_BASE_URL')],
    ['Timeout (s)', escapeHtml(String(acc.timeout_s || ''))],
    ['Configured', dot(!!acc.configured) + (acc.configured ? 'ready for host E2E' : 'incomplete')],
    ['Env keys', '<span class="mono">' + escapeHtml((acc.env_keys || []).join(', ')) + '</span>'],
    ['Note', escapeHtml(acc.note || '')],
  ]);
  document.getElementById('adminHostTable').innerHTML = kvRows([
    ['Available', dot(!!host.available) + (host.available ? 'yes' : 'no')],
    ['Source', '<span class="mono">' + escapeHtml(host.source || '—') + '</span>'],
    ['Account', host.account
      ? ('<span class="mono">' + escapeHtml(host.account || '') + '</span>')
      : (dot(false) + 'not set (env)')],
    ['Base URL', host.base_url
      ? ('<span class="mono">' + escapeHtml(host.base_url || '') + '</span>')
      : (dot(false) + 'not set (env)')],
    ['Password', dot(!!host.password_set) + (host.password_set ? 'set' : 'missing')],
    ['Hint', escapeHtml(host.hint || host.error || '')],
  ]);
  const invKey = inv.api_key || {};
  document.getElementById('adminInventTable').innerHTML = kvRows([
    ['Configured', dot(!!inv.configured) + (inv.configured ? 'ready' : 'incomplete')],
    ['Base URL', '<span class="mono">' + escapeHtml(inv.base_url || '—') + '</span>'],
    ['Model', '<span class="mono">' + escapeHtml(inv.model || '—') + '</span>'],
    ['API key', invKey.set
      ? (dot(true) + 'set · ' + escapeHtml(invKey.preview || '') + ' · len=' + invKey.length)
      : (dot(false) + 'not set')],
    ['Timeout (s)', escapeHtml(String(inv.timeout_s ?? ''))],
    ['Max proposals / scenarios', escapeHtml(String(inv.max_proposals ?? '')) + ' / '
      + escapeHtml(String(inv.max_scenarios ?? ''))],
    ['Prompt', '<span class="mono">' + escapeHtml(inv.prompt_path || '') + '</span>'],
    ['Env vars', '<span class="mono">' + escapeHtml((inv.env_keys || []).join(', ')) + '</span>'],
  ]);
  const rev = d.findings_reviewer || {};
  const revTable = document.getElementById('adminReviewerTable');
  if (revTable) {
    revTable.innerHTML = kvRows([
      ['Mode (active)', dot(true) + '<span class="mono">' + escapeHtml(rev.mode || 'session') + '</span>'
        + ' <span class="muted">(default ' + escapeHtml(rev.default || 'session') + ')</span>'],
      ['Session agent label', escapeHtml(rev.session_agent_label || 'session coding agent')],
      ['Delivery', escapeHtml(rev.delivery || 'session handoff (Verdict queue)')],
      ['Verdict queue (backlog)', rev.uses_backlog_handoff
        ? (dot(true) + 'yes · <span class="mono">' + escapeHtml(rev.backlog_dir || '') + '</span>')
        : (dot(false) + 'no')],
      ['Review command', '<code>' + escapeHtml(rev.command_review || 'review conjecture backlog') + '</code>'],
      ['Fix command', '<code>' + escapeHtml(rev.command_fix || 'fix') + '</code>'],
      ['Env', '<span class="mono">' + escapeHtml(rev.env || 'CONJECTURE_FINDINGS_REVIEWER') + '</span>'],
      ['Optional label env', '<span class="mono">' + escapeHtml(rev.env_label || 'CONJECTURE_SESSION_AGENT_LABEL') + '</span>'],
      ['Note', escapeHtml(rev.note || '')],
    ]);
  }
  const finKey = fin.api_key || {};
  const finInUse = !!(fin.in_use || fin.enabled);
  // When idle (session mode), keep the remote-LLM card minimal — no invent fallback noise.
  if (!finInUse) {
    document.getElementById('adminFindingsTable').innerHTML = kvRows([
      ['Status', dot(false) + 'idle (session mode is active)'],
      ['Enable with', '<span class="mono">CONJECTURE_FINDINGS_REVIEWER=openai</span>'],
      ['Note', escapeHtml(fin.note || 'Not the active reviewer path.')],
    ]);
  } else {
    document.getElementById('adminFindingsTable').innerHTML = kvRows([
      ['Status', dot(true) + 'active'],
      ['Configured', fin.configured
        ? (dot(true) + 'ready')
        : (dot(false) + 'incomplete — set base + model + API key')],
      ['Base URL', '<span class="mono">' + escapeHtml(fin.base_url || '—') + '</span>'],
      ['Model', '<span class="mono">' + escapeHtml(fin.model || '—') + '</span>'],
      ['API key', finKey.set
        ? (dot(true) + 'set · ' + escapeHtml(finKey.preview || ''))
        : (dot(false) + 'not set')],
      ['Falls back to invent LLM', fin.falls_back_to_invent ? 'yes' : 'no'],
      ['Prompt', '<span class="mono">' + escapeHtml(fin.prompt_path || '') + '</span>'],
      ['Note', escapeHtml(fin.note || '')],
    ]);
  }
  document.getElementById('adminCandTable').innerHTML = kvRows([
    ['Resolved', dot(!!cand.resolved) + (cand.resolved ? 'yes' : 'no')],
    ['Directory', '<span class="mono">' + escapeHtml(cand.dir || '—') + '</span>'],
    ['CONJECTURE_CANDIDATES_DIR', '<span class="mono">' + escapeHtml(cand.env || '(auto-discover)') + '</span>'],
  ]);
  document.getElementById('adminConsoleTable').innerHTML = kvRows([
    ['cwd', '<span class="mono">' + escapeHtml(con.cwd || '') + '</span>'],
    ['VIRTUAL_ENV', '<span class="mono">' + escapeHtml(con.python || '—') + '</span>'],
  ]);
  // Portable host abuse controls (+ optional host profile overlay from API)
  const limCtrl = d.host_abuse_controls || {};
  const limFlat = d.product_limits_note || {};
  const limTitle = document.getElementById('adminLimitsTitle');
  const limLead = document.getElementById('adminLimitsLead');
  const limHint = document.getElementById('adminLimitsHint');
  if (limTitle) {
    limTitle.textContent = limCtrl.title || limFlat.title
      || 'Host product abuse controls (why empty shells / 429s)';
  }
  if (limLead) {
    limLead.textContent = limCtrl.lead || limFlat.lead
      || 'Host adapter runs hit the product\'s own rate limits.';
  }
  if (limHint) {
    const profile = limCtrl.host_profile || limFlat.host_profile || '';
    const source = limCtrl.source || limFlat.source || '';
    const hint = limCtrl.tune_hint || limFlat.tune_hint || '';
    const bits = [];
    if (source) bits.push('source=' + source);
    if (profile) bits.push('profile=' + profile);
    if (hint) bits.push(hint);
    limHint.textContent = bits.join(' · ');
  }
  const limEl = document.getElementById('adminLimitsTable');
  if (limEl) {
    const rows = limCtrl.rows || [];
    if (rows.length) {
      limEl.innerHTML = kvRows(rows.map(r => {
        const label = r.label || r.key || '';
        let body = r.detail || '';
        if (r.host_knob) {
          body = '<span class="mono">' + escapeHtml(String(r.host_knob)) + '</span>'
            + (r.default != null && r.default !== ''
              ? ' <span class="muted">default ' + escapeHtml(String(r.default)) + '</span>'
              : '')
            + (body ? '<div class="muted" style="margin-top:.2rem">' + escapeHtml(body) + '</div>' : '');
        } else {
          body = escapeHtml(body || '— host SPI has not published a knob for this category —');
        }
        return [label, body];
      }));
    } else {
      limEl.innerHTML = kvRows([
        ['Auth / login', escapeHtml(limFlat.login || '')],
        ['Chat / turn API', escapeHtml(limFlat.chat || limFlat.bot0_chat || '')],
        ['LLM burst', escapeHtml(limFlat.llm_burst || '')],
        ['LLM hourly', escapeHtml(limFlat.llm_hour || '')],
        ['Thread create', escapeHtml(limFlat.thread_create || limFlat.conversation_create || '')],
        ['Empty shells', escapeHtml(limFlat.empty_shells || '')],
      ]);
    }
  }
  const meta = document.getElementById('adminCleanupMeta');
  if (meta) {
    meta.textContent = 'prefixes=' + (clean.title_prefixes || []).join(', ')
      + ' · account=' + (clean.account || '')
      + ' · ' + (clean.product_action || '');
  }
  const warns = d.warnings || [];
  const wEl = document.getElementById('adminWarnings');
  if (wEl) {
    if (warns.length) {
      wEl.style.display = 'block';
      wEl.innerHTML = warns.map(w => '<li>' + escapeHtml(w) + '</li>').join('');
    } else {
      wEl.style.display = 'none';
      wEl.innerHTML = '';
    }
  }
}
async function loadRunnerLog() {
  const el = document.getElementById('adminRunnerLog');
  if (!el) return;
  try {
    const r = await fetch('/api/logs?limit=80');
    const d = await r.json();
    const entries = d.entries || [];
    if (!entries.length) {
      el.textContent = 'No events yet — run a candidate (geometry or host).';
      return;
    }
    el.textContent = entries.map(e => {
      const bits = [e.ts || '', (e.level || '').padEnd(7), e.event || '', e.msg || ''];
      const extra = Object.keys(e).filter(k =>
        !['ts','level','event','msg'].includes(k)
      ).map(k => k + '=' + JSON.stringify(e[k])).join(' ');
      return bits.join(' ') + (extra ? ' | ' + extra : '');
    }).join('\n');
  } catch (e) {
    el.textContent = 'log fetch failed: ' + String(e);
  }
}
async function loadAdminStatus() {
  const st = document.getElementById('status');
  try {
    const r = await fetch('/api/admin/status');
    const d = await r.json();
    window._adminStatus = d;
    loadRunnerLog();
    renderAdminStatus(d);
    if (st && !st.textContent) st.textContent = 'admin loaded';
  } catch (e) {
    renderAdminStatus({ ok: false, error: String(e) });
  }
}

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
  // #/home | #/laws[/<registry_id>] | #/seek[?registry=]
  // #/program/<category_id>
  // #/candidates | #/run | #/verdict|#/backlog | #/admin | #/demo | #/help
  // #/candidate/<id>[/trajectory|scenario|script|evidence]
  // #/cleanup → admin (alias)
  const h = (location.hash || '').replace(/^#/, '');
  const qIdx = h.indexOf('?');
  const pathPart = qIdx >= 0 ? h.slice(0, qIdx) : h;
  const queryPart = qIdx >= 0 ? h.slice(qIdx + 1) : '';
  const params = {};
  if (queryPart) {
    queryPart.split('&').forEach(pair => {
      const [k, v] = pair.split('=');
      if (k) params[decodeURIComponent(k)] = decodeURIComponent(v || '');
    });
  }
  const parts = pathPart.split('/').filter(Boolean);
  if (parts[0] === 'candidate' && parts[1]) {
    return {
      view: 'candidates',
      id: decodeURIComponent(parts[1]),
      tab: parts[2] || 'trajectory',
      params,
    };
  }
  if (parts[0] === 'program') {
    const cat = parts[1] ? decodeURIComponent(parts[1]) : 'code_poison_laundry';
    const navKey = {
      code_poison_laundry: 'program-laundry',
      construction_antipattern: 'program-antipattern',
      product_voice: 'program-voice',
      purity_scoreboard: 'program-purity',
      memory_management: 'program-memory',
      surface_law_coverage: 'program-surface',
      cognitive_authority: 'program-authority',
    }[cat] || 'program-laundry';
    return {
      view: navKey,
      id: null,
      tab: 'trajectory',
      programId: cat,
      params,
    };
  }
  if (parts[0] === 'laws') {
    return {
      view: 'laws',
      id: null,
      tab: 'trajectory',
      lawId: parts[1] ? decodeURIComponent(parts[1]) : null,
      params,
    };
  }
  if (parts[0] === 'seek' || parts[0] === 'coverage') {
    return {
      view: 'seek',
      id: null,
      tab: 'trajectory',
      registry: params.registry || null,
      params,
    };
  }
  // Aliases for quality-program voice
  if (parts[0] === 'authority') {
    return { view: 'laws', id: null, tab: 'trajectory', params };
  }
  if (parts[0] === 'purity') {
    return { view: 'program-purity', programId: 'purity_scoreboard', id: null, tab: 'trajectory', params };
  }
  if (parts[0] === 'laundry') {
    return { view: 'program-laundry', programId: 'code_poison_laundry', id: null, tab: 'trajectory', params };
  }
  const views = [
    'home', 'laws', 'seek', 'candidates', 'run', 'runner',
    'techniques', 'how-we-run', 'proof',
    'backlog', 'verdict', 'admin', 'cleanup', 'demo', 'help',
    'program-laundry', 'program-antipattern', 'program-voice',
    'program-purity', 'program-memory', 'program-surface', 'program-authority',
    'map', 'approach',
  ];
  if (parts[0] && views.includes(parts[0])) {
    let v = parts[0];
    if (v === 'cleanup') v = 'admin';
    if (v === 'verdict') v = 'backlog';  // Verdict tab = backlog store
    if (v === 'runner') v = 'run';      // Runner tab id remains "run"
    if (v === 'map' || v === 'approach') v = 'home';
    if (v === 'how-we-run' || v === 'proof') v = 'techniques';
    return { view: v, id: null, tab: 'trajectory', params, mode: params.mode || null };
  }
  // Empty hash → Map (quality programs)
  return { view: 'home', id: null, tab: 'trajectory', params };
}
function setHash(id, tab) {
  const t = tab || 'trajectory';
  location.hash = id
    ? ('/candidate/' + encodeURIComponent(id) + '/' + t)
    : '/candidates';
}
function showTab(tab) {
  ['trajectory','scenario','script','evidence'].forEach(name => {
    const panel = document.getElementById('candPanel' + name.charAt(0).toUpperCase() + name.slice(1));
    if (panel) panel.style.display = name === tab ? 'block' : 'none';
  });
  document.querySelectorAll('.cand-tab').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tab);
  });
}
function renderEvidence(ev) {
  // Early error contract surface (runner_log.error_contract)
  if (ev && ev.ok === false && (ev.error_code || ev.error || ev.message)) {
    const panel = document.getElementById('candPanelEvidence');
    if (!panel) return;
    let html = '<div class="turn bad">';
    html += '<strong>Run error</strong> '
      + '<span class="badge fail">' + escapeHtml(ev.error_code || ev.error || 'error') + '</span>';
    if (ev.stage) html += ' <span class="muted mono">stage=' + escapeHtml(ev.stage) + '</span>';
    if (ev.adapter) html += ' <span class="muted mono">adapter=' + escapeHtml(ev.adapter) + '</span>';
    html += '<p style="margin:.5rem 0 0">' + escapeHtml(ev.message || ev.error || '') + '</p>';
    if (ev.exc_type) {
      html += '<p class="muted mono" style="margin:.35rem 0">exc=' + escapeHtml(ev.exc_type)
        + ': ' + escapeHtml(ev.exc_message || '') + '</p>';
    }
    if (ev.traceback) {
      html += '<details class="help-block" open><summary style="cursor:pointer;font-weight:600">Traceback</summary>'
        + '<pre style="max-height:16rem">' + escapeHtml(ev.traceback) + '</pre></details>';
    }
    html += '<p class="muted" style="margin:.5rem 0 0;font-size:.8rem">See Admin → Runner log, or stderr with '
      + '<span class="mono">CONJECTURE_LOG_LEVEL=DEBUG</span>.</p>';
    html += '</div>';
    if (ev.findings) html += renderFindingsBlock(ev.findings);
    html += '<pre style="margin-top:.75rem">' + escapeHtml(JSON.stringify(ev, null, 2)) + '</pre>';
    panel.innerHTML = html;
    return;
  }
  const panel = document.getElementById('candPanelEvidence');
  if (!panel) return;
  if (!ev || ev.ok === false && !ev.run) {
    panel.innerHTML = '<p class="muted">' + escapeHtml((ev && ev.error) || 'No run yet. Use Run buttons above.') + '</p>';
    return;
  }
  const tax = ev.taxonomy || {};
  const split = ev.candidate_split || {};
  const run = ev.run || {};
  const passed = run.passed;
  let html = '<p class="muted"><strong>Execution evidence</strong> — taxonomy-shaped; under '
    + '<span class="mono">evidence/</span> (gitignored). Stub GeometryHoldAdapter unless host Driver is wired.</p>';
  html += '<div class="row"><span class="badge ' + (passed ? 'pass' : 'fail') + '">'
    + (passed ? 'PASS' : 'FAIL') + '</span>'
    + '<span class="muted mono">' + escapeHtml(ev.evidence_path || '') + '</span></div>';
  html += '<table class="muted" style="width:100%;font-size:.85rem;margin:.75rem 0;border-collapse:collapse">';
  html += '<tr><td style="padding:.25rem"><strong>Failure-mode mapping</strong></td><td class="mono">'
    + escapeHtml(tax.failure_mode || split.failure_mode_mapping || '') + '</td></tr>';
  html += '<tr><td style="padding:.25rem"><strong>Candidate scenario</strong></td><td class="mono">'
    + escapeHtml(tax.candidate_scenario || ev.scenario_id || '') + '</td></tr>';
  html += '<tr><td style="padding:.25rem"><strong>User trajectory</strong></td><td>'
    + escapeHtml(split.user_trajectory || '—') + '</td></tr>';
  html += '<tr><td style="padding:.25rem"><strong>Scenario geometry</strong></td><td class="mono">'
    + escapeHtml(JSON.stringify(split.scenario_geometry || {})) + '</td></tr>';
  html += '<tr><td style="padding:.25rem"><strong>Mode detection</strong></td><td><ul style="margin:0">'
    + (split.mode_detection || []).map(x => '<li>' + escapeHtml(x) + '</li>').join('')
    + '</ul></td></tr>';
  html += '<tr><td style="padding:.25rem"><strong>Adapter</strong></td><td class="mono">'
    + escapeHtml((run.adapter || '') + (run.planted_steal ? ' · planted_steal' : ' · healthy'))
    + '</td></tr>';
  html += '</table>';
  // Incident-shaped turn table (conv_1732aa88 report form)
  const wah = ev.what_actually_happened || {};
  if ((wah.turns || []).length) {
    html += '<div class="report-card" style="margin:.75rem 0"><strong>What actually happened'
      + (wah.incident_id ? ' — ' + escapeHtml(String(wah.incident_id)) : '')
      + '</strong>';
    if (wah.verdict) {
      html += ' <span class="badge ' + (wah.verdict === 'PASS' ? 'pass' : 'fail') + '">'
        + escapeHtml(wah.verdict) + '</span>';
    }
    html += '<table style="width:100%;font-size:.85rem;margin:.5rem 0;border-collapse:collapse">'
      + '<thead><tr style="text-align:left"><th style="padding:.25rem">#</th>'
      + '<th style="padding:.25rem">Role</th><th style="padding:.25rem">What happened</th></tr></thead><tbody>';
    (wah.turns || []).forEach(t => {
      html += '<tr style="border-top:1px solid #e4e4e7">'
        + '<td class="mono" style="padding:.35rem;vertical-align:top">' + escapeHtml(String(t.index ?? '')) + '</td>'
        + '<td class="mono" style="padding:.35rem;vertical-align:top">' + escapeHtml(t.role || '') + '</td>'
        + '<td style="padding:.35rem">' + escapeHtml(t.what_happened || '') + '</td></tr>';
    });
    html += '</tbody></table>';
    if (wah.ledger) html += '<p class="muted"><strong>Ledger:</strong> ' + escapeHtml(wah.ledger) + '</p>';
    if (wah.code_path) html += '<p class="muted mono"><strong>Code path:</strong> ' + escapeHtml(wah.code_path) + '</p>';
    if (wah.root_cause) html += '<p class="muted"><strong>Root cause:</strong> ' + escapeHtml(wah.root_cause) + '</p>';
    html += '</div>';
  }
  // Findings author report (LLM proposes · code validates)
  const fin = ev.findings || {};
  if (fin.headline || fin.verdict || (fin.what_went_wrong || fin.expected_vs_observed)) {
    html += '<div class="report-card" style="margin:.75rem 0;border-color:#c7d2fe">'
      + '<div class="row" style="justify-content:space-between">'
      + '<strong>Findings</strong>'
      + '<span class="badge ' + (fin.verdict === 'PASS' ? 'pass' : (fin.verdict === 'FAIL' ? 'fail' : 'open')) + '">'
      + escapeHtml(fin.verdict || '—') + '</span>'
      + '<span class="muted mono">source=' + escapeHtml(fin.source || '') + '</span>'
      + '</div>';
    if (fin.headline) html += '<p style="margin:.5rem 0 0;font-weight:600">' + escapeHtml(fin.headline) + '</p>';
    if ((fin.what_should_have_happened || []).length) {
      html += '<p class="muted" style="margin:.75rem 0 .25rem"><strong>What should have happened</strong></p>'
        + '<table style="width:100%;font-size:.85rem;border-collapse:collapse">'
        + '<tbody>' + fin.what_should_have_happened.map(t =>
          '<tr style="border-top:1px solid #e4e4e7"><td class="mono" style="padding:.3rem;vertical-align:top">'
          + escapeHtml(String(t.index ?? '')) + '</td><td class="mono" style="padding:.3rem;vertical-align:top">'
          + escapeHtml(t.role || '') + '</td><td style="padding:.3rem">'
          + escapeHtml(t.what_happened || '') + '</td></tr>'
        ).join('') + '</tbody></table>';
    }
    if ((fin.expected_vs_observed || []).length) {
      html += '<p class="muted" style="margin:.75rem 0 .25rem"><strong>Expected vs observed</strong></p>'
        + '<table style="width:100%;font-size:.85rem;border-collapse:collapse"><thead><tr>'
        + '<th style="text-align:left;padding:.25rem">Aspect</th><th style="text-align:left;padding:.25rem">Expected</th>'
        + '<th style="text-align:left;padding:.25rem">Observed</th><th></th></tr></thead><tbody>'
        + fin.expected_vs_observed.map(r =>
          '<tr style="border-top:1px solid #e4e4e7"><td class="mono" style="padding:.3rem">' + escapeHtml(r.aspect || '')
          + '</td><td style="padding:.3rem">' + escapeHtml(r.expected || '')
          + '</td><td style="padding:.3rem">' + escapeHtml(r.observed || '')
          + '</td><td style="padding:.3rem"><span class="badge ' + (r.match ? 'pass' : 'fail') + '">'
          + (r.match ? 'match' : 'diff') + '</span></td></tr>'
        ).join('') + '</tbody></table>';
    }
    if (fin.what_went_wrong) {
      html += '<div class="turn bad" style="margin-top:.75rem"><strong>What went wrong</strong><p style="margin:.35rem 0 0">'
        + escapeHtml(fin.what_went_wrong) + '</p></div>';
    }
    if (fin.root_cause_hypothesis) {
      html += '<p class="muted" style="margin:.5rem 0"><strong>Root cause hypothesis:</strong> '
        + escapeHtml(fin.root_cause_hypothesis) + '</p>';
    }
    if (fin.code_path_hypothesis) {
      html += '<p class="muted mono" style="margin:.35rem 0"><strong>Code path:</strong> '
        + escapeHtml(fin.code_path_hypothesis) + '</p>';
    }
    if (fin.failure_mode_slug) {
      html += '<p class="muted mono">failure_mode=' + escapeHtml(fin.failure_mode_slug) + '</p>';
    }
    if (fin.seal_recommendation) {
      html += '<p class="muted" style="margin:.5rem 0"><strong>Seal recommendation:</strong> '
        + escapeHtml(fin.seal_recommendation) + '</p>';
    }
    if (fin.error) {
      html += '<p class="muted mono">findings note: ' + escapeHtml(fin.error) + '</p>';
    }
    html += '</div>';
  }
  if ((run.failures || []).length) {
    html += '<div class="turn bad"><strong>Failures</strong><ul>'
      + run.failures.map(f => '<li class="mono">' + escapeHtml(f) + '</li>').join('')
      + '</ul></div>';
  }
  html += '<pre style="margin-top:.75rem">' + escapeHtml(JSON.stringify(ev, null, 2)) + '</pre>';
  panel.innerHTML = html;
}
async function runCandidate(steal) {
  const id = (window._candData && window._candData.scenario_id) || parseHash().id;
  if (!id) return;
  const st = document.getElementById('status');
  st.textContent = steal ? 'running planted steal…' : 'running candidate…';
  try {
    const r = await fetch('/api/candidates/' + encodeURIComponent(id) + '/run'
      + (steal ? '?steal=1' : ''), { method: 'POST' });
    const data = await r.json();
    window._candEvidence = data;
    renderEvidence(data);
    showTab('evidence');
    if (data.ok === false) {
      st.textContent = (data.error_code || data.error || 'run failed')
        + (data.stage ? ' @' + data.stage : '')
        + (data.message && data.message !== data.error ? ': ' + data.message : '');
    } else {
      st.textContent = (data.run && data.run.passed) ? 'PASS' : 'FAIL';
    }
  } catch (e) {
    st.textContent = 'network/parse: ' + String(e);
  }
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
  const checked = window._candSelected && window._candSelected.has(id) ? ' checked' : '';
  return `<div class="turn cand ${active === id ? 'active' : ''}" data-id="${escapeHtml(id)}">
    <div class="row">
      <input type="checkbox" class="chk cand-pick" data-id="${escapeHtml(id)}"${checked}
        title="Include in Selected only batch" onclick="event.stopPropagation()" />
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
function ensureCandSelected() {
  if (!window._candSelected) window._candSelected = new Set();
  return window._candSelected;
}
function updateSelCount() {
  const n = ensureCandSelected().size;
  const el = document.getElementById('candSelCount');
  if (el) el.textContent = n ? (n + ' checked') : '0 checked';
}
function wireCandCheckboxes() {
  document.querySelectorAll('.cand-pick').forEach(cb => {
    cb.onchange = () => {
      const set = ensureCandSelected();
      const id = cb.getAttribute('data-id');
      if (cb.checked) set.add(id); else set.delete(id);
      updateSelCount();
      if (window._appView === 'run') updateRunSelectedHint();
    };
  });
  updateSelCount();
}
function renderTurnTable(rows, caption) {
  if (!rows || !rows.length) return '';
  let html = (caption ? '<p class="muted" style="margin:.5rem 0 .2rem"><strong>'
    + escapeHtml(caption) + '</strong></p>' : '');
  html += '<table class="turn-table"><thead><tr><th class="idx">#</th><th class="role">Role</th>'
    + '<th>What happened</th></tr></thead><tbody>';
  rows.forEach(t => {
    html += '<tr><td class="idx">' + escapeHtml(String(t.index ?? '')) + '</td>'
      + '<td class="role">' + escapeHtml(t.role || '') + '</td>'
      + '<td>' + escapeHtml(t.what_happened || '') + '</td></tr>';
  });
  html += '</tbody></table>';
  return html;
}
function renderEvoTable(rows) {
  if (!rows || !rows.length) return '';
  let html = '<p class="muted" style="margin:.5rem 0 .2rem"><strong>Expected vs observed</strong></p>'
    + '<table class="turn-table"><thead><tr><th>Aspect</th><th>Expected</th><th>Observed</th><th></th></tr></thead><tbody>';
  rows.forEach(r => {
    html += '<tr><td class="mono">' + escapeHtml(r.aspect || '') + '</td>'
      + '<td>' + escapeHtml(r.expected || '') + '</td>'
      + '<td>' + escapeHtml(r.observed || '') + '</td>'
      + '<td><span class="badge ' + (r.match ? 'pass' : 'fail') + '">'
      + (r.match ? 'match' : 'diff') + '</span></td></tr>';
  });
  html += '</tbody></table>';
  return html;
}
function renderFindingsBlock(fin) {
  if (!fin || typeof fin !== 'object') {
    return '<p class="bl-empty">No findings object on this item yet.</p>';
  }
  const hasTables = (fin.what_should_have_happened || []).length
    || (fin.what_actually_happened || []).length
    || (fin.expected_vs_observed || []).length
    || (fin.suggested_fixes || []).length;
  const hasNarrative = !!(fin.headline || fin.verdict || fin.what_went_wrong
    || fin.root_cause_hypothesis || fin.code_path_hypothesis || fin.seal_recommendation
    || fin.note || fin.error);
  if (!hasTables && !hasNarrative) {
    return '<p class="bl-empty">Findings empty — deterministic/session author not run, or skeleton only.</p>';
  }
  const v = fin.verdict || '—';
  const vCls = v === 'PASS' ? 'pass' : (v === 'FAIL' || v === 'ERROR' ? 'fail' : 'open');
  let html = '<div class="findings-block">';
  html += '<div class="row" style="justify-content:space-between;margin-bottom:.35rem">'
    + '<h4 style="margin:0">Findings</h4>'
    + '<span class="badge ' + vCls + '">' + escapeHtml(v) + '</span>'
    + '<span class="muted mono">source=' + escapeHtml(fin.source || '') + '</span>'
    + (fin.reviewer ? '<span class="muted mono">reviewer=' + escapeHtml(fin.reviewer) + '</span>' : '')
    + '</div>';
  if (fin.headline) {
    html += '<p style="margin:.25rem 0 .5rem;font-weight:600">' + escapeHtml(fin.headline) + '</p>';
  }
  // Always show table sections with empty markers so the report card is complete
  if ((fin.what_should_have_happened || []).length) {
    html += renderTurnTable(fin.what_should_have_happened, 'What should have happened');
  } else {
    html += '<p class="muted" style="margin:.5rem 0 .2rem"><strong>What should have happened</strong></p>'
      + blEmpty('No rows — session review should fill expected trajectory');
  }
  if ((fin.what_actually_happened || []).length) {
    html += renderTurnTable(fin.what_actually_happened, 'What actually happened');
  } else {
    html += '<p class="muted" style="margin:.5rem 0 .2rem"><strong>What actually happened</strong></p>'
      + blEmpty('No rows in findings — see execution envelope below if present');
  }
  if ((fin.expected_vs_observed || []).length) {
    html += renderEvoTable(fin.expected_vs_observed);
  } else {
    html += '<p class="muted" style="margin:.5rem 0 .2rem"><strong>Expected vs observed</strong></p>'
      + blEmpty('No aspect rows yet');
  }
  if (fin.what_went_wrong) {
    html += '<div class="turn bad" style="margin-top:.5rem"><strong>What went wrong</strong>'
      + '<p style="margin:.35rem 0 0">' + escapeHtml(fin.what_went_wrong) + '</p></div>';
  } else {
    html += '<p class="muted" style="margin:.45rem 0"><strong>What went wrong:</strong> '
      + '<span class="bl-empty">—</span></p>';
  }
  html += blKv([
    ['Root cause hypothesis', fin.root_cause_hypothesis || ''],
    ['Code path hypothesis', fin.code_path_hypothesis || ''],
    ['Failure mode slug', fin.failure_mode_slug || ''],
    ['Seal recommendation', fin.seal_recommendation || ''],
    ['Classification (findings)', fin.classification || ''],
    ['Confidence', fin.confidence != null && fin.confidence !== '' ? String(fin.confidence) : ''],
    ['Note', fin.note || ''],
    ['Error', fin.error || ''],
  ]);
  if ((fin.suggested_fixes || []).length) {
    html += '<p class="muted" style="margin:.65rem 0 .25rem"><strong>Suggested fixes</strong></p><ul>';
    fin.suggested_fixes.forEach(fx => {
      html += '<li><span class="badge open">' + escapeHtml(fx.priority || 'P1') + '</span> '
        + '<strong>' + escapeHtml(fx.title || '') + '</strong>'
        + (fx.layer ? ' <span class="muted mono">[' + escapeHtml(fx.layer) + ']</span>' : '')
        + '<div class="muted">' + escapeHtml(fx.action || '') + '</div>'
        + ((fx.files || []).length
          ? '<div class="mono" style="font-size:.75rem">' + escapeHtml((fx.files || []).join(', ')) + '</div>'
          : '')
        + (fx.ratchet ? '<div class="muted mono">ratchet: ' + escapeHtml(fx.ratchet) + '</div>' : '')
        + '</li>';
    });
    html += '</ul>';
  }
  html += '</div>';
  return html;
}
function renderBatchReport(rep) {
  const box = document.getElementById('candBatchReport');
  if (!box) return;
  if (!rep) { box.style.display = 'none'; return; }
  box.style.display = 'block';
  if (rep.ok === false && !(rep.results || []).length) {
    box.innerHTML = '<div class="turn bad"><strong>Batch failed</strong><div class="mono">'
      + escapeHtml(rep.error || 'unknown') + '</div>'
      + (rep.host && rep.host.hint ? '<p class="muted">' + escapeHtml(rep.host.hint) + '</p>' : '')
      + '</div>';
    return;
  }
  const s = rep.summary || {};
  const badgeCls = (s.failed || 0) + (s.errors || 0) === 0 && (s.total || 0) > 0
    ? 'pass' : ((s.passed || 0) > 0 ? 'partial' : 'fail');
  // Organize by scenario_id (stable sort: errors, fails, then pass)
  const results = (rep.results || []).slice().sort((a, b) => {
    const rank = (r) => (!r.ok ? 0 : (r.passed ? 2 : 1));
    const d = rank(a) - rank(b);
    if (d !== 0) return d;
    return String(a.scenario_id || '').localeCompare(String(b.scenario_id || ''));
  });
  let html = '<div class="row" style="justify-content:space-between">'
    + '<span class="sum">Results by scenario</span>'
    + '<span class="badge ' + badgeCls + '">' + escapeHtml(rep.adapter || '') + '</span>'
    + '</div>';
  html += '<div class="row" style="margin:.5rem 0">'
    + '<span class="badge pass">' + (s.passed || 0) + ' pass</span>'
    + '<span class="badge fail">' + (s.failed || 0) + ' fail</span>'
    + '<span class="badge open">' + (s.errors || 0) + ' error</span>'
    + '<span class="muted mono">total ' + (s.total || 0) + '</span>'
    + (rep.account ? '<span class="muted mono">account=' + escapeHtml(rep.account) + '</span>' : '')
    + '</div>';
  if (rep.note) html += '<p class="muted" style="margin:.25rem 0 .5rem">' + escapeHtml(rep.note) + '</p>';
  html += '<p class="muted" style="font-size:.8rem;margin:0 0 .5rem">Expand a scenario for trajectory tables + LLM findings.</p>';

  results.forEach((r, i) => {
    const cls = !r.ok ? 'bad' : (r.passed ? 'ok' : 'bad');
    const mark = !r.ok ? 'ERROR' : (r.passed ? 'PASS' : 'FAIL');
    const badgeClass = (r.passed && r.ok) ? 'pass' : 'fail';
    const fin = r.findings || {};
    const openFirst = i === 0 && results.length <= 5;
    html += '<details class="scenario-result ' + cls + '"' + (openFirst ? ' open' : '') + '>';
    html += '<summary>'
      + '<span class="badge ' + badgeClass + '">' + mark + '</span>'
      + '<a class="mono" href="#/candidate/' + encodeURIComponent(r.scenario_id) + '/evidence" '
      + 'onclick="event.stopPropagation()">' + escapeHtml(r.scenario_id) + '</a>';
    if (r.failure_mode) {
      html += '<span class="muted mono">mode=' + escapeHtml(r.failure_mode) + '</span>';
    }
    if (fin.headline) {
      html += '<span class="muted" style="flex:1;min-width:8rem">'
        + escapeHtml(String(fin.headline).slice(0, 100))
        + (String(fin.headline).length > 100 ? '…' : '') + '</span>';
    } else if (r.headline) {
      html += '<span class="muted">' + escapeHtml(String(r.headline).slice(0, 100)) + '</span>';
    }
    html += '</summary><div class="scenario-result-body">';

    // Scenario identity
    html += '<p class="muted" style="margin:0 0 .5rem"><strong>Scenario</strong> · '
      + '<span class="mono">' + escapeHtml(r.scenario_id) + '</span>';
    if (r.incident_id) html += ' · incident=<span class="mono">' + escapeHtml(r.incident_id) + '</span>';
    html += '</p>';
    if (r.scenario_purpose) {
      html += '<p class="muted" style="margin:0 0 .35rem"><strong>Purpose:</strong> '
        + escapeHtml(r.scenario_purpose) + '</p>';
    }
    if (r.user_trajectory) {
      html += '<p class="muted" style="margin:0 0 .35rem"><strong>User trajectory:</strong> '
        + escapeHtml(r.user_trajectory) + '</p>';
    }
    if (r.thread_id) {
      html += '<p class="muted mono" style="margin:0 0 .25rem">thread=' + escapeHtml(r.thread_id) + '</p>';
    }
    if (r.evidence_path) {
      html += '<p class="muted mono" style="margin:0 0 .35rem;font-size:.75rem">'
        + escapeHtml(r.evidence_path) + '</p>';
    }
    if (r.error) {
      html += '<div class="turn bad"><strong>Run error</strong><div class="mono">'
        + escapeHtml(r.error) + '</div></div>';
    }
    if ((r.failures || []).length) {
      html += '<div class="turn bad"><strong>Invariant failures</strong><ul>'
        + r.failures.map(f => '<li class="mono">' + escapeHtml(f) + '</li>').join('')
        + '</ul></div>';
    }
    // Authored / observed turn table from evidence when findings thin
    const wah = r.what_actually_happened || {};
    if ((wah.turns || []).length && !(fin.what_actually_happened || []).length) {
      html += renderTurnTable(wah.turns, 'What actually happened (evidence)');
      if (wah.ledger) html += '<p class="muted"><strong>Ledger:</strong> ' + escapeHtml(wah.ledger) + '</p>';
      if (wah.code_path) html += '<p class="muted mono"><strong>Code path:</strong> ' + escapeHtml(wah.code_path) + '</p>';
      if (wah.root_cause) html += '<p class="muted"><strong>Root cause:</strong> ' + escapeHtml(wah.root_cause) + '</p>';
    }
    // Full findings (LLM / deterministic) — agreed format
    html += renderFindingsBlock(fin);
    html += '<div class="row" style="margin-top:.65rem">'
      + '<a class="deep-link" href="#/candidate/' + encodeURIComponent(r.scenario_id) + '/trajectory">Trajectory</a>'
      + '<a class="deep-link" href="#/candidate/' + encodeURIComponent(r.scenario_id) + '/evidence">Evidence</a>'
      + '<a class="deep-link" href="#/candidate/' + encodeURIComponent(r.scenario_id) + '/scenario">Scenario YAML</a>'
      + '</div>';
    html += '</div></details>';
  });
  box.innerHTML = html;
}
async function loadHostRunnerStatus() {
  const el = document.getElementById('hostRunnerMeta');
  try {
    const r = await fetch('/api/host-runner');
    const data = await r.json();
    window._hostRunner = data;
    if (!el) return;
    if (data.available) {
      el.textContent = 'host ready · ' + (data.account || '') + ' · ' + (data.base_url || '');
      el.style.color = data.password_set ? '#047857' : '#c2410c';
      if (!data.password_set) el.textContent += ' · set CONJECTURE_HOST_PASSWORD';
    } else {
      el.textContent = 'host not wired · geometry only';
      el.title = data.hint || data.error || '';
    }
  } catch (e) {
    if (el) el.textContent = 'host status failed';
  }
}
function renderCleanupReport(rep) {
  const box = document.getElementById('candCleanupReport');
  if (!box) return;
  if (!rep) { box.style.display = 'none'; return; }
  box.style.display = 'block';
  if (rep.ok === false) {
    box.innerHTML = '<div class="turn bad"><strong>Cleanup failed</strong><div class="mono">'
      + escapeHtml(rep.error || 'unknown') + '</div></div>';
    return;
  }
  let html = '<div class="row" style="justify-content:space-between">'
    + '<span class="sum">' + (rep.dry_run ? 'Cleanup preview' : 'Cleanup done') + '</span>'
    + '<span class="muted mono">account=' + escapeHtml(rep.account || '') + '</span></div>';
  html += '<div class="row" style="margin:.5rem 0">'
    + '<span class="badge open">' + (rep.matched_count || 0) + ' matched</span>'
    + '<span class="badge fail">' + (rep.empty_matched || 0) + ' empty</span>'
    + (rep.dry_run
      ? '<span class="muted">dry-run — nothing archived</span>'
      : '<span class="badge pass">' + (rep.archived_count || 0) + ' archived</span>')
    + ((rep.error_count || 0) ? '<span class="badge fail">' + rep.error_count + ' errors</span>' : '')
    + '</div>';
  if (rep.note) html += '<p class="muted" style="margin:.25rem 0">' + escapeHtml(rep.note) + '</p>';
  const rows = rep.matched || [];
  if (rows.length) {
    html += '<table style="width:100%;font-size:.8rem;border-collapse:collapse;margin-top:.5rem">'
      + '<thead><tr><th style="text-align:left;padding:.25rem">Title</th>'
      + '<th style="text-align:left;padding:.25rem">Msgs</th>'
      + '<th style="text-align:left;padding:.25rem">Id</th></tr></thead><tbody>';
    rows.slice(0, 40).forEach(r => {
      html += '<tr style="border-top:1px solid #e4e4e7">'
        + '<td class="mono" style="padding:.3rem">' + escapeHtml(r.title || '') + '</td>'
        + '<td style="padding:.3rem">' + escapeHtml(String(r.message_count ?? '—')) + '</td>'
        + '<td class="mono" style="padding:.3rem">' + escapeHtml(r.conversation_id || '') + '</td></tr>';
    });
    if (rows.length > 40) {
      html += '<tr><td colspan="3" class="muted" style="padding:.3rem">… +'
        + (rows.length - 40) + ' more</td></tr>';
    }
    html += '</tbody></table>';
  } else {
    html += '<p class="muted">No Conjecture-titled conversations matched.</p>';
  }
  box.innerHTML = html;
}
async function runCleanup(dryRun) {
  showAppView('admin');
  const st = document.getElementById('status');
  const emptyOnly = !!(document.getElementById('cleanupEmptyOnly')
    && document.getElementById('cleanupEmptyOnly').checked);
  if (!dryRun) {
    const nHint = emptyOnly ? 'empty Conjecture shells' : 'all Conjecture-titled runs (cbr- / conjecture*)';
    if (!window.confirm('Archive ' + nHint + ' for the host account? Soft-delete only (product API).')) {
      return;
    }
  }
  st.textContent = dryRun ? 'preview cleanup…' : 'cleaning up…';
  try {
    const r = await fetch('/api/cleanup-conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dry_run: !!dryRun,
        empty_only: emptyOnly,
        max_delete: 200,
      }),
    });
    const rep = await r.json();
    renderCleanupReport(rep);
    st.textContent = rep.ok === false
      ? (rep.error || 'cleanup failed')
      : (dryRun
        ? ('preview: ' + (rep.matched_count || 0) + ' match · ' + (rep.empty_matched || 0) + ' empty')
        : ('archived ' + (rep.archived_count || 0) + ' / ' + (rep.matched_count || 0)));
  } catch (e) {
    st.textContent = String(e);
    renderCleanupReport({ ok: false, error: String(e) });
  }
}
async function runBatch() {
  const st = document.getElementById('status');
  const btn = document.getElementById('btnCandBatchRun');
  const mode = (document.querySelector('input[name="candSelMode"]:checked') || {}).value || 'ids';
  const adapter = document.getElementById('candAdapter').value || 'geometry';
  const steal = !!(document.getElementById('candBatchSteal') && document.getElementById('candBatchSteal').checked);
  let ids = [];
  if (mode === 'ids') {
    ids = Array.from(ensureCandSelected());
    if (!ids.length) {
      st.textContent = 'No checkboxes selected. Open Candidates, tick rows, then Selected only → Run batch.';
      showAppView('run');
      updateRunSelectedHint();
      return;
    }
  }
  if (mode === 'all' && adapter === 'host') {
    const vis = (window._candVisibleIds || []).length;
    if (vis > 15 && !window.confirm(
      'Host HTTP on ~' + vis + ' filtered scenarios will burn LLM quota and may hit the hourly limit (429). Continue?'
    )) {
      return;
    }
  }
  const body = {
    selection: mode,
    ids: ids,
    adapter: adapter,
    steal: steal,
    filters: {
      seal: document.getElementById('candSeal').value || '',
      priority: document.getElementById('candPri').value || '',
      source: document.getElementById('candSrc').value || '',
      q: document.getElementById('candQ').value.trim() || '',
      limit: 50,
    },
    max_scenarios: 50,
  };
  st.textContent = 'running batch (' + adapter + ')…';
  if (btn) btn.disabled = true;
  try {
    const r = await fetch('/api/candidates/run-batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const rep = await r.json();
    window._batchReport = rep;
    // Remember failures/errors for "Re-run last failures"
    window._lastFailedIds = (rep.results || [])
      .filter(r => !r.passed || !r.ok || r.error)
      .map(r => r.scenario_id)
      .filter(Boolean);
    const failBtn = document.getElementById('btnRunFailedOnly');
    if (failBtn) {
      failBtn.style.display = window._lastFailedIds.length ? 'inline-block' : 'none';
      failBtn.textContent = 'Re-run last failures (' + window._lastFailedIds.length + ')';
    }
    showAppView('run');
    renderBatchReport(rep);
    updateRunSelectedHint();
    const s = rep.summary || {};
    st.textContent = rep.ok === false && !(rep.results || []).length
      ? (rep.error || 'batch failed')
      : ('batch: ' + (s.passed || 0) + ' pass / ' + (s.failed || 0) + ' fail / '
         + (s.errors || 0) + ' err · n=' + (s.total || 0));
  } catch (e) {
    st.textContent = String(e);
    showAppView('run');
    renderBatchReport({ ok: false, error: String(e), results: [] });
  } finally {
    if (btn) btn.disabled = false;
  }
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
  wireCandCheckboxes();
  window._candVisibleIds = (data.scenarios || []).map(s => s.scenario_id);
}
async function openCandidate(id, tab) {
  tab = tab || 'trajectory';
  showAppView('candidates');
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
  // load latest evidence if any
  fetch('/api/candidates/' + encodeURIComponent(id) + '/evidence')
    .then(r => r.json())
    .then(evlist => {
      if (evlist && evlist.runs && evlist.runs[0]) {
        renderEvidence(evlist.runs[0]);
      } else {
        renderEvidence(null);
      }
    }).catch(() => renderEvidence(null));
  showTab(tab);
  window._candData = data;
}
document.getElementById('btnCandRun').onclick = () => runCandidate(false);
document.getElementById('btnCandSteal').onclick = () => runCandidate(true);
document.getElementById('btnCandFindings').onclick = async () => {
  const id = (window._candData && window._candData.scenario_id) || parseHash().id;
  if (!id) return;
  const st = document.getElementById('status');
  st.textContent = 'authoring findings…';
  try {
    const r = await fetch('/api/candidates/' + encodeURIComponent(id) + '/findings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ use_llm: true }),
    });
    const data = await r.json();
    if (data.evidence) {
      window._candEvidence = data.evidence;
      renderEvidence(data.evidence);
    } else {
      renderEvidence({ ok: false, error: data.error || 'findings failed', findings: data.findings });
    }
    showTab('evidence');
    st.textContent = (data.findings && data.findings.verdict)
      ? ('findings ' + data.findings.verdict + ' · ' + (data.findings.source || ''))
      : (data.error || 'findings done');
  } catch (e) {
    st.textContent = String(e);
  }
};
document.getElementById('btnCandRunHost').onclick = async () => {
  const id = (window._candData && window._candData.scenario_id) || parseHash().id;
  if (!id) return;
  const st = document.getElementById('status');
  st.textContent = 'running host HTTP…';
  try {
    const r = await fetch('/api/candidates/run-batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ selection: 'ids', ids: [id], adapter: 'host', max_scenarios: 1 }),
    });
    const rep = await r.json();
    showAppView('run');
    renderBatchReport(rep);
    const row = (rep.results || [])[0];
    if (row && row.ok !== false && !row.error) {
      const er = await fetch('/api/candidates/' + encodeURIComponent(id) + '/evidence');
      const evlist = await er.json();
      if (evlist && evlist.runs && evlist.runs[0]) {
        window._candEvidence = evlist.runs[0];
        renderEvidence(evlist.runs[0]);
      }
      showTab('evidence');
      showAppView('candidates');
      st.textContent = (row.passed ? 'PASS' : 'FAIL')
        + ' host · thread=' + (row.thread_id || '—');
    } else {
      // Surface error contract on Evidence tab so single host runs are debuggable
      const errEv = {
        ok: false,
        error: (row && (row.error_code || row.error)) || rep.error || 'host_run_failed',
        error_code: (row && row.error_code) || rep.error || 'host_run_failed',
        message: (row && row.error) || rep.error || rep.message || 'host run failed',
        stage: (row && row.stage) || 'host',
        scenario_id: id,
        adapter: (row && row.adapter) || 'host',
        traceback: row && row.traceback,
        findings: (row && row.findings) || {
          verdict: 'ERROR',
          headline: 'Host run failed',
          what_went_wrong: (row && row.error) || rep.error || '',
          source: 'runtime',
        },
        run: { passed: false, failures: [(row && row.error) || rep.error || 'host failed'] },
      };
      window._candEvidence = errEv;
      showAppView('candidates');
      renderEvidence(errEv);
      showTab('evidence');
      st.textContent = (errEv.error_code || 'ERROR')
        + (errEv.stage ? ' @' + errEv.stage : '')
        + ': ' + String(errEv.message || '').slice(0, 120);
    }
  } catch (e) {
    st.textContent = 'network/parse: ' + String(e);
  }
};
document.getElementById('btnCandBatchRun').onclick = () => runBatch();
document.getElementById('btnCleanupPreview').onclick = () => runCleanup(true);
document.getElementById('btnCleanupRun').onclick = () => runCleanup(false);
document.getElementById('btnCandSelectVisible').onclick = () => {
  const set = ensureCandSelected();
  (window._candVisibleIds || []).forEach(id => set.add(id));
  document.querySelectorAll('.cand-pick').forEach(cb => { cb.checked = true; });
  // Prefer Selected only after mass-select
  const idsRadio = document.getElementById('candSelModeIds');
  if (idsRadio) idsRadio.checked = true;
  updateRunSelectedHint();
};
document.getElementById('btnCandClearSel').onclick = () => {
  ensureCandSelected().clear();
  document.querySelectorAll('.cand-pick').forEach(cb => { cb.checked = false; });
  updateRunSelectedHint();
};
document.getElementById('btnRunFailedOnly').onclick = () => {
  const fails = window._lastFailedIds || [];
  if (!fails.length) {
    document.getElementById('status').textContent = 'no last failures to re-run';
    return;
  }
  const set = ensureCandSelected();
  set.clear();
  fails.forEach(id => set.add(id));
  const idsRadio = document.getElementById('candSelModeIds');
  if (idsRadio) idsRadio.checked = true;
  updateRunSelectedHint();
  document.getElementById('status').textContent =
    'selected ' + fails.length + ' last failure(s) — click Run batch';
};
['candSelModeIds', 'candSelModeAll'].forEach(id => {
  const el = document.getElementById(id);
  if (el) el.onchange = () => updateRunSelectedHint();
});
document.getElementById('candAdapter').onchange = () => {
  const isGeo = document.getElementById('candAdapter').value === 'geometry';
  const lab = document.getElementById('candStealLabel');
  if (lab) lab.style.display = isGeo ? 'inline-flex' : 'none';
};
function routeFromHash() {
  const parsed = parseHash();
  const { view, id, tab, lawId, registry, mode, params, programId } = parsed;
  if (id) {
    openCandidate(id, tab);
    return;
  }
  if (programId) window._programId = programId;
  showAppView(view || 'home');
  if ((view || 'home') === 'candidates') {
    document.getElementById('candDetail').style.display = 'none';
    document.getElementById('candList').style.display = 'block';
    // Deep-link: #/candidates?mode=<registry_id>
    if (mode || (params && params.mode)) {
      const m = mode || params.mode;
      const q = document.getElementById('candQ');
      if (q && m) q.value = m;
    }
    loadCandidates();
  }
  if (view === 'run') updateRunSelectedHint();
  if (view === 'backlog') loadBacklog();
  if (view === 'admin') loadAdminStatus();
  if (view === 'demo') loadStory();
  if (view === 'laws') {
    loadLaws(lawId || null);
    if (lawId) showLawDetail(lawId);
  }
  if (view === 'seek') {
    loadSeek(registry || (params && params.registry) || null);
  }
  if (view === 'home') loadHome();
  if (view && String(view).startsWith('program-') && (programId || PROGRAM_NAV[view])) {
    loadProgram(programId || PROGRAM_NAV[view]);
  }
}
document.getElementById('btnCandReload').onclick = () => loadCandidates();
document.getElementById('btnAdminRefresh').onclick = () => loadAdminStatus();
const btnLog = document.getElementById('btnRunnerLogRefresh');
if (btnLog) btnLog.onclick = () => loadRunnerLog();
document.getElementById('btnBacklogRefresh').onclick = () => loadBacklog();
document.getElementById('btnGoRunFromList').onclick = () => {
  location.hash = '#/run';
};
document.getElementById('btnGoCandidatesFromRun').onclick = () => {
  location.hash = '#/candidates';
};
document.getElementById('btnOpenInRunTab').onclick = () => {
  const id = (window._candData && window._candData.scenario_id) || parseHash().id;
  if (id) {
    ensureCandSelected().add(id);
    updateSelCount();
  }
  location.hash = '#/run';
  updateRunSelectedHint();
};
const btnOpenVerdict = document.getElementById('btnOpenVerdict');
if (btnOpenVerdict) {
  btnOpenVerdict.onclick = () => { location.hash = '#/verdict'; };
}
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
// Quality Console: Home / Laws / Seek controls
document.querySelectorAll('[data-goto]').forEach(btn => {
  btn.onclick = () => { location.hash = '#/' + btn.getAttribute('data-goto'); };
});
const btnHomeRefresh = document.getElementById('btnHomeRefresh');
if (btnHomeRefresh) btnHomeRefresh.onclick = () => loadQualitySnapshot({ rebuild: true }).then(() => loadHome());
const btnReloadViz = document.getElementById('btnReloadViz');
if (btnReloadViz) {
  btnReloadViz.onclick = () => {
    const fr = document.getElementById('homeVizFrame');
    if (fr) fr.src = '/surface-map?t=' + Date.now();
  };
}
const btnJumpViz = document.getElementById('btnJumpViz');
if (btnJumpViz) {
  btnJumpViz.onclick = (e) => {
    e.preventDefault();
    location.hash = '#/home';
    showAppView('home');
    const el = document.getElementById('homeVizCard');
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };
}
const btnHomeRunSeek = document.getElementById('btnHomeRunSeek');
if (btnHomeRunSeek) btnHomeRunSeek.onclick = async () => {
  location.hash = '#/seek';
  await runSeekBattery({ quick: true, live: false });
};
const btnLawsReload = document.getElementById('btnLawsReload');
if (btnLawsReload) btnLawsReload.onclick = async () => {
  await loadQualitySnapshot({ rebuild: true });
  loadLaws(window._lawFocusId);
};
const btnLawsShowAll = document.getElementById('btnLawsShowAll');
if (btnLawsShowAll) {
  btnLawsShowAll.onclick = () => {
    ['lawsQ','lawsLife','lawsCategory','lawsPlane','lawsHealth'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
    ['lawsSoakOnly','lawsSurfaceRed'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.checked = false;
    });
    renderLawsTable(window._lawFocusId);
  };
}
['lawsQ','lawsLife','lawsCategory','lawsPlane','lawsHealth','lawsSoakOnly','lawsSurfaceRed'].forEach(id => {
  const el = document.getElementById(id);
  if (!el) return;
  el.onchange = () => renderLawsTable(window._lawFocusId);
  el.oninput = () => {
    clearTimeout(window._lawsT);
    window._lawsT = setTimeout(() => renderLawsTable(window._lawFocusId), 150);
  };
});
const btnSeekReload = document.getElementById('btnSeekReload');
if (btnSeekReload) btnSeekReload.onclick = () => loadSeek(window._seekFilterReg);
const btnSeekRunQuick = document.getElementById('btnSeekRunQuick');
if (btnSeekRunQuick) btnSeekRunQuick.onclick = () => runSeekBattery({ quick: true, live: false });
const btnSeekRunFull = document.getElementById('btnSeekRunFull');
if (btnSeekRunFull) btnSeekRunFull.onclick = () => runSeekBattery({ quick: false, live: false });
const btnSeekRunLive = document.getElementById('btnSeekRunLive');
if (btnSeekRunLive) btnSeekRunLive.onclick = () => runSeekBattery({ quick: true, live: true });
const btnSeekStop = document.getElementById('btnSeekStop');
if (btnSeekStop) btnSeekStop.onclick = () => stopSeekBattery();
['seekLayer','seekStatus'].forEach(id => {
  const el = document.getElementById(id);
  if (el) el.onchange = () => renderSeekChecks();
});
const seekQ = document.getElementById('seekQ');
if (seekQ) seekQ.oninput = () => {
  clearTimeout(window._seekQT);
  window._seekQT = setTimeout(renderSeekChecks, 150);
};
window.addEventListener('hashchange', routeFromHash);
loadHostRunnerStatus();
// Warm chrome from snapshot (non-blocking)
loadQualitySnapshot({}).catch(() => {});
routeFromHash();
if ((parseHash().view || 'home') === 'demo') loadStory();
</script>
</body>
</html>
"""
    # Portable brand: default "session coding agent"; hosts set
    # CONJECTURE_SESSION_AGENT_LABEL in env (never bake vendor names into package).
    try:
        from conjecture_behaviour_runner.review_backlog import session_agent_label

        label = session_agent_label()
    except Exception:  # noqa: BLE001
        label = (
            (os.environ.get("CONJECTURE_SESSION_AGENT_LABEL") or "").strip()
            or "session coding agent"
        )
    # Escape for HTML text nodes / attributes
    safe = (
        label.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    # JS string for window._sessionAgentLabel
    js_safe = (
        label.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", " ")
    )
    html = html.replace("__SESSION_AGENT_LABEL__", safe)
    # Inject early so backlog render can use it
    inject = (
        f"<script>window._sessionAgentLabel = '{js_safe}';</script>\n"
    )
    if "<head>" in html:
        html = html.replace("<head>", "<head>\n" + inject, 1)
    else:
        html = inject + html
    return html.encode("utf-8")


def _static_dir() -> Path:
    return Path(__file__).resolve().parent / "static"


def _serve_static_file(
    handler: BaseHTTPRequestHandler, *, rel: str, content_type: str
) -> bool:
    """Serve a file from package static/. Returns True if handled."""
    base = _static_dir()
    # Allow only basename paths under static/
    name = Path(rel).name
    path = base / name
    if not path.is_file():
        # Prefer monorepo frontend favicon when package static missing
        mono = Path.cwd() / "frontend" / "public" / name
        if mono.is_file():
            path = mono
        else:
            return False
    try:
        body = path.read_bytes()
    except OSError:
        return False
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "public, max-age=3600")
    handler.end_headers()
    handler.wfile.write(body)
    return True


def _surface_map_path() -> Path | None:
    """Host monorepo surface×agent×FM heat map (artifact), if present."""
    candidates = (
        Path.cwd()
        / "conjecture_host"
        / "artifacts"
        / "surface_map"
        / "surface_area_map.html",
        Path(__file__).resolve().parents[4]
        / "conjecture_host"
        / "artifacts"
        / "surface_map"
        / "surface_area_map.html",
    )
    for p in candidates:
        try:
            if p.is_file():
                return p
        except OSError:
            continue
    return None


def _serve_surface_map(handler: BaseHTTPRequestHandler) -> bool:
    path = _surface_map_path()
    if path is None:
        return False
    try:
        body = path.read_bytes()
    except OSError:
        return False
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
    handler.end_headers()
    handler.wfile.write(body)
    return True


def _make_handler() -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:  # quieter default
            if "/api/" in (args[0] if args else ""):
                super().log_message(fmt, *args)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query or "")
            # Browser tab icon (Bot0 mark reused)
            if path in ("/favicon.ico", "/favicon.svg", "/static/favicon.svg"):
                if _serve_static_file(
                    self, rel="favicon.svg", content_type="image/svg+xml"
                ):
                    return
            if path in ("/static/bot0-logo.png", "/apple-touch-icon.png"):
                if _serve_static_file(
                    self, rel="bot0-logo.png", content_type="image/png"
                ):
                    return
            if path in ("/", "/index.html"):
                body = _html_page()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                self.end_headers()
                self.wfile.write(body)
                return
            # Host surface area heat map (same port as console — no :8766 required)
            if path in (
                "/surface-map",
                "/surface-map.html",
                "/surface_area_map.html",
                "/docs/surface-map",
            ):
                if _serve_surface_map(self):
                    return
                _json_response(
                    self,
                    404,
                    {
                        "error": "surface_map_missing",
                        "hint": (
                            "Generate host artifact: "
                            "host_artifacts/surface_map/surface_area_map.html"
                        ),
                    },
                )
                return
            if path == "/api/logs":
                from conjecture_behaviour_runner.runner_log import recent_logs

                def _one_log(key: str) -> Optional[str]:
                    vals = qs.get(key) or []
                    return vals[0] if vals else None

                try:
                    lim = int(_one_log("limit") or "80")
                except ValueError:
                    lim = 80
                entries = recent_logs(limit=lim, level=_one_log("level"))
                _json_response(
                    self,
                    200,
                    {
                        "ok": True,
                        "count": len(entries),
                        "level": _one_log("level"),
                        "entries": entries,
                    },
                )
                return
            if path == "/api/story":
                from conjecture_behaviour_runner.path_faithful import sole_continue_story

                _json_response(self, 200, sole_continue_story())
                return
            if path == "/api/host-runner":
                from conjecture_behaviour_runner.candidate_run import host_runner_status

                _json_response(self, 200, host_runner_status())
                return
            # Quality Console: law_seek + snapshot + laws board
            if path == "/api/law-seek":
                from conjecture_behaviour_runner.quality_console_api import get_law_seek

                def _one_ls(key: str) -> Optional[str]:
                    vals = qs.get(key) or []
                    return vals[0] if vals else None

                run = (_one_ls("run") or "") in ("1", "true", "yes")
                live = (_one_ls("live") or "") in ("1", "true", "yes")
                quick_raw = (_one_ls("quick") or "1").lower()
                quick = quick_raw not in ("0", "false", "no")
                try:
                    payload = get_law_seek(run=run, live=live, quick=quick)
                    code = 200 if payload.get("ok") or payload.get("available") else 503
                    _json_response(self, code, payload)
                except Exception as exc:  # noqa: BLE001
                    _json_response(self, 500, {"ok": False, "error": str(exc)})
                return
            if path == "/api/quality-snapshot":
                from conjecture_behaviour_runner.quality_console_api import (
                    get_quality_snapshot,
                )

                def _one_qs(key: str) -> Optional[str]:
                    vals = qs.get(key) or []
                    return vals[0] if vals else None

                rebuild = (_one_qs("rebuild") or "") in ("1", "true", "yes")
                run_seek = (_one_qs("run_seek") or "") in ("1", "true", "yes")
                live = (_one_qs("live") or "") in ("1", "true", "yes")
                quick_raw = (_one_qs("quick") or "1").lower()
                quick = quick_raw not in ("0", "false", "no")
                try:
                    payload = get_quality_snapshot(
                        rebuild=rebuild,
                        run_seek=run_seek,
                        live=live,
                        quick=quick,
                    )
                    code = 200 if payload.get("ok") or payload.get("available") else 503
                    _json_response(self, code, payload)
                except Exception as exc:  # noqa: BLE001
                    _json_response(self, 500, {"ok": False, "error": str(exc)})
                return
            if path == "/api/laws":
                from conjecture_behaviour_runner.quality_console_api import get_laws

                def _one_law(key: str) -> Optional[str]:
                    vals = qs.get(key) or []
                    return vals[0] if vals else None

                try:
                    payload = get_laws(registry_id=_one_law("id") or _one_law("registry_id"))
                    code = 200 if payload.get("ok") else 404
                    _json_response(self, code, payload)
                except Exception as exc:  # noqa: BLE001
                    _json_response(self, 500, {"ok": False, "error": str(exc)})
                return
            if path.startswith("/api/laws/"):
                from conjecture_behaviour_runner.quality_console_api import get_laws

                rid = unquote(path[len("/api/laws/") :].strip("/"))
                try:
                    payload = get_laws(registry_id=rid)
                    code = 200 if payload.get("ok") else 404
                    _json_response(self, code, payload)
                except Exception as exc:  # noqa: BLE001
                    _json_response(self, 500, {"ok": False, "error": str(exc)})
                return
            if path in ("/api/admin/status", "/api/admin/env"):
                from conjecture_behaviour_runner.console_admin import (
                    console_admin_status,
                )

                try:
                    _json_response(self, 200, console_admin_status())
                except Exception as exc:  # noqa: BLE001
                    _json_response(self, 500, {"ok": False, "error": str(exc)})
                return
            if path == "/api/backlog":
                from conjecture_behaviour_runner.review_backlog import list_backlog

                def _one(key: str) -> Optional[str]:
                    vals = qs.get(key) or []
                    return vals[0] if vals else None

                try:
                    lim = int(_one("limit") or "100")
                except ValueError:
                    lim = 100
                _json_response(
                    self,
                    200,
                    list_backlog(
                        status=_one("status"),
                        classification=_one("classification"),
                        limit=lim,
                    ),
                )
                return
            if path.startswith("/api/backlog/"):
                from conjecture_behaviour_runner.review_backlog import get_backlog_item

                bid = unquote(path[len("/api/backlog/") :].strip("/"))
                payload = get_backlog_item(bid)
                _json_response(self, 200 if payload.get("ok") else 404, payload)
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
                rest = unquote(path[len("/api/candidates/") :].strip("/"))
                if rest.endswith("/evidence"):
                    from conjecture_behaviour_runner.candidate_run import list_evidence

                    sid = rest[: -len("/evidence")].strip("/")
                    payload = list_evidence(sid)
                    _json_response(self, 200 if payload.get("ok") else 404, payload)
                    return
                from conjecture_behaviour_runner.candidates_ui import get_candidate

                payload = get_candidate(rest)
                _json_response(self, 200 if payload.get("ok") else 404, payload)
                return
            _json_response(self, 404, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query or "")
            try:
                if path == "/api/law-seek/stop":
                    from conjecture_behaviour_runner.quality_console_api import (
                        request_law_seek_stop,
                    )

                    _read_json_body(self)  # consume body if any
                    _json_response(self, 200, request_law_seek_stop())
                    return
                if path in ("/api/law-seek/run", "/api/law-seek"):
                    from conjecture_behaviour_runner.quality_console_api import (
                        get_law_seek,
                    )

                    body = _read_json_body(self)
                    live = bool(body.get("live"))
                    if "live" not in body:
                        live = (qs.get("live") or [""])[0] in ("1", "true", "yes")
                    quick = body.get("quick")
                    if quick is None:
                        quick_raw = (qs.get("quick") or ["1"])[0].lower()
                        quick = quick_raw not in ("0", "false", "no")
                    else:
                        quick = bool(quick)
                    skip_scripts = bool(body.get("skip_scripts"))
                    try:
                        payload = get_law_seek(
                            run=True,
                            live=live,
                            quick=bool(quick),
                            skip_scripts=skip_scripts,
                        )
                        code = 200 if payload.get("ok") else 500
                        _json_response(self, code, payload)
                    except Exception as exc:  # noqa: BLE001
                        _json_response(self, 500, {"ok": False, "error": str(exc)})
                    return
                if path == "/api/quality-snapshot":
                    from conjecture_behaviour_runner.quality_console_api import (
                        get_quality_snapshot,
                    )

                    body = _read_json_body(self)
                    try:
                        payload = get_quality_snapshot(
                            rebuild=bool(body.get("rebuild", True)),
                            run_seek=bool(body.get("run_seek")),
                            live=bool(body.get("live")),
                            quick=bool(body.get("quick", True)),
                        )
                        code = 200 if payload.get("ok") else 503
                        _json_response(self, code, payload)
                    except Exception as exc:  # noqa: BLE001
                        _json_response(self, 500, {"ok": False, "error": str(exc)})
                    return
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
                if path.startswith("/api/backlog/") and path.rstrip("/").endswith(
                    "/update"
                ):
                    from conjecture_behaviour_runner.review_backlog import (
                        update_backlog_item,
                    )

                    mid = path[len("/api/backlog/") :].strip("/")
                    if mid.endswith("/update"):
                        mid = mid[: -len("/update")].strip("/")
                    bid = unquote(mid)
                    body = _read_json_body(self)
                    payload = update_backlog_item(
                        bid,
                        classification=body.get("classification"),
                        status=body.get("status"),
                        analysis=body.get("analysis"),
                        suggested_fixes=body.get("suggested_fixes"),
                        fix_notes=body.get("fix_notes"),
                        related_item_ids=body.get("related_item_ids"),
                        findings=body.get("findings"),
                        reviewer=body.get("reviewer") or "session_agent",
                    )
                    _json_response(
                        self, 200 if payload.get("ok") else 400, payload
                    )
                    return
                # Session "fix" command: close open item(s) + document patch
                if path == "/api/backlog/close" or path.rstrip("/").endswith(
                    "/api/backlog/close"
                ):
                    from conjecture_behaviour_runner.review_backlog import (
                        close_open_with_patch,
                        close_with_patch,
                    )

                    body = _read_json_body(self)
                    reviewer = body.get("reviewer") or "session_agent"
                    patch = body.get("patch")
                    if patch is None and body.get("summary"):
                        patch = {
                            "summary": body.get("summary"),
                            "files": body.get("files") or [],
                            "commits": body.get("commits") or [],
                            "tests": body.get("tests") or [],
                            "seal": body.get("seal") or "",
                            "notes": body.get("fix_notes") or body.get("notes") or "",
                        }
                    item_id = body.get("item_id") or body.get("id")
                    item_ids = body.get("item_ids")
                    if item_id and not item_ids:
                        payload = close_with_patch(
                            str(item_id),
                            patch=patch,
                            fix_notes=body.get("fix_notes"),
                            related_item_ids=body.get("related_item_ids"),
                            findings=body.get("findings"),
                            analysis=body.get("analysis"),
                            reviewer=reviewer,
                        )
                    else:
                        if not patch:
                            payload = {
                                "ok": False,
                                "error": "patch_required",
                                "hint": "Body needs patch or summary (+ optional files/commits/tests)",
                            }
                        else:
                            payload = close_open_with_patch(
                                patch=patch,
                                item_ids=[str(x) for x in item_ids]
                                if isinstance(item_ids, list)
                                else None,
                                fix_notes=body.get("fix_notes"),
                                reviewer=reviewer,
                            )
                    _json_response(
                        self, 200 if payload.get("ok") else 400, payload
                    )
                    return
                if path.startswith("/api/backlog/") and path.rstrip("/").endswith(
                    "/close"
                ):
                    from conjecture_behaviour_runner.review_backlog import (
                        close_with_patch,
                    )

                    mid = path[len("/api/backlog/") :].strip("/")
                    if mid.endswith("/close"):
                        mid = mid[: -len("/close")].strip("/")
                    bid = unquote(mid)
                    body = _read_json_body(self)
                    patch = body.get("patch")
                    if patch is None and (
                        body.get("summary") or body.get("fix_notes")
                    ):
                        patch = {
                            "summary": body.get("summary") or body.get("fix_notes"),
                            "files": body.get("files") or [],
                            "commits": body.get("commits") or [],
                            "tests": body.get("tests") or [],
                            "seal": body.get("seal") or "",
                            "notes": body.get("fix_notes") or body.get("notes") or "",
                        }
                    payload = close_with_patch(
                        bid,
                        patch=patch,
                        fix_notes=body.get("fix_notes"),
                        related_item_ids=body.get("related_item_ids"),
                        findings=body.get("findings"),
                        analysis=body.get("analysis"),
                        reviewer=body.get("reviewer") or "session_agent",
                    )
                    _json_response(
                        self, 200 if payload.get("ok") else 400, payload
                    )
                    return
                if path == "/api/cleanup-conversations":
                    body = _read_json_body(self)
                    dry_run = body.get("dry_run")
                    if dry_run is None:
                        dry_run = True
                    empty_only = bool(body.get("empty_only"))
                    try:
                        max_del = int(body.get("max_delete") or 200)
                    except (TypeError, ValueError):
                        max_del = 200
                    # Host monorepo driver (product APIs only)
                    try:
                        from conjecture_host.http_driver import (
                            cleanup_conjecture_conversations,
                        )
                    except Exception as imp_exc:  # noqa: BLE001
                        _json_response(
                            self,
                            400,
                            {
                                "ok": False,
                                "error": (
                                    "cleanup_unavailable: host driver not importable "
                                    f"({type(imp_exc).__name__}: {imp_exc})"
                                ),
                            },
                        )
                        return
                    try:
                        payload = cleanup_conjecture_conversations(
                            dry_run=bool(dry_run),
                            empty_only=empty_only,
                            max_delete=max_del,
                        )
                    except Exception as exc:  # noqa: BLE001
                        _json_response(
                            self,
                            500,
                            {"ok": False, "error": str(exc)},
                        )
                        return
                    code = 200 if payload.get("ok") is not False else 400
                    _json_response(self, code, payload)
                    return
                if path == "/api/candidates/run-batch":
                    from conjecture_behaviour_runner.candidate_run import (
                        run_candidate_batch,
                    )

                    body = _read_json_body(self)
                    selection = str(body.get("selection") or "ids")
                    adapter = str(body.get("adapter") or "geometry")
                    steal = bool(body.get("steal"))
                    ids_raw = body.get("ids") or []
                    ids = [str(x) for x in ids_raw if str(x).strip()] if isinstance(
                        ids_raw, list
                    ) else []
                    filters = body.get("filters") if isinstance(body.get("filters"), dict) else {}
                    try:
                        max_sc = int(body.get("max_scenarios") or 50)
                    except (TypeError, ValueError):
                        max_sc = 50
                    payload = run_candidate_batch(
                        selection=selection,
                        ids=ids,
                        adapter=adapter,
                        steal=steal,
                        filters=filters,
                        max_scenarios=max_sc,
                        write=True,
                    )
                    code = 200
                    if payload.get("ok") is False and not payload.get("results"):
                        code = 400
                    _json_response(self, code, payload)
                    return
                if path.startswith("/api/candidates/") and path.rstrip("/").endswith(
                    "/run"
                ):
                    from conjecture_behaviour_runner.candidate_run import run_candidate

                    mid = path[len("/api/candidates/") :].strip("/")
                    if mid.endswith("/run"):
                        mid = mid[: -len("/run")].strip("/")
                    sid = unquote(mid)
                    steal = (qs.get("steal") or [""])[0] in ("1", "true", "yes")
                    payload = run_candidate(sid, steal=steal, write=True)
                    _json_response(
                        self, 200 if payload.get("ok") is not False else 400, payload
                    )
                    return
                if path.startswith("/api/candidates/") and path.rstrip("/").endswith(
                    "/findings"
                ):
                    from conjecture_behaviour_runner.candidate_run import list_evidence
                    from conjecture_behaviour_runner.candidates_ui import get_candidate
                    from conjecture_behaviour_runner.findings_author import (
                        attach_findings_to_evidence,
                    )

                    mid = path[len("/api/candidates/") :].strip("/")
                    if mid.endswith("/findings"):
                        mid = mid[: -len("/findings")].strip("/")
                    sid = unquote(mid)
                    body = _read_json_body(self)
                    use_llm = body.get("use_llm")
                    if use_llm is None:
                        use_llm = True
                    cand = get_candidate(sid)
                    scenario = cand.get("scenario") if cand.get("ok") else {}
                    evlist = list_evidence(sid)
                    evidence = None
                    if evlist.get("runs"):
                        evidence = dict(evlist["runs"][0])
                    if not evidence:
                        # Minimal empty evidence shell from scenario alone
                        evidence = {
                            "ok": True,
                            "scenario_id": sid,
                            "run": {"passed": None, "failures": [], "turns": []},
                            "what_actually_happened": {
                                "turns": (scenario or {}).get("incident_turns") or [],
                            },
                        }
                    attach_findings_to_evidence(
                        evidence,
                        scenario=scenario if isinstance(scenario, dict) else {},
                        use_llm=bool(use_llm),
                    )
                    # Persist latest with findings
                    try:
                        from pathlib import Path
                        from conjecture_behaviour_runner.candidates_ui import (
                            resolve_candidates_dir,
                        )

                        cdir = resolve_candidates_dir()
                        if cdir is not None:
                            ed = Path(cdir) / "evidence" / sid
                            ed.mkdir(parents=True, exist_ok=True)
                            (ed / "latest.json").write_text(
                                json.dumps(evidence, indent=2) + "\n",
                                encoding="utf-8",
                            )
                            evidence["latest_path"] = str(ed / "latest.json")
                    except Exception:  # noqa: BLE001
                        pass
                    _json_response(
                        self,
                        200,
                        {
                            "ok": True,
                            "scenario_id": sid,
                            "findings": evidence.get("findings"),
                            "evidence": evidence,
                        },
                    )
                    return
            except Exception as exc:  # noqa: BLE001
                _json_response(self, 500, {"error": str(exc)})
                return
            _json_response(self, 404, {"error": "not_found"})

    return Handler


def _default_ui_host() -> str:
    """Bind host for local console.

    Default **0.0.0.0** so WSL2 / Docker / LAN browsers can reach the port
    (127.0.0.1-only is invisible from Windows host when forwarding fails).
    Override: ``CONJECTURE_UI_HOST=127.0.0.1``.
    """
    env = (os.environ.get("CONJECTURE_UI_HOST") or "").strip()
    if env:
        return env
    return "0.0.0.0"


def _guess_lan_ips() -> list[str]:
    """Best-effort non-loopback IPv4s for WSL/Windows open hints."""
    ips: list[str] = []
    try:
        import socket

        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip and not ip.startswith("127.") and ip not in ips:
                ips.append(ip)
    except Exception:  # noqa: BLE001
        pass
    # /proc net route heuristic (WSL eth0)
    try:
        import subprocess

        out = subprocess.check_output(
            ["hostname", "-I"], text=True, stderr=subprocess.DEVNULL, timeout=2,
        )
        for tok in out.split():
            if tok and not tok.startswith("127.") and tok not in ips:
                ips.append(tok)
    except Exception:  # noqa: BLE001
        pass
    return ips[:4]


def serve_ui(
    *,
    host: str | None = None,
    port: int = 8765,
    open_browser: bool = True,
) -> None:
    """Block and serve the local Quality Console (Conjecture UI)."""
    bind_host = (host or _default_ui_host()).strip() or "0.0.0.0"
    handler = _make_handler()

    class _ReuseHTTPServer(ThreadingHTTPServer):
        allow_reuse_address = True

    try:
        httpd = _ReuseHTTPServer((bind_host, port), handler)
    except OSError as exc:
        print(
            f"ERROR: cannot bind {bind_host}:{port} ({exc}).\n"
            f"  Is another console already running?\n"
            f"  Check: ss -ltnp | grep {port}\n"
            f"  Stop:  scripts/quality-console.sh stop",
            flush=True,
        )
        raise SystemExit(1) from exc

    open_url = f"http://127.0.0.1:{port}/"
    print(
        f"Conjecture · Conversational Agentic Quality  (Quality Console)",
        flush=True,
    )
    print(f"  Listening on {bind_host}:{port}  ·  single port for all quality UI", flush=True)
    print(f"  Open → {open_url}", flush=True)
    print(
        f"         {open_url}#/home  ·  #/laws  ·  #/program/purity_scoreboard  ·  #/seek",
        flush=True,
    )
    print(
        f"  Surface map (same port, no http.server) → {open_url}surface-map",
        flush=True,
    )
    if bind_host in ("0.0.0.0", "::", "[::]"):
        for ip in _guess_lan_ips():
            print(
                f"  WSL/LAN (if localhost fails from Windows) → "
                f"http://{ip}:{port}/",
                flush=True,
            )
    print(
        "  Programs: Map · Authority · Laundry · Antipatterns · Voice · Purity · Surface×law",
        flush=True,
    )
    print(
        "  Proof tools: Coverage battery · Author · Runner · Verdict | Ops: Demo · Admin · Help",
        flush=True,
    )
    print("  APIs: /api/quality-snapshot · /api/law-seek · /api/laws", flush=True)
    print(
        "  Port policy: do not spin extra ports for quality artifacts "
        f"(no python -m http.server). Use this :{port} only.",
        flush=True,
    )
    print("Ctrl+C to stop.", flush=True)
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(open_url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
    finally:
        httpd.server_close()


def main(argv: Optional[list[str]] = None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="conjecture ui")
    p.add_argument(
        "--host",
        default=None,
        help="Bind address (default: CONJECTURE_UI_HOST or 0.0.0.0)",
    )
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-browser", action="store_true")
    args = p.parse_args(argv)
    serve_ui(host=args.host, port=args.port, open_browser=not args.no_browser)
    return 0
