"""Obstacle detection: Gemini scene analysis (A) + OWL-ViT tight boxes (B).

Pipeline:
  A  Ask Gemini to identify obstacle names + approximate boxes in one VLM call.
  B  Run OWL-ViT with those specific names to get tight pixel-accurate boxes.
  C  Merge Gemini boxes (conservative region) + OWL-ViT boxes (tight), apply NMS.

Fallback: if Gemini is unavailable, uses static OBSTACLE_QUERIES with OWL-ViT.
"""
from __future__ import annotations
import json
import re
import time
from typing import List, Tuple

import numpy as np

# Score assigned to Gemini-sourced boxes (treated as "high confidence region")
_GEMINI_BOX_SCORE = 0.5

# Max fraction of image area a single obstacle box may cover (filters walls/bg)
_MAX_BOX_AREA_FRAC = 0.15
# Top fraction of image excluded — above this y-ratio is ceiling/wall/background
_MIN_BOX_YMIN_FRAC = 0.10
# Hard cap on the number of distinct obstacles we will query OWL-ViT with
_MAX_OBSTACLE_LABELS = 5

_GEMINI_PROMPT = """\
A robot navigates on the floor of this room. Answer two questions in one JSON:

Return ONLY valid JSON — no markdown, no explanation:
{
  "floor": {"y_top": <int 0-1000>},
  "obstacles": [{"name": "short label", "box": [y_min, x_min, y_max, x_max]}]
}

"floor.y_top": y-coordinate (0-1000 scale) where the visible floor surface BEGINS.
  Everything above this line is wall / ceiling / background — the robot cannot go there.
  (In a typical room photo, the floor occupies the lower portion of the image.)

"obstacles": solid objects physically ON the floor that block the robot (max 5).
  box values: integers 0-1000  (0 = top-left, 1000 = bottom-right)

  INCLUDE only floor-level obstacles:
  - Boxes, crates, bins, laundry baskets, bags, suitcases on the floor
  - Chairs, stools, tables with legs visible on the floor
  - People, pets, vehicles on the floor

  DO NOT INCLUDE:
  - Walls, doors, door frames, baseboards
  - Ceiling, ceiling lights
  - Windows, curtains, blinds
  - Pictures, shelves on walls
  - Objects in the far background
  - The floor surface itself

If no floor obstacles: {"floor": {"y_top": <int>}, "obstacles": []}"""


# ── public API ────────────────────────────────────────────────────────────────

def detect_obstacles(image: np.ndarray, cfg) -> Tuple[List[dict], int | None]:
    """Run A+B pipeline; return (obstacle_boxes, floor_y_top_px).

    obstacle_boxes: list of {"x1","y1","x2","y2"} ready for hop_loop.
    floor_y_top_px: pixel y where the floor surface starts (None if unknown).
                    Everything above this line is wall/ceiling — robot must
                    stay below it.

    Step A: Gemini identifies obstacle names + approximate boxes + floor line.
    Step B: OWL-ViT refines boxes using those specific names.
    Step C: NMS merges; virtual wall added above floor line.
    """
    if not getattr(cfg, "DETECT_OBSTACLES", True):
        return [], None

    threshold = getattr(cfg, "OBSTACLE_THRESHOLD", 0.01)
    model_id  = getattr(cfg, "DETECTOR_MODEL_ID", "google/owlvit-base-patch32")

    # ── Step A: Gemini scene analysis ────────────────────────────────────────
    gemini_labels: List[str]  = []
    gemini_boxes:  List[dict] = []
    floor_y_top:   int | None = None
    gemini_ok = False
    try:
        gemini_labels, gemini_boxes, floor_y_top = _ask_gemini_obstacles(image, cfg)
        gemini_ok = True
        print(f"[obstacles] Gemini found {len(gemini_labels)} obstacle type(s): "
              f"{gemini_labels}")
        for b in gemini_boxes:
            print(f"  Gemini  ({b['x1']},{b['y1']})-({b['x2']},{b['y2']})  "
                  f"label={b.get('label','?')}")
    except Exception as exc:
        print(f"[obstacles] Gemini scene analysis failed ({exc!r}) "
              f"- falling back to static queries")

    # ── Step B: OWL-ViT with Gemini labels (or static fallback) ──────────────
    # If Gemini succeeded but found nothing, trust it (skip OWL-ViT to avoid
    # false positives from generic queries).  If Gemini failed, fall back.
    if gemini_ok:
        queries = gemini_labels          # may be empty — that's valid
    else:
        queries = getattr(cfg, "OBSTACLE_QUERIES",
                          ["block", "box", "cube", "chair", "table", "object"])

    owl_boxes: List[dict] = []
    if queries:
        from localization.detector import locate_all
        t0 = time.time()
        raw_owl = locate_all(image, queries, threshold=threshold,
                             model_id=model_id)
        elapsed = round(time.time() - t0, 2)
        h_img, w_img = image.shape[:2]
        owl_boxes = []
        for b in raw_owl:
            bw, bh = b["x2"] - b["x1"], b["y2"] - b["y1"]
            if bw > 0 and bh / bw > 2.5:
                continue   # tall-narrow false positive (door, wall edge)
            owl_boxes.append(b)
        print(f"[obstacles] OWL-ViT: {len(owl_boxes)} box(es) kept "
              f"({len(raw_owl)} raw) in {elapsed}s  queries={queries}")
        for b in owl_boxes:
            print(f"  OWL-ViT ({b['x1']},{b['y1']})-({b['x2']},{b['y2']})  "
                  f"score={b['score']:.3f}")

    # ── Step C: Merge + NMS ──────────────────────────────────────────────────
    all_boxes = gemini_boxes + owl_boxes
    if not all_boxes:
        print("[obstacles] No obstacles detected")
        return []

    deduped = _nms(all_boxes, iou_threshold=0.3)
    print(f"[obstacles] {len(deduped)} obstacle(s) after NMS")

    clean = [{"x1": b["x1"], "y1": b["y1"],
              "x2": b["x2"], "y2": b["y2"]} for b in deduped]
    return clean, floor_y_top


