"""CLI entry point for both input modes.

Prompt mode:  python main.py --image IMG --goal "move to bench" --vlm gemini
Click mode:   python main.py --image IMG --start X,Y --goal-xy X,Y
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

# Allow running from the project root without install
sys.path.insert(0, str(Path(__file__).parent))


def parse_args():
    p = argparse.ArgumentParser(description="Physical AI Planning Agent")
    p.add_argument("--image", required=True, help="Path to input image")
    # Mode A
    p.add_argument("--goal", default=None,
                   help="Natural-language goal instruction (Mode A)")
    p.add_argument("--vlm", default=None, choices=["gemini", "claude"],
                   help="VLM backend for intent parsing and reasoning")
    # Mode B — simulate clicks
    p.add_argument("--start", default=None,
                   help="Start pixel X,Y (Mode B; skips localization)")
    p.add_argument("--goal-xy", default=None, dest="goal_xy",
                   help="Goal pixel X,Y (Mode B; skips localization)")
    return p.parse_args()


def main():
    args = parse_args()

    import cv2
    import config
    from core import run_pipeline
    from input.click_input import parse_coord_string, validate_click

    # Load image
    image = cv2.imread(args.image)
    if image is None:
        print(f"[ERROR] Could not load image: {args.image}")
        sys.exit(1)

    # Override VLM backend from CLI flag
    if args.vlm:
        config.VLM_BACKEND = args.vlm

    # ── determine start / goal ───────────────────────────────────────────────
    if args.start and args.goal_xy:
        # Mode B: click-simulation (skips localization entirely)
        start_pos = validate_click(parse_coord_string(args.start), image.shape)
        goal_pos  = validate_click(parse_coord_string(args.goal_xy), image.shape)
        print(f"[Mode B] start={start_pos}  goal={goal_pos}")

    elif args.goal:
        # Mode A: prompt (localization stubbed until Steps 4–6)
        print("[Mode A] Localization not yet implemented — using image-quadrant stub.")
        h, w = image.shape[:2]
        start_pos = (w // 4, h // 2)
        goal_pos  = (3 * w // 4, h // 2)
        print(f"[Mode A stub] start={start_pos}  goal={goal_pos}")

    else:
        print("[ERROR] Provide --start X,Y --goal-xy X,Y  (Mode B)  "
              "or --goal '...'  (Mode A)")
        sys.exit(1)

    # ── run pipeline ─────────────────────────────────────────────────────────
    result = run_pipeline(image, start_pos, goal_pos, config)

    # ── print summary ────────────────────────────────────────────────────────
    print("\n=== Run complete ===")
    print(f"  Start:        {result.start_pos}")
    print(f"  Goal:         {result.goal_pos}")
    print(f"  Final pos:    {result.final_pos}")
    print(f"  Reached goal: {result.reached_goal}")
    print(f"  Hops:         {len(result.hops)}")
    print(f"  Reasoning:    {result.reasoning}")
    print("  Outputs:")
    for k, v in result.output_paths.items():
        print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
