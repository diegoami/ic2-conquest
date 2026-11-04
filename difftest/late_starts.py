"""Late-year starts (owner 2026-11-04, "we need to get to the later years"): a catalogue of every stored game's
checkpoints by date, so a later run can start in any year instead of replaying from 270 BC.

    python3 -m difftest.late_starts [--min-year-bc 267] [--out runs/experiments/data/late-starts/catalogue-vN.json]

For each campaign folder under artifacts/run-exp-longrun-*/ (and any given with --root), every turn's start state is the
previous turn's final checkpoint (`original/tNN-aKK.SAV`, the last KK; t00-start for turn 1), i.e. the human seat's turn
before its orders. The entry records its date, the human nation, the path, its sha256 and, when the game ran with
IC2_LOG_RANDSEED=1, the RandSeed logged right after that checkpoint (`randseed_after`): writing it back after loading
continues the original's own random stream exactly (findings/2026-11-04-v092-followups.md §4). Any entry is a valid START.SAV
for difftest.campaign (a fresh game from that state: new seed, free-running), for difftest.anchored-style probes, and for the
hook runners (IC2_START_RANDSEEDS).
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from state.sav import NATIONS, load  # noqa: E402


def catalogue(camp):
    odir = camp / "original"
    rec = [json.loads(l) for l in (odir / "receipt.jsonl").read_text().splitlines() if l.strip()] \
        if (odir / "receipt.jsonl").exists() else []
    after = {e["checkpoint"]: e["value"] for e in rec if e.get("kind") == "randseed_after"}
    turns = sorted({int(p.name[1:3]) for p in odir.glob("t[0-9][0-9]-a*.SAV")})
    out = []
    for k in [0] + turns:
        ck = (odir / "t00-start.SAV") if k == 0 else sorted(odir.glob(f"t{k:02d}-a*.SAV"))[-1]
        if not ck.exists():
            continue
        s = load(ck)
        out.append({"game": camp.name, "start_of_turn": k + 1, "checkpoint": str(ck.relative_to(ROOT)),
                    "date": s["date"], "year_bc": s["year_bc"], "human": NATIONS[s["current_nation"]],
                    "sha256": hashlib.sha256(ck.read_bytes()).hexdigest(), "randseed_after": after.get(ck.stem)})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", default=[])
    ap.add_argument("--min-year-bc", type=int, default=None, help="keep entries at or after this year (e.g. 267)")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    camps = sorted(p.parent for p in ROOT.glob("artifacts/run-exp-longrun-*/*/original/receipt.jsonl"))
    camps = [c.parent if c.name == "original" else c for c in camps] + [Path(r) for r in a.root]
    rows = []
    for c in camps:
        rows += catalogue(c)
    if a.min_year_bc is not None:
        rows = [r for r in rows if r["year_bc"] <= a.min_year_bc]
    text = json.dumps(rows, indent=1)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        if Path(a.out).exists():
            raise SystemExit(f"refusing to overwrite {a.out} (rule 6): write a new version")
        Path(a.out).write_text(text)
    years = {}
    for r in rows:
        years.setdefault(r["year_bc"], 0)
        years[r["year_bc"]] += 1
    print(f"{len(rows)} starts in {len(camps)} games; by year BC: {dict(sorted(years.items(), reverse=True))}")


if __name__ == "__main__":
    main()
