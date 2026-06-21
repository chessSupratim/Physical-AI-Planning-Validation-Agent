"""Route a {type, value} field to a pixel coordinate.

direction  -> heuristic.goal_to_pixel      (Step 5)
object     -> detector.locate + HSV verify (Step 4)
memory     -> session_state lookup         (Step 8)
"""
from __future__ import annotations
from typing import Optional, Tuple

import numpy as np


def resolve(field: dict,
            image: np.ndarray,
            session_context: Optional[dict] = None,
            cfg=None) -> Optional[Tuple[int, int]]:
    """Return (x, y) pixel for {type, value}, or None on failure."""
    ftype = field.get("type", "")
    value = field.get("value", "")

    # ── direction ────────────────────────────────────────────────────────────
    if ftype == "direction":
        from localization.heuristic import goal_to_pixel
        return goal_to_pixel(value, image.shape)

    # ── named object ─────────────────────────────────────────────────────────
    if ftype == "object":
        from localization.detector import locate
        from localization.hsv_verify import verify_point, nearest_matching_blob

        threshold = getattr(cfg, "DETECTOR_THRESHOLD", 0.1)
        model_id  = getattr(cfg, "DETECTOR_MODEL_ID",  "google/owlvit-base-patch32")
        do_hsv    = getattr(cfg, "HSV_VERIFY",          True)

        det = locate(image, value, threshold=threshold, model_id=model_id)
        if det is None:
            print(f"[router] No detection for '{value}' (threshold={threshold})")
            return None

        print(f"[router] '{value}' -> center={det['center']}  "
              f"score={det['score']:.3f}  t={det['elapsed_s']}s")

        center = det["center"]

        if do_hsv:
            if verify_point(image, center, color_hint=value):
                print(f"[router] HSV verify PASS at {center}")
            else:
                print(f"[router] HSV verify FAIL at {center} — trying blob snap")
                snap = nearest_matching_blob(image, value)
                if snap:
                    print(f"[router] Blob snap → {snap}")
                    center = snap
                else:
                    print(f"[router] No blob; accepting detector result as-is")

        return center

    # ── memory reference ─────────────────────────────────────────────────────
    if ftype == "memory":
        if session_context:
            pos = session_context.get("current_pos") or session_context.get("start_pos")
            if pos:
                return tuple(pos)
        print(f"[router] Memory ref '{value}' — no session context available")
        return None

    print(f"[router] Unknown field type: {ftype!r}")
    return None
