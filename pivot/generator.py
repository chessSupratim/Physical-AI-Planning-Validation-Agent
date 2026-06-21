"""Generate straight candidate arrows from the current position (PIVOT-style)."""
from __future__ import annotations
from typing import List, Tuple
import numpy as np


def generate_candidates(pos: Tuple[int, int], goal: Tuple[int, int],
                        step_len: int, n_candidates: int = 8) -> List[dict]:
    """Return list of candidate dicts: {start, end, angle, length}."""
    raise NotImplementedError
