"""st.session_state helpers: current/start position and run history.

Keeps a rolling window of the last _MAX_HISTORY runs so that the intent
parser can resolve memory references ("go back", "original position", etc.).
"""
from __future__ import annotations

import streamlit as st

_MAX_HISTORY = 5

_EMPTY_CTX: dict = {
    "current_pos": None,
    "start_pos":   None,
    "last_goal":   None,
    "run_count":   0,
    "history":     [],
}


def init_session_state() -> None:
    """Initialise the session_ctx key in st.session_state if absent."""
    if "session_ctx" not in st.session_state:
        st.session_state["session_ctx"] = dict(_EMPTY_CTX, history=[])


def get_context() -> dict:
    """Return session context dict (for intent parser / router).

    Returns an empty dict when no run has completed yet, so callers can
    check truthiness: `if get_context():`.
    """
    ctx = st.session_state.get("session_ctx") or {}
    return ctx if ctx.get("current_pos") is not None else {}


def update_after_run(result, instruction: str = "") -> None:
    """Persist final position and run summary after each completed run."""
    ctx = st.session_state.get("session_ctx") or dict(_EMPTY_CTX, history=[])

    ctx["current_pos"] = tuple(result.final_pos)
    ctx["start_pos"]   = tuple(result.start_pos)
    ctx["last_goal"]   = tuple(result.goal_pos)
    ctx["run_count"]   = ctx.get("run_count", 0) + 1

    entry: dict = {
        "run":     ctx["run_count"],
        "start":   tuple(result.start_pos),
        "goal":    tuple(result.goal_pos),
        "final":   tuple(result.final_pos),
        "reached": result.reached_goal,
        "hops":    len(result.hops),
    }
    if instruction:
        entry["instruction"] = instruction

    history: list = list(ctx.get("history") or [])
    history.append(entry)
    ctx["history"] = history[-_MAX_HISTORY:]

    st.session_state["session_ctx"] = ctx


def clear_context() -> None:
    """Reset session context (e.g. when user presses 'Clear history')."""
    st.session_state["session_ctx"] = dict(_EMPTY_CTX, history=[])
