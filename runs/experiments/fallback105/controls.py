#!/usr/bin/env python3
"""Research #105 (delegated 2026-10-30): controls for the AI army move's no-progress fallback FUN_0044cec8 and the direct-line
test FUN_0044cb40, run in Unicorn on the pinned unpatched original EXE against a port of the remake's
ClassicalArmyNavigation.LocalFallback / DirectLine (v0.8.4, d9cc71b). Never launches the game.

    python3.12 runs/experiments/fallback105/controls.py --exe EXE --output OUT.json [--saves SAV ...]

The map grid is the SAV's first 89,600 bytes: the in-memory grid DAT_0045e870, markers included (army 100-299 and city 20-99
read as land, fleet 300+ as sea, exactly as both routines test `code < 2 || code > 299`).
- CEC8(P, &out): every army position of every save, plus every coast-adjacent land cell and every edge-row cell of BASE.SAV,
  each with DAT_004a0340 = 0 (the army phase FUN_0044f31c) and = 1 (the fleet phase FUN_0044f608). The port has no flag.
- CB40(a, b): random pairs (fixed RNG seed) on each save's grid, distance 1-40.
"""
import argparse
import hashlib
import json
import random
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_EDX, UC_X86_REG_EIP

MAP, FLAG = 0x45E870, 0x4A0340
CEC8, CB40 = 0x44CEC8, 0x44CB40
EXE_SHA = "9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31"
RET, OUT = 0x600000, 0x810000
ROOT = Path(__file__).resolve().parents[3]
import sys  # noqa: E402
sys.path.insert(0, str(ROOT))


def sea(g, x, y):
    c = g[x * 140 + y]
    return c < 2 or c > 299


def port_fallback(g, x, y):
    """ClassicalArmyNavigation.LocalFallback (remake v0.8.4) on the grid."""
    chosen, s = None, sea(g, x, y)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            good, last = True, None
            for n in (1, 2, 3):
                last = (min(max(x + dx * n, 0), 319), min(max(y + dy * n, 0), 139))
                if sea(g, *last) != s:
                    good = False
            if good:
                chosen = last
    return chosen


