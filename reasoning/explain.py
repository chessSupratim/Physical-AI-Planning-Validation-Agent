"""MANDATORY LLM reasoning over the hop result, with deterministic fallback.

Every run must produce a non-empty reasoning string.
Step 7 will wire in the real LLM call; until then explain_plan returns the fallback.
"""
from __future__ import annotations
from typing import List


def explain_plan(hop_log: List[dict], goal: tuple, cfg) -> str:
    """Call LLM to explain the trajectory; fall back to deterministic string on failure."""
    # Step 7 will implement the LLM call here.
    return _build_fallback(hop_log, goal)


def _build_fallback(hop_log: List[dict], goal: tuple) -> str:
    """Deterministic fallback reasoning assembled from hop_log (never empty)."""
    n_hops = len(hop_log)
    n_detours = sum(1 for h in hop_log if h.get("detour"))
    if n_hops == 0:
        return "Start and goal are within tolerance — no movement needed."
    detour_note = f" with {n_detours} detour(s) around obstacles" if n_detours else ""
    return (f"Reached goal in {n_hops} hop(s){detour_note}. "
            f"Target position: {goal}.")
