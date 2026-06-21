"""Write log.json with set/frozenset-safe serialisation."""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np


class _SafeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (set, frozenset)):
            return sorted(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def log_run(run_result, save_path: str = "outputs/log.json") -> None:
    """Serialise RunResult to log.json using set-safe encoder."""
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    data = {
        "start_pos":    run_result.start_pos,
        "goal_pos":     run_result.goal_pos,
        "reached_goal": run_result.reached_goal,
        "final_pos":    run_result.final_pos,
        "n_hops":       len(run_result.hops),
        "hops":         run_result.hops,
        "reasoning":    run_result.reasoning,
        "output_paths": run_result.output_paths,
    }
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, cls=_SafeEncoder)
