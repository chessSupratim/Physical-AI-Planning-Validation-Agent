"""Unified VLM / LLM backend — routes to Gemini or Claude based on cfg.VLM_BACKEND."""
from __future__ import annotations
import io
import os
from typing import Optional

import numpy as np
from dotenv import load_dotenv

load_dotenv()


def ask_vlm(prompt: str, cfg, image: Optional[np.ndarray] = None) -> str:
    """Send `prompt` (+ optional image) to the configured backend; return text response."""
    backend = getattr(cfg, "VLM_BACKEND", "gemini")
    model   = getattr(cfg, "GEMINI_MODEL", "gemini-2.0-flash-lite")

    if backend == "gemini":
        return _ask_gemini(prompt, model, image)
    if backend == "claude":
        return _ask_claude(prompt, image)
    raise ValueError(f"Unknown VLM_BACKEND: {backend!r}  (expected 'gemini' or 'claude')")


# ── Gemini ───────────────────────────────────────────────────────────────────

def _ask_gemini(prompt: str, model: str,
                image: Optional[np.ndarray] = None) -> str:
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in .env")

    client = genai.Client(api_key=api_key)

    if image is not None:
        import cv2
        from PIL import Image as PILImage
        pil_img = PILImage.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        contents = [pil_img, prompt]
    else:
        contents = prompt

    response = client.models.generate_content(model=model, contents=contents)
    return response.text


# ── Claude ───────────────────────────────────────────────────────────────────

def _ask_claude(prompt: str, image: Optional[np.ndarray] = None) -> str:
    import anthropic
    import base64
    import cv2
    from PIL import Image as PILImage

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in .env")

    client = anthropic.Anthropic(api_key=api_key)

    if image is not None:
        pil_img = PILImage.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        content = [
            {
                "type": "image",
                "source": {
                    "type":       "base64",
                    "media_type": "image/png",
                    "data":       img_b64,
                },
            },
            {"type": "text", "text": prompt},
        ]
    else:
        content = prompt

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": content}],
    )
    return message.content[0].text
