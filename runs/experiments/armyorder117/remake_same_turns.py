#!/usr/bin/env python3
"""Research #117: the remake's End turn from the ORIGINAL's own pre-End-turn saves of the death turns (order-in-play-<input>.json):
the remake imports the original SAV, plays End turn (seed 12345), exports; the export's live army order is compared with the pre
table by the same identity matching. Runs go to artifacts/run-exp-armyorder117/remake-<version>/<campaign>-t<NN>/.

    python3 runs/experiments/armyorder117/remake_same_turns.py --input v2 --version v1
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import order_in_play as O  # noqa: E402
from difftest import remake  # noqa: E402
from state import sav  # noqa: E402

ART = O.ROOT / "artifacts/run-exp-armyorder117"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--version", required=True)
    a = ap.parse_args()
    out = O.DATA / f"remake-same-turns-{a.version}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    rows = []
    for r in json.loads((O.DATA / f"order-in-play-{a.input}.json").read_text()):
        if not r["died_or_merged"]:
            continue
        pre_f = O.CAMP / r["campaign"] / "original" / r["pre"]
        d = ART / f"remake-{a.version}" / f"{r['campaign']}-t{r['turn']:02d}"
        remake.run([{"op": "end_turn"}], pre_f, d, log=lambda *x: None, seed=12345)
        post_f = sorted(d.glob("a*.SAV"))[-1]
        t = O.transition(sav.parse(pre_f.read_bytes()), sav.parse(post_f.read_bytes()))
        rows.append(dict(campaign=r["campaign"], turn=r["turn"], pre=r["pre"], remake_post=str(post_f.relative_to(O.ROOT)), **t,
                         original_died=r["died_or_merged"], original_order_kept=r["order_preserved"]))
        print(r["campaign"], r["turn"], "remake died", t["died_or_merged"], "kept", t["order_preserved"], "| original died",
              r["died_or_merged"], "kept", r["order_preserved"], flush=True)
    out.write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
