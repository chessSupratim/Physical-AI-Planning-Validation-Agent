"""Unified VLM / LLM backend — routes to Gemini or Claude based on cfg.VLM_BACKEND."""
from __future__ import annotations
from typing import Optional
import numpy as np


def ask_vlm(prompt: str, cfg, image: Optional[np.ndarray] = None) -> str:
    """Send `prompt` (+ optional image) to the configured backend; return text response."""
    raise NotImplementedError


def _ask_gemini(prompt: str, model: str,
                image: Optional[np.ndarray] = None) -> str:
    raise NotImplementedError


def _ask_claude(prompt: str, image: Optional[np.ndarray] = None) -> str:
    raise NotImplementedError
