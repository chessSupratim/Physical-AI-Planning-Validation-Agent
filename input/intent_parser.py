"""Mode A: parse a messy natural-language instruction into {source, target} JSON.

The LLM returns STRICT JSON only:
  {"source": {"type": "direction|object|memory", "value": "..."},
   "target": {"type": "direction|object|memory", "value": "..."}}
The LLM never returns pixel coordinates.
"""
from __future__ import annotations
import json
import re
from typing import Optional

# ── LLM prompt ───────────────────────────────────────────────────────────────

_PROMPT = """\
You are a structured intent extractor for a physical robot movement system.

Given a natural-language instruction about moving an object or agent in an image,
extract SOURCE (where it starts) and TARGET (where it should go).

Return ONLY valid JSON - no markdown, no explanation, no extra text:
{{
  "source": {{"type": "direction|object|memory", "value": "..."}},
  "target": {{"type": "direction|object|memory", "value": "..."}}
}}

Type rules:
- "direction" - a spatial region phrase: "top left", "bottom right", "center", "left side"
- "object"    - a named physical thing to locate: "bench", "round red block", "chair"
- "memory"    - refers to a prior/current position: "current position", "it", "there", "back"

Guidelines:
- Prefer direction over object for the SOURCE when a location is stated explicitly
  (e.g. "the robot is in the left corner" -> source type=direction, value="left corner")
- Use the most descriptive object name possible; include colour and shape
- NEVER return pixel coordinates
- If only a TARGET is mentioned (e.g. "go to the bench"), set source to
  {{"type": "memory", "value": "current position"}}
{context_block}
Instruction: {instruction}"""


# ── public API ───────────────────────────────────────────────────────────────

def parse_intent(instruction: str, cfg,
                 session_context: Optional[dict] = None) -> dict:
    """Return {source, target} parsed from instruction.

    Falls back to _keyword_fallback if the LLM is unavailable.
    """
    context_block = ""
    if session_context:
        context_block = f"\nSession context: {json.dumps(session_context)}\n"

    prompt = _PROMPT.format(instruction=instruction,
                            context_block=context_block)

    if getattr(cfg, "USE_LLM_PARSER", True):
        try:
            from vlm.api_backend import ask_vlm
            raw    = ask_vlm(prompt, cfg)
            result = _extract_json(raw)
            _validate(result)
            return result
        except Exception as exc:
            print(f"[intent_parser] LLM failed ({exc!r}), using keyword fallback")

    return _keyword_fallback(instruction)


# ── JSON extraction + validation ─────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """Strip markdown fences and return the first JSON object found."""
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object in LLM response: {text[:200]!r}")
    return json.loads(match.group())


def _validate(parsed: dict) -> None:
    for key in ("source", "target"):
        if key not in parsed:
            raise ValueError(f"Missing key: {key!r}")
        field = parsed[key]
        if "type" not in field or "value" not in field:
            raise ValueError(f"Field {key!r} missing type/value: {field}")
        if field["type"] not in ("direction", "object", "memory"):
            raise ValueError(f"Unknown type {field['type']!r}")


# ── keyword fallback ─────────────────────────────────────────────────────────

_DIR_TOKENS = {
    "left", "right", "top", "bottom", "upper", "lower",
    "center", "centre", "middle", "above", "below",
    "corner", "up", "down", "side",
    # common misspellings
    "buttom", "botton", "lft", "rght", "tpo",
}

_FILLER = {
    "the", "a", "an", "is", "in", "at", "on", "of", "and",
    "move", "go", "should", "needs", "navigate", "robot",
    "object", "agent", "it", "to", "from",
}


def _keyword_fallback(instruction: str) -> dict:
    """Deterministic keyword parser used when LLM is unavailable (logged as degraded)."""
    t = instruction.lower()
    parts = re.split(r"\bto\b", t, maxsplit=1)

    if len(parts) == 2:
        src_raw, tgt_raw = parts
    else:
        src_raw, tgt_raw = "", t

    src_field = _classify(src_raw) if src_raw.strip() else {
        "type": "memory", "value": "current position"
    }
    tgt_field = _classify(tgt_raw)
    return {"source": src_field, "target": tgt_field}


def _classify(text: str) -> dict:
    """Return a {type, value} field from a text fragment."""
    words = text.lower().split()
    dir_words = [w for w in words if w in _DIR_TOKENS]
    if dir_words:
        return {"type": "direction", "value": " ".join(dir_words)}
    obj_words = [w for w in words if w not in _FILLER and len(w) > 1]
    if not obj_words:
        return {"type": "memory", "value": "current position"}
    return {"type": "object", "value": " ".join(obj_words)}
