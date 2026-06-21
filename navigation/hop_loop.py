"""Multi-hop straight stepping with per-hop full-line obstacle look-ahead."""
from __future__ import annotations
import math
from typing import List, Optional, Tuple

from navigation.rollout import simulate_trajectory, _segment_intersects_box
from navigation.cost_function import compute_cost, select_best
from navigation.detour import compute_detour
from pivot.generator import generate_candidates
from input.click_input import validate_click


def _find_blocking_box(p0: tuple, p1: tuple,
                       boxes: List[dict]) -> Optional[dict]:
    """Return the first obstacle box blocking segment p0→p1, or None."""
    for box in boxes:
        if _segment_intersects_box(p0, p1, box):
            return box
    return None


def _line_blocked(p0: tuple, p1: tuple, boxes: List[dict]) -> bool:
    return _find_blocking_box(p0, p1, boxes) is not None


def _filter_boxes(obstacle_boxes: List[dict], goal_pos: tuple,
                  image_shape: tuple,
                  start_pos: Optional[tuple] = None) -> List[dict]:
    """Drop hallucinated boxes, boxes containing the goal, and boxes containing start."""
    h, w = image_shape[:2]
    gx, gy = goal_pos
    result = []
    for b in obstacle_boxes:
        # Discard boxes spanning >80% of image dimension
        if (b["x2"] - b["x1"]) >= 0.8 * w:
            continue
        if (b["y2"] - b["y1"]) >= 0.8 * h:
            continue
        # Goal-inside-obstacle exception: destination is not a wall
        if b["x1"] <= gx <= b["x2"] and b["y1"] <= gy <= b["y2"]:
            continue
        # Start-inside-obstacle exception: the mover itself is not an obstacle
        if start_pos is not None:
            sx, sy = start_pos
            if b["x1"] <= sx <= b["x2"] and b["y1"] <= sy <= b["y2"]:
                continue
        result.append(b)
    return result


def _waypoints_to_hops(waypoints: List[Tuple[int, int]]) -> List[dict]:
    """Convert A* waypoints to hop records compatible with the greedy format."""
    hops = []
    for i in range(len(waypoints) - 1):
        p0, p1 = waypoints[i], waypoints[i + 1]
        hops.append({
            "from":               list(p0),
            "to":                 list(p1),
            "best_candidate_idx": 0,
            "cost":               math.dist(p0, p1),
            "detour":             False,
            "detour_waypoint":    None,
        })
    return hops


def run_hop_loop(image,
                 start_pos: Tuple[int, int],
                 goal_pos: Tuple[int, int],
                 obstacle_boxes: List[dict],
                 cfg,
                 floor_y_top: Optional[int] = None) -> List[dict]:
    """Return list of hop records {from, to, best_candidate_idx, cost, detour, detour_waypoint}."""
    valid_boxes = _filter_boxes(obstacle_boxes, goal_pos, image.shape,
                               start_pos=tuple(start_pos))

    # Floor awareness: if the goal is above the floor line, lower the constraint
    # so the robot can actually reach it (destination exception).
    if floor_y_top is not None:
        goal_tol = getattr(cfg, "GOAL_TOLERANCE_PX", 25)
        if goal_pos[1] < floor_y_top:
            floor_y_top = max(0, goal_pos[1] - goal_tol)
            print(f"[hop_loop] Goal above floor line — relaxing floor_y_top to {floor_y_top}")

    # ── A* pather (optional) ─────────────────────────────────────────────────
    if getattr(cfg, "PATHER", "detour") == "astar":
        from navigation.astar import astar_path
        cell_size = getattr(cfg, "ASTAR_CELL_SIZE", 10)
        waypoints = astar_path(start_pos, goal_pos, valid_boxes,
                               image.shape, cell_size)
        if waypoints is not None:
            print(f"[A*] Path found: {len(waypoints)} waypoints")
            return _waypoints_to_hops(waypoints)
        print("[A*] No path found - falling back to greedy detour")

    pos: Tuple[int, int] = tuple(start_pos)
    goal: Tuple[int, int] = tuple(goal_pos)
    hops: List[dict] = []
    committed_detour = None  # (waypoint, blocking_box) or None

    for _ in range(cfg.MAX_HOPS):
        dist_to_goal = math.dist(pos, goal)
        if dist_to_goal <= cfg.GOAL_TOLERANCE_PX:
            break

        # ── manage committed detour ──────────────────────────────────────────
        if committed_detour is not None:
            wp, blk = committed_detour
            if math.dist(pos, wp) <= cfg.GOAL_TOLERANCE_PX:
                # Reached the detour waypoint; resume toward goal
                committed_detour = None
                sub_goal = goal
            elif _find_blocking_box(pos, goal, valid_boxes) is None:
                # Direct path is now clear
                committed_detour = None
                sub_goal = goal
            else:
                sub_goal = wp
        else:
            sub_goal = goal

        # ── commit a new detour if the direct path to goal is blocked ────────
        if committed_detour is None and sub_goal == goal:
            blk = _find_blocking_box(pos, goal, valid_boxes)
            if blk is not None:
                wp = compute_detour(pos, goal, blk, image.shape)
                committed_detour = (wp, blk)
                sub_goal = wp

        # ── step length ──────────────────────────────────────────────────────
        dist_to_sub = math.dist(pos, sub_goal)
        step_len = max(cfg.MIN_STEP_PIXELS, cfg.STEP_FRACTION * dist_to_goal)
        step_len = min(step_len, dist_to_sub)
        step_len = int(step_len)

        if step_len < 1:
            break

        # ── generate candidates + cost-select ────────────────────────────────
        candidates = generate_candidates(pos, sub_goal, step_len)

        # Floor awareness: drop candidates whose endpoint is in the wall/ceiling
        # region (y < floor_y_top).  Exception: landing within GOAL_TOLERANCE of
        # the final goal is always allowed so the agent can still reach it.
        if floor_y_top is not None:
            goal_tol = getattr(cfg, "GOAL_TOLERANCE_PX", 25)
            on_floor = [c for c in candidates
                        if c["end"][1] >= floor_y_top
                        or math.dist(c["end"], goal) <= goal_tol]
            if on_floor:
                candidates = on_floor  # keep originals if ALL would be filtered

        costs = [
            compute_cost(
                simulate_trajectory(pos, c, valid_boxes, image.shape),
                goal,
                cfg.COLLISION_PENALTY,
            )
            for c in candidates
        ]
        best_idx = select_best(candidates, costs)
        new_pos = validate_click(candidates[best_idx]["end"], image.shape)

        hops.append({
            "from": list(pos),
            "to": list(new_pos),
            "best_candidate_idx": best_idx,
            "cost": costs[best_idx],
            "detour": committed_detour is not None,
            "detour_waypoint": list(committed_detour[0]) if committed_detour else None,
        })
        pos = new_pos

    return hops
