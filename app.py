"""Streamlit app: radio (prompt | click), upload, run, display outputs."""
from __future__ import annotations
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

import config
from core import run_pipeline
from input.click_input import validate_click
from memory.session import init_session_state, get_context, update_after_run, clear_context

# Maximum width for the interactive image display (px)
_MAX_DISPLAY_W = 720


# ── image helpers ─────────────────────────────────────────────────────────────

def _to_pil(bgr: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))


def _scale_for_display(bgr: np.ndarray):
    """Return (scale_factor, PIL image) scaled to _MAX_DISPLAY_W."""
    h, w = bgr.shape[:2]
    scale = min(1.0, _MAX_DISPLAY_W / w)
    dw, dh = int(w * scale), int(h * scale)
    return scale, _to_pil(cv2.resize(bgr, (dw, dh)))


def _annotate(bgr: np.ndarray,
              start: tuple | None = None,
              goal: tuple | None = None) -> np.ndarray:
    out = bgr.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    if start:
        cv2.circle(out, start, 14, (0, 0, 255), -1)
        cv2.circle(out, start, 14, (0, 0, 0), 2)
        cv2.putText(out, "S", (start[0] + 16, start[1] + 8), font, 0.8, (255, 255, 255), 2)
    if goal:
        cv2.circle(out, goal, 14, (0, 255, 255), -1)
        cv2.circle(out, goal, 14, (0, 0, 0), 2)
        cv2.putText(out, "G", (goal[0] + 16, goal[1] + 8), font, 0.8, (0, 0, 0), 2)
    return out


def _gif_html(path: str) -> None:
    """Display an animated GIF reliably via base64-embedded HTML."""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    st.markdown(
        f'<img src="data:image/gif;base64,{data}" style="width:100%;border-radius:4px">',
        unsafe_allow_html=True,
    )


def _png_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


# ── session state ─────────────────────────────────────────────────────────────

