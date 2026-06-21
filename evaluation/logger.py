"""Write log.json with set/frozenset-safe serialisation."""
from __future__ import annotations
import json
from pathlib import Path


class _SafeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (set, frozenset)):
            return sorted(obj)
        return super().default(obj)


def log_run(run_result, save_path: str = "outputs/log.json") -> None:
    """Serialise RunResult to log.json using set-safe encoder."""
    raise NotImplementedError
