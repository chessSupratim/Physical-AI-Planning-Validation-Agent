"""Draw candidate arrows on an image for visualisation."""
from __future__ import annotations
from typing import List, Optional
import numpy as np


def draw_candidates(image: np.ndarray, candidates: List[dict],
                    best_idx: Optional[int] = None) -> np.ndarray:
    """Return a copy of `image` with candidate arrows drawn; highlight best_idx."""
    raise NotImplementedError
