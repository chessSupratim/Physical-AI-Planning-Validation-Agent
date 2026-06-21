"""Committed detour waypoint logic — prevents oscillation around obstacles."""
from __future__ import annotations
import math
from typing import Tuple


def pick_side(pos: Tuple[int, int], goal: Tuple[int, int], box: dict) -> str:
    """Deterministically choose which side of the box to detour around.

    Uses the sign of the cross product of travel-direction × obstacle-direction.
    Returns 'A' (left-perp) or 'B' (right-perp) — labels are arbitrary but stable.
    """
    cx = (box["x1"] + box["x2"]) / 2
    cy = (box["y1"] + box["y2"]) / 2
    dx = goal[0] - pos[0]
    dy = goal[1] - pos[1]
    ox = cx - pos[0]
    oy = cy - pos[1]
    cross = dx * oy - dy * ox
    return "A" if cross >= 0 else "B"


def compute_detour(pos: Tuple[int, int], goal: Tuple[int, int],
                   blocking_box: dict, image_shape: tuple,
                   margin: int = 30) -> Tuple[int, int]:
    """Return a single detour waypoint perpendicular to the blocking box edge.

    The waypoint is past the obstacle's near edge + margin so the mover clears it.
    """
    h, w = image_shape[:2]
    x1, y1, x2, y2 = (blocking_box["x1"], blocking_box["y1"],
                       blocking_box["x2"], blocking_box["y2"])
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2

    dx = goal[0] - pos[0]
    dy = goal[1] - pos[1]
    travel_len = math.hypot(dx, dy)
    if travel_len < 1:
        return (int(cx), int(cy))

    # Unit travel direction
    tx, ty = dx / travel_len, dy / travel_len

    side = pick_side(pos, goal, blocking_box)
    # Perpendicular unit vector (two choices)
    if side == "A":
        px, py = -ty, tx
    else:
        px, py = ty, -tx

    # How far to offset: project box half-extents onto perp direction
    half_w = (x2 - x1) / 2
    half_h = (y2 - y1) / 2
    extent = abs(px) * half_w + abs(py) * half_h

    wp_x = int(cx + px * (extent + margin))
    wp_y = int(cy + py * (extent + margin))

    # Clamp to image with margin
    wp_x = max(margin, min(w - margin, wp_x))
    wp_y = max(margin, min(h - margin, wp_y))
    return (wp_x, wp_y)
