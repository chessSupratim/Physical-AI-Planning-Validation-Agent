"""Optional grid A* pather — swappable via config PATHER='astar'.

Set cfg.PATHER = "astar" to use this instead of the greedy detour planner.
Falls back to greedy detour if no path is found.
"""
from __future__ import annotations
import heapq
import math
from typing import List, Optional, Tuple

import numpy as np

# 8-connected movement: (row_delta, col_delta, cost)
_DIRS = [
    (-1,  0, 1.0), ( 1,  0, 1.0), ( 0, -1, 1.0), ( 0,  1, 1.0),
    (-1, -1, math.sqrt(2)), (-1,  1, math.sqrt(2)),
    ( 1, -1, math.sqrt(2)), ( 1,  1, math.sqrt(2)),
]


def build_grid(image_shape: Tuple[int, ...],
               obstacle_boxes: List[dict],
               cell_size: int = 10) -> np.ndarray:
    """Return a boolean grid (True=blocked) from obstacle boxes.

    A 1-cell margin is added around each obstacle for clearance.
    """
    h, w  = image_shape[:2]
    rows  = math.ceil(h / cell_size)
    cols  = math.ceil(w / cell_size)
    grid  = np.zeros((rows, cols), dtype=bool)
    margin = 1

    for b in obstacle_boxes:
        r1 = max(0,      int(b["y1"] / cell_size) - margin)
        r2 = min(rows-1, int(b["y2"] / cell_size) + margin)
        c1 = max(0,      int(b["x1"] / cell_size) - margin)
        c2 = min(cols-1, int(b["x2"] / cell_size) + margin)
        grid[r1:r2+1, c1:c2+1] = True

    return grid


def astar(grid: np.ndarray,
          start: Tuple[int, int],
          goal:  Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
    """Return list of (row, col) waypoints from start to goal, or None if unreachable.

    Uses 8-connected movement with Euclidean heuristic.
    """
    rows, cols = grid.shape
    if grid[start] or grid[goal]:
        return None

    g_score: dict[Tuple[int, int], float] = {start: 0.0}
    came_from: dict[Tuple[int, int], Tuple[int, int]] = {}

    def h(cell: Tuple[int, int]) -> float:
        return math.hypot(cell[0] - goal[0], cell[1] - goal[1])

    # heap entries: (f, g, row, col)  — all numeric, avoids tuple comparison issues
    heap: list = [(h(start), 0.0, start[0], start[1])]

    while heap:
        f, g, r, c = heapq.heappop(heap)
        curr = (r, c)

        if curr == goal:
            path = []
            while curr in came_from:
                path.append(curr)
                curr = came_from[curr]
            path.append(start)
            path.reverse()
            return path

        if g > g_score.get(curr, math.inf):
            continue

        for dr, dc, cost in _DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not grid[nr, nc]:
                nxt    = (nr, nc)
                new_g  = g + cost
                if new_g < g_score.get(nxt, math.inf):
                    g_score[nxt]   = new_g
                    came_from[nxt] = curr
                    heapq.heappush(heap, (new_g + h(nxt), new_g, nr, nc))

    return None


def grid_to_pixels(path: List[Tuple[int, int]],
                   cell_size: int) -> List[Tuple[int, int]]:
    """Convert (row, col) cells to pixel (x, y) center coordinates."""
    half = cell_size // 2
    return [(c * cell_size + half, r * cell_size + half) for r, c in path]


def _simplify(waypoints: List[Tuple[int, int]],
              tol: float = 1.5) -> List[Tuple[int, int]]:
    """Remove approximately collinear intermediate waypoints.

    Keeps turns; removes straight-line redundancy.  Reduces hop count for
    long diagonal A* paths without losing shape.
    """
    if len(waypoints) <= 2:
        return list(waypoints)

    def _perp_dist(p0, p1, p2):
        dx, dy = p2[0] - p0[0], p2[1] - p0[1]
        px, py = p1[0] - p0[0], p1[1] - p0[1]
        d = math.hypot(dx, dy)
        return abs(dx * py - dy * px) / d if d > 0 else 0.0

    result = [waypoints[0]]
    i = 0
    while i < len(waypoints) - 1:
        j = i + 1
        while j < len(waypoints) - 1:
            if _perp_dist(result[-1], waypoints[j], waypoints[j + 1]) < tol:
                j += 1
            else:
                break
        result.append(waypoints[j])
        i = j
    return result


def astar_path(start_px:      Tuple[int, int],
               goal_px:       Tuple[int, int],
               obstacle_boxes: List[dict],
               image_shape:   Tuple[int, ...],
               cell_size:     int = 10) -> Optional[List[Tuple[int, int]]]:
    """Public API: run A* in pixel space; return simplified waypoints or None.

    Returns None if no path exists (caller falls back to greedy detour).
    """
    grid = build_grid(image_shape, obstacle_boxes, cell_size)
    rows, cols = grid.shape

    # Pixel → grid cell (x → col, y → row)
    def to_cell(px):
        return (min(int(px[1] / cell_size), rows - 1),
                min(int(px[0] / cell_size), cols - 1))

    sc, gc = to_cell(start_px), to_cell(goal_px)
    # Always unblock start/goal so the path can be found
    grid[sc] = False
    grid[gc] = False

    path_cells = astar(grid, sc, gc)
    if path_cells is None:
        return None

    raw = grid_to_pixels(path_cells, cell_size)

    # Pin exact pixel endpoints and simplify collinear runs
    if raw:
        raw[0]  = tuple(start_px)
        raw[-1] = tuple(goal_px)
    return _simplify(raw)
