"""Animated trajectory GIF — Scenario A: marker hops over the fixed background."""
from __future__ import annotations
from typing import List, Tuple

import cv2
import imageio
import numpy as np

_C_TRAIL  = (50,  165, 255)
_C_START  = (0,   0,   255)
_C_GOAL   = (0,   255, 255)
_C_MOVER  = (255, 255, 255)
_FONT     = cv2.FONT_HERSHEY_SIMPLEX


def _render_hop_frame(image: np.ndarray, hop_log: List[dict],
                      hop_idx: int,
                      start_pos: Tuple[int, int],
                      goal_pos: Tuple[int, int]) -> np.ndarray:
    frame = image.copy()
    # Trail up to this hop
    pts = [tuple(start_pos)] + [tuple(h["to"]) for h in hop_log[: hop_idx + 1]]
    for i in range(len(pts) - 1):
        cv2.line(frame, pts[i], pts[i + 1], _C_TRAIL, 2)
    # Best arrow for this hop
    hop = hop_log[hop_idx]
    cv2.arrowedLine(frame, tuple(hop["from"]), tuple(hop["to"]),
                    (0, 100, 255), 2, tipLength=0.25)
    # Start / goal markers
    cv2.circle(frame, tuple(start_pos), 12, _C_START, -1)
    cv2.circle(frame, tuple(goal_pos),  12, _C_GOAL,  -1)
    # Mover dot
    cv2.circle(frame, tuple(hop["to"]), 9, _C_MOVER, -1)
    cv2.circle(frame, tuple(hop["to"]), 9, (0, 0, 0), 2)
    # Hop counter
    cv2.putText(frame, f"Hop {hop_idx + 1}/{len(hop_log)}",
                (10, 35), _FONT, 1.0, (255, 255, 255), 2)
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def create_trajectory_gif(image: np.ndarray, hop_log: List[dict],
                          start_pos: Tuple[int, int],
                          goal_pos: Tuple[int, int],
                          save_path: str, fps: int = 6) -> None:
    """Write trajectory.gif: one frame per hop, trail grows, hop counter shown."""
    # Frame 0: initial state (no hops yet)
    init = image.copy()
    cv2.circle(init, tuple(start_pos), 12, _C_START, -1)
    cv2.circle(init, tuple(goal_pos),  12, _C_GOAL,  -1)
    cv2.circle(init, tuple(start_pos), 9,  (255, 255, 255), -1)
    cv2.putText(init, "Hop 0", (10, 35), _FONT, 1.0, (255, 255, 255), 2)
    frames = [cv2.cvtColor(init, cv2.COLOR_BGR2RGB)]

    for i in range(len(hop_log)):
        frames.append(_render_hop_frame(image, hop_log, i, start_pos, goal_pos))

    duration = 1.0 / max(fps, 1)
    imageio.mimsave(save_path, frames, duration=duration, loop=0)
