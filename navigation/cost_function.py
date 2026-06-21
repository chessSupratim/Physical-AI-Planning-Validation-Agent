"""Cost function and candidate selector for hop-wise planning."""
from __future__ import annotations
import math
from typing import List, Tuple


def compute_cost(sim_result: dict, goal: Tuple[int, int],
                 collision_penalty: float) -> float:
    """goal_distance + collision_penalty * collision + path_length."""
    goal_dist = math.dist(sim_result["end_pos"], goal)
    return goal_dist + collision_penalty * int(sim_result["collision"]) + sim_result["path_length"]


def select_best(candidates: List[dict], costs: List[float]) -> int:
    """Return the index of the minimum-cost candidate (first on tie)."""
    return min(range(len(costs)), key=lambda i: costs[i])
