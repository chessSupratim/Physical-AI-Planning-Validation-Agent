"""Multi-hop straight stepping with per-hop full-line obstacle look-ahead."""
from __future__ import annotations
from typing import List, Tuple
import numpy as np


def run_hop_loop(image: np.ndarray,
                 start_pos: Tuple[int, int],
                 goal_pos: Tuple[int, int],
                 obstacle_boxes: List[dict],
                 cfg) -> List[dict]:
    """Return list of hop records {from, to, best_candidate, cost, detour}."""
    raise NotImplementedError


def _line_blocked(p0: Tuple[int, int], p1: Tuple[int, int],
                  boxes: List[dict]) -> bool:
    """Return True if the segment p0→p1 intersects any obstacle box."""
    raise NotImplementedError
