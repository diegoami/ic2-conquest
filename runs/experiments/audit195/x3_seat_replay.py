#!/usr/bin/env python3
"""#195 X3: the five AI seats the original played twice after a battle with the human's army
(findings/2026-10-31-ai-seat-replayed-after-human-battle.md), replayed on the remake in Instant and Tactical mode with
every AI pass's own log (adapter option "ailog"). Remake only; the original side is the hook logs of run-exp-econ.

    IC2_REMAKE=... IC2_DIFF_BUILD=<adapter build with ailog> \
    python3 runs/experiments/audit195/x3_seat_replay.py <out dir> [--seeds 12345,...]

Per seat, seed and mode: the round from the original's round-start save, the human gives no orders ("end"); a battle that
opens on the board is fought by the computer general for the human ("battle general on", which plays it to the end).
Writes <out>/<seat>-<mode>-s<seed>/ (commands.txt, receipt.jsonl, a000/a001 saves) and <out>/passes.jsonl: per run,
the seat nation's AI passes in order (issued orders and log lines) and the battle lines. Never overwrites.
"""
import argparse
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ART = Path("/home/diego/projects/ic2-conquest/artifacts")
AID = ART / "run-exp-aidecide/orig-v1"
SEATS = [  # (label, round-start save, replayed seat)
    ("S01r5", AID / "S01_Carthage_AUTO0720/hooked-t04-AUTO0724.SAV", "celtiberia"),
    ("S02r4", AID / "S02_Seleucid_AUTO0720/hooked-t03-AUTO0723.SAV", "bithynia"),
    ("S03r1", ART / "run-exp-civ-sweep/S03_Ptolemaic_AUTO0720.SAV", "seleucid"),
    ("S06r2", AID / "S06_Gaul_AUTO0720/hooked-t01-AUTO0721.SAV", "rome"),
    ("S08r2", AID / "S08_Celtiberia_AUTO0720/hooked-t01-AUTO0721.SAV", "carthage"),
]
COMMANDS = "#checkpoint a000\nend\n" + "battle general on\n" * 3 + "#checkpoint a001\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out"), ap.add_argument("--seeds", default="12345")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    remake, build = os.environ["IC2_REMAKE"], Path(os.environ["IC2_DIFF_BUILD"])
    adapter = build / "adapter/bin/RemakeAdapter/release/RemakeAdapter.dll"
    dotnet = Path.home() / ".dotnet/dotnet"
    with open(out / "passes.jsonl", "w") as summary:
        for label, start, seat in SEATS:
            for seed in [int(x) for x in a.seeds.split(",")]:
                for mode in ("instant", "tactical"):
                    d = out / f"{label}-{mode}-s{seed}"
                    d.mkdir()
                    (d / "commands.txt").write_text(COMMANDS)
                    opts = [f"seed={seed}", "ailog"] + (["tactical"] if mode == "tactical" else [])
                    with open(d / "receipt.jsonl", "w") as rec:
                        p = subprocess.run([str(dotnet), str(adapter), remake, str(start), str(start), str(d / "commands.txt"),
                                            str(d)] + opts, stdout=rec, stderr=subprocess.PIPE, text=True,
                                           env=dict(os.environ, DOTNET_ROOT=str(dotnet.parent)))
                    (d / "stderr.txt").write_text(p.stderr)
                    ev = [json.loads(l) for l in (d / "receipt.jsonl").read_text().splitlines() if l.strip()]
                    passes = [{"issued": e["issued"], "lines": e["lines"]} for e in ev if e["kind"] == "ai" and e["nation"] == seat]
                    battle = [l for e in ev if e["kind"] == "command" for l in (e.get("lines") or [])
                              if "attacks" in l or "defeats" in l or "Battle:" in l or "takes its turn" in l and seat in l.lower()]
                    row = {"seat": label, "nation": seat, "mode": mode, "seed": seed, "exit": p.returncode,
                           "passes": passes, "battle_lines": battle}
                    summary.write(json.dumps(row) + "\n")
                    summary.flush()
                    print(label, mode, seed, "exit", p.returncode, "passes", len(passes), [x["issued"] for x in passes], flush=True)


if __name__ == "__main__":
    main()
