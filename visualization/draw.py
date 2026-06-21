"""Static visualisation frames: candidates, selected, final, and trail-line still."""
from __future__ import annotations
from typing import List, Tuple
import numpy as np


def draw_candidates_png(image: np.ndarray, candidates: List[dict],
                        save_path: str) -> None:
    """Save candidates.png with all candidate arrows drawn."""
    raise NotImplementedError


def draw_selected_png(image: np.ndarray, hop_log: List[dict],
                      save_path: str) -> None:
    """Save selected.png with the best candidate highlighted per hop."""
    raise NotImplementedError


def draw_final_png(image: np.ndarray, hop_log: List[dict],
                   start_pos: Tuple[int, int], goal_pos: Tuple[int, int],
                   save_path: str) -> None:
    """Save final.png: mover at goal position with full trail drawn."""
    raise NotImplementedError


def draw_trail_png(image: np.ndarray, hop_log: List[dict],
                   start_pos: Tuple[int, int], goal_pos: Tuple[int, int],
                   save_path: str) -> None:
    """Save trail.png: complete path as a single static line over the original image."""
    raise NotImplementedError
