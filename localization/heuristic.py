"""Map direction phrases to pixel coordinates — deterministic, no model needed."""
from __future__ import annotations
from typing import Tuple

# Canonical direction tokens and their aliases (misspelling-tolerant)
_ALIASES = {
    "top":    ["top", "upper", "up"],
    "bottom": ["bottom", "lower", "down", "buttom", "botton"],
    "left":   ["left", "lft"],
    "right":  ["right", "rght"],
    "center": ["center", "centre", "middle"],
}


def goal_to_pixel(direction: str, image_shape: Tuple[int, int]) -> Tuple[int, int]:
    """Return (x, y) pixel for a direction phrase given image (H, W, ...)."""
    raise NotImplementedError


def _normalise(direction: str) -> str:
    """Lowercase + alias-expand a direction phrase."""
    raise NotImplementedError
