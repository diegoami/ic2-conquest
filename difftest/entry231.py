"""#231 natural battle entry: both games open the same strategic save, the human army attacks the adjacent enemy army, and
the battle board is read before any command (original: memory as soon as the battle window is up; remake: the adapter's
`battleentry` view). Nothing is fought.

    python3 -m difftest.entry231 run --side remake|original --seeds 1 2 ...
    python3 -m difftest.entry231 compare

Start: artifacts/run-exp-diff084-entry/staged/rome-vs-gaul.SAV (BASE.SAV with Rome's army 0 staged to (94,29), beside
Gaul's army 9 at (93,28); difftest.stage "army_pos"). Outputs: artifacts/run-exp-diff084-entry/<side>-s<seed>.json, never
overwritten. Compared per seed: every live slot's (type, troops, quality, x, y, moves, shots, target) and the side to move
exactly; morale per slot as a sample over seeds.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "artifacts/run-exp-diff084-entry"
START = OUT / "staged/rome-vs-gaul.SAV"
ATTACKER, TARGET = 0, 9
FIELDS = ("type", "troops", "quality", "x", "y", "moves", "shots", "target")


def run_remake(seed):
    from difftest.remake import ADAPTER, DOTNET, REMAKE
    out = OUT / f"remake-s{seed}.json"
    if out.exists():
        return
    p = subprocess.run([str(DOTNET), str(ADAPTER), "battleentry", str(REMAKE), str(START), str(ATTACKER), str(TARGET), str(out),
                        f"seed={seed}"], capture_output=True, text=True, env=dict(os.environ, DOTNET_ROOT=str(DOTNET.parent)))
    if p.returncode:
        raise RuntimeError(p.stderr[-1500:])


def run_original(seed):
    from difftest.tactical import run_original_entry
    out = OUT / f"original-s{seed}.json"
    if out.exists():
        return
    r = run_original_entry(START, ATTACKER, TARGET, seed, f"ENT231S{seed}")
    out.write_text(json.dumps(dict(r, seed=seed)))


def board(side, seed):
    d = json.loads((OUT / f"{side}-s{seed}.json").read_text())
    if side == "remake":
        v = d["view"]
        slots = {s["k"]: {"type": s["Type"], "troops": s["Troops"], "quality": s["Quality"], "x": s["X"], "y": s["Y"],
                          "moves": s["Moves"], "shots": s["Shots"], "target": s["Target"], "morale": s["Morale"]}
                 for s in v["slots"] if s["Troops"] > 0}
        return {"slots": slots, "side": v["SideToMove"], "counter": v["Counter"]}
    slots = {s["k"]: {f: s[f] for f in FIELDS + ("morale",)} for s in d["slots"] if s["troops"] > 0}
    return {"slots": slots, "side": d["side"], "counter": d["counter"]}


def compare():
    seeds = sorted({int(p.stem.split("-s")[1]) for p in OUT.glob("original-s*.json")}
                   & {int(p.stem.split("-s")[1]) for p in OUT.glob("remake-s*.json")})
    morale = {}
    for seed in seeds:
        o, r = board("original", seed), board("remake", seed)
        diffs = []
        if set(o["slots"]) != set(r["slots"]):
            diffs.append(f"slots original {sorted(o['slots'])} remake {sorted(r['slots'])}")
        for k in sorted(set(o["slots"]) & set(r["slots"])):
            for f in FIELDS:
                if o["slots"][k][f] != r["slots"][k][f]:
                    diffs.append(f"slot {k} {f} {o['slots'][k][f]} vs {r['slots'][k][f]}")
            morale.setdefault(k, ([], []))
            morale[k][0].append(o["slots"][k]["morale"])
            morale[k][1].append(r["slots"][k]["morale"])
        for f in ("side", "counter"):
            if o[f] != r[f]:
                diffs.append(f"{f} {o[f]} vs {r[f]}")
        print(f"seed {seed}: " + ("identical" if not diffs else "; ".join(diffs)))
    for k, (a, b) in sorted(morale.items()):
        print(f"morale slot {k}: original {sorted(set(a))} remake {sorted(set(b))}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "compare"])
    ap.add_argument("--side", choices=["original", "remake"])
    ap.add_argument("--seeds", nargs="*", type=int, default=[])
    a = ap.parse_args()
    if a.cmd == "compare":
        return compare()
    for seed in a.seeds:
        (run_remake if a.side == "remake" else run_original)(seed)
        print(a.side, seed, "done", flush=True)


if __name__ == "__main__":
    main()
