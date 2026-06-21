"""Optional grid A* pather — swappable via config PATHER='astar'."""
from __future__ import annotations
from typing import List, Optional, Tuple
import numpy as np


def build_grid(image_shape: Tuple[int, int], obstacle_boxes: List[dict],
               cell_size: int = 10) -> np.ndarray:
    """Return a boolean grid (True=blocked) from obstacle boxes."""
    raise NotImplementedError


def astar(grid: np.ndarray, start: Tuple[int, int],
          goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
    """Return list of (row, col) waypoints from start to goal, or None if unreachable."""
    raise NotImplementedError


def grid_to_pixels(path: List[Tuple[int, int]],
                   cell_size: int) -> List[Tuple[int, int]]:
    """Convert grid cell coordinates back to pixel coordinates."""
    raise NotImplementedError