# ── Gemini scene analysis ─────────────────────────────────────────────────────

def _ask_gemini_obstacles(image: np.ndarray,
                          cfg) -> Tuple[List[str], List[dict], int | None]:
    """Call Gemini with the image; parse obstacle names + boxes + floor y_top.

    Returns (labels, pixel_boxes, floor_y_top_px).
    floor_y_top_px: pixel y where floor starts (None if Gemini didn't return it).
    Boxes use score=_GEMINI_BOX_SCORE so they win NMS over OWL-ViT sub-boxes.
    """
    from vlm.api_backend import ask_vlm
    raw = ask_vlm(_GEMINI_PROMPT, cfg, image=image)
    parsed = _extract_json(raw)

    h, w = image.shape[:2]

    # Parse floor region
    floor_y_top_px: int | None = None
    floor_data = parsed.get("floor", {})
    if isinstance(floor_data, dict) and "y_top" in floor_data:
        try:
            floor_y_top_px = max(0, int(int(floor_data["y_top"]) / 1000 * h))
            print(f"[obstacles] Floor starts at y={floor_y_top_px}px "
                  f"({floor_data['y_top']}/1000)")
        except (TypeError, ValueError):
            pass

    obstacles = parsed.get("obstacles", [])
    if not isinstance(obstacles, list):
        return [], [], floor_y_top_px


    img_area  = h * w
    labels: List[str]  = []
    boxes:  List[dict] = []

    for o in obstacles:
        name = o.get("name") or o.get("label") or ""

        raw_box = o.get("box") or o.get("bbox") or o.get("bounding_box")
        if not raw_box or len(raw_box) != 4:
            if name:
                labels.append(name)
            continue

        # Gemini returns [y_min, x_min, y_max, x_max] in 0-1000 scale
        y_min_n, x_min_n, y_max_n, x_max_n = raw_box
        x1 = max(0,   int(x_min_n / 1000 * w))
        y1 = max(0,   int(y_min_n / 1000 * h))
        x2 = min(w-1, int(x_max_n / 1000 * w))
        y2 = min(h-1, int(y_max_n / 1000 * h))

        if x2 <= x1 or y2 <= y1:
            continue

        # ── post-filters: reject background / full-scene / tall-narrow boxes ──
        box_area = (x2 - x1) * (y2 - y1)
        bw, bh   = x2 - x1, y2 - y1
        if box_area > _MAX_BOX_AREA_FRAC * img_area:
            print(f"  [filter] dropped '{name}' — area {box_area/img_area:.0%} > {_MAX_BOX_AREA_FRAC:.0%}")
            continue
        if y1 < _MIN_BOX_YMIN_FRAC * h:
            print(f"  [filter] dropped '{name}' — top edge {y1/h:.0%} above limit")
            continue
        if bw > 0 and bh / bw > 2.5:
            print(f"  [filter] dropped '{name}' — tall-narrow (h/w={bh/bw:.1f}) looks like door/wall")
            continue

        if name:
            labels.append(name)
        boxes.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2,
                      "score": _GEMINI_BOX_SCORE, "label": name})

    # Deduplicate labels (same label from two separate objects → one OWL-ViT query)
    seen: set = set()
    unique_labels = [lb for lb in labels if not (lb in seen or seen.add(lb))]
    # Cap labels fed to OWL-ViT to avoid query explosion
    return unique_labels[:_MAX_OBSTACLE_LABELS], boxes, floor_y_top_px


def _extract_json(text: str) -> dict:
    """Strip markdown fences and return the first JSON object."""
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in Gemini response: {text[:200]!r}")
    return json.loads(match.group())


# ── IoU-based NMS ─────────────────────────────────────────────────────────────

def _iou(a: dict, b: dict) -> float:
    ix1 = max(a["x1"], b["x1"])
    iy1 = max(a["y1"], b["y1"])
    ix2 = min(a["x2"], b["x2"])
    iy2 = min(a["y2"], b["y2"])
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter  = (ix2 - ix1) * (iy2 - iy1)
    area_a = (a["x2"] - a["x1"]) * (a["y2"] - a["y1"])
    area_b = (b["x2"] - b["x1"]) * (b["y2"] - b["y1"])
    union  = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _nms(boxes: list, iou_threshold: float = 0.5) -> list:
    """Greedy NMS — highest score wins when two boxes overlap significantly."""
    boxes = sorted(boxes, key=lambda b: b["score"], reverse=True)
    keep: list = []
    for b in boxes:
        if all(_iou(b, k) < iou_threshold for k in keep):
            keep.append(b)
    return keep
