"""Central pipeline: given two pixel points, navigate and produce all outputs."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import numpy as np


@dataclass
class RunResult:
    start_pos: Tuple[int, int]
    goal_pos: Tuple[int, int]
    hops: List[dict] = field(default_factory=list)
    final_pos: Tuple[int, int] = (0, 0)
    reasoning: str = ""
    reached_goal: bool = False
    output_paths: dict = field(default_factory=dict)


def run_pipeline(image: np.ndarray, start_pos: Tuple[int, int],
                 goal_pos: Tuple[int, int], cfg) -> RunResult:
    """Main entry point called by both CLI and Streamlit."""
    raise NotImplementedError
