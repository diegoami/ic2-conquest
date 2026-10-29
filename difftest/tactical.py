"""Tactical battles with the same commands in both games (#231).

    python3 -m difftest.tactical CASES_MODULE run-exp-<name> [--only ID ...] [--seed N]

A case stages one battle (`stage`): the strategic save `saves/fleet-split-antium-0734.SAV` with Rome's army 0 and
army 13 (owner set to Carthage, at war with Rome) given the case's units; BOTH nations are made human, so no
computer general plays either side and our script commands both; the battle block is synthetic
(`state/battle_block.py`): fixed morale 70, the case's positions, the movement phase. The same block goes to both
games: the original opens the staged save; the remake imports the strategic part and the block
(difftest/remake_adapter, `tactical` mode).

Script lines (shared): `move s x y`, `attack s e` (melee target), `shoot s e`, `end` (end the half-round).
Original: left click the unit, then left click the destination / the adjacent enemy; right click the enemy to
shoot (gui80: `findings/2026-10-26-tactical-enemy-click-gui80.md`); `end` is the battle toolbar's End turn.
After every line the board is read: original from memory (the block's slots at BATTLE_SLOTS), remake from the session.

Exact comparison per step: every slot's x, y, type, moves (the original's `state`), shots (`ammo`), target, and the
side to move. Troops and morale depend on combat draws, which come from different generators in the two games
(original: the global Random; remake: a SplitMix64 stream per battle), so they are reported, and compared exactly
only for steps that drew nothing (a move); losses go to the many-seed comparison (#233 method).
"""
import argparse
import importlib
import json
import os
import struct
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from state import battle_block as BB  # noqa: E402
from state import sav  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "saves/fleet-split-antium-0734.SAV"
ATTACKER, DEFENDER, DEFENDER_OWNER = 0, 13, 1          # Rome's army 0; army 13 handed to Carthage
NATION_HUMAN = 0x490
EXACT = ("x", "y", "type", "moves", "shots", "target")


def _offsets(b):
    """Byte offsets of the army table, fleet table and nation table of a save (state/sav.py layout)."""
    na = struct.unpack_from("<h", b, sav.ARMY_OFF)[0]
    a = sav.ARMY_OFF + 2
    f = a + na * sav.ARMY_LEN
    nf = struct.unpack_from("<h", b, f)[0]
    n = f + 2 + nf * sav.FLEET_LEN
    return a, f + 2, n


def _army_units(b, army, units):
    a, _, _ = _offsets(b)
    off = a + army * sav.ARMY_LEN
    b[off + 16:off + sav.ARMY_LEN] = bytes(sav.ARMY_LEN - 16)
    for k, (typ, troops, q) in enumerate(units):
        u = off + 16 + 32 * k
        struct.pack_into("<4h", b, u, 0, sav.UNIT_TYPES.index(typ), troops, q)
        name = f"D{army}S{k}".encode()
        b[u + 8:u + 8 + len(name)] = name


def stage(case, out):
    """Write <out>/staged.SAV (with the battle), strategic.SAV (no battle, flag 0) and block.bin; return the block."""
    out.mkdir(parents=True, exist_ok=False)
    b = bytearray(FIXTURE.read_bytes())
    a, _, n = _offsets(b)
    _army_units(b, ATTACKER, case["attacker"])
    _army_units(b, DEFENDER, case["defender"])
    struct.pack_into("<h", b, a + DEFENDER * sav.ARMY_LEN + 4, DEFENDER_OWNER)
    for nation in (0, DEFENDER_OWNER):
        b[n + nation * sav.NATION_LEN + NATION_HUMAN] = 1
    q = lambda u: (u[0], u[1], u[2], 0, "")
    block = BB.synthetic_block([q(u) for u in case["attacker"]], [q(u) for u in case["defender"]],
                               attacker_army=ATTACKER, defender_army=DEFENDER, half_round=case.get("half_round", 3))
    block["y1"] = 1                                   # movement phase (gui80 staged it the same way)
    for slot, (x, y) in case["positions"].items():
        block["slots"][int(slot)].update(x=x, y=y)
    for s in block["slots"]:
        s["state"] = {"li": 4, "hi": 2, "ar": 4, "lc": 6, "hc": 5}[s["type"]] if s["alive"] else 0
    block["grid"] = [BB.EMPTY] * (BB.GRID_W * BB.GRID_H)
    std = {"li": 15000, "hi": 6000, "ar": 3500, "lc": 7000, "hc": 2500}
    for s in block["slots"]:
        if s["alive"]:
            cls = 0 if s["troops"] * 3 < std[s["type"]] else 1 if s["troops"] * 3 < 2 * std[s["type"]] else 2
            block["grid"][BB.cell(s["x"], s["y"])] = 20 * s["side"] + 3 * BB.TYPES.index(s["type"]) + cls
    tail = sav.parse(bytes(b))["tail_off"]
    (out / "strategic.SAV").write_bytes(bytes(b))
    raw = BB.encode_block(block)
    (out / "block.bin").write_bytes(raw)
    staged = bytearray(b)
    staged[tail + 54] = 1
    staged.extend(raw)
    (out / "staged.SAV").write_bytes(bytes(staged))
    (out / "block.json").write_text(json.dumps(block, indent=1))
    return block


