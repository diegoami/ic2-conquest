#!/usr/bin/env python3
"""Machine-code reader/writer index of the original-SAV fields (conquest issue #107).

    pip install capstone            # the only extra dependency
    python3 scripts/sav_atlas_asm.py --exe "$B/original/Imperial Conquest 2.exe" \
        --decompile $B/decompile/all_app_functions.txt \
        --out-dir runs/experiments/data/run-exp-sav-atlas107 --tag v1

The decompile-based index (`sav_atlas_access.py`) sees only what Ghidra
decompiled and only literal addresses. This pass reads the EXE itself: it
disassembles the CODE section linearly and, inside each function, follows
  - literal displacements inside a serialized runtime table (as v1);
  - registers and stack slots ([ebp+d], [esp+d]) that hold a table address
    (`mov r, imm`, `lea r, [..+disp]`, copies, `add r, imm`, `add r, k*stride`);
  - calls whose register arguments (eax, edx, ecx: Delphi register
    convention) point into a table: known helpers are classed by their own
    code (StrCopy/StrCat/Move/FillChar/word swap write their destination;
    `call [vmt+0]` / `call [vmt+4]` with edx = buffer and ecx = length are
    TStream Read / Write), others are escapes;
  - `rep movs` / `rep stos` with a tracked edi / esi.
Each hit is classed write, read or escape, with the instruction address.

Heuristic limits, kept explicit: register facts flow only along the linear
order (dropped after jmp/ret, kept across a fall-through loop head); an index
term is assumed to be a multiple of the record stride when it is scaled by the
stride, otherwise the hit is `unresolved`; indirect calls other than the
stream slots are escapes. It is a lead index, not alias closure. Output holds
addresses, classes and field ids only, never code bytes or listings. Files are
created exclusively (CLAUDE.md rule 6).
"""
import argparse
import csv
import hashlib
import json
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sav_atlas_coverage as cov  # noqa: E402
from sav_atlas_access import TABLES, fields_over, scalar_fields  # noqa: E402

# Helpers identified from their own code (addresses in the pinned EXE):
# name -> (dest register, source register, length register or None, kind)
HELPERS = {
    0x405B00: ("strcopy", "eax", "edx"),    # copies the NUL-terminated string edx -> eax
    0x405BC8: ("strcat", "eax", "edx"),     # StrEnd(eax) then StrCopy
    0x402704: ("move", "edx", "eax"),       # Move(src=eax, dst=edx, n=ecx)
    0x40282C: ("fillchar", "eax", None),    # FillChar(dst=eax, n=edx, value=cl)
    0x448FE0: ("swap16", "eax", "edx"),     # exchanges the words at eax and edx (both written)
    0x448FF0: ("swap32", "eax", "edx"),     # exchanges the dwords at eax and edx
}
# The application units start here: the first game class, TBattleDelays, has its methods
# from 0x4367E0 and its unit code from 0x436104; below are System/SysUtils/VCL, where the
# only table-looking hits are inline data decoded as code.
APP_LO = 0x436000
ARG_REGS = ("eax", "edx", "ecx")
VOLATILE = ("eax", "ecx", "edx")
REG32 = {"al": "eax", "ah": "eax", "ax": "eax", "eax": "eax", "bl": "ebx", "bh": "ebx", "bx": "ebx",
         "ebx": "ebx", "cl": "ecx", "ch": "ecx", "cx": "ecx", "ecx": "ecx", "dl": "edx", "dh": "edx",
         "dx": "edx", "edx": "edx", "si": "esi", "esi": "esi", "di": "edi", "edi": "edi",
         "bp": "ebp", "ebp": "ebp", "sp": "esp", "esp": "esp"}


def pe_code(path):
    """(VA, bytes) of the PE's CODE section (first executable section)."""
    b = Path(path).read_bytes()
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    nsec = struct.unpack_from("<H", b, pe + 6)[0]
    opt = struct.unpack_from("<H", b, pe + 20)[0]
    base = struct.unpack_from("<I", b, pe + 24 + 28)[0]
    for k in range(nsec):
        s = pe + 24 + opt + 40 * k
        vsize, va, rsize, raw, chars = (struct.unpack_from("<I", b, s + o)[0] for o in (8, 12, 16, 20, 36))
        if chars & 0x20000000:
            return base + va, b[raw:raw + min(vsize, rsize)], b
    raise SystemExit("no executable section")


SCALAR_ARRAYS = []  # (field_id, start, width) of the scalar fields, so a pointer to one is tracked


