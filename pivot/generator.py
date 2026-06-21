"""Generate straight candidate arrows from the current position (PIVOT-style)."""
from __future__ import annotations
import math
from typing import List, Tuple


# Angular offsets (degrees) around the goal direction, ordered by priority
_OFFSETS_DEG = [0, 45, -45, 90, -90, 135, -135, 180]


def generate_candidates(pos: Tuple[int, int], sub_goal: Tuple[int, int],
                        step_len: int) -> List[dict]:
    """Return one candidate dict per angular offset around the goal direction.

    Each dict: {start, end, angle_deg, length}
    """
    dx = sub_goal[0] - pos[0]
    dy = sub_goal[1] - pos[1]
    dist = math.hypot(dx, dy)

    if dist < 1 or step_len < 1:
        return [{"start": pos, "end": pos, "angle_deg": 0.0, "length": 0}]

    goal_angle = math.atan2(dy, dx)
    candidates = []
    for offset in _OFFSETS_DEG:
        angle = goal_angle + math.radians(offset)
        end = (
            int(round(pos[0] + step_len * math.cos(angle))),
            int(round(pos[1] + step_len * math.sin(angle))),
        )
        candidates.append({
            "start": pos,
            "end": end,
            "angle_deg": math.degrees(angle),
            "length": step_len,
        })
    return candidates
