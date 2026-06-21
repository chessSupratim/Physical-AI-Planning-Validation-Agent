"""OWL-ViT object detector — load once, reuse across calls."""
from __future__ import annotations
import time
from typing import Optional

import cv2
import numpy as np
import torch
from PIL import Image

_processor = None
_model = None
_loaded_model_id: Optional[str] = None


def load_detector(model_id: str = "google/owlvit-base-patch32"):
    """Load and cache the OWL-ViT processor + model (no-op if already loaded)."""
    global _processor, _model, _loaded_model_id
    if _model is not None and _loaded_model_id == model_id:
        return _processor, _model

    from transformers import OwlViTForObjectDetection, OwlViTProcessor

    print(f"[detector] Loading {model_id} …")
    t0 = time.time()
    _processor = OwlViTProcessor.from_pretrained(model_id)
    _model = OwlViTForObjectDetection.from_pretrained(model_id)
    _model.eval()
    _loaded_model_id = model_id
    print(f"[detector] Model ready in {time.time() - t0:.1f}s")
    return _processor, _model


def _post_process(processor, outputs, threshold: float,
                  h: int, w: int) -> list:
    """Robust post-processing across transformers 4.x and 5.x API changes."""
    target_sizes = [(h, w)]

    # transformers 5.x: method lives on image_processor
    if hasattr(processor, "image_processor") and hasattr(
        processor.image_processor, "post_process_object_detection"
    ):
        return processor.image_processor.post_process_object_detection(
            outputs=outputs, threshold=threshold, target_sizes=target_sizes
        )

    # transformers 4.x: method lives directly on processor
    if hasattr(processor, "post_process_object_detection"):
        return processor.post_process_object_detection(
            outputs=outputs, threshold=threshold, target_sizes=target_sizes
        )

    # Last resort: decode logits + pred_boxes manually
    return _manual_post_process(outputs, threshold, h, w)


def _manual_post_process(outputs, threshold: float,
                         h: int, w: int) -> list:
    """Convert raw OWL-ViT outputs to [{boxes, scores, labels}]."""
    logits    = outputs.logits[0]       # [num_queries, num_labels]
    pred_boxes = outputs.pred_boxes[0]  # [num_queries, 4] cx,cy,bw,bh normalised

    probs          = torch.sigmoid(logits)
    scores, labels = probs.max(dim=-1)

    keep   = scores > threshold
    scores = scores[keep].detach().cpu()
    labels = labels[keep].detach().cpu()
    norm   = pred_boxes[keep].detach().cpu().numpy()

    boxes = []
    for cx, cy, bw, bh in norm:
        x1 = int((cx - bw / 2) * w)
        y1 = int((cy - bh / 2) * h)
        x2 = int((cx + bw / 2) * w)
        y2 = int((cy + bh / 2) * h)
        boxes.append([x1, y1, x2, y2])

    return [{
        "boxes":  torch.tensor(boxes, dtype=torch.float32),
        "scores": scores,
        "labels": labels,
    }]


def locate(image: np.ndarray,
           description: str,
           threshold: float = 0.1,
           model_id: str = "google/owlvit-base-patch32") -> Optional[dict]:
    """Return {box, center, score, elapsed_s} for the best match, or None.

    Uses the FULL descriptive phrase so the model can disambiguate
    between same-colour objects ('round red disc' vs 'red square').
    """
    processor, model = load_detector(model_id)

    h, w = image.shape[:2]
    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    t0 = time.time()
    inputs = processor(text=[[description]], images=pil_img, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    elapsed = round(time.time() - t0, 2)

    results = _post_process(processor, outputs, threshold, h, w)

    boxes  = results[0]["boxes"].cpu().numpy()
    scores = results[0]["scores"].cpu().numpy()

    if len(scores) == 0:
        return None

    # Discard hallucinated boxes spanning >80 % of either image dimension
    valid = (
        ((boxes[:, 2] - boxes[:, 0]) < 0.8 * w) &
        ((boxes[:, 3] - boxes[:, 1]) < 0.8 * h)
    )
    boxes, scores = boxes[valid], scores[valid]
    if len(scores) == 0:
        return None

    best = int(scores.argmax())
    x1, y1, x2, y2 = [int(c) for c in boxes[best]]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w - 1, x2), min(h - 1, y2)
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

    return {
        "box":       {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
        "center":    (cx, cy),
        "score":     float(scores[best]),
        "elapsed_s": elapsed,
    }
