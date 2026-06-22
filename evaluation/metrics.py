"""Evaluation metrics: task success, goal-distance error, path cost, collision rate."""
from __future__ import annotations
import math
from typing import Tuple


def task_success(final_pos: Tuple[int, int],
                 goal_pos:  Tuple[int, int],
                 tolerance_px: int) -> bool:
    """True if the agent reached within tolerance_px of the goal."""
    return math.dist(final_pos, goal_pos) <= tolerance_px


def goal_distance_error(final_pos: Tuple[int, int],
                        goal_pos:  Tuple[int, int]) -> float:
    """Euclidean distance (px) between final position and goal."""
    return math.dist(final_pos, goal_pos)


def path_cost(hops: list) -> float:
    """Total Euclidean path length in pixels across all hops."""
    return sum(math.dist(h["from"], h["to"]) for h in hops)


def collision_rate(hops: list) -> float:
    """Fraction of hops that involved a committed detour (0.0–1.0)."""
    if not hops:
        return 0.0
    return sum(1 for h in hops if h.get("detour")) / len(hops)


def compute_metrics(run_result, tolerance_px: int = 25) -> dict:
    """Return all four metrics as a flat dict.

    Keys: task_success, goal_distance_error_px, path_cost_px, collision_rate,
          n_hops, reached_goal.
    """
    fp = run_result.final_pos
    gp = run_result.goal_pos
    hs = run_result.hops
    return {
        "task_success":          task_success(fp, gp, tolerance_px),
        "goal_distance_error_px": round(goal_distance_error(fp, gp), 1),
        "path_cost_px":          round(path_cost(hs), 1),
        "collision_rate":        round(collision_rate(hs), 3),
        "n_hops":                len(hs),
        "reached_goal":          run_result.reached_goal,
    }


def print_metrics(run_result, tolerance_px: int = 25) -> None:
    """Print a formatted metrics summary to stdout."""
    m = compute_metrics(run_result, tolerance_px=tolerance_px)
    print("\n=== Metrics ===")
    print(f"  Task success:          {'YES' if m['task_success'] else 'NO'}")
    print(f"  Goal distance error:   {m['goal_distance_error_px']} px")
    print(f"  Path cost:             {m['path_cost_px']} px")
    print(f"  Collision (detour) rate: {m['collision_rate']:.1%}")
    print(f"  Hops:                  {m['n_hops']}")
