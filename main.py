"""CLI entry point for both input modes.

Prompt mode:  python main.py --image IMG --goal "move to bench" --vlm gemini
Click mode:   python main.py --image IMG --start X,Y --goal-xy X,Y
"""
import argparse


def parse_args():
    p = argparse.ArgumentParser(description="Physical AI Planning Agent")
    p.add_argument("--image", required=True, help="Path to input image")
    # Mode A
    p.add_argument("--goal", default=None, help="Natural-language goal instruction (Mode A)")
    p.add_argument("--vlm", default="gemini", choices=["gemini", "claude"],
                   help="VLM backend for intent parsing and reasoning")
    # Mode B — simulate clicks
    p.add_argument("--start", default=None, help="Start pixel X,Y (Mode B; skips localization)")
    p.add_argument("--goal-xy", default=None, dest="goal_xy",
                   help="Goal pixel X,Y (Mode B; skips localization)")
    return p.parse_args()


def main():
    args = parse_args()
    raise NotImplementedError("Step 2 will implement the pipeline call")


if __name__ == "__main__":
    main()
