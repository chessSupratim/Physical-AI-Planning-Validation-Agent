# CLAUDE.md — Physical AI Planning & Validation Agent

## Project overview

A **Physical AI Planning and Validation Agent** that takes an image and a start/goal (either from a typed instruction or two manual clicks) and produces a validated hop-by-hop trajectory from start to goal, routing around obstacles. Outputs include an animated GIF and a trail-line still image, plus structured logs and LLM reasoning.

Full spec: `SPEC_new.md` | Full build plan: `PLAN.md`

---

## CRITICAL — Virtual environment

A virtualenv named **`my_env`** exists in the project root. It **MUST** be activated before every `pip install` and every `python`/`streamlit` command. Never install into system Python. Never create a new venv.

```powershell
# Windows PowerShell (user's shell)
my_env\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source my_env/bin/activate
```

**Rules:**
- Always activate `my_env` first, then run `pip install -r requirements.txt`.
- New packages go into `requirements.txt` before installing.
- A typical session: activate → `pip install -r requirements.txt` → `python main.py ...`

---

## Build order (step-gated — approval required before each step)

```
0 venv + requirements.txt
→ 1 skeleton + config.py
→ 2 CLI navigation core, BOTH modes headless (GIF + trail.png)
→ 3 Click mode UI in Streamlit (Mode B)
→ 4 Object detector localization (OWL-ViT / Grounding DINO)
→ 5 Direction goals + misspelling tolerance
→ 6 LLM intent parser (Mode A)
→ 7 MANDATORY LLM reasoning (every run)
→ 8 Session context (st.session_state)
→ 9 (OPTIONAL) A* pather
→ 10 Metrics + README + deploy
```

**At every step:** state what will be built, STOP for approval, implement, summarize + show test command, STOP again before the next step.

---

## Separation of concerns (SPEC §2 — core rule)

| Job | Tool |
|---|---|
| Parse messy sentence → structured intent | LLM (intent parser) |
| Find a named object's pixel location | Object detector (OWL-ViT / Grounding DINO) |
| Direction targets ("bottom left") | Heuristic `_goal_to_pixel` |
| Navigate / avoid obstacles | Deterministic geometry (hops + detour / A*) |
| Reason about / explain the path | LLM / VLM |
| Manual start/goal | User clicks (bypasses localization entirely) |

**The LLM never returns pixel coordinates.** Coordinates come only from the detector or the heuristic.

---

## Input modes

### Mode B — Click (primary demo path, most reliable)
User clicks red START, then yellow GOAL directly on the image. No LLM, no detector, no localization needed. The clicked pixels ARE `start_pos` / `goal_pos`. Implemented with `streamlit-image-coordinates`.

### Mode A — Prompt
User types a (possibly messy) instruction → LLM intent parser → `{source, target}` JSON → router resolves each to a pixel via detector or heuristic → HSV cross-check → `start_pos`, `goal_pos`.

**Both modes call the identical `run_pipeline(image, start_pos, goal_pos, cfg)` from `core.py` — all downstream steps are the same.**

---

## CLI test commands (both modes)

```powershell
# Click / coordinate mode (no localization models needed)
python main.py --image data/images/2d-1.png --start 240,718 --goal-xy 1003,283

# Prompt mode
python main.py --image data/images/3d-1.png --goal "move to the bench" --vlm gemini
```

---

## Navigation core rules (SPEC §7)

- **Multi-hop straight stepping** using `STEP_FRACTION` / `MIN_STEP_PIXELS`; never overshoots goal.
- **Full-line obstacle look-ahead every hop** before committing a move.
- **Committed detour waypoint** (no oscillation): compute ONE perpendicular detour, store it, keep advancing to it until the direct path to goal is clear.
- **Goal-inside-obstacle** exception: an obstacle box containing the goal does NOT block (destination is not a wall).
- **Discard hallucinated boxes** spanning > 80 % of image width or height.
- Detect obstacles **once per run**, reuse across hops (no per-hop model calls).
- Graceful stop within `GOAL_TOLERANCE_PX` or at the closest reachable point.

---

## Reasoning — MANDATORY (SPEC §8)

