"""Static visualisation frames: candidates, selected, final, and trail-line still."""
from __future__ import annotations
from typing import List, Optional, Tuple

import cv2
import numpy as np

# BGR colour palette
_C_TRAIL    = (50,  165, 255)   # orange
_C_START    = (0,   0,   255)   # red
_C_GOAL     = (0,   255, 255)   # yellow
_C_MOVER    = (255, 255, 255)   # white
_C_CAND     = (0,   200, 0)     # green
_C_BEST     = (0,   100, 255)   # orange-red
_C_DETOUR   = (255, 80,  80)    # blue
_FONT       = cv2.FONT_HERSHEY_SIMPLEX


def _mark_start_goal(img: np.ndarray,
                     start: Tuple[int, int],
                     goal:  Tuple[int, int]) -> None:
    cv2.circle(img, start, 12, _C_START, -1)
    cv2.circle(img, start, 12, (0, 0, 0), 2)
    cv2.circle(img, goal,  12, _C_GOAL,  -1)
    cv2.circle(img, goal,  12, (0, 0, 0), 2)


def _draw_trail(img: np.ndarray, points: List[Tuple[int, int]]) -> None:
    for i in range(len(points) - 1):
        cv2.line(img, tuple(points[i]), tuple(points[i + 1]), _C_TRAIL, 2)


def draw_candidates_png(image: np.ndarray, candidates: List[dict],
                        start_pos: Tuple[int, int], goal_pos: Tuple[int, int],
                        save_path: str) -> None:
    img = image.copy()
    for i, c in enumerate(candidates):
        color = _C_BEST if i == 0 else _C_CAND
        cv2.arrowedLine(img, tuple(c["start"]), tuple(c["end"]),
                        color, 2, tipLength=0.25)
    _mark_start_goal(img, start_pos, goal_pos)
    cv2.imwrite(save_path, img)


def draw_selected_png(image: np.ndarray, hop_log: List[dict],
                      start_pos: Tuple[int, int], goal_pos: Tuple[int, int],
                      save_path: str) -> None:
    img = image.copy()
    for hop in hop_log:
        cv2.arrowedLine(img, tuple(hop["from"]), tuple(hop["to"]),
                        _C_BEST, 2, tipLength=0.25)
    _mark_start_goal(img, start_pos, goal_pos)
    cv2.imwrite(save_path, img)


def draw_final_png(image: np.ndarray, hop_log: List[dict],
                   start_pos: Tuple[int, int], goal_pos: Tuple[int, int],
                   save_path: str) -> None:
    img = image.copy()
    pts = [tuple(start_pos)] + [tuple(h["to"]) for h in hop_log]
    _draw_trail(img, pts)
    _mark_start_goal(img, start_pos, goal_pos)
    if hop_log:
        final = tuple(hop_log[-1]["to"])
        cv2.circle(img, final, 9, _C_MOVER, -1)
        cv2.circle(img, final, 9, (0, 0, 0), 2)
    cv2.imwrite(save_path, img)


def draw_trail_png(image: np.ndarray, hop_log: List[dict],
                   start_pos: Tuple[int, int], goal_pos: Tuple[int, int],
                   save_path: str) -> None:
    """Trail-line still: full path as a single static line over the original image."""
    img = image.copy()
    pts = [tuple(start_pos)] + [tuple(h["to"]) for h in hop_log]
    _draw_trail(img, pts)
    _mark_start_goal(img, start_pos, goal_pos)
    if hop_log:
        final = tuple(hop_log[-1]["to"])
        cv2.circle(img, final, 9, _C_MOVER, -1)
        cv2.circle(img, final, 9, (0, 0, 0), 2)
    cv2.putText(img, f"{len(hop_log)} hops", (10, 35),
                _FONT, 1.0, (255, 255, 255), 2)
    cv2.imwrite(save_path, img)
