"""Research #42 part 1 (delegated 2026-10-30): crossed tiles in play, from patches/step_hook.py.

    python3.12 -m difftest.probes.step_hook_run OUT_DIR

Sessions, each played by the hooked build and then by the unpatched seed build with startup seed 12345; their saves must be
byte-identical (inert.json):
  c4-far   BASE.SAV (= run0-start-AUTO0720-seed12345.SAV), human order: army 0 (100,37), 8 moves -> (100,25); File > Save
  c4-near  the same -> (100,32)
  ai-2     BASE.SAV, two End turns (the AI's walks)
The log (one record per call of the army step FUN_0044d420) is read from memory after the order or each End turn.
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
import step_hook as SH  # noqa: E402
import walk_hook as W  # noqa: E402
from difftest.original import move_army  # noqa: E402
from harness.driver import EXE, G, Game  # noqa: E402

BASE = Path.home() / "ic2-work/fixtures/BASE.SAV"
SEED = 12345


def read_log(g, seen):
    count, magic = struct.unpack_from("<II", g.mem(W.CTL, 8), 0)
    if magic != SH.MAGIC:
        raise SystemExit("step hook magic mismatch: wrong build?")
    if count <= seen:
        return [], seen
    return SH.decode(g.mem(W.BUF + seen * SH.REC, (count - seen) * SH.REC), count - seen), count


def session(exe, name, out, tag, hooked):
    g = Game(exe=exe)
    g.move_aside(sorted(G.glob("AUTO*")))
    g.load(BASE, seed=SEED)
    records, seen, saves = [], 0, []
    if name.startswith("c4"):
        goal = (100, 25) if name == "c4-far" else (100, 32)
        texts = move_army(g, 0, *goal)
        if hooked:
            new, seen = read_log(g, seen)
            records += [dict(r, phase="order") for r in new]
        p = g.save_as(f"STH-{tag}-{name}-{time.strftime('%H%M%S')}.SAV")
        dst = out / f"{tag}-{name}.SAV"
        shutil.copy(p, dst)
        saves.append(dst)
    else:
        for t in (1, 2):
            line, _ = g.end_turn(peace=False)
            dst = out / f"{tag}-{name}-t{t}-{line}"
            shutil.copy(G / line, dst)
            saves.append(dst)
            if hooked:
                new, seen = read_log(g, seen)
                records += [dict(r, phase=f"end_turn_{t}") for r in new]
    g.kill()
    return records, [{"file": s.name, "sha256": hashlib.sha256(s.read_bytes()).hexdigest()} for s in saves]


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    hooked_exe = G / SH.DST
    if not hooked_exe.exists():
        b = bytearray((G / SH.SRC).read_bytes())
        SH.build(b)
        hooked_exe.write_bytes(bytes(b))
    for name in ("c4-far", "c4-near", "ai-2"):
        if (out / f"{name}-inert.json").exists():
            continue
        recs, hs = session(SH.DST, name, out, "hooked", True)
        _, ps = session(EXE, name, out, "plain", False)
        (out / f"{name}-steps.jsonl").write_text("".join(json.dumps(r) + "\n" for r in recs))
        same = [a["sha256"] == b["sha256"] for a, b in zip(hs, ps)]
        (out / f"{name}-inert.json").write_text(json.dumps({"hooked": hs, "plain": ps, "identical": all(same),
                                                            "hooked_exe_sha256": hashlib.sha256(hooked_exe.read_bytes()).hexdigest()}, indent=1))
        print(f"{name}: {len(recs)} step records; saves identical to the plain build: {all(same)}", flush=True)


if __name__ == "__main__":
    main()