Every run (CLI and UI) **must** produce a non-empty reasoning string:
1. After navigation, call the LLM with the hop summary → natural-language explanation.
2. If the LLM call fails: retry once, then emit a deterministic fallback string built from the hop log (e.g. "Reached goal in N hops with M detours around detected obstacles").
3. The reasoning field is **never empty**. It is displayed in the UI and saved in `log.json`.

---

## Key configuration (config.py — SPEC §14)

```python
DEFAULT_INPUT_MODE   = "click"
VLM_BACKEND          = "gemini"          # "gemini" | "claude"
GEMINI_MODEL         = "gemini-3.1-flash-lite"
USE_LLM_PARSER       = True
USE_DETECTOR         = True
DETECTOR_MODEL_ID    = "google/owlvit-base-patch32"
DETECTOR_THRESHOLD   = 0.1
LOCALIZER_ORDER      = ["detector", "vlm"]
HSV_VERIFY           = True
STEP_FRACTION        = 0.30
MIN_STEP_PIXELS      = 30
MAX_HOPS             = 40
GOAL_TOLERANCE_PX    = 25
PATHER               = "detour"          # "detour" | "astar"
COLLISION_PENALTY    = 10000
GIF_FPS              = 6
SAVE_TRAIL_STILL     = True
SESSION_CONTEXT      = True
```

---

## Repository structure (SPEC §13)

```
Project_DL/
├── my_env/                     # EXISTING virtualenv — never recreate
├── .env                        # GEMINI_API_KEY / ANTHROPIC_API_KEY (never commit)
├── .gitignore
├── requirements.txt
├── config.py
├── core.py                     # run_pipeline(image, start_pos, goal_pos, cfg) -> RunResult
├── main.py                     # CLI: --image, --goal | --start/--goal-xy, --vlm
├── app.py                      # Streamlit app
├── input/
│   ├── intent_parser.py        # LLM: messy prompt -> {source, target} JSON
│   └── click_input.py          # Mode B helpers
├── localization/
│   ├── router.py               # {type,value} -> detector | heuristic | memory
│   ├── detector.py             # OWL-ViT / Grounding DINO (load once)
│   ├── heuristic.py            # _goal_to_pixel(direction, image_shape)
│   └── hsv_verify.py           # cross-check point lands on matching-color region
├── pivot/
│   ├── generator.py            # straight candidate arrows (PIVOT-style)
│   └── visual_prompt.py        # draw candidates on image
├── navigation/
│   ├── hop_loop.py             # multi-hop stepping + per-hop obstacle check
│   ├── detour.py               # committed detour waypoint logic
│   ├── astar.py                # OPTIONAL grid A* pather
│   ├── rollout.py              # simulate_trajectory -> SimulationResult
│   └── cost_function.py        # compute_cost; validator/select_best
├── reasoning/
│   └── explain.py              # MANDATORY LLM reasoning + deterministic fallback
├── vlm/
│   └── api_backend.py          # ask_vlm(image, prompt) -> gemini | claude
├── visualization/
│   ├── draw.py                 # candidates.png, selected.png, final.png, trail.png
│   └── animate.py              # trajectory.gif
├── memory/
│   └── session.py              # st.session_state helpers
├── evaluation/
│   ├── logger.py               # log.json (set/frozenset-safe)
│   └── metrics.py              # task success, goal-distance error, path cost, collision rate
├── data/images/                # 2d-*.png, 3d-*.png
└── outputs/                    # per-run artifacts (gitignored)
```

---

## Outputs per run

| File | Description |
|---|---|
| `outputs/trajectory.gif` | Animated hops over the fixed background image |
| `outputs/trail.png` | Trail-line still: full path drawn on original image, start (red) + goal (yellow) |
| `outputs/candidates.png` | Hop-0 candidate arrows |
| `outputs/selected.png` | Best candidate per hop |
| `outputs/final.png` | Mover at goal with full trail |
| `outputs/log.json` | Hop table + decisions (set-safe serialization) |

---

## Secrets / API keys

- `.env` holds `GEMINI_API_KEY` and `ANTHROPIC_API_KEY`.
- `.env` is gitignored and never committed.
- `vlm/api_backend.py` reads keys via `python-dotenv`.

---

## Deployment target

Streamlit Community Cloud (free, deploy from GitHub). Fallback: Hugging Face Spaces if models exceed ~1 GB RAM. Both run the same `app.py` unchanged. OWL-ViT downloads ~600 MB on first cold start.
