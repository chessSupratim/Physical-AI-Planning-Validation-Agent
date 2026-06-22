# Physical AI Planning & Validation Agent

A Streamlit web app (and CLI) that takes an image and a start/goal — given either by two manual clicks or by a natural-language instruction — and produces a **validated hop-by-hop trajectory** from start to goal, routing around detected obstacles.

Outputs include an **animated GIF**, a **trail-line still image**, annotated candidate arrows, a cost/hop table, LLM reasoning, and a structured log.

---

## How it works (honest framing)

| Component | What it does | What it does NOT do |
|---|---|---|
| **OWL-ViT detector** | Locates named objects in the image (e.g. "bench") by outputting a bounding box | It is not perfect on cluttered scenes; Mode B (click) is the reliable fallback |
| **Gemini VLM** | Identifies obstacle names + approximate regions + floor line from the scene | Does not navigate or return pixel coordinates for start/goal |
| **Heuristic** | Maps direction phrases ("bottom left") to pixel coordinates deterministically | Uses fixed image fractions — not camera-calibrated 3D positions |
| **Deterministic navigator** | Hops in short straight steps, checks obstacle boxes each hop, commits a perpendicular detour if blocked | 2D pixel-space only — not a physics simulator or 3D planner |
| **LLM reasoning** | Explains the resulting path in natural language | Does not plan the path — reasoning happens after navigation |

**The system treats every image as a 2D plane.** Trajectory arrows are drawn on the pixel canvas; the animated GIF replays those pixel hops. This is a planning and validation demo, not a physical robot controller.

---

## Setup

### Prerequisites
- Python 3.10+
- A virtualenv named `my_env` already exists in the project root — **never recreate it**
- API keys: `GEMINI_API_KEY` and/or `ANTHROPIC_API_KEY`

### 1 — Activate the virtualenv

```powershell
# Windows PowerShell
my_env\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source my_env/bin/activate
```

**Always activate `my_env` before installing packages or running any script.**

### 2 — Install dependencies

```powershell
pip install -r requirements.txt
```

### 3 — Set API keys

Create a `.env` file in the project root (never commit it):

```
GEMINI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

---

## Running the Streamlit app

```powershell
# venv must be active
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### Mode B — Click (most reliable)
1. Upload an image (PNG/JPG).
2. Select **"Click locations"** mode.
3. Click the **START** point on the image (marked red).
4. Click the **GOAL** point (marked yellow).
5. Press **Run pipeline**.

### Mode A — Prompt
1. Upload an image.
2. Select **"Describe with prompt"** mode.
3. Type a natural-language instruction, e.g.:
   - `"move from bottom right to the bench"`
   - `"a robot is in the left corner and should move to the boxes"`
4. Press **Parse & Run**.

The sidebar (click `›` on the left edge) lets you switch between the **greedy detour** and **A\*** pathfinders and view run history.

---

## CLI usage

### Mode B — Click simulation (no LLM or detector needed)

```powershell
python main.py --image data/images/2d-1.png --start 240,718 --goal-xy 1003,283
```

### Mode A — Prompt

```powershell
python main.py --image data/images/3d-3.png --goal "move to the bench" --vlm gemini
```

Both modes produce the same outputs and print metrics to stdout.

---

## Outputs (saved to `outputs/`)

| File | Description |
|---|---|
| `trajectory.gif` | Animated hops over the fixed image |
| `trail.png` | Full path as a single trail line, start (red) + goal (yellow) |
| `candidates.png` | Hop-0 candidate arrows with obstacle boxes |
| `selected.png` | Best candidate per hop |
| `final.png` | Mover at final position with full trail |
| `log.json` | Hop table, costs, reasoning, and output paths |

---

## Configuration (`config.py`)

| Key | Default | Description |
|---|---|---|
| `DEFAULT_INPUT_MODE` | `"click"` | Starting UI mode |
| `VLM_BACKEND` | `"gemini"` | `"gemini"` or `"claude"` |
| `GEMINI_MODEL` | `"gemini-3.1-flash-lite"` | Must use dashes + lowercase |
| `DETECT_OBSTACLES` | `True` | Run A+B obstacle pipeline |
| `FLOOR_AWARE` | `True` | Constrain path to floor region |
| `PATHER` | `"detour"` | `"detour"` or `"astar"` |
| `STEP_FRACTION` | `0.30` | Hop length as fraction of remaining distance |
| `MAX_HOPS` | `40` | Safety cap (graceful stop, not the main limiter) |
| `GOAL_TOLERANCE_PX` | `25` | Distance (px) considered "at goal" |

---

## Deployment

### Streamlit Community Cloud (recommended)

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → select the repo, branch `main`, file `app.py`.
3. Under **Advanced settings → Secrets**, add:
   ```toml
   GEMINI_API_KEY = "your_key"
   ANTHROPIC_API_KEY = "your_key"
   ```
4. Deploy. OWL-ViT (~600 MB) downloads on first cold start — allow ~2 min.

### Hugging Face Spaces (fallback if memory exceeds ~1 GB)

Create a new Space with **Streamlit** SDK, upload all files, set the same secrets under **Settings → Repository secrets**. The `app.py` is identical — no code changes needed.

---

## Project structure

```
Project_DL/
├── my_env/              # virtualenv — activate before every run
├── .env                 # API keys (never committed)
├── requirements.txt
├── config.py            # all configuration constants
├── core.py              # run_pipeline(image, start_pos, goal_pos, cfg)
├── main.py              # CLI entry point
├── app.py               # Streamlit UI
├── input/               # intent parser + click helpers
├── localization/        # detector, heuristic, router, HSV verify, obstacles
├── navigation/          # hop loop, detour, A*, rollout, cost function
├── reasoning/           # mandatory LLM explanation
├── vlm/                 # Gemini / Claude API backend
├── visualization/       # draw.py (stills) + animate.py (GIF)
├── memory/              # session state helpers
├── evaluation/          # logger + metrics
└── data/images/         # 2d-*.png, 3d-*.png test images
```
