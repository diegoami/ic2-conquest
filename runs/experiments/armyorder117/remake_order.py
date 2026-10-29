#!/usr/bin/env python3
"""Research #117: the remake's army order across its own End turns in the #232 campaigns (v0.8.4 exports,
artifacts/run-exp-diff084-campaign/<campaign>/remake/tNN/aKKK.SAV: the last checkpoint of turn NN against turn NN+1's a000).
Same identity matching as order_in_play.py (v2). Writes remake-order-<version>.json.

    python3 runs/experiments/armyorder117/remake_order.py --version v1
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import order_in_play as O  # noqa: E402
from state import sav  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    v = ap.parse_args().version
    out = O.DATA / f"remake-order-{v}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    rows = []
    for c in sorted(p for p in O.CAMP.iterdir() if (p / "remake").is_dir()):
        turns = sorted(int(d.name[1:]) for d in (c / "remake").iterdir() if d.is_dir() and d.name.startswith("t"))
        for t in turns:
            # v2: inside the turn folder, End turn is the last command: its checkpoint is the last aKKK, the one before it is
            # the state at the click. (v1 compared the last checkpoint with the next folder's a000, the same state imported
            # again, so it could not show a death.)
            cur = sorted((c / "remake" / f"t{t:02d}").glob("a*.SAV"))
            if len(cur) < 2:
                continue
            r = O.transition(sav.parse(cur[-2].read_bytes()), sav.parse(cur[-1].read_bytes()))
            rows.append(dict(campaign=c.name, turn=t, pre=str(cur[-2].relative_to(c)), post=str(cur[-1].relative_to(c)), **r))
    out.write_text(json.dumps(rows, indent=1))
    d = [r for r in rows if r["died_or_merged"]]
    print("remake transitions", len(rows), "with deaths", len(d), "order kept when deaths", sum(r["order_preserved"] for r in d),
          "tombstones", sum(r["post_tombstones"] > 0 for r in rows))
    for r in d:
        if not r["order_preserved"]:
            print(" NOT kept:", r["campaign"], r["turn"], r["died_or_merged"], r["new"])


if __name__ == "__main__":
    main()
