"""HSV cross-check: verify a detected point lands on a matching-colour region.

Prevents the 'located on empty floor' failure by rejecting off-object points.
"""
from __future__ import annotations
from typing import Optional, Tuple

import cv2
import numpy as np

# OpenCV HSV: H 0-179, S 0-255, V 0-255
# Each entry is a list of (lower_bound, upper_bound) tuples
_COLOR_RANGES: dict[str, list] = {
    "red":    [((0,   80,  80),  (10,  255, 255)),
               ((160, 80,  80),  (179, 255, 255))],
    "orange": [((10,  100, 100), (25,  255, 255))],
    "yellow": [((22,  100, 100), (38,  255, 255))],
    "green":  [((35,  50,  50),  (90,  255, 255))],
    "cyan":   [((80,  50,  50),  (100, 255, 255))],
    "blue":   [((90,  50,  50),  (130, 255, 255))],
    "purple": [((125, 50,  50),  (160, 255, 255))],
    "pink":   [((155, 50,  100), (175, 255, 255))],
    "white":  [((0,   0,   180), (179, 40,  255))],
    "grey":   [((0,   0,   60),  (179, 50,  180))],
    "gray":   [((0,   0,   60),  (179, 50,  180))],
    "black":  [((0,   0,   0),   (179, 255, 55))],
}

_SAMPLE_RADIUS  = 15    # pixel radius of the sampled patch
_MATCH_THRESH   = 0.15  # fraction of patch pixels that must match colour


def _extract_color(text: str) -> Optional[str]:
    """Return the first recognised colour keyword in `text`, or None."""
    t = text.lower()
    for color in _COLOR_RANGES:
        if color in t:
            return color
    return None


def _build_mask(hsv: np.ndarray, color: str) -> np.ndarray:
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for (lo, hi) in _COLOR_RANGES[color]:
        mask |= cv2.inRange(hsv,
                            np.array(lo, dtype=np.uint8),
                            np.array(hi, dtype=np.uint8))
    return mask


def verify_point(image: np.ndarray,
                 point: Tuple[int, int],
                 color_hint: Optional[str] = None) -> bool:
    """Return True if the pixel region at `point` matches the colour in color_hint.

    Returns True (pass-through) when no recognisable colour keyword is present.
    """
    if color_hint is None:
        return True
    color = _extract_color(color_hint)
    if color is None:
        return True

    x, y = int(point[0]), int(point[1])
    h, w = image.shape[:2]
    r = _SAMPLE_RADIUS
    patch = image[max(0, y - r): min(h, y + r + 1),
                  max(0, x - r): min(w, x + r + 1)]
    if patch.size == 0:
        return False

    hsv  = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    mask = _build_mask(hsv, color)
    ratio = float(mask.sum()) / (mask.shape[0] * mask.shape[1] * 255)
    return ratio >= _MATCH_THRESH


def nearest_matching_blob(image: np.ndarray,
                          color_hint: str) -> Optional[Tuple[int, int]]:
    """Return centroid of the largest blob matching the colour as a snap-to fallback."""
    color = _extract_color(color_hint)
    if color is None:
        return None

    hsv  = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = _build_mask(hsv, color)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask   = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    M = cv2.moments(largest)
    if M["m00"] == 0:
        return None
    return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
