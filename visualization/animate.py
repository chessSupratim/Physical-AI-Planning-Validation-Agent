"""Animated trajectory GIF — Scenario A: marker hops over the fixed background."""
from __future__ import annotations
from typing import List, Tuple
import numpy as np


def create_trajectory_gif(image: np.ndarray, hop_log: List[dict],
                           start_pos: Tuple[int, int], goal_pos: Tuple[int, int],
                           save_path: str, fps: int = 6) -> None:
    """Write trajectory.gif: one frame per hop, trail grows, hop counter shown."""
    raise NotImplementedError


def _render_hop_frame(image: np.ndarray, hop_log: List[dict],
                      hop_idx: int, goal_pos: Tuple[int, int]) -> np.ndarray:
    """Return one RGB frame for hop_idx."""
    raise NotImplementedError