def port_direct(g, a, b):
    """ClassicalArmyNavigation.DirectLine (remake v0.8.4), a != b."""
    s = sea(g, *a)
    dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
    sx = (b[0] > a[0]) - (b[0] < a[0])
    sy = (b[1] > a[1]) - (b[1] < a[1])
    xmaj = dx >= dy
    major, minor = max(dx, dy), min(dx, dy)
    err, x, y = 2 * minor - major, a[0], a[1]
    for step in range(major):
        while err >= 0:
            if xmaj:
                y += sy
            else:
                x += sx
            err -= 2 * major
        if xmaj:
            x += sx
        else:
            y += sy
        err += 2 * minor
        if step < major - 1 and sea(g, x, y) != s:
            return False
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--saves", type=Path, nargs="*")
    a = ap.parse_args()
    if a.output.exists():
        raise SystemExit("output exists; choose a new name")
    exe = a.exe.read_bytes()
    assert hashlib.sha256(exe).hexdigest() == EXE_SHA
    pe = struct.unpack_from("<I", exe, 0x3C)[0]
    n, opt = struct.unpack_from("<H", exe, pe + 6)[0], struct.unpack_from("<H", exe, pe + 20)[0]
    ib = struct.unpack_from("<I", exe, pe + 24 + 28)[0]
    u = Uc(UC_ARCH_X86, UC_MODE_32)
    u.mem_map(0x400000, 0x300000)
    u.mem_map(0x800000, 0x20000)
    for k in range(n):
        o = pe + 24 + opt + 40 * k
        vs, va, rs, rp = struct.unpack_from("<4I", exe, o + 8)
        if rs:
            u.mem_write(ib + va, exe[rp:rp + rs])

    def call(entry, eax, edx):
        esp = 0x81F000
        u.mem_write(esp, struct.pack("<I", RET))
        u.reg_write(UC_X86_REG_ESP, esp)
        u.reg_write(UC_X86_REG_EAX, eax)
        u.reg_write(UC_X86_REG_EDX, edx)
        u.emu_start(entry, RET, count=200000)
        assert u.reg_read(UC_X86_REG_EIP) == RET
        return u.reg_read(UC_X86_REG_EAX)

    saves = a.saves or sorted((ROOT / "saves").glob("*.SAV")) + [Path.home() / "ic2-work/fixtures/BASE.SAV"]
    from state import sav as S
    rng = random.Random(105)
    report = {"exe_sha256": EXE_SHA, "remake": "ic2-remake v0.8.4 d9cc71b ClassicalArmyNavigation", "saves": [], "cec8": {},
              "cb40": {}, "mismatches": []}
    for flag in (0, 1):
        report["cec8"][f"flag{flag}"] = {"cases": 0, "agree": 0, "none": 0, "land_origin": 0}
    report["cb40"] = {"cases": 0, "agree": 0, "true": 0}
    for p in saves:
        b = p.read_bytes()
        g = struct.unpack_from("<44800h", b, 0)
        u.mem_write(MAP, b[:89600])
        st = S.parse(b)
        pts = {(ar["x"], ar["y"]) for ar in st["armies"] if ar.get("owner", -1) >= 0 and 0 <= ar["x"] < 320 and 0 <= ar["y"] < 140}
        if p.name == "BASE.SAV":
            for x in range(320):
                for y in range(140):
                    if not sea(g, x, y) and any(0 <= x + i < 320 and 0 <= y + j < 140 and sea(g, x + i, y + j)
                                                for i in (-1, 0, 1) for j in (-1, 0, 1)):
                        pts.add((x, y))
                pts.update({(x, 0), (x, 139)})
            pts.update({(0, y) for y in range(140)} | {(319, y) for y in range(140)})
        report["saves"].append({"file": p.name, "sha256": hashlib.sha256(b).hexdigest(), "cec8_points": len(pts)})
        for flag in (0, 1):
            u.mem_write(FLAG, bytes([flag]))
            r = report["cec8"][f"flag{flag}"]
            for (x, y) in sorted(pts):
                u.mem_write(OUT, struct.pack("<2h", -7, -7))
                call(CEC8, x | (y << 16), OUT)
                ox, oy = struct.unpack("<2h", u.mem_read(OUT, 4))
                orig = None if ox == -1 else (ox, oy)
                port = port_fallback(g, x, y)
                r["cases"] += 1
                r["none"] += orig is None
                r["land_origin"] += not sea(g, x, y)
                if orig == port:
                    r["agree"] += 1
                elif len(report["mismatches"]) < 400:
                    report["mismatches"].append({"routine": "CEC8", "save": p.name, "flag": flag, "origin": [x, y],
                                                 "origin_sea": sea(g, x, y), "original": orig, "port": port})
        u.mem_write(FLAG, b"\0")
        for _ in range(3000):
            ax, ay = rng.randrange(320), rng.randrange(140)
            d = rng.randrange(1, 41)
            bx, by = min(max(ax + rng.randint(-d, d), 0), 319), min(max(ay + rng.randint(-d, d), 0), 139)
            if (ax, ay) == (bx, by):
                continue
            orig = bool(call(CB40, ax | (ay << 16), bx | (by << 16)) & 0xFF)
            port = port_direct(g, (ax, ay), (bx, by))
            report["cb40"]["cases"] += 1
            report["cb40"]["true"] += orig
            if orig == port:
                report["cb40"]["agree"] += 1
            elif len(report["mismatches"]) < 400:
                report["mismatches"].append({"routine": "CB40", "save": p.name, "a": [ax, ay], "b": [bx, by], "original": orig, "port": port})
    a.output.write_text(json.dumps(report, indent=1))
    print(json.dumps({k: report[k] for k in ("cec8", "cb40")}), "mismatches", len(report["mismatches"]))


if __name__ == "__main__":
    main()
