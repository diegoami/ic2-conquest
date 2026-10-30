#!/usr/bin/env python3.12
"""Research #37 Q2 (2026-10-31): TUnitMap_PaintForm re-runs TUnitMap_SelectUnit on the highlighted square (form +0x21A) on
every refresh (TChangeTax_OK -> TPremierForm_RefreshForms -> PaintForm; rename -> TUnitMap_UpdateUMSelection -> PaintForm).
Every branch of SelectUnit that changes game state resets the selected army 0x4A0328 to -1, except the enemy-fleet branch,
which leaves the selected fleet 0x4A032A as it was. This control executes the original SelectUnit twice on the #187 RAM
snapshot: once as the click, then again on the resulting state as the refresh's re-run, to see whether the second call
repeats the question or the attack.

Unicorn on the pinned EXE (runs/experiments/navigation187/core.py sections and snapshot). The form object is a zeroed
buffer with only the fields SelectUnit reads (+0x21A square, +0x21E code, +0x220/+0x222/+0x224 indices). Stubbed (logged,
return 0 unless stated): the drawing/info/button calls, MessageDlg FUN_0042d750 (returns the scripted answer: 6 Yes, 7 No)
and the order routines it would start (naval battle FUN_0044b5d0, army battle FUN_0044aee4, siege FUN_0044b27c, embark
FUN_0044b79c, the relation setter FUN_00449b40). Distance, adjacency, docking and index helpers run unmodified.

    python3.12 runs/experiments/savexport37/selectunit.py --version v1            # order routines stubbed
    python3.12 runs/experiments/savexport37/selectunit.py --version v2 --real     # naval battle and relation setter run
"""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runs/experiments/navigation187"))
import core as C  # noqa: E402
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE  # noqa: E402
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EDX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP  # noqa: E402

DATA = ROOT / "runs/experiments/data/run-exp-savexport37"
SELECT = 0x4466CC
FORM = 0x700000
FLEETS, FREC = 0x49C26C, 0x1A
NATION = 1
STUBS = {0x445B38: "PrintMapSquare", 0x4465A8: "FUN_004465a8", 0x446EAC: "EndUMSelection", 0x445D38: "PaintForm",
         0x43B940: "PrintNews", 0x43C890: "ShowFleetDetails", 0x446188: "FleetButtonsOn", 0x446128: "ArmyButtonsOn",
         0x446268: "CityButtonsOn", 0x4460A8: "AllButtonsOff", 0x42D750: "MessageDlg", 0x44B5D0: "naval_battle",
         0x44AEE4: "army_battle", 0x44B27C: "siege", 0x44B79C: "embark", 0x449B40: "set_relation"}


REAL = {0x44B5D0, 0x449B40}       # with --real these run unmodified (their own news/presentation calls stubbed below)
NEWS = {0x45BF28: "sound", 0x449240: "news_line", 0x405B00: "str_copy", 0x405BC8: "str_cat", 0x405C98: "str_upper"}


