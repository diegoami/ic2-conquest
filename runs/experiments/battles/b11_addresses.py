#!/usr/bin/env python3
"""B11 address checks: every address the hook uses is [R-code] (the research report) and is checked here before the hook is relied on (task Design 2).

    python3 runs/experiments/battles/b11_addresses.py static                 # offline: the call-site table, byte checks, branch-into-displaced check (needs capstone)
    python3 runs/experiments/battles/b11_addresses.py live [cell] [seed]     # the game (hooked lab exe; needs the b11_common.py environment): header words, flag
                                                                              #   timeline, RandSeed vs the buffer, Save As block vs memory
    python3 runs/experiments/battles/b11_addresses.py entries TRIAL...       # offline, on a hooked trial's saves and log: the markers fire where the snapshots
                                                                              #   say a shot / melee / rout happened

Every check writes a tracked `b11-<what>-<stamp>.json` (common.write_new: never overwritten).
"""
import json
import struct
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b11_common as B  # noqa: E402  (sets the data/artifacts folders of run-exp-battle-hook; requires IC2_WORK and DISPLAY_IC2)

C = B.C
ROOT = C.ROOT
sys.path.insert(0, str(ROOT / "patches"))
import battle_hook as H  # noqa: E402


def exe_bytes():
    import os
    p = Path(os.environ.get("IC2_WORK", Path.home() / "ic2-work")) / "build" / "Imperial Conquest 2.exe"
    return bytearray(p.read_bytes()), p


# ---------------------------------------------------------------------------------------------------------------------------------------------
def static():
    """The call-site table and every static check. Capstone is used for the instruction at each site and the short-branch check."""
    from capstone import CS_ARCH_X86, CS_MODE_32, Cs
    import hashlib
    b, p = exe_bytes()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    res = {"exe": p.name, "exe_sha256": hashlib.sha256(bytes(b)).hexdigest()}
    H.check_sites(b)
    inside, outside = H.check_scan(b)
    H.check_entries(b)
    refs = H.scan_random_refs(b)
    res["random_refs_total"] = len(refs)
    res["random_ref_kinds"] = sorted({k for _, k in refs})
    import collections
    res["ref_kind_counts"] = dict(collections.Counter(k for _, k in refs))
    mods = (H.BATTLE_MODULE, H.BATTLEOVER_MODULE)
    res["non_E8_references_inside_the_two_modules"] = [(hex(v), k) for v, k in refs if k != "E8" and H.in_ranges(v, mods)]
    res["unresolved_indirect_outside_the_modules"] = [hex(v) for v, k in refs if k.endswith("?")]
    # every FF 15 / FF 25 (indirect call / jump through a pointer) inside the two modules and how its pointer resolves (R1: the dword AT the operand is what counts)
    code = bytes(b[H.CODE_RAW:H.CODE_RAW + H.CODE_SIZE])
    ff = collections.Counter()
    for i in range(len(code) - 6):
        if code[i] == 0xFF and code[i + 1] in (0x15, 0x25) and H.in_ranges(H.CODE_VA + i, mods):
            ff[H.resolve_pointer(b, struct.unpack_from("<I", code, i + 2)[0])[0]] += 1
    res["FF15_FF25_inside_the_two_modules_by_pointer_resolution"] = dict(ff)
    res["E9_rel32_to_Random_anywhere"] = [hex(v) for v, k in refs if k == "E9"]
    res["inside_module_and_battleover"] = [hex(v) for v in inside]
    res["hooked_list"] = [hex(v) for v in H.SITES]
    res["lists_equal"] = inside == sorted(H.SITES)
    res["outside_count"] = len(outside)
    res["outside"] = [hex(v) for v in outside]
    res["battle_module"] = [hex(v) for v in H.BATTLE_MODULE]
    res["battleover_unit"] = [hex(v) for v in H.BATTLEOVER_MODULE]
    table = []
    for va in H.SITES:
        o = H.off(va)
        # the 3 instructions before the call show how the range reaches EAX
        ctx = []
        for i in md.disasm(bytes(b[o - 12:o + 5]), va - 12):
            ctx.append("%x %s %s" % (i.address, i.mnemonic, i.op_str))
        table.append({"site": hex(va), "bytes": bytes(b[o:o + 5]).hex(), "target": hex(va + 5 + struct.unpack_from("<i", b, o + 1)[0]),
                      "module": "TBattleMap" if H.in_ranges(va, (H.BATTLE_MODULE,)) else "TBattleOver", "context": ctx[-4:]})
    res["sites"] = table
    # displaced ranges: the bytes and a disassembly; short branches into them from the function around
    disp = []
    for name, va, exp in list(H.MARKERS) + [(n, v, H.FLAG_CLEAR_BYTES) for n, v in H.FLAG_CLEAR] + list(H.RESEED):
        o = H.off(va)
        ins = ["%x %s %s" % (i.address, i.mnemonic, i.op_str) for i in md.disasm(bytes(b[o:o + len(exp)]), va)]
        disp.append({"name": name, "va": hex(va), "bytes": bytes(b[o:o + len(exp)]).hex(), "instructions": ins})
    res["displaced"] = disp
    starts = {"shot": 0x43910C, "melee": 0x4393EC, "rout": 0x438FB0, "battle_over_clear": 0x437B8C, "after_battle_clear": 0x45C208, "reseed_450c7b": 0x450C68}
    res["function_starts_used"] = {k: hex(v) for k, v in starts.items()}
    # the TBattlePols reseed (0x457907): find the function start by scanning back for a prologue that decodes linearly onto the site
    site = 0x457907
    found = None
    for s0 in range((site - 0x400) & ~3, site, 4):                  # Delphi aligns procedures to 4 bytes; the nearest `push ebp; mov ebp,esp` from which a linear sweep lands on the site
        o = H.off(s0)
        if bytes(b[o:o + 3]) == b"\x55\x8B\xEC" and any(i.address == site for i in md.disasm(bytes(b[o:o + 0x400]), s0)):
            found = s0
    starts["reseed_battlepols"] = found
    res["function_starts_used"]["reseed_battlepols"] = hex(found) if found else None
    bad = []
    spans = {n: (v, v + len(e)) for n, v, e in H.MARKERS + tuple((n, v, H.FLAG_CLEAR_BYTES) for n, v in H.FLAG_CLEAR) + H.RESEED}
    for name, (lo, hi) in spans.items():
        s = starts.get(name) or starts.get("reseed_battlepols" if "battlepols" in name else name)
        if s is None:
            bad.append({"name": name, "why": "no function start"})
            continue
        o = H.off(s)
        n_ins = 0
        for i in md.disasm(bytes(b[o:o + 0x1000]), s):
            n_ins += 1
            if i.mnemonic.startswith("j") or i.mnemonic == "call":
                try:
                    tgt = int(i.op_str, 16)
                except ValueError:
                    continue
                if lo < tgt < hi:
                    bad.append({"name": name, "branch": hex(i.address), "target": hex(tgt)})
            if i.mnemonic == "ret" and i.address > hi + 0x300:
                break
    res["short_branch_into_displaced_bytes"] = bad
    res["pass"] = res["lists_equal"] and not bad
    p = C.write_new(C.DATA, "b11-static-%s.json" % time.strftime("%Y%m%d-%H%M%S"), json.dumps(res, indent=1))
    print(p.name, "lists_equal", res["lists_equal"], "outside", len(outside), "branch problems", bad)
    return res


