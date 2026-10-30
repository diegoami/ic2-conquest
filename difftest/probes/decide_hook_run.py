"""AI decision comparison with remake main (owner, 2026-10-30): run the original with patches/decide_hook.py and log every
input of the army phase FUN_0044f31c's branch, per army and turn.

    python3 -m difftest.probes.decide_hook_run OUT_DIR TURNS START.SAV [START.SAV ...]

Per start: a fresh process of the hooked build ("... seed decidehook.exe", written into the game folder once) with startup seed
12345 plays TURNS End turns (the human seat gives no orders). After each End turn the log is read from the game's memory and the
new records are appended to OUT_DIR/<start>-decide.jsonl; the autosaves are copied to OUT_DIR/<start>/. Then the UNPATCHED seed
build plays the same turns from the same start and seed, and its autosaves must be byte-identical (OUT_DIR/<start>/inert.json).
Same runner as difftest/probes/capdef_hook_run.py.
"""
import hashlib
import json
import shutil
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "patches"))
import decide_hook as FH  # noqa: E402
import walk_hook as WH  # noqa: E402
from harness.driver import EXE, G, Game  # noqa: E402

SEED = 12345


def play(exe, start, turns, out, tag, log_path=None):
    g = Game(exe=exe)
    moved = g.move_aside(sorted(G.glob("AUTO*")))
    g.load(start, seed=SEED)
    seen, saves = 0, []
    for t in range(1, turns + 1):
        line, texts = g.end_turn(peace=False)
        src = G / line
        dst = out / f"{tag}-t{t:02d}-{line}"
        shutil.copy(src, dst)
        saves.append({"turn": t, "file": dst.name, "sha256": hashlib.sha256(dst.read_bytes()).hexdigest()})
        if log_path:
            ctl = g.mem(WH.CTL, 12)
            count, magic = struct.unpack_from("<II", ctl, 0)
            if magic != FH.MAGIC:
                raise SystemExit(f"decide hook magic {magic:#x} is not {FH.MAGIC:#x}: wrong build?")
            if count > seen:
                buf = g.mem(WH.BUF + seen * FH.REC, (count - seen) * FH.REC)
                with open(log_path, "a") as f:
                    for r in FH.decode(buf, count - seen):
                        r["turn"] = t
                        f.write(json.dumps(r) + "\n")
                seen = count
    g.kill()
    return {"moved_aside": str(moved) if moved else None, "saves": saves, "records": seen}


def main():
    out, turns, starts = Path(sys.argv[1]), int(sys.argv[2]), [Path(p) for p in sys.argv[3:]]
    out.mkdir(parents=True, exist_ok=True)
    hooked = G / FH.DST
    if not hooked.exists():
        b = bytearray((G / WH.SRC).read_bytes())
        FH.build(b)
        hooked.write_bytes(bytes(b))
    for start in starts:
        d = out / start.stem
        if (d / "inert.json").exists():
            continue
        d.mkdir(exist_ok=True)
        log_path = out / f"{start.stem}-decide.jsonl"
        if log_path.exists():
            log_path = out / f"{start.stem}-decide-{time.strftime('%H%M%S')}.jsonl"
        h = play(FH.DST, start, turns, d, "hooked", log_path)
        p = play(EXE, start, turns, d, "plain")
        same = [a["sha256"] == b["sha256"] for a, b in zip(h["saves"], p["saves"])]
        (d / "inert.json").write_text(json.dumps({"start": str(start), "seed": SEED, "turns": turns, "hooked": h, "plain": p,
                                                  "identical": all(same), "per_turn": same}, indent=1))
        print(f"{start.stem}: {h['records']} records; autosaves identical to the plain build: {all(same)} {same}", flush=True)


if __name__ == "__main__":
    main()
