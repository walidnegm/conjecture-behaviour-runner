"""Optional adapters that bind Conjecture to a specific runtime.

Everything here is import-guarded: the portable core (``run_script``, invariants,
protocol) never imports these, so the base package stays dependency-free. Install
the relevant extra to use one — e.g. ``conjecture-behaviour-runner[control-plane]``.
"""
