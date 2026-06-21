"""Mode A: parse a messy natural-language instruction into {source, target} JSON.

The LLM returns STRICT JSON only:
  {"source": {"type": "direction|object|memory", "value": "..."},
   "target": {"type": "direction|object|memory", "value": "..."}}
The LLM never returns pixel coordinates.
"""
from __future__ import annotations
from typing import Optional


def parse_intent(instruction: str, session_context: Optional[dict] = None) -> dict:
    """Return {source: {type, value}, target: {type, value}} from a raw instruction."""
    raise NotImplementedError


def _keyword_fallback(instruction: str) -> dict:
    """Deterministic keyword parser used when the LLM is unavailable (logged as degraded)."""
    raise NotImplementedError
