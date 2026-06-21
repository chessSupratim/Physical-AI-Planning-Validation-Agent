"""Mode B helpers: validate and normalise clicked pixel coordinates."""
from __future__ import annotations
from typing import Tuple


def parse_coord_string(s: str) -> Tuple[int, int]:
    """Parse 'X,Y' string (from CLI --start / --goal-xy) into (x, y) ints."""
    parts = s.split(",")
    if len(parts) != 2:
        raise ValueError(f"Expected 'X,Y', got: {s!r}")
    return int(parts[0].strip()), int(parts[1].strip())


def validate_click(point: Tuple[int, int], image_shape: tuple) -> Tuple[int, int]:
    """Clamp click to image bounds and return validated (x, y)."""
    h, w = image_shape[:2]
    x = max(0, min(int(point[0]), w - 1))
    y = max(0, min(int(point[1]), h - 1))
    return (x, y)