def table_of(addr, indexed=False):
    """Table holding addr. An indexed label within one stride below a table's base is that
    table's record -1 (`F - 1` style, the v1 rule)."""
    if indexed:
        for name, base, stride, count, rec in TABLES:
            if base - stride <= addr < base:
                return name, base, stride, rec
    for name, base, stride, count, rec in TABLES:
        if base <= addr < base + stride * count:
            return name, base, stride, rec
    for fid, start, width in SCALAR_ARRAYS:
        if start <= addr < start + width:
            return "scalar", start, 1 << 20, ("scalar", fid)
    return None


class Fact:
    """A register/slot holding table address base + idx*stride + off (off known mod stride)."""
    __slots__ = ("table", "off")

    def __init__(self, table, off):
        self.table, self.off = table, off


def resolve(fact_or_addr, disp=0, width=1, scal=None, indexed=False):
    """(fields, table name, record type) for a tracked fact plus displacement, or a literal address."""
    if isinstance(fact_or_addr, Fact):
        name, base, stride, rec = fact_or_addr.table
        off = (fact_or_addr.off + disp) % stride
    else:
        a = fact_or_addr
        t = table_of(a, indexed)
        if scal and a in scal and not (t and t[0] != "scalar"):
            return [scal[a][0]], "scalar", None
        if not t:
            return None
        name, base, stride, rec = t
        off = (a - base) % stride
    if rec is None:
        return ["BATTLE.grid"], name, rec
    if isinstance(rec, tuple):
        return [rec[1]], name, None
    return fields_over(cov_rows(), rec, off, width), name, rec


_ROWS = []


def cov_rows():
    return _ROWS


def function_starts(code_va, code, decompile=None):
    """Targets of decoded direct calls, plus the decompile's function starts."""
    from capstone import CS_ARCH_X86, CS_MODE_32, Cs
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    starts = set()
    for ins in md.disasm(code, code_va):
        if ins.mnemonic == "call" and ins.op_str.startswith("0x"):
            tgt = int(ins.op_str, 16)
            if code_va <= tgt < code_va + len(code):
                starts.add(tgt)
    if decompile:
        for line in open(decompile, encoding="latin1"):
            m = re.match(r"^// ==== .+? @ ([0-9a-fA-F]+) ====", line)
            if m:
                starts.add(int(m.group(1), 16))
    return starts


