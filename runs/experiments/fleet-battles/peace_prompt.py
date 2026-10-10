#!/usr/bin/env python3
"""The fleet peace prompt: two fleets adjacent at sea on trade terms (no war order; `python3 -m tests.make_fleet_battle_fixture --no-war`,
fixture T1P_FIXTURE_fleets_adjacent.SAV at Ptolemaic's seat), Ptolemaic's fleet attacks Carthage's.

  no   click the enemy fleet, read the box, answer No; read both fleets and both relation entries before and after
  cancel  click, press Cancel (the box has Yes, No and Cancel); the same readings as `no`
  yes  click, answer Yes; read both fleets and the relations, save, End turn and read the news of the next autosave

    python3 runs/experiments/fleet-battles/peace_prompt.py [no] [cancel] [yes] [--seeds N]
"""
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness.driver import G, NATIONS, NATION_LEN, Game  # noqa: E402
from state import sav  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-peace-prompt"
from harness import environment as _env  # noqa: E402  every game start writes environment-<stamp>.json beside the outputs
_env.folder_sink(OUT, 'fleet-battles/peace_prompt.py')
FIX = OUT / "T1P_FIXTURE_fleets_adjacent.SAV"
ATT, DEF = 1, 0           # Ptolemaic's fleet attacks Carthage's


def rel(g):
    """Both relation entries (nation record +0x26 + 2 j): Carthage (1) toward Ptolemaic (3) and back."""
    return {"carthage_to_ptolemaic": g.i16(NATIONS + 1 * NATION_LEN + 0x26 + 2 * 3), "ptolemaic_to_carthage": g.i16(NATIONS + 3 * NATION_LEN + 0x26 + 2 * 1),
            "ptolemaic_row": [g.i16(NATIONS + 3 * NATION_LEN + 0x26 + 2 * j) for j in range(16)],        # toward nations 0..15 (own entry unused)
            "carthage_row": [g.i16(NATIONS + 1 * NATION_LEN + 0x26 + 2 * j) for j in range(16)]}


def trial(branch, seed):
    g = Game()
    try:
        g.load(FIX, seed=seed)
        before = {"att": g.fleet_state(ATT), "def": g.fleet_state(DEF), "rel": rel(g)}
        if branch in ("no", "cancel"):
            texts = g.attack_fleet(ATT, DEF)                 # reads the box and leaves it open
            box_open = bool(g.find_windows("^Confirm$"))
            if seed == 1:
                g.shot(OUT / f"peace_prompt_box_{branch}_seed{seed}.png")
            for _ in range(3):      # the first click into an inactive window may only activate it: at most two retries
                if not (box_open and g.find_windows("^Confirm$")):
                    break
                if branch == "no":
                    g.answer("Confirm", yes=False)
                else:
                    cs = g.controls("Confirm")
                    g.click_control(next(c for c in cs if "cancel" in c["text"].lower()), pause=0.8)
                time.sleep(1.5)
            if box_open:      # the click must have closed the box: dismiss_popups would answer a Confirm still open with Yes
                g.wait(lambda: not g.find_windows("^Confirm$"), 8, f"the box to close after {branch}")
            after_texts = g.dismiss_popups()
            time.sleep(1.0)
            after = {"att": g.fleet_state(ATT), "def": g.fleet_state(DEF), "rel": rel(g)}
            return {"branch": branch, "seed": seed, "box": texts, "box_open": box_open, "after_texts": after_texts, "before": before, "after": after}
        texts = g.attack_fleet(ATT, DEF, answer=True)
        time.sleep(1.0)
        after = {"att": g.fleet_state(ATT), "def": g.fleet_state(DEF), "rel": rel(g)}
        r = {"branch": branch, "seed": seed, "texts": texts, "before": before, "after": after}
        if seed == 1:
            shutil.copy(g.save_as(f"PP_yes_seed{seed}.SAV"), OUT / f"PP_yes_seed{seed}.SAV")
        name, et = g.end_turn(timeout=300)
        s = sav.load(str(G / name))
        r["next_autosave"] = name
        r["end_turn_texts"] = et
        r["news"] = s["news"][-14:]
        r["relations_next"] = {"carthage_to_ptolemaic": s["nations"][1]["relations"]["Ptolemaic"], "ptolemaic_to_carthage": s["nations"][3]["relations"]["Carthage"]}
        if seed == 1:
            shutil.copy(G / name, OUT / f"PP_yes_seed{seed}_{name}")
        return r
    finally:
        g.kill()


def main():
    args = sys.argv[1:]
    n = int(args[args.index("--seeds") + 1]) if "--seeds" in args else 1
    branches = [a for a in args if a in ("no", "cancel", "yes")] or ["no", "cancel", "yes"]
    if not FIX.exists():
        sys.exit(f"missing {FIX}: run python3 -m tests.make_fleet_battle_fixture --no-war first")
    f = OUT / "peace_prompt.json"
    res = json.loads(f.read_text()) if f.exists() else []
    for b in branches:
        for seed in range(1, n + 1):
            try:
                r = trial(b, seed)
            except Exception as e:     # noqa: BLE001
                r = {"branch": b, "seed": seed, "error": f"{type(e).__name__}: {e}"}
            res = [x for x in res if not (x["branch"] == b and x["seed"] == seed)] + [r]
            f.write_text(json.dumps(res, indent=1, default=str))
            print(json.dumps(r, default=str)[:900], flush=True)


if __name__ == "__main__":
    main()
