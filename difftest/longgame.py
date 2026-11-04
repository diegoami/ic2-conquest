"""One long game to a target number of human turns, across human-seat handovers (owner 2026-11-04: the 150-turn games,
"save checkpoints so that we can continue if interrupted", and "hand over the human seat" when the bot's nation falls).

    python3 -m difftest.longgame START.SAV artifacts/run-exp-longgames/<game> --turns 150 [--pin a44c42fc]

Parts: OUT (the game from START), then OUT-h1, OUT-h2, ... Each part is a `difftest.campaign --original-only` run. A part
that stops without summary.json is resumed exactly (`--resume`). A part that ends with End of Game short of the target is
followed by a handover:
- the last completed turn's final checkpoint is copied with the human flag moved to the living nation with the most
  cities (difftest/handover.py);
- the next part starts from it, with the RandSeed logged after that checkpoint written back (`--start-randseed`).

The conquered seat's own turn then passes without orders inside the first End turn, and the original stops at the heir's
turn. Each handover is appended to OUT.handovers.jsonl. Every 25 turns and at each part's end a pack goes to the save
corpus (difftest/save_corpus.py: release ic2-save-corpus + gdrive:IC2/artifacts/save-corpus). Each finished part then
gets the anchored replay with per-turn seeds, failed turns retried.

Re-running the same command continues where it stopped.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from difftest.handover import handover  # noqa: E402


def rows(part):
    tj = part / "turns.jsonl"
    return [json.loads(l) for l in tj.read_text().splitlines() if l.strip()] if tj.exists() else []


def summary(part):
    f = part / "summary.json"
    return json.loads(f.read_text()) if f.exists() else None


def say(base, msg):
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(base.parent / f"{base.name}.longgame.log", "a") as f:
        f.write(line + "\n")


def run_part(base, part, start, turns, start_randseed, pin):
    cmd = [sys.executable, "-m", "difftest.campaign", str(start), str(part), "--turns", str(turns), "--seed", "12345",
           "--original-only"]
    if part.exists():
        cmd.append("--resume")
    elif start_randseed is not None:
        cmd += ["--start-randseed", str(start_randseed)]
    say(base, f"{'resume' if part.exists() else 'start'} {part.name}: {turns} turns")
    with open(base.parent / f"{part.name}.log", "a") as log:
        p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
        published = len(rows(part)) // 25
        while p.poll() is None:
            time.sleep(60)
            if len(rows(part)) // 25 > published:
                published = len(rows(part)) // 25
                corpus(base, part)
    if p.returncode or not summary(part):
        raise SystemExit(f"{part.name} stopped (exit {p.returncode}) without summary.json: re-run to resume")
    corpus(base, part)


def corpus(base, part):
    r = subprocess.run([sys.executable, "-m", "difftest.save_corpus", "publish", str(part)], capture_output=True, text=True,
                       cwd=ROOT)
    say(base, (r.stdout.strip() or r.stderr.strip()[-300:]).splitlines()[-1] if (r.stdout or r.stderr) else "publish: no output")


def anchored(base, part, pin):
    done = part.parent / f"{part.name}.anchored-done"
    if done.exists():
        return
    for extra in ([], ["--retry-errors"]):
        subprocess.run([sys.executable, "-m", "difftest.anchored", str(part), "--pin", pin, "--turn-seed", "12345",
                        "--out", "anchored-turnseed", *extra], cwd=ROOT,
                       stdout=open(part.parent / f"{part.name}.anchored-turnseed.log", "a"), stderr=subprocess.STDOUT)
    done.touch()
    say(base, f"anchored {part.name} done")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("start")
    ap.add_argument("out")
    ap.add_argument("--turns", type=int, default=150)
    ap.add_argument("--pin", default="a44c42fc")
    a = ap.parse_args(argv)
    base = Path(a.out)
    os.environ.setdefault("IC2_LOG_RANDSEED", "1")
    import re
    parts = [base] + sorted((p for p in base.parent.glob(f"{base.name}-h*")
                             if p.is_dir() and re.fullmatch(re.escape(base.name) + r"-h\d+", p.name)),
                            key=lambda p: int(p.name.rsplit("-h", 1)[1]))
    parts = [p for p in parts if p.exists() or p == base]
    hand = base.parent / f"{base.name}.handovers.jsonl"
    handovers = [json.loads(l) for l in hand.read_text().splitlines() if l.strip()] if hand.exists() else []
    for i, part in enumerate(parts):
        played = sum(len(rows(p)) for p in parts[:i])
        if summary(part) is None:
            h = handovers[i - 1] if i else None
            run_part(base, part, h["start"] if h else a.start, a.turns - played, h["randseed"] if h else None, a.pin)
        anchored(base, part, a.pin)
    while True:
        part = parts[-1]
        s = summary(part)
        total = sum(len(rows(p)) for p in parts)
        if not s.get("game_over") or total >= a.turns:
            break
        k = s["game_over"]["turn"]
        odir = part / "original"
        ck = sorted(odir.glob(f"t{k - 1:02d}-a*.SAV"))[-1] if k > 1 else odir / "t00-start.SAV"
        rec = [json.loads(l) for l in (odir / "receipt.jsonl").read_text().splitlines() if l.strip()]
        seed = [e["value"] for e in rec if e.get("kind") == "randseed_after" and e.get("checkpoint") == ck.stem][-1]
        nxt = base.parent / f"{base.name}-h{len(parts)}"
        start = base.parent / f"{nxt.name}-start.SAV"
        if start.exists():
            # Written by an earlier attempt that stopped before recording the handover: check it, never rewrite it.
            from state.sav import load, NATIONS
            d = load(start)
            info = {"from": [NATIONS[n] for n in range(16) if load(ck)["nations"][n]["human"]],
                    "to": NATIONS[[n for n in range(16) if d["nations"][n]["human"]][0]], "date": d["date"],
                    "cities": d["nations"][[n for n in range(16) if d["nations"][n]["human"]][0]]["cities_count"],
                    "current_seat": NATIONS[d["current_nation"]], "reused_start": True}
        else:
            info = handover(ck, start)
        h = {"part": nxt.name, "after_part": part.name, "game_over": s["game_over"], "from_checkpoint": str(ck),
             "start": str(start), "randseed": seed, **info, "time": time.strftime("%Y-%m-%dT%H:%M:%S")}
        with open(hand, "a") as f:
            f.write(json.dumps(h) + "\n")
        say(base, f"handover after {part.name} turn {k}: {info['from']} -> {info['to']} ({info['cities']} cities), {info['date']}")
        run_part(base, nxt, start, a.turns - total, seed, a.pin)
        anchored(base, nxt, a.pin)
        parts.append(nxt)
    say(base, f"done: {sum(len(rows(p)) for p in parts)} turns in {len(parts)} part(s)")


if __name__ == "__main__":
    main()