def board_from_block(blk):
    return [{"k": k, "x": s["x"], "y": s["y"], "type": BB.TYPES.index(s["type"]) if isinstance(s["type"], str) else s["type"],
             "troops": s["troops"], "quality": s["quality"], "morale": s["morale"], "moves": s["state"], "shots": s["ammo"],
             "target": s["target"]} for k, s in enumerate(blk["slots"])]


def run_remake(case_dir, script, seed):
    from difftest.remake import ADAPTER, DOTNET, REMAKE
    out = case_dir / f"remake-s{seed}.jsonl"
    n = 1
    while out.exists():
        n += 1
        out = case_dir / f"remake-s{seed}-r{n}.jsonl"
    env = dict(os.environ, DOTNET_ROOT=str(DOTNET.parent))
    p = subprocess.run([str(DOTNET), str(ADAPTER), "tactical", str(REMAKE), str(case_dir / "strategic.SAV"), str(case_dir / "block.bin"),
                        str(script), str(out), f"seed={seed}"], capture_output=True, text=True, env=env)
    out.with_suffix(".stderr.txt").write_text(p.stderr)
    if p.returncode:
        raise RuntimeError(f"remake tactical adapter failed: {p.stderr[-1500:]}")
    rows = []
    for l in out.read_text().splitlines():
        e = json.loads(l)
        if "board" in e:
            bd = e["board"]
            e["slots"] = [{"k": s["k"], "x": s["X"], "y": s["Y"], "type": s["Type"], "troops": s["Troops"], "quality": s["Quality"],
                           "morale": s["Morale"], "moves": s["Moves"], "shots": s["Shots"], "target": s["Target"]} for s in bd["slots"]]
            e["side"] = bd["side"]
        rows.append(e)
    return rows