# ---------------------------------------------------------------------------------------------------------------------------------------------
def live(cell="ar-ar-one", seed=1):
    import b11_run as R
    from harness.driver import BATTLE_FLAG, BATTLE_HEADER, RAND_SEED
    from state import battle_block as BB, sav
    log = C.Log("b11-live")
    B.start_xvfb()
    g = B.HookGame(exe=B.HOOK_EXE % seed)
    B.kill_mine(g)
    res = {"cell": cell, "seed": seed, "exe": B.HOOK_EXE % seed}
    try:
        start, expect = R.stage_start(cell)
        for f in C.D.G.glob("BATTLE*.SAV"):
            C.keep(f, "stray_live_%s" % f.name)
            f.unlink()
        g.start()
        g.open(start)
        res["flag_before_attack"] = g.mem(BATTLE_FLAG, 1)[0]
        g.select_army(C.ROME_ARMY, *C.STAGE_TILE)
        g.click_tile(*C.GAUL_TILE, pause=0.0)
        R.T.wait_battle(g, log)
        time.sleep(1.0)
        # (1) header words, flag, RandSeed and the buffer, at the open battle (human placement phase)
        words = {k: struct.unpack("<h", g.mem(a, 2))[0] for k, a in BATTLE_HEADER.items() if k != "y1"}
        words["y1"] = g.mem(BATTLE_HEADER["y1"], 1)[0]
        words["flag"] = g.mem(BATTLE_FLAG, 1)[0]
        mem_block = g.battle_state()
        ctl, recs = g.hook_read()
        seed_mem = int.from_bytes(g.mem(RAND_SEED, 4), "little")
        res["open_battle"] = {"header_words_memory": words, "seed_memory": seed_mem, "records": len(recs), "last_seed_after": recs[-1]["seed_after"] if recs else None,
                              "seed_memory_equals_last_record_seed_after": bool(recs) and recs[-1]["seed_after"] == seed_mem,
                              "kinds": {k: sum(1 for r in recs if r["kind"] == k) for k in {r["kind"] for r in recs}}}
        # (2) Save As block against memory
        saved = C.keep(g.save_as("B11_open.SAV"))
        blk = BB.from_save(saved)
        res["save_as_block_equals_memory"] = blk == mem_block
        res["save_as_header"] = {k: blk[k] for k in ("attacker_army", "defender_army", "x2", "y1", "half_round")}
        res["memory_header_parsed"] = {k: mem_block[k] for k in ("attacker_army", "defender_army", "x2", "y1", "half_round")}
        # (3) the flag timeline across the battle: a poller thread reads the flag, the windows and the buffer index
        timeline, stop = [], threading.Event()
        t0 = time.time()

        def poll():
            last = None
            while not stop.is_set():
                try:
                    st = (g.mem(BATTLE_FLAG, 1)[0], bool(g.find_windows("Battle ended")), int.from_bytes(g.mem(H.CTL, 4), "little"))
                except Exception as e:      # noqa: BLE001
                    st = ("err", str(e), 0)
                key = st[:2]
                if key != last:
                    timeline.append({"t": round(time.time() - t0, 2), "flag": st[0], "battle_ended_window": st[1], "hook_index": st[2]})
                    last = key
                time.sleep(0.15)
        th = threading.Thread(target=poll, daemon=True)
        th.start()
        out = g.play_battle(on_dialog="capture")
        stop.set()
        th.join(3)
        res["flag_timeline"] = timeline
        res["flag_after_play_battle"] = g.mem(BATTLE_FLAG, 1)[0]
        ctl2, recs2 = g.hook_read()
        res["flag_clear_records"] = [(r["seq"], hex(r["site"]), r["counter"]) for r in recs2 if r["kind"] == "flag_clear"]
        res["reseed_records"] = [(r["seq"], hex(r["site"])) for r in recs2 if r["kind"] == "reseed"]
        res["dialogs"] = [d["title"] for d in out["dialogs"]]
        res["records_total"] = len(recs2)
        for f in C.D.G.glob("BATTLE*.SAV"):
            C.keep(f, "live_%s" % f.name)
            f.unlink()
        flag1 = [t for t in timeline if t["flag"] == 1]
        flag0_after = [t for t in timeline if t["flag"] == 0 and t["t"] > (flag1[0]["t"] if flag1 else 0)]
        res["flag_seen_1_in_battle"] = bool(flag1)
        res["flag_0_when_battle_ended_window_first_seen"] = next((t["flag"] for t in timeline if t["battle_ended_window"]), None)
        res["pass"] = (res["flag_before_attack"] == 0 and words["flag"] == 1 and res["save_as_block_equals_memory"] and res["flag_after_play_battle"] == 0
                       and res["open_battle"]["seed_memory_equals_last_record_seed_after"] and bool(flag1) and bool(flag0_after))
    finally:
        res["pids_killed"] = B.kill_mine(g)
        p = C.write_new(C.DATA, "b11-live-%s.json" % time.strftime("%Y%m%d-%H%M%S"), json.dumps(res, indent=1, default=str))
        print(p.name, "pass", res.get("pass"))
    return res


