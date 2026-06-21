"""VLMPC-style deterministic predictive rollout for a single candidate."""
from __future__ import annotations
import math
from typing import List, Tuple
import numpy as np


# ── geometry helpers ─────────────────────────────────────────────────────────

def _cross2d(o: tuple, u: tuple, v: tuple) -> float:
    return (u[0] - o[0]) * (v[1] - o[1]) - (u[1] - o[1]) * (v[0] - o[0])


def _segs_cross(a: tuple, b: tuple, c: tuple, d: tuple) -> bool:
    """True if segment AB properly crosses segment CD."""
    d1 = _cross2d(c, d, a)
    d2 = _cross2d(c, d, b)
    d3 = _cross2d(a, b, c)
    d4 = _cross2d(a, b, d)
    return (
        ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and
        ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0))
    )


def _segment_intersects_box(p0: tuple, p1: tuple, box: dict) -> bool:
    """Return True if segment p0→p1 intersects the obstacle rectangle."""
    x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]
    # Either endpoint strictly inside box
    if x1 < p0[0] < x2 and y1 < p0[1] < y2:
        return True
    if x1 < p1[0] < x2 and y1 < p1[1] < y2:
        return True
    # Segment crosses any of the four box edges
    corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    for i in range(4):
        if _segs_cross(p0, p1, corners[i], corners[(i + 1) % 4]):
            return True
    return False


# ── rollout ──────────────────────────────────────────────────────────────────

def simulate_trajectory(pos: Tuple[int, int],
                        candidate: dict,
                        obstacle_boxes: List[dict],
                        image_shape: tuple) -> dict:
    """Simulate one candidate hop; return {end_pos, collision, path_length}."""
    h, w = image_shape[:2]
    end = candidate["end"]

    # Out-of-bounds counts as collision
    collision = not (0 <= end[0] < w and 0 <= end[1] < h)

    if not collision:
        for box in obstacle_boxes:
            if _segment_intersects_box(pos, end, box):
                collision = True
                break

    # Clamp end to image when out of bounds
    end_safe = (max(0, min(w - 1, end[0])), max(0, min(h - 1, end[1])))
    path_length = math.dist(pos, end)

    return {
        "end_pos": end_safe,
        "collision": collision,
        "path_length": path_length,
    }