def run_original(case_dir, script, seed, tag):
    from harness.driver import BATTLE_SLOTS, G, Game, sh
    sys.path.insert(0, str(ROOT / "runs/experiments/battles"))
    from common import battle_end_turn
    g = Game()
    g.move_aside(sorted(G.glob("AUTO*")))
    name = f"{tag}.SAV"
    target = G / name
    if target.exists():
        raise RuntimeError(f"{target} exists; use a new tag")
    target.write_bytes((case_dir / "staged.SAV").read_bytes())
    rows = []
    try:
        g.load(target, seed=seed)
        g.wait(lambda: g.in_battle() and g.find_windows(" v "), 20, "battle window after load")
        w = g.find_windows(" v ")[0]

        def read():
            # The slots and grid are contiguous at BATTLE_SLOTS; the header is NOT stored just before them (read there it
            # is garbage), so it is not read. The side to move is at 0x4A0B78 (gui80's observer).
            raw = bytes(BB.HEADER_LEN) + g.mem(BATTLE_SLOTS, BB.BLOCK_LEN - BB.HEADER_LEN)
            blk = BB.parse_block(raw)
            return {"slots": board_from_block(blk), "side": struct.unpack_from("<h", g.mem(0x4A0B78, 2))[0]}

        def cellclick(x, y, button=1):
            sh("xdotool", "windowraise", str(w[0]), check=False)
            sh("xdotool", "mousemove", str(w[2] + 16 + x * 32), str(w[3] + 30 + 16 + y * 32))
            time.sleep(0.15)
            sh("xdotool", "click", "--window", str(w[0]), str(button))
            time.sleep(0.7)

        st = read()
        rows.append({"kind": "start", **st})
        for step, line in enumerate(l.strip() for l in Path(script).read_text().splitlines()):
            if not line or line.startswith("#"):
                continue
            p = line.split()
            cur = {s["k"]: s for s in st["slots"]}
            err = None
            try:
                if p[0] == "move":
                    s = cur[int(p[1])]
                    cellclick(s["x"], s["y"])
                    cellclick(int(p[2]), int(p[3]))
                elif p[0] == "attack":
                    s, e = cur[int(p[1])], cur[int(p[2])]
                    cellclick(s["x"], s["y"])
                    cellclick(e["x"], e["y"])
                elif p[0] == "shoot":
                    s, e = cur[int(p[1])], cur[int(p[2])]
                    cellclick(s["x"], s["y"])
                    cellclick(e["x"], e["y"], 3)
                elif p[0] == "end":
                    battle_end_turn(g, w[0])
                else:
                    err = "unknown command"
            except Exception as ex:          # recorded; the board is still read
                err = f"{type(ex).__name__}: {ex}"
            texts = g.dismiss_popups() if not g.in_battle() else []
            st = read() if g.in_battle() else {"slots": [], "side": None}
            rows.append({"kind": "command", "step": step, "command": line, "error": err, "popups": texts,
                         "in_battle": g.in_battle(), **st})
    finally:
        g.kill()
    target_log = case_dir / f"original-s{seed}.jsonl"
    if target_log.exists():
        target_log = case_dir / f"original-s{seed}-{tag}.jsonl"
    target_log.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return rows


def compare_steps(orig, rem):
    """Per step: the exact fields' differences, and troops/morale reported separately."""
    out = []
    o = [r for r in orig if "slots" in r]
    r = [x for x in rem if "slots" in x]
    for k, (a, b) in enumerate(zip(o, r)):
        exact, combat = [], []
        sb = {s["k"]: s for s in b["slots"]}
        for s in a["slots"]:
            t = sb.get(s["k"])
            if t is None:
                continue
            alive_a, alive_b = s["troops"] > 0, t["troops"] > 0
            if alive_a or alive_b:
                for f in EXACT:
                    if s[f] != t[f]:
                        exact.append({"slot": s["k"], "field": f, "original": s[f], "remake": t[f]})
            for f in ("troops", "morale"):
                if s[f] != t[f]:
                    combat.append({"slot": s["k"], "field": f, "original": s[f], "remake": t[f]})
        if a.get("side") is not None and a.get("side") != b.get("side"):
            exact.append({"slot": None, "field": "side", "original": a.get("side"), "remake": b.get("side")})
        out.append({"step": k, "command": a.get("command", "start"), "exact": exact, "combat": combat,
                    "original_error": a.get("error"), "remake_accepted": b.get("Accepted")})
    return out


