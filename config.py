# ── input / UI ──────────────────────────────────────────────────────────────
DEFAULT_INPUT_MODE = "click"        # "prompt" | "click"

# ── LLM intent parser + reasoning ───────────────────────────────────────────
VLM_BACKEND   = "gemini"            # "gemini" | "claude"  (REQUIRED)
GEMINI_MODEL  = "gemini-3.1-flash-lite"
USE_LLM_PARSER = True               # parse messy prompts -> {source, target}

# ── localization ─────────────────────────────────────────────────────────────
USE_DETECTOR       = True
DETECTOR_MODEL_ID  = "google/owlvit-base-patch32"
DETECTOR_THRESHOLD = 0.01   # OWL-ViT scores on tabletop/non-web images are low
LOCALIZER_ORDER    = ["detector", "vlm"]   # detector first, vlm fallback
HSV_VERIFY         = True                  # reject off-object points

# ── obstacle detection (runs once per pipeline call) ─────────────────────────
DETECT_OBSTACLES   = True
OBSTACLE_QUERIES   = ["block", "box", "cube", "chair", "table", "object"]
OBSTACLE_THRESHOLD = 0.01   # all queries batched into one OWL-ViT forward pass
FLOOR_AWARE        = True    # constrain path to floor region (y >= floor_y_top)

# ── navigation ───────────────────────────────────────────────────────────────
STEP_FRACTION     = 0.30
MIN_STEP_PIXELS   = 30
MAX_HOPS          = 40              # safety cap (graceful stop, not the limiter)
GOAL_TOLERANCE_PX = 25
PATHER            = "detour"        # "detour" | "astar"
ASTAR_CELL_SIZE   = 10              # grid cell size in pixels for A* pather
COLLISION_PENALTY = 10000           # > image diagonal: clear path always beats collision

# ── outputs ──────────────────────────────────────────────────────────────────
GIF_FPS          = 6
SAVE_TRAIL_STILL = True             # write trail.png (trail-line still image)

# ── session context ──────────────────────────────────────────────────────────
SESSION_CONTEXT = True              # st.session_state history + positions