def select(ram, square, answer, real=False):
    u = Uc(UC_ARCH_X86, UC_MODE_32)
    u.mem_map(0x400000, 0x300000)
    u.mem_map(0x700000, 0x110000)
    for va, rp, rs in C.SECTIONS:
        if rs:
            u.mem_write(va, C.EXE[rp:rp + rs])
    u.mem_write(C.ORIGIN, bytes(ram))
    form = bytearray(0x400)
    struct.pack_into("<I", form, 0x21A, C.point(square))
    for off in (0x220, 0x222, 0x224):
        struct.pack_into("<h", form, off, -1)
    u.mem_write(FORM, bytes(form))
    esp = 0x80F000
    u.mem_write(esp, struct.pack("<I", 0x600000))
    for reg, v in ((UC_X86_REG_EAX, FORM), (UC_X86_REG_EDX, C.point(square)), (UC_X86_REG_ECX, 0), (UC_X86_REG_ESP, esp)):
        u.reg_write(reg, v)
    calls = []

    stubs = {a: n for a, n in STUBS.items() if not (real and a in REAL)}
    if real:
        stubs.update(NEWS)

    def hook(uc, addr, size, data):
        if real and addr in REAL:
            calls.append({"call": STUBS[addr] + " (real)", "eax": uc.reg_read(UC_X86_REG_EAX) & 0xFFFF,
                          "edx": uc.reg_read(UC_X86_REG_EDX)})
        if addr in stubs:
            name = stubs[addr]
            row = {"call": name, "eax": uc.reg_read(UC_X86_REG_EAX) & 0xFFFF, "edx": uc.reg_read(UC_X86_REG_EDX)}
            if name == "MessageDlg":
                row["text"] = bytes(uc.mem_read(uc.reg_read(UC_X86_REG_EAX), 64)).split(b"\0")[0].decode("latin1")
            calls.append(row)
            sp = uc.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack("<I", uc.mem_read(sp, 4))[0]
            uc.reg_write(UC_X86_REG_EAX, answer if name == "MessageDlg" else 0)
            uc.reg_write(UC_X86_REG_ESP, sp + 4 + (4 if name == "MessageDlg" else 0))   # FUN_0042d750 takes one stack arg
            uc.reg_write(UC_X86_REG_EIP, ret)
    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(SELECT, 0x600000, count=5_000_000)
    assert u.reg_read(UC_X86_REG_EIP) == 0x600000, hex(u.reg_read(UC_X86_REG_EIP))
    out = bytearray(u.mem_read(C.ORIGIN, C.SIZE))
    return out, calls, {"selected_army": C.short(out, 0x4A0328), "selected_fleet": C.short(out, 0x4A032A)}


def stage(war):
    r = bytearray(C.RAM)
    C.put(r, 0x4A0320, NATION)
    n = C.short(r, 0x4A0326)
    own = next(i for i in range(n) if C.short(r, FLEETS + i * FREC + 8) == NATION)
    enemy = next(i for i in range(n) if C.short(r, FLEETS + i * FREC + 8) not in (NATION, -1))
    eo = C.short(r, FLEETS + enemy * FREC + 8)
    # two adjacent open-sea cells away from every city (FUN_004494e4 must find no own city of the enemy next to it)
    a, b = (100, 100), (101, 100)
    for i, p in ((own, a), (enemy, b)):
        C.put(r, FLEETS + i * FREC, p[0]); C.put(r, FLEETS + i * FREC + 2, p[1])
        C.setcell(r, p, 300 + i)
    C.put(r, FLEETS + own * FREC + 0xC, 8)                     # own fleet moves
    C.put(r, FLEETS + own * FREC + 0x16, -1)
    C.put(r, 0x4A032A, own)
    C.put(r, 0x4A0328, -1)
    rel = 3 if war else 0
    C.put(r, 0x474696 + NATION * 0x494 + eo * 2, rel)
    C.put(r, 0x474696 + eo * 0x494 + NATION * 2, rel)
    return r, {"own_fleet": own, "enemy_fleet": enemy, "enemy_owner": eo, "own_at": a, "enemy_at": b,
               "map_codes": [C.cell(r, a), C.cell(r, b)], "relation": rel}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--real", action="store_true")
    a = ap.parse_args()
    v = a.version
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / f"selectunit-{v}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    rows = []
    for war, answer in ((True, 6), (False, 7), (False, 6)):
        r, setup = stage(war)
        r1, calls1, sel1 = select(r, setup["enemy_at"], answer, a.real)
        r2, calls2, sel2 = select(r1, setup["enemy_at"], answer, a.real)  # the refresh's re-run on the same square
        sel1["own_moves"] = C.short(r1, FLEETS + setup["own_fleet"] * FREC + 0xC)
        sel1["enemy_square_code"] = C.cell(r1, setup["enemy_at"])
        rows.append({"case": f"{'war' if war else 'peace'}, dialog answer {answer}", "setup": setup,
                     "click": {"calls": calls1, "after": sel1}, "refresh_rerun": {"calls": calls2, "after": sel2}})
    out.write_text(json.dumps({"ram": "#187 snapshot (private)", "real_order_routines": a.real, "rows": rows}, indent=1))
    for row in rows:
        print(row["case"], row["setup"]["map_codes"])
        for k in ("click", "refresh_rerun"):
            print("  ", k, [c["call"] + (":" + c.get("text", "")[:30] if c["call"] == "MessageDlg" else "") for c in row[k]["calls"]], row[k]["after"])


if __name__ == "__main__":
    main()
