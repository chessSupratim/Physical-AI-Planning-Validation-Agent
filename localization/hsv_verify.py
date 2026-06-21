"""HSV cross-check: verify a point lands on a region matching the named colour.

Rejects off-object points (e.g. empty floor) before navigation begins.
"""
from __future__ import annotations
from typing import Optional, Tuple
import numpy as np


def verify_point(image: np.ndarray, point: Tuple[int, int],
                 color_hint: Optional[str] = None) -> bool:
    """Return True if the pixel at `point` matches `color_hint`; False to reject."""
    raise NotImplementedError


def nearest_matching_blob(image: np.ndarray,
                          color_hint: str) -> Optional[Tuple[int, int]]:
    """Snap to the centroid of the nearest blob matching colour as a fallback."""
    raise NotImplementedError
