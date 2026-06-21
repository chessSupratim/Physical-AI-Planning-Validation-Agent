"""Evaluation metrics: task success, goal-distance error, path cost, collision rate."""
from __future__ import annotations
from typing import Tuple


def compute_metrics(run_result) -> dict:
    """Return dict with task_success, goal_distance_error, path_cost, collision_rate."""
    raise NotImplementedError


def task_success(final_pos: Tuple[int, int], goal_pos: Tuple[int, int],
                 tolerance_px: int) -> bool:
    raise NotImplementedError


def goal_distance_error(final_pos: Tuple[int, int],
                        goal_pos: Tuple[int, int]) -> float:
    raise NotImplementedError