def _init_state() -> None:
    defaults = {
        "phase":      "start",   # start → goal → ready → done
        "image_bgr":  None,
        "image_key":  None,      # filename+size to detect new uploads
        "start_pos":  None,
        "goal_pos":   None,
        "run_result": None,
        "cur_mode":   config.DEFAULT_INPUT_MODE,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _reset_clicks() -> None:
    st.session_state.phase      = "start"
    st.session_state.start_pos  = None
    st.session_state.goal_pos   = None
    st.session_state.run_result = None


# ── results panel ─────────────────────────────────────────────────────────────

def _show_results(result) -> None:
    st.divider()
    reached = result.reached_goal
    st.success(f"{'Goal reached' if reached else 'Stopped early'} — {len(result.hops)} hops")

    # GIF + trail
    col_gif, col_trail = st.columns(2)
    with col_gif:
        st.subheader("Trajectory GIF")
        if "gif" in result.output_paths:
            _gif_html(result.output_paths["gif"])
    with col_trail:
        st.subheader("Trail Still")
        if "trail" in result.output_paths:
            st.image(_png_bytes(result.output_paths["trail"]))

    # Candidates + selected
    col_cand, col_sel = st.columns(2)
    with col_cand:
        st.subheader("Candidates (hop 0)")
        if "candidates" in result.output_paths:
            st.image(_png_bytes(result.output_paths["candidates"]))
    with col_sel:
        st.subheader("Selected per hop")
        if "selected" in result.output_paths:
            st.image(_png_bytes(result.output_paths["selected"]))

    # Hop table
    st.subheader("Hop / Cost table")
    if result.hops:
        rows = [
            {
                "Hop":    i + 1,
                "From":   str(tuple(h["from"])),
                "To":     str(tuple(h["to"])),
                "Cost":   round(h["cost"], 1),
                "Detour": "yes" if h["detour"] else "",
            }
            for i, h in enumerate(result.hops)
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    # Reasoning + log
    with st.expander("Reasoning"):
        st.write(result.reasoning)
    with st.expander("Log JSON"):
        if "log" in result.output_paths:
            with open(result.output_paths["log"]) as f:
                st.json(json.load(f))


# ── click mode UI ─────────────────────────────────────────────────────────────

def _run_pipeline(image: np.ndarray) -> None:
    start = st.session_state.start_pos
    goal  = st.session_state.goal_pos
    with st.spinner("Planning trajectory…"):
        result = run_pipeline(image, start, goal, config)
    update_after_run(result)
    st.session_state.run_result = result
    st.session_state.phase      = "done"
    st.rerun()


def _click_mode(image: np.ndarray) -> None:
    phase = st.session_state.phase

    # ── instructions ──────────────────────────────────────────────────────────
    if phase == "start":
        st.info("**Step 1 of 2** — Click the **START** position on the image (will be marked in red)")
    elif phase == "goal":
        st.info("**Step 2 of 2** — Click the **GOAL** position on the image (will be marked in yellow)")
    elif phase in ("ready", "done"):
        st.info("Start **(S)** and Goal **(G)** are set. Press **Run** to plan the trajectory.")

    # ── annotated image ───────────────────────────────────────────────────────
    annotated = _annotate(image,
                          start=st.session_state.start_pos,
                          goal=st.session_state.goal_pos)
    scale, display_pil = _scale_for_display(annotated)

    if phase in ("start", "goal"):
        # Interactive: capture next click
        coords = streamlit_image_coordinates(display_pil, key=f"click_{phase}")
        if coords is not None:
            orig = validate_click(
                (int(coords["x"] / scale), int(coords["y"] / scale)),
                image.shape,
            )
            if phase == "start":
                st.session_state.start_pos = orig
                st.session_state.phase     = "goal"
            else:
                st.session_state.goal_pos = orig
                st.session_state.phase    = "ready"
            st.rerun()
    else:
        # Static once both points are chosen
        st.image(display_pil, width=_MAX_DISPLAY_W)

    # ── action buttons ────────────────────────────────────────────────────────
    btn_col, rst_col = st.columns([2, 1])
    with btn_col:
        if phase == "ready" and st.button("Run pipeline", type="primary"):
            _run_pipeline(image)
        if phase == "done" and st.button("Run again", type="secondary"):
            _run_pipeline(image)
    with rst_col:
        if st.button("Reset"):
            _reset_clicks()
            st.rerun()

    # ── results ───────────────────────────────────────────────────────────────
    if st.session_state.run_result is not None:
        _show_results(st.session_state.run_result)


# ── prompt mode UI (Mode A) ───────────────────────────────────────────────────

def _prompt_mode(image: np.ndarray) -> None:
    st.info(
        "**Mode A — Prompt**: Type a natural-language instruction. "
        "The LLM will extract start and goal, then the detector/heuristic will resolve them to pixels."
    )

    # Image preview (static — no click needed in prompt mode)
    _, display_pil = _scale_for_display(image)
    st.image(display_pil, caption="Uploaded image", width=_MAX_DISPLAY_W)

    instruction = st.text_input(
        "Instruction",
        placeholder='e.g. "move the red block to the bottom left corner"',
        key="prompt_instruction",
    )

    col_run, col_rst = st.columns([2, 1])
    with col_run:
        run_btn = st.button("Parse & Run", type="primary",
                            disabled=not instruction.strip())
    with col_rst:
        if st.button("Reset", key="prompt_reset"):
            st.session_state.run_result = None
            st.rerun()

    if run_btn and instruction.strip():
        from input.intent_parser import parse_intent
        from localization.router import resolve
        from input.click_input import validate_click as _vc

        with st.spinner("Parsing instruction…"):
            intent = parse_intent(instruction, config,
                                  session_context=get_context())

        st.write("**Parsed intent:**", intent)

        with st.spinner("Resolving locations…"):
            start_pos = resolve(intent["source"], image, cfg=config)
            goal_pos  = resolve(intent["target"], image, cfg=config)

        if start_pos is None:
            h, w = image.shape[:2]
            start_pos = (w // 2, h // 2)
            st.warning(f"Source unresolved — using image centre {start_pos}")

        if goal_pos is None:
            st.error("Could not resolve target location. Try a more specific instruction.")
            return

        start_pos = _vc(start_pos, image.shape)
        goal_pos  = _vc(goal_pos,  image.shape)
        st.write(f"**Start:** {start_pos}   **Goal:** {goal_pos}")

        with st.spinner("Planning trajectory…"):
            result = run_pipeline(image, start_pos, goal_pos, config)

        update_after_run(result, instruction=instruction)
        st.session_state.run_result = result

    if st.session_state.run_result is not None:
        _show_results(st.session_state.run_result)


# ── main ──────────────────────────────────────────────────────────────────────

def _sidebar_context() -> None:
    """Sidebar panel: pather toggle + session history."""
    with st.sidebar:
        # ── pather selector ───────────────────────────────────────────────
        st.header("Settings")
        pather = st.radio(
            "Navigation pather",
            options=["detour", "astar"],
            format_func=lambda p: "Greedy detour (default)" if p == "detour"
                                  else "A* grid pather",
            index=0 if config.PATHER == "detour" else 1,
            key="pather_choice",
        )
        config.PATHER = pather

        st.divider()
        st.header("Session")
        ctx = get_context()
        if not ctx:
            st.caption("No runs yet this session.")
        else:
            st.metric("Runs", ctx.get("run_count", 0))
            st.write(f"**Last final pos:** {ctx.get('current_pos')}")
            st.write(f"**Last goal:** {ctx.get('last_goal')}")

            history = ctx.get("history") or []
            if history:
                with st.expander("Run history", expanded=False):
                    for h in reversed(history):
                        label = h.get("instruction", f"run {h['run']}")
                        reached = "reached" if h["reached"] else "stopped"
                        st.write(
                            f"**#{h['run']}** — {label[:40]}  \n"
                            f"start {h['start']} -> final {h['final']}  \n"
                            f"{h['hops']} hops, {reached}"
                        )

        if st.button("Clear history"):
            clear_context()
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="Physical AI Planning Agent", layout="wide",
                       initial_sidebar_state="collapsed")
    st.title("Physical AI Planning & Validation Agent")

    _init_state()
    init_session_state()
    _sidebar_context()

    # Mode radio
    mode = st.radio(
        "Input mode",
        options=["click", "prompt"],
        format_func=lambda m: "Click locations (Mode B — click start & goal)" if m == "click"
                              else "Describe with prompt (Mode A — LLM intent parser)",
        horizontal=True,
        index=0 if config.DEFAULT_INPUT_MODE == "click" else 1,
    )
    if mode != st.session_state.cur_mode:
        st.session_state.cur_mode = mode
        _reset_clicks()

    # Image upload
    uploaded = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if uploaded is None:
        st.info("Upload an image to begin.")
        return

    # Detect new upload and reload
    img_key = f"{uploaded.name}_{uploaded.size}"
    if st.session_state.image_key != img_key:
        arr = np.asarray(bytearray(uploaded.read()), dtype=np.uint8)
        st.session_state.image_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        st.session_state.image_key = img_key
        _reset_clicks()

    image = st.session_state.image_bgr
    if image is None:
        st.error("Could not decode image.")
        return

    if mode == "click":
        _click_mode(image)
    else:
        _prompt_mode(image)


if __name__ == "__main__":
    main()
