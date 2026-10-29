#!/usr/bin/env python3
"""Research #42: on a real save's map and fleet, find move targets where the original's human fleet handler (two walker calls)
ends elsewhere than one walker call. Unicorn on the pinned EXE; the save's map and fleet record are loaded as they are.

    python3.12 runs/experiments/fleet42/search_real_map.py --exe EXE --dat DAT --save SAV --fleet N --output OUT.json
"""
import argparse, hashlib, json, struct
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_EDX, UC_X86_REG_ECX, UC_X86_REG_EIP
from state import sav

STUBS = (0x445B38, 0x45BF28, 0x446EF4, 0x446EAC)


def main():
    ap = argparse.ArgumentParser()
    for k in ("exe", "dat", "save", "output"):
        ap.add_argument("--" + k, type=Path, required=True)
    ap.add_argument("--fleet", type=int, required=True)
    a = ap.parse_args()
    if a.output.exists():
        raise SystemExit("output exists")
    exe, dat, save = a.exe.read_bytes(), a.dat.read_bytes(), a.save.read_bytes()
    pe = struct.unpack_from("<I", exe, 0x3C)[0]
    n, opt = struct.unpack_from("<H", exe, pe + 6)[0], struct.unpack_from("<H", exe, pe + 20)[0]
    ib = struct.unpack_from("<I", exe, pe + 24 + 28)[0]
    secs = [(ib + struct.unpack_from("<4I", exe, pe + 24 + opt + 40 * k + 8)[1], *struct.unpack_from("<4I", exe, pe + 24 + opt + 40 * k + 8)[3:1:-1])
            for k in range(n)]
    s = sav.parse(save)
    na = struct.unpack_from("<h", save, sav.ARMY_OFF)[0]
    fo = sav.ARMY_OFF + 2 + na * sav.ARMY_LEN + 2 + a.fleet * sav.FLEET_LEN
    frec = save[fo:fo + 26]
    f = s["fleets"][a.fleet]
    me = f["owner"]

    def run(entry, goal):
        u = Uc(UC_ARCH_X86, UC_MODE_32)
        u.mem_map(0x400000, 0x300000); u.mem_map(0x800000, 0x20000)
        for va, rp, rs in secs:
            if rs:
                u.mem_write(va, exe[rp:rp + rs])
        u.mem_write(0x4792E4, dat[0x1F622:0x1F622 + 168])
        u.mem_write(0x45E870, save[:89600])
        u.mem_write(0x49C26C, frec)
        u.mem_write(0x4A0320, struct.pack("<h", me))
        u.mem_write(0x474B00 + me, b"\x01")
        def hook(uc, addr, size, data):
            if addr in STUBS:
                esp = uc.reg_read(UC_X86_REG_ESP); ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
                uc.reg_write(UC_X86_REG_ESP, esp + 4); uc.reg_write(UC_X86_REG_EIP, ret)
        u.hook_add(UC_HOOK_CODE, hook)
        u.mem_write(0x81F000, struct.pack("<I", 0x600000)); u.reg_write(UC_X86_REG_ESP, 0x81F000)
        if entry == 0x446E24:
            u.mem_write(0x810000, bytes(0x400)); u.mem_write(0x810224, struct.pack("<h", 0)); u.reg_write(UC_X86_REG_EAX, 0x810000)
        else:
            u.reg_write(UC_X86_REG_EAX, 0)
        u.reg_write(UC_X86_REG_EDX, goal[0] | (goal[1] << 16)); u.reg_write(UC_X86_REG_ECX, 0)
        u.emu_start(entry, 0x600000, count=2000000)
        x, y = struct.unpack("<2h", u.mem_read(0x49C26C, 4))
        return [x, y], struct.unpack("<h", u.mem_read(0x49C26C + 12, 2))[0]

    out = {"save": str(a.save), "save_sha256": hashlib.sha256(save).hexdigest(), "fleet": a.fleet, "start": [f["x"], f["y"]],
           "moves": f["moves"], "differing": []}
    for gx in range(f["x"] - 14, f["x"] + 15):
        for gy in range(f["y"] - 14, f["y"] + 15):
            if not (0 <= gx < 320 and 0 <= gy < 140) or sav.cell(s, gx, gy) not in (0, 1):
                continue
            once, h = run(0x44E094, (gx, gy)), run(0x446E24, (gx, gy))
            if once != h:
                out["differing"].append({"goal": [gx, gy], "once": once, "handler": h})
    a.output.write_text(json.dumps(out, indent=1))
    print(len(out["differing"]), "targets differ; first:", out["differing"][:8])


if __name__ == "__main__":
    main()
