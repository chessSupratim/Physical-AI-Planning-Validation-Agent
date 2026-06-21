"""VLMPC-style deterministic predictive rollout for a single candidate."""
from __future__ import annotations
from typing import List, Tuple
import numpy as np


def simulate_trajectory(pos: Tuple[int, int],
                        candidate: dict,
                        obstacle_boxes: List[dict],
                        image_shape: Tuple[int, int]) -> dict:
    """Simulate one candidate hop; return {end_pos, collision, path_length}."""
    raise NotImplementedError