def scan(code_va, code, starts, scal, lo=0, hi=None):
    from capstone import CS_ARCH_X86, CS_MODE_32, CS_AC_WRITE, CS_AC_READ, Cs
    from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    hi = hi or code_va + len(code)
    bounds = sorted({s for s in starts if lo <= s < hi} | {max(lo, code_va)})
    bounds.append(hi)
    hits = []
    facts, imm, func = {}, {}, None

    def rn(r):
        return md.reg_name(r) if r else None

    def mem_fact(op):
        """Fact or literal address addressed by a memory operand (without the index term)."""
        m = op.mem
        base, index = rn(m.base), rn(m.index)
        if base and base in facts:
            return facts[base], m.disp
        if not base and index in facts and m.scale == 1:
            return facts[index], m.disp
        idx = bool(m.index or m.base)
        if m.disp and (table_of(m.disp & 0xFFFFFFFF, idx) or (m.disp & 0xFFFFFFFF) in scal):
            return (m.disp & 0xFFFFFFFF), idx
        return None

    def slot(op):
        m = op.mem
        base = rn(m.base)
        if base in ("ebp", "esp") and not m.index and base not in facts:
            return f"{base}{m.disp:+d}"
        return None

    def record(ins, kind, target, disp, width, form, extra=None, indexed=False):
        res = resolve(target, disp, width, scal, indexed)
        if not res:
            return
        fields, tname, rec = res
        h = dict(function=hex(func) if func else None, va=hex(ins.address), kind=kind, form=form,
                 table=tname, fields=fields, width=width)
        if extra:
            h.update(extra)
        hits.append(h)

    def drop(reg):
        facts.pop(reg, None)
        imm.pop(reg, None)

    def region():
        """Each function region disassembled from its own start (resyncs after inline data)."""
        nonlocal func, facts, imm
        for a, b in zip(bounds, bounds[1:]):
            func, facts, imm = (a if a in starts else None), {}, {}
            pending.clear()
            stack.clear()
            yield from md.disasm(code[a - code_va:b - code_va], a)

    pending, dead, stack = {}, False, []  # forward-branch target -> facts; push/pop shadow
    for ins in region():
        if dead:
            # after a jmp the next block is mostly a loop body entered by a backward branch:
            # keep only the callee-saved registers and stack slots (heuristic, documented)
            facts = {k: v for k, v in facts.items() if k not in VOLATILE} if dead == "jmp" else {}
            imm = {}
        if ins.address in pending:
            pf, pi = pending.pop(ins.address)
            facts = {**facts, **pf} if dead else {**pf, **facts}
            if dead:
                imm = pi
        dead = False
        if ins.mnemonic == ".byte":
            facts, imm = {}, {}
            continue
        mn, ops = ins.mnemonic, list(ins.operands)
        if mn.startswith("j") and ops and ops[0].type == X86_OP_IMM and ops[0].imm > ins.address:
            tgt = ops[0].imm
            old = pending.get(tgt)
            pending[tgt] = ({**old[0], **facts}, dict(imm)) if old else (dict(facts), dict(imm))
        # 1. memory operands: reads and writes of table bytes
        for op in ops:
            if op.type != X86_OP_MEM:
                continue
            if mn == "lea":
                continue
            mf = mem_fact(op)
            if mf is None:
                continue
            tgt, extra = mf
            disp = op.mem.disp if isinstance(tgt, Fact) else 0
            idx = (not isinstance(tgt, Fact)) and extra  # a literal label with an index term
            acc = op.access
            if acc & CS_AC_WRITE:
                record(ins, "write", tgt, disp, op.size, "mem", indexed=idx)
            if acc & CS_AC_READ or not acc:
                record(ins, "read", tgt, disp, op.size, "mem", indexed=idx)
        # 2. string/block instructions with tracked edi/esi
        if mn.startswith("rep") and ("movs" in mn or "stos" in mn):
            n = imm.get("ecx")
            unit = {"b": 1, "w": 2, "d": 4}.get(mn[-1], 4) if mn[-1] in "bwd" else 4
            width = n * unit if n is not None else None
            if "edi" in facts:
                record(ins, "write", facts["edi"], 0, width, "rep")
            if "movs" in mn and "esi" in facts:
                record(ins, "read", facts["esi"], 0, width, "rep")
            for r in ("edi", "esi", "ecx"):
                drop(r)
            continue
        # 3. calls: helpers, stream slots, escapes
        if mn == "call":
            op = ops[0] if ops else None
            tgt = op.imm if op is not None and op.type == X86_OP_IMM else None
            if tgt in HELPERS:
                name, dst, src = HELPERS[tgt]
                n = imm.get("ecx") if name == "move" else imm.get("edx") if name == "fillchar" else None
                if dst in facts:
                    record(ins, "write", facts[dst], 0, n, "call:" + name)
                    if name in ("strcat", "swap16", "swap32"):
                        record(ins, "read", facts[dst], 0, n, "call:" + name)
                if src and src in facts:
                    kind = "write" if name.startswith("swap") else "read"
                    record(ins, kind, facts[src], 0, n, "call:" + name)
                    if name.startswith("swap"):
                        record(ins, "read", facts[src], 0, n, "call:" + name)
            elif op is not None and op.type == X86_OP_MEM and op.mem.base and not op.mem.index \
                    and op.mem.disp in (0, 4) and "edx" in facts:
                kind = "write" if op.mem.disp == 0 else "read"
                record(ins, kind, facts["edx"], 0, imm.get("ecx"), "call:stream_" + ("read" if kind == "write" else "write"))
            else:
                for r in ARG_REGS:
                    if r in facts:
                        record(ins, "escape", facts[r], 0, None, "call:arg", {"callee": hex(tgt) if tgt else "indirect", "reg": r})
            for r in VOLATILE:
                drop(r)
            continue
        # 4. register / slot dataflow
        if mn in ("mov", "lea") and len(ops) == 2:
            d, s = ops
            dname = rn(d.reg) if d.type == X86_OP_REG else slot(d) if d.type == X86_OP_MEM else None
            if dname and d.type == X86_OP_REG and dname not in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp"):
                drop(REG32.get(dname, dname))
                continue
            new, newimm = None, None
            if mn == "lea":
                m = s.mem
                base = rn(m.base)
                if base in facts:
                    new = Fact(facts[base].table, (facts[base].off + m.disp) % facts[base].table[2])
                elif not base and rn(m.index) in facts and m.scale == 1:
                    new = Fact(facts[rn(m.index)].table, (facts[rn(m.index)].off + m.disp) % facts[rn(m.index)].table[2])
                else:
                    t = table_of(m.disp & 0xFFFFFFFF, bool(m.index or m.base))
                    if t and base not in ("ebp", "esp"):
                        new = Fact(t, ((m.disp & 0xFFFFFFFF) - t[1]) % t[2])
            elif s.type == X86_OP_IMM:
                v = s.imm & 0xFFFFFFFF
                t = table_of(v)
                new = Fact(t, (v - t[1]) % t[2]) if t else None
                newimm = v
            elif s.type == X86_OP_REG:
                src = rn(s.reg)
                if src in facts:
                    new = facts[src]
                newimm = imm.get(src)
            elif s.type == X86_OP_MEM and slot(s) in facts:
                new = facts[slot(s)]
            if dname:
                drop(dname)
                if new:
                    facts[dname] = new
                if newimm is not None:
                    imm[dname] = newimm
            continue
        if mn in ("add", "sub") and len(ops) == 2:
            d, s = ops
            dname = rn(d.reg) if d.type == X86_OP_REG else slot(d) if d.type == X86_OP_MEM else None
            if dname in facts:
                f = facts[dname]
                if s.type == X86_OP_IMM:
                    sign = 1 if mn == "add" else -1
                    facts[dname] = Fact(f.table, (f.off + sign * s.imm) % f.table[2])
                # a register addend is taken as a whole number of records
                imm.pop(dname, None)
                continue
            if dname and d.type == X86_OP_REG and s.type == X86_OP_REG and rn(s.reg) in facts:
                facts[dname] = facts[rn(s.reg)]
                imm.pop(dname, None)
                continue
        if mn == "push" and ops:
            r = rn(ops[0].reg) if ops[0].type == X86_OP_REG else None
            stack.append((facts.get(r), imm.get(r)) if r else (None, None))
            continue
        if mn == "pop" and ops and ops[0].type == X86_OP_REG:
            r = REG32.get(rn(ops[0].reg))
            f, i = stack.pop() if stack else (None, None)
            drop(r)
            if f:
                facts[r] = f
            if i is not None:
                imm[r] = i
            continue
        if mn in ("jmp", "ret", "retn"):
            dead = "jmp" if mn == "jmp" else "ret"
            continue
        # 5. anything else that writes a register clobbers it
        try:
            _, written = ins.regs_access()
        except Exception:  # noqa: BLE001
            written = []
        for r in written:
            n = REG32.get(rn(r))
            if n:
                drop(n)
        for op in ops:
            if op.type == X86_OP_MEM and op.access & CS_AC_WRITE and slot(op):
                drop(slot(op))
    return hits


