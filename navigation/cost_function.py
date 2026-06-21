"""Cost function and candidate selector for hop-wise planning."""
from __future__ import annotations
from typing import List, Tuple
import numpy as np


def compute_cost(sim_result: dict, goal: Tuple[int, int],
                 collision_penalty: float) -> float:
    """Return scalar cost: goal_distance + collision_penalty * collision + path_length."""
    raise NotImplementedError


def select_best(candidates: List[dict], costs: List[float]) -> int:
    """Return the index of the minimum-cost candidate."""
    raise NotImplementedError
