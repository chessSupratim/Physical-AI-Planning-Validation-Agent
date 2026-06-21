"""Map direction phrases to pixel coordinates — deterministic, no model needed.

Pixel layout (image coords: y increases downward):
  top-left     (w/4, h/4)   |  top-center  (cx, h/4)  |  top-right     (3w/4, h/4)
  center-left  (w/4,  cy)   |  center      (cx,  cy)  |  center-right  (3w/4,  cy)
  bottom-left  (w/4, 3h/4)  |  bot-center  (cx, 3h/4) |  bottom-right  (3w/4, 3h/4)
"""
from __future__ import annotations
from typing import Tuple

# Word-level alias table: raw token → canonical keyword
# Covers common misspellings, synonyms, and phrase fragments
_WORD_MAP: dict[str, str] = {
    # top synonyms / misspellings
    "upper":  "top",
    "above":  "top",
    "up":     "top",
    "tpo":    "top",
    "tp":     "top",
    # bottom synonyms / misspellings
    "lower":  "bottom",
    "below":  "bottom",
    "down":   "bottom",
    "buttom": "bottom",
    "botton": "bottom",
    "bottm":  "bottom",
    "bttom":  "bottom",
    "bot":    "bottom",
    # left misspellings
    "lft":    "left",
    "lef":    "left",
    # right misspellings
    "rght":   "right",
    "rgt":    "right",
    "ight":   "right",
    # center synonyms
    "centre": "center",
    "middle": "center",
    "mid":    "center",
}

# Punctuation to strip before tokenising
_STRIP = str.maketrans("", "", "-_,.")


def _normalise(phrase: str) -> str:
    """Lowercase, strip punctuation, apply alias table; return canonical tokens string."""
    tokens = phrase.lower().translate(_STRIP).split()
    return " ".join(_WORD_MAP.get(t, t) for t in tokens)


def goal_to_pixel(direction: str, image_shape: tuple) -> Tuple[int, int]:
    """Return (x, y) pixel for a direction phrase given image shape (H, W[, C]).

    Misspelling-tolerant via _normalise.  Unknown phrases default to image centre.
    """
    h, w = image_shape[:2]
    cx, cy = w // 2, h // 2

    n = _normalise(direction)

    has_top    = "top"    in n.split()
    has_bottom = "bottom" in n.split()
    has_left   = "left"   in n.split()
    has_right  = "right"  in n.split()
    has_center = "center" in n.split()

    # "corner" without a vertical qualifier → treat as top (per SPEC §6)
    if "corner" in n and not has_top and not has_bottom:
        has_top = True

    # Diagonals
    if has_top    and has_left:  return (w // 4,     h // 4)
    if has_top    and has_right: return (3 * w // 4, h // 4)
    if has_bottom and has_left:  return (w // 4,     3 * h // 4)
    if has_bottom and has_right: return (3 * w // 4, 3 * h // 4)

    # Cardinals
    if has_top:    return (cx,         h // 4)
    if has_bottom: return (cx,         3 * h // 4)
    if has_left:   return (w // 4,     cy)
    if has_right:  return (3 * w // 4, cy)
    if has_center: return (cx,         cy)

    # Fallback: image centre (logged by caller)
    return (cx, cy)
