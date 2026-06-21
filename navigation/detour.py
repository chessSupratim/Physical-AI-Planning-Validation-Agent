"""Committed detour waypoint logic — prevents oscillation around obstacles."""
from __future__ import annotations
from typing import Optional, Tuple


def compute_detour(pos: Tuple[int, int],
                   goal: Tuple[int, int],
                   blocking_box: dict,
                   margin: int = 20) -> Tuple[int, int]:
    """Return a single detour waypoint perpendicular to the blocking box edge."""
    raise NotImplementedError


def pick_side(pos: Tuple[int, int], goal: Tuple[int, int],
              box: dict) -> str:
    """Deterministically choose 'left' or 'right' side to detour around box."""
    raise NotImplementedError
