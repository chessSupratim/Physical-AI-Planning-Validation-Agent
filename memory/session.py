"""st.session_state helpers: current/start position and run history."""
from __future__ import annotations
from typing import Optional, Tuple


def init_session_state() -> None:
    """Initialise session_state keys if not already present."""
    raise NotImplementedError


def get_context() -> dict:
    """Return the current session context dict for the intent parser."""
    raise NotImplementedError


def update_after_run(final_pos: Tuple[int, int], instruction: str,
                     source: dict, target: dict, result) -> None:
    """Write final position and append to history after a completed run."""
    raise NotImplementedError
