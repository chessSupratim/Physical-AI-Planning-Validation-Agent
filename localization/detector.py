"""OWL-ViT (or Grounding DINO) object detector — load once, reuse across calls."""
from __future__ import annotations
from typing import Optional, Tuple
import numpy as np

_model = None
_processor = None


def load_detector(model_id: str):
    """Load and cache the detector model + processor."""
    raise NotImplementedError


def locate(image: np.ndarray, description: str,
           threshold: float = 0.1) -> Optional[dict]:
    """Return {box, center, score} for the best match above threshold, or None."""
    raise NotImplementedError
