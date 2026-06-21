"""Central pipeline: given two pixel points, navigate and produce all outputs."""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

from navigation.hop_loop import run_hop_loop
from pivot.generator import generate_candidates
from visualization.draw import (draw_candidates_png, draw_selected_png,
                                draw_final_png, draw_trail_png)
from visualization.animate import create_trajectory_gif
from evaluation.logger import log_run
from reasoning.explain import explain_plan


@dataclass
class RunResult:
    start_pos:    Tuple[int, int]
    goal_pos:     Tuple[int, int]
    hops:         List[dict] = field(default_factory=list)
    final_pos:    Tuple[int, int] = (0, 0)
    reasoning:    str = ""
    reached_goal: bool = False
    output_paths: dict = field(default_factory=dict)


def run_pipeline(image: np.ndarray,
                 start_pos: Tuple[int, int],
                 goal_pos:  Tuple[int, int],
                 cfg) -> RunResult:
    """Main entry point called by both CLI and Streamlit.

    obstacle_boxes are detected once before the loop (Steps 4+).
    For Steps 2–3 the list is empty and the path is a straight multi-hop line.
    """
    Path("outputs").mkdir(exist_ok=True)

    # Obstacles detected once per run (populated in Step 4)
    obstacle_boxes: List[dict] = []

    # ── navigation ───────────────────────────────────────────────────────────
    hops = run_hop_loop(image, start_pos, goal_pos, obstacle_boxes, cfg)

    final_pos = tuple(hops[-1]["to"]) if hops else tuple(start_pos)
    reached_goal = math.dist(final_pos, goal_pos) <= cfg.GOAL_TOLERANCE_PX

    # ── reasoning (mandatory) ────────────────────────────────────────────────
    reasoning = explain_plan(hops, goal_pos, cfg)

    # ── visualisations ───────────────────────────────────────────────────────
    output_paths: dict = {}

    # Initial candidates (hop 0 direction) — for candidates.png
    init_dist = math.dist(start_pos, goal_pos)
    init_step = max(cfg.MIN_STEP_PIXELS, int(cfg.STEP_FRACTION * init_dist))
    init_candidates = generate_candidates(start_pos, goal_pos, init_step)

    p_cand = "outputs/candidates.png"
    draw_candidates_png(image, init_candidates, start_pos, goal_pos, p_cand)
    output_paths["candidates"] = p_cand

    p_sel = "outputs/selected.png"
    draw_selected_png(image, hops, start_pos, goal_pos, p_sel)
    output_paths["selected"] = p_sel

    p_final = "outputs/final.png"
    draw_final_png(image, hops, start_pos, goal_pos, p_final)
    output_paths["final"] = p_final

    if cfg.SAVE_TRAIL_STILL:
        p_trail = "outputs/trail.png"
        draw_trail_png(image, hops, start_pos, goal_pos, p_trail)
        output_paths["trail"] = p_trail

    p_gif = "outputs/trajectory.gif"
    create_trajectory_gif(image, hops, start_pos, goal_pos, p_gif, cfg.GIF_FPS)
    output_paths["gif"] = p_gif

    # ── log ──────────────────────────────────────────────────────────────────
    result = RunResult(
        start_pos=tuple(start_pos),
        goal_pos=tuple(goal_pos),
        hops=hops,
        final_pos=final_pos,
        reasoning=reasoning,
        reached_goal=reached_goal,
        output_paths=output_paths,
    )
    p_log = "outputs/log.json"
    log_run(result, p_log)
    result.output_paths["log"] = p_log

    return result