def displacement_scan(code_va, code, starts, rec, spans, app_lo):
    """Every memory operand of the application code whose displacement, read as an offset
    into one `rec` record (or as an absolute address inside the table), falls in `spans`,
    whatever its base register. The callee-side complement of the pointer tracking."""
    from capstone import CS_ARCH_X86, CS_MODE_32, Cs
    from capstone.x86 import X86_OP_MEM
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    name, base, stride, count, _ = next(t for t in TABLES if t[4] == rec)
    want = {b for lo, hi in spans for b in range(lo, hi + 1)}
    bounds = sorted(x for x in starts if x >= app_lo) + [code_va + len(code)]
    out, seen = [], set()
    for a, b in zip(bounds, bounds[1:]):
        for ins in md.disasm(code[a - code_va:b - code_va], a):
            if ins.mnemonic == ".byte" or ins.address in seen:
                continue
            for op in ins.operands:
                if op.type != X86_OP_MEM:
                    continue
                d = op.mem.disp & 0xFFFFFFFF
                rel = d if d < stride else (d - base) % stride if base <= d < base + stride * count else None
                if rel in want:
                    seen.add(ins.address)
                    out.append(dict(function=hex(a), va=hex(ins.address), offset=hex(rel),
                                    base=md.reg_name(op.mem.base) if op.mem.base else None,
                                    absolute=d >= stride, write=bool(op.access & 2)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exe", type=Path, required=True)
    ap.add_argument("--decompile", type=Path, help="all_app_functions.txt: adds its function starts")
    ap.add_argument("--field-map", type=Path, default=cov.FIELD_MAP)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--disp-scan", nargs="+", metavar="FIELD",
                    help="only write asm-dispscan-<tag>.json: the displacement scan of these fields")
    ap.add_argument("--app-lo", type=lambda x: int(x, 0), default=APP_LO,
                    help="hits below this address (runtime library/VCL) are listed, not indexed")
    a = ap.parse_args()
    _ROWS[:] = cov.load_map(a.field_map)
    scal_rows = scalar_fields(_ROWS)
    scal = {}
    for addr, (r, w) in scal_rows.items():
        SCALAR_ARRAYS.append((r["field_id"], addr, w))
        for k in range(w):
            scal[addr + k] = (r["field_id"], k)
    code_va, code, exe = pe_code(a.exe)
    starts = function_starts(code_va, code, a.decompile)
    if a.disp_scan:
        rows = {r["field_id"]: r for r in _ROWS}
        res = {}
        for fid in a.disp_scan:
            r = rows[fid]
            res[fid] = displacement_scan(code_va, code, starts, r["record"], [(r["first"], r["last"])], a.app_lo)
        out = dict(exe_sha256=hashlib.sha256(exe).hexdigest(), app_lo=hex(a.app_lo),
                   method="every memory operand of the application code whose displacement is an offset "
                          "inside the field (any base register) or an absolute address inside it",
                   fields={k: dict(n=len(v), operands=v) for k, v in res.items()})
        with open(a.out_dir / f"asm-dispscan-{a.tag}.json", "x") as fh:
            json.dump(out, fh, indent=1); fh.write("\n")
        print({k: len(v) for k, v in res.items()})
        return 0
    allhits = scan(code_va, code, starts, scal)
    hits = [h for h in allhits if int(h["va"], 16) >= a.app_lo]
    library = [h for h in allhits if int(h["va"], 16) < a.app_lo]
    per = defaultdict(lambda: {"read": set(), "write": set(), "escape": set(), "n": defaultdict(int)})
    for h in hits:
        for fid in h["fields"]:
            p = per[fid]
            p[h["kind"]].add(f"{h['function']}@{h['va']}" if h["kind"] != "write" else f"{h['function']}@{h['va']}:{h['form']}")
            p["n"][h["kind"]] += 1
    out = a.out_dir
    with open(out / f"asm-index-{a.tag}.csv", "x", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["field_id", "record", "n_write", "n_read", "n_escape", "writer_functions", "writes", "reader_functions"])
        for r in _ROWS:
            if r["type"].startswith("rec:"):
                continue
            p = per.get(r["field_id"])
            n = p["n"] if p else {}
            wf = sorted({x.split("@")[0] for x in p["write"]}) if p else []
            rf = sorted({x.split("@")[0] for x in p["read"]}) if p else []
            w.writerow([r["field_id"], r["record"], n.get("write", 0), n.get("read", 0), n.get("escape", 0),
                        ";".join(wf), ";".join(sorted(p["write"])) if p else "", ";".join(rf)])
    with open(out / f"asm-refs-{a.tag}.jsonl", "x") as fh:
        for h in hits:
            fh.write(json.dumps(h) + "\n")
    summary = {"exe_sha256": hashlib.sha256(exe).hexdigest(),
               "decompile_sha256": hashlib.sha256(a.decompile.read_bytes()).hexdigest() if a.decompile else None,
               "field_map": a.field_map.name,
               "field_map_sha256": hashlib.sha256(a.field_map.read_bytes()).hexdigest(),
               "method": "linear capstone sweep of CODE; per-function register/stack-slot table-pointer "
                         "tracking; helper and TStream call classing; not alias closure",
               "function_starts": len(starts), "hits": len(hits), "app_lo": hex(a.app_lo),
               "library_region_hits": [dict(va=h["va"], kind=h["kind"], fields=h["fields"]) for h in library],
               "by_kind": {k: sum(h["kind"] == k for h in hits) for k in ("write", "read", "escape")},
               "fields_without_write": [r["field_id"] for r in _ROWS if not r["type"].startswith("rec:")
                                        and not (per.get(r["field_id"]) and per[r["field_id"]]["write"])],
               "fields_without_any_access": [r["field_id"] for r in _ROWS if not r["type"].startswith("rec:")
                                             and r["field_id"] not in per]}
    with open(out / f"asm-summary-{a.tag}.json", "x") as fh:
        json.dump(summary, fh, indent=1); fh.write("\n")
    print(json.dumps({k: summary[k] for k in ("function_starts", "hits", "by_kind")}))
    print("fields without a write:", len(summary["fields_without_write"]), summary["fields_without_write"])


if __name__ == "__main__":
    sys.exit(main())
