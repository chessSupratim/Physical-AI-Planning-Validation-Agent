"""MANDATORY LLM reasoning over the hop result, with deterministic fallback.

Every run must produce a non-empty reasoning string (SPEC §8):
1. Build a compact hop-summary prompt.
2. Call the LLM via vlm.api_backend.ask_vlm.
3. Retry once on failure.
4. If both attempts fail: emit a deterministic fallback string (never empty).
"""
from __future__ import annotations
import math
from typing import List, Optional

import numpy as np

_PROMPT_TEMPLATE = """\
You are a navigation AI that just completed a path-planning task. \
Explain what happened in 2-3 clear, natural sentences.

Navigation summary:
  Start position : {start}
  Goal position  : {goal}
  Reached goal   : {reached}
  Total hops     : {n_hops}
  Detour hops    : {n_detours}

Hop trace (from -> to):
{hop_lines}

Describe: whether the goal was reached, how many steps it took, \
whether any detours were needed to avoid obstacles, and the general direction of travel. \
Be concise — 2 sentences maximum."""


def explain_plan(hop_log: List[dict],
                 goal: tuple,
                 cfg,
                 image: Optional[np.ndarray] = None) -> str:
    """Call LLM to explain the trajectory; fall back to deterministic string on failure.

    The reasoning field is NEVER empty (SPEC §8).
    """
    prompt = _build_prompt(hop_log, goal)

    for attempt in range(2):
        try:
            from vlm.api_backend import ask_vlm
            text = ask_vlm(prompt, cfg, image=image).strip()
            if text:
                return text
        except Exception as exc:
            print(f"[reasoning] LLM attempt {attempt + 1} failed: {exc!r}")

    return _build_fallback(hop_log, goal)


# ── prompt builder ────────────────────────────────────────────────────────────

def _build_prompt(hop_log: List[dict], goal: tuple) -> str:
    n_hops    = len(hop_log)
    n_detours = sum(1 for h in hop_log if h.get("detour"))
    start     = tuple(hop_log[0]["from"]) if hop_log else goal

    final_pos = tuple(hop_log[-1]["to"]) if hop_log else goal
    reached   = math.dist(final_pos, goal) <= 25

    # Keep the trace compact: show at most 8 hops (first 4 + last 4)
    if n_hops <= 8:
        shown = list(enumerate(hop_log, 1))
    else:
        shown = (list(enumerate(hop_log[:4], 1))
                 + [(-1, None)]
                 + list(enumerate(hop_log[-4:], n_hops - 3)))

    lines = []
    for idx, h in shown:
        if h is None:
            lines.append(f"  ... ({n_hops - 8} hops omitted)")
        else:
            tag = " [DETOUR]" if h.get("detour") else ""
            lines.append(f"  Hop {idx:2d}: {tuple(h['from'])} -> {tuple(h['to'])}{tag}")

    return _PROMPT_TEMPLATE.format(
        start=start,
        goal=goal,
        reached=reached,
        n_hops=n_hops,
        n_detours=n_detours,
        hop_lines="\n".join(lines),
    )


# ── deterministic fallback ────────────────────────────────────────────────────

def _build_fallback(hop_log: List[dict], goal: tuple) -> str:
    """Assembled from hop_log — guaranteed non-empty."""
    n_hops    = len(hop_log)
    n_detours = sum(1 for h in hop_log if h.get("detour"))
    if n_hops == 0:
        return "Start and goal are within tolerance - no movement needed."
    detour_note = (f" with {n_detours} detour(s) around obstacles"
                   if n_detours else "")
    return (f"Reached goal in {n_hops} hop(s){detour_note}. "
            f"Target position: {goal}.")
