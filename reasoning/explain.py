"""MANDATORY LLM reasoning over the hop result, with deterministic fallback.

Every run must produce a non-empty reasoning string.
If the LLM call fails: retry once, then build a fallback from the hop log.
"""
from __future__ import annotations
from typing import List


def explain_plan(hop_log: List[dict], goal: tuple, cfg) -> str:
    """Call LLM to explain the trajectory; return fallback string if LLM fails."""
    raise NotImplementedError


def _build_fallback(hop_log: List[dict], goal: tuple) -> str:
    """Deterministic fallback reasoning assembled from hop_log (never empty)."""
    n_hops = len(hop_log)
    n_detours = sum(1 for h in hop_log if h.get("detour"))
    return (f"Reached goal in {n_hops} hop(s) with {n_detours} detour(s) "
            f"around detected obstacles.")
