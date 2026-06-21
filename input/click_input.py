"""Mode B helpers: validate and normalise clicked pixel coordinates."""
from __future__ import annotations
from typing import Tuple


def parse_coord_string(s: str) -> Tuple[int, int]:
    """Parse 'X,Y' string (from CLI --start / --goal-xy) into (x, y) ints."""
    raise NotImplementedError


def validate_click(point: Tuple[int, int], image_shape: Tuple[int, int]) -> Tuple[int, int]:
    """Clamp click to image bounds and return validated (x, y)."""
    raise NotImplementedError
