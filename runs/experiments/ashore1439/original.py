#!/usr/bin/env python3.12
"""imperial_conquest_2#1439 (delegated by research 2026-10-30): the original's all-ashore AI embark path (B79C → F8FC, every unit
overflows) with SEVERAL live armies: raw army-table order, tombstones and indices before and after.

    python3.12 runs/experiments/ashore1439/original.py --version v1

Unmodified original instructions in Unicorn on the #174 complete-RAM baseline (runs/experiments/fleet-overflow174/original.py:
`build` places the source army beside fleet 0 and adds 3000-troop own armies on remote land cells; no helper or RNG replaced).
Cases: the source (6000 troops, all overflow) at raw index 0, 2 or 4 of five live armies; and index 2 of five with a tombstone at
index 1. B79C is entered with EAX = the source index. Then the dead-record sweep FUN_0044adb0 (run before every AI seat's
turn by FUN_00451fdc) is run, unmodified, on the result. Full RAM stays private (artifacts/run-exp-ashore1439/); the public rows
are the per-record (index, owner, x, y, troops) table before and after, the army count word and the calls made.
"""
import argparse
import importlib.util
import json
import struct
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("ov174", R / "runs/experiments/fleet-overflow174/original.py")
O = importlib.util.module_from_spec(spec)
sys.argv_saved = sys.argv
spec.loader.exec_module(O)
from unicorn import UC_HOOK_CODE  # noqa: E402
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ESP, UC_X86_REG_EIP  # noqa: E402

A = R / "artifacts/run-exp-ashore1439"
D = R / "runs/experiments/data/run-exp-ashore1439"
ARMY, REC = 0x47c1ec, 656


def swap(r, i, j):
    a, b = ARMY + i * REC - O.old.RAM_BASE, ARMY + j * REC - O.old.RAM_BASE
    r[a:a + REC], r[b:b + REC] = bytes(r[b:b + REC]), bytes(r[a:a + REC])


def table(raw):
    n = O.short(raw, 0x4a0324)
    rows = []
    for i in range(n + 1):
        p = ARMY + i * REC
        x, y = O.xy(raw, p)
        troops = sum(O.short(raw, p + 16 + 32 * k + 4) for k in range(20))
        rows.append({"index": i, "owner": O.short(raw, p + 4), "x": x, "y": y, "moves": O.short(raw, p + 6), "troops": troops,
                     "first_unit_name": bytes(O.read(raw, p + 16 + 8, 8)).split(b"\0")[0].decode("latin1")})
    return {"count_word": n, "records": rows}


def execute(raw, eax):
    u = O.old.machine(raw)
    u.mem_write(0x80f000, struct.pack("<I", 0x600000))
    u.reg_write(UC_X86_REG_ESP, 0x80f000)
    u.reg_write(UC_X86_REG_EAX, eax)
    calls = []

    def hook(uc, pc, size, data):
        if pc in O.SITES:
            calls.append(O.SITES[pc])
    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(0x44b79c, 0x600000, count=5_000_000)
    assert u.reg_read(UC_X86_REG_EIP) == 0x600000
    assert "random" not in calls
    return bytes(u.mem_read(O.old.RAM_BASE, O.old.RAM_SIZE)), calls


def sweep(raw):
    """FUN_0044adb0, the dead-record sweep run before every AI seat's turn (FUN_00451fdc), unmodified."""
    u = O.old.machine(raw)
    u.mem_write(0x80f000, struct.pack("<I", 0x600000))
    u.reg_write(UC_X86_REG_ESP, 0x80f000)
    u.emu_start(0x44adb0, 0x600000, count=5_000_000)
    assert u.reg_read(UC_X86_REG_EIP) == 0x600000
    return bytes(u.mem_read(O.old.RAM_BASE, O.old.RAM_SIZE))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    v = ap.parse_args().version
    private = A / f"private-{v}"
    private.mkdir(parents=True)
    D.mkdir(parents=True, exist_ok=True)
    legacy = R / "artifacts/run-exp-strategic-tracks/fleet-controls-v3/embark-units-4000-2000"
    base = (legacy / "before.ram").read_bytes()
    cases = [("source0-of5", 0, None), ("source2-of5", 2, None), ("source4-of5", 4, None), ("source2-of5-tombstone1", 2, 1)]
    rows = []
    for name, src, tomb in cases:
        before, geometry = O.build({"id": name, "units": [6000], "table_count": 5}, base)
        before = bytearray(before)
        if src:
            swap(before, 0, src)
        if tomb is not None:
            p = ARMY + tomb * REC
            x, y = O.xy(before, p)
            O.put(before, O.MAP + 2 * (x * 140 + y), O.short(before, p + 8))
            O.put(before, p + 4, -1)
            O.put(before, p + 20, 0)
        before = bytes(before)
        after, calls = execute(before, src)
        O.save_private(private / name, "before", before) if (private / name).mkdir() is None else None
        O.save_private(private / name, "after", after)
        swept = sweep(after)
        O.save_private(private / name, "after-sweep", swept)
        row = {"case": name, "source_index": src, "tombstone_index": tomb, "geometry": geometry,
               "before": table(before), "after": table(after), "after_sweep": table(swept), "calls": calls}
        out = D / f"{v}_{name}.json"
        if out.exists():
            raise SystemExit(f"refusing to overwrite {out}")
        out.write_text(json.dumps(row, indent=1))
        rows.append(row)
        print(name, "calls", calls)
        for t in ("before", "after", "after_sweep"):
            print(" ", t, "count", row[t]["count_word"], [(r["index"], r["owner"], (r["x"], r["y"]), r["troops"], r["first_unit_name"]) for r in row[t]["records"]])


if __name__ == "__main__":
    main()