def run_stats(mod_name, name):
    """Many seeds per case in both games; one line per (case, side, seed) in artifacts/<name>/trials.jsonl, resumable.
    Analyse with `python3 -m difftest.stats analyze <module> <name>` (the module's SCENARIOS and ALPHA)."""
    mod = importlib.import_module(mod_name)
    out = ROOT / "artifacts" / name
    out.mkdir(parents=True, exist_ok=True)
    tf = out / "trials.jsonl"
    done = {(t["scenario"], t["side"], t["seed"]) for t in (json.loads(l) for l in tf.read_text().splitlines() if l.strip())
            if "metrics" in t} if tf.exists() else set()
    for c in mod.CASES:
        base = out / c["id"]
        if not base.exists():
            stage(c, base)
            (base / "script.txt").write_text("\n".join(c["script"]) + "\n")
        for seed in c["seeds"]:
            for side in ("remake", "original"):
                if (c["id"], side, seed) in done:
                    continue
                rec = {"scenario": c["id"], "side": side, "seed": seed, "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
                try:
                    if side == "remake":
                        rows = run_remake(base, base / "script.txt", seed)
                    else:
                        rows = run_original(base, base / "script.txt", seed, f"TS-{name[-6:]}-{c['id']}-s{seed}-{int(time.time())}")
                    first = next(r for r in rows if "slots" in r)
                    last = [r for r in rows if r.get("slots")][-1]
                    s0 = {s["k"]: s for s in first["slots"]}
                    s1 = {s["k"]: s for s in last["slots"]}
                    rec["metrics"] = {}
                    for k in c["slots"]:
                        rec["metrics"][f"slot{k}_troops_lost"] = s0[k]["troops"] - max(s1[k]["troops"], 0)
                        rec["metrics"][f"slot{k}_morale"] = s1[k]["morale"]
                    rec["errors"] = [r.get("error") for r in rows if r.get("error")]
                except Exception as e:
                    rec["error"] = f"{type(e).__name__}: {e}"[:400]
                rec["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                with open(tf, "a") as f:
                    f.write(json.dumps(rec) + "\n")
                print(f"{c['id']} {side} seed {seed}: {rec.get('metrics', rec.get('error'))}", flush=True)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        run_stats(sys.argv[2], sys.argv[3])
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("cases")
    ap.add_argument("name")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--seed", type=int, default=12345)
    a = ap.parse_args()
    cases = importlib.import_module(a.cases).CASES
    out = ROOT / "artifacts" / a.name
    out.mkdir(parents=True, exist_ok=True)
    resfile = out / "results.jsonl"
    done = {json.loads(l)["id"] for l in resfile.read_text().splitlines() if l.strip()} if resfile.exists() else set()
    for c in cases:
        if c["id"] in done or (a.only and c["id"] not in a.only):
            continue
        d, n = out / c["id"], 1
        while d.exists():
            n += 1
            d = out / f"{c['id']}-r{n}"
        rec = {"id": c["id"], "note": c["note"], "dir": d.name, "seed": a.seed, "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
        try:
            stage(c, d)
            script = d / "script.txt"
            script.write_text("\n".join(c["script"]) + "\n")
            rem = run_remake(d, script, a.seed)
            orig = run_original(d, script, a.seed, f"TAC-{a.name[-6:]}-{d.name}")
            steps = compare_steps(orig, rem)
            first = next((s for s in steps if s["exact"]), None)
            rec.update(verdict="same-exact" if not first else "differs", first=first, steps=steps)
        except Exception as e:
            rec.update(verdict="error", error=f"{type(e).__name__}: {e}"[:500])
        rec["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        with open(resfile, "a") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        print(f"{c['id']}: {rec['verdict']} {json.dumps(rec.get('first') or rec.get('error', ''))[:300]}", flush=True)


if __name__ == "__main__":
    main()


def run_original_entry(start, attacker, target, seed, tag):
    """#231 natural entry: the original opens `start` with startup seed `seed`, army `attacker` (the human's) clicks the
    adjacent enemy army `target`, and the battle board is read from memory as soon as the battle window is up, before any
    command. Returns {"slots", "side", "counter"}; the game is then killed (nothing is fought)."""
    from harness.driver import BATTLE_SLOTS, G, Game
    from state.sav import load
    g = Game()
    g.move_aside(sorted(G.glob("AUTO*")))
    name = f"{tag}.SAV"
    if (G / name).exists():
        raise RuntimeError(f"{G / name} exists; use a new tag")
    (G / name).write_bytes(Path(start).read_bytes())
    try:
        g.load(G / name, seed=seed)
        s = load(G / name)
        t = s["armies"][target]
        ax, ay = g.army_pos(attacker)
        g.select_army(attacker, ax, ay)
        g.click_tile(t["x"], t["y"], pause=1.5)
        g.wait(lambda: g.in_battle() and g.find_windows(" v "), 30, "battle window")
        time.sleep(1.0)
        raw = bytes(BB.HEADER_LEN) + g.mem(BATTLE_SLOTS, BB.BLOCK_LEN - BB.HEADER_LEN)
        blk = BB.parse_block(raw)
        return {"slots": board_from_block(blk), "side": struct.unpack_from("<h", g.mem(0x4A0B78, 2))[0],
                "counter": g.half_round_counter(), "title": g.find_windows(" v ")[0][1]}
    finally:
        g.kill()
