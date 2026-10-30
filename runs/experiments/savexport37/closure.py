#!/usr/bin/env python3
"""Research #37 Q2 (2026-10-31): static call closure of a function in the pinned decompile, and every assignment in it whose
left side names a global inside a block the saver FUN_004484d0 writes to the SAV (SAVED below, read from its stream calls).

    python3 runs/experiments/savexport37/closure.py <function name> [--stop name,name]

The decompile is the private pinned dump (artifacts/cloud-migration-20261021/.../all_app_functions.txt); output is function
names, addresses and the matched source lines only. Indirect calls (VCL virtual methods, event pointers) are listed as
unresolved: a closure over direct calls only.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DUMP = ROOT / "artifacts/cloud-migration-20261021/ic2-research-inputs-20261021/decompile/all_app_functions.txt"
# (start, length) of every block FUN_004484d0 streams; tables at their maximal extent
SAVED = [(0x45E870, 0x15E00), (0x479590, 0x2C5C), (0x4A0324, 2), (0x47C1EC, 0x290 * 200), (0x4A0326, 2),
         (0x49C26C, 0x1A * 140), (0x474670, 0x4940), (0x49DA10, 50 * 12), (0x4A031E, 2), (0x49F994, 0x3D * 40),
         (0x49EFE8, 0x20), (0x49F008, 4), (0x4A0320, 2), (0x4A0322, 2), (0x4A0330, 2), (0x4A0332, 2), (0x4A032E, 2),
         (0x4A0338, 8), (0x4A0B7C, 1), (0x4A0B74, 2), (0x4A0B76, 2), (0x4A0B78, 2), (0x4A0B7D, 1), (0x4A0B7A, 2),
         (0x4A0344, 0x6E0), (0x4A0A24, 0x150)]


def saved(a):
    return any(s <= a < s + n for s, n in SAVED)


HEAD = re.compile(r"^// ==== (\S+) @ ([0-9a-f]+) ====")
CALL = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
GLOBAL_W = re.compile(r"(?:\(\s*&?DAT_([0-9a-f]{8})|\bDAT_([0-9a-f]{8}))[^=;]*?(?<![=!<>])=(?!=)")


def parse():
    funcs, cur, buf, addr = {}, None, [], None
    for line in DUMP.read_text(errors="replace").splitlines():
        m = HEAD.match(line)
        if m:
            if cur:
                funcs[cur] = (addr, buf)
            cur, addr, buf = m[1], m[2], []
        elif cur:
            buf.append(line)
    if cur:
        funcs[cur] = (addr, buf)
    return funcs


def main():
    name = sys.argv[1]
    stop = set(sys.argv[sys.argv.index("--stop") + 1].split(",")) if "--stop" in sys.argv else set()
    funcs = parse()
    seen, todo, unresolved = [], [name], set()
    while todo:
        f = todo.pop()
        if f in seen or f not in funcs or f in stop:
            continue
        seen.append(f)
        for line in funcs[f][1]:
            for c in CALL.findall(line):
                if c in funcs and c not in seen:
                    todo.append(c)
            if "(**(code **)" in line or "(*(code *)" in line:
                unresolved.add(f)
    hits = []
    for f in seen:
        for i, line in enumerate(funcs[f][1]):
            for m in GLOBAL_W.finditer(line):
                a = int(m[1] or m[2], 16)
                if saved(a) and "==" not in line.split("=")[0]:
                    hits.append({"function": f, "address": funcs[f][0], "global": hex(a), "line": line.strip()[:160]})
    out = {"root": name, "functions": [[f, funcs[f][0]] for f in seen], "indirect_calls_in": sorted(unresolved),
           "state_writes": hits}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
