"""Per-trial sub-driver: launch a Game(), load the patched pre-state SAV, run
join_fleets(2), save the post-state SAV.

Run via trial.py (the orchestrator).
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from harness.driver import Game


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--pre', required=True, help='patched pre-state SAV path')
    p.add_argument('--post', required=True, help='post-state SAV output path')
    args = p.parse_args()

    pre = Path(args.pre)
    post = Path(args.post)
    assert pre.exists(), pre

    g = Game()
    g.load(str(pre), seed=12345)
    g.join_fleets(2)
    out = g.save_as(post.name)
    Path(out).rename(post)


if __name__ == '__main__':
    main()
