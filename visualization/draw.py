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
_C_OBSTACLE = (200, 0,   200)   # magenta — detected obstacle boxes
_FONT       = cv2.FONT_HERSHEY_SIMPLEX


def _draw_obstacle_boxes(img: np.ndarray, obstacle_boxes: list,
                         floor_y_top: int | None = None) -> None:
    """Draw magenta obstacle boxes and (optionally) a cyan floor boundary line."""
    for b in (obstacle_boxes or []):
        cv2.rectangle(img, (b["x1"], b["y1"]), (b["x2"], b["y2"]),
                      _C_OBSTACLE, 2)
        cv2.putText(img, "obs", (b["x1"], max(0, b["y1"] - 4)),
                    _FONT, 0.4, _C_OBSTACLE, 1)
    if floor_y_top is not None:
        h, w = img.shape[:2]
        cv2.line(img, (0, floor_y_top), (w, floor_y_top), (255, 255, 0), 1)
        cv2.putText(img, "floor", (4, max(4, floor_y_top - 4)),
                    _FONT, 0.35, (255, 255, 0), 1)


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
                        save_path: str,
                        obstacle_boxes: Optional[List[dict]] = None,
                        floor_y_top: Optional[int] = None) -> None:
    img = image.copy()
    _draw_obstacle_boxes(img, obstacle_boxes, floor_y_top)
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
                   save_path: str,
                   obstacle_boxes: Optional[List[dict]] = None,
                   floor_y_top: Optional[int] = None) -> None:
    img = image.copy()
    _draw_obstacle_boxes(img, obstacle_boxes, floor_y_top)
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
                   save_path: str,
                   obstacle_boxes: Optional[List[dict]] = None,
                   floor_y_top: Optional[int] = None) -> None:
    """Trail-line still: full path as a single static line over the original image."""
    img = image.copy()
    _draw_obstacle_boxes(img, obstacle_boxes, floor_y_top)
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
