"""Route a {type, value} field to a pixel coordinate.

direction -> heuristic._goal_to_pixel
object    -> detector.locate  (+ HSV verify)
memory    -> session_state lookup
"""
from __future__ import annotations
from typing import Tuple, Optional
import numpy as np


def resolve(field: dict, image: np.ndarray,
            session_context: Optional[dict] = None, cfg=None) -> Tuple[int, int]:
    """Return (x, y) pixel for a single {type, value} field."""
    raise NotImplementedError