# ---------------------------------------------------------------------------------------------------------------------------------------------
def entries(tags):
    """The markers fire where the snapshots say a shot, melee or rout happened (offline)."""
    import b11_exchange as X
    out = {}
    for tag in tags:
        blocks, names = X.load_series(C.ART, tag)
        recs = X.load_log(C.DATA / ("hooklog-%s.csv" % tag))
        n = len(blocks)
        shot_markers = {}
        for r in recs:
            if r["kind"] == "marker" and r["site"] == X.MARK_SHOT and r["counter"] >= 2:
                s = X.sx16(r["eax"])
                shot_markers[s] = shot_markers.get(s, 0) + 1
        ammo_drop = {}
        for u in range(40):
            d = blocks[0]["slots"][u]["ammo"] - blocks[-1]["slots"][u]["ammo"]
            if d:
                ammo_drop[u] = d
        melee_markers = sum(1 for r in recs if r["kind"] == "marker" and r["site"] == X.MARK_MELEE)
        # a melee draw group (4 draws) per exchange; the exchanges that the snapshots' targets imply are checked in b11_exchange
        rout_markers = sum(1 for r in recs if r["kind"] == "marker" and r["site"] == X.MARK_ROUT)
        alive0 = sum(1 for s in blocks[0]["slots"] if s["alive"])
        alive_n = sum(1 for s in blocks[-1]["slots"] if s["alive"])
        out[tag] = {"half_rounds": n, "melee_markers": melee_markers, "melee_markers_equal_half_rounds": melee_markers == n,
                    "shots_by_slot_from_markers": shot_markers, "ammo_drop_by_slot_from_snapshots": ammo_drop,
                    "shots_equal_ammo_drop_every_slot": shot_markers == ammo_drop, "rout_markers": rout_markers, "alive_first_snapshot": alive0, "alive_last_snapshot": alive_n}
    p = C.write_new(C.DATA, "b11-entries-%s.json" % time.strftime("%Y%m%d-%H%M%S"), json.dumps(out, indent=1, default=str))
    print(p.name, {t: (v["melee_markers_equal_half_rounds"], v["shots_equal_ammo_drop_every_slot"]) for t, v in out.items()})
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "static":
        static()
    elif a[0] == "live":
        live(*(a[1:2] or ["ar-ar-one"]), *(int(x) for x in a[2:3]))
    elif a[0] == "entries":
        entries(a[1:])
