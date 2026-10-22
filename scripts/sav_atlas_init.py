#!/usr/bin/env python3
"""Initialisation provenance of the original-SAV fields (conquest issue #107).

    B=$HOME/ic2-inputs/ic2-research-inputs-20261021
    python3 -I scripts/sav_atlas_init.py --exe "$B/original/Imperial Conquest 2.exe" \
        --dat "$B/original/Imperial Conquest 2.dat" --root $B \
        $B/source-saves $B/native-evidence $B/research40-saves \
        --out runs/experiments/data/run-exp-sav-atlas107/<new-name>.json

Three checks, all static (no game is run):

1. DAT layout. The DAT loader FUN_004481A0 (program start and File > New, both
   just before the NewGame initialiser FUN_00448AA4) reads the DAT with one
   TStream.Read per block. DAT_LAYOUT lists each read: destination, length,
   repeat and the address of the instruction that loads the destination and the
   length. The script checks those instruction bytes in the EXE, then that the
   reads sum to the DAT's size (the whole file is consumed, nothing else).
2. NewGame constants. The nation colour dwords the initialiser stores are read
   from its own instructions (capstone).
3. Corpus. Each SAV is framed (sav_atlas_coverage.frame) and compared field by
   field with the DAT (static tables, start-of-game copies) and the NewGame
   values. The output holds counts only, never bytes or values.

Files are created exclusively (CLAUDE.md rule 6).
"""
import argparse
import hashlib
import json
import struct
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sav_atlas_coverage as cov  # noqa: E402

NATION_BASE, NATION_LEN = 0x474670, 1172
# (block, runtime destination (nation blocks: offset in the record), length, repeat,
#  VA of the instruction loading the destination, VA of the one loading the length)
# Destination loads are `mov edx, imm32` (BA) or `mov esi, imm32` (BE) or `lea edx, [esi+disp32]`
# (8D 96) / `lea edx, [esi+disp8]` (8D 56); lengths are `mov ecx, imm32` (B9).
DAT_LAYOUT = [
    ("map", 0x45E870, 0x15E00, 1, 0x4481E1, 0x4481E6),
    ("city", 0x479590, 0x2C5C, 1, 0x4481F1, 0x4481F6),
    ("army", 0x47C1EC, 0x290, 15, 0x448207, 0x44820E),
    ("fleet", 0x49C26C, 0x1A, 2, 0x448234, 0x44823B),
    ("nation.name", 0x000, 0xB, 16, None, 0x44826A),
    ("nation.relations", 0x026, 0x20, 16, 0x448277, 0x44827A),
    ("nation.neighbours", 0x046, 0x2, 16, 0x448285, 0x448288),
    ("nation.city_list", 0x048, 0x29C, 16, 0x448293, 0x448296),
    ("nation.recruit", 0x2E4, 0x140, 16, 0x4482A1, 0x4482A7),
    ("nation.wealth", 0x430, 0x4, 16, 0x4482B2, 0x4482B8),
    ("nation.treasury", 0x438, 0x4, 16, 0x4482CF, 0x4482D5),
    ("nation.unity", 0x440, 0x2, 16, 0x4482EC, 0x4482F2),
    ("nation.mobilization", 0x442, 0x2, 16, 0x4482FD, 0x448303),
    ("nation.capital", 0x444, 0x2, 16, 0x44830E, 0x448314),
    ("nation.cities", 0x446, 0x2, 16, 0x44831F, 0x448325),
    ("nation.tax", 0x44A, 0x2, 16, 0x44833E, 0x448344),
    ("nation.tax_base", 0x44C, 0x2, 16, 0x44834F, 0x448355),
    ("nation.conqueror", 0x44E, 0x2, 16, 0x448360, 0x448366),
    ("const.478FB0", 0x478FB0, 0xC8, 1, 0x448382, 0x448387),
    ("const.479078", 0x479078, 0x28, 1, 0x448392, 0x448397),
    ("const.4790A0", 0x4790A0, 0xA, 1, 0x4483A2, 0x4483A7),
    ("const.4790AC", 0x4790AC, 0xE8, 1, 0x4483B2, 0x4483B7),
    ("const.479194", 0x479194, 0x150, 1, 0x4483C2, 0x4483C7),
    ("const.4792E4", 0x4792E4, 0xA8, 1, 0x4483D2, 0x4483D7),
    ("const.47938C", 0x47938C, 0x6E, 1, 0x4483E2, 0x4483E7),
    ("const.4793FC", 0x4793FC, 0x6E, 1, 0x4483F2, 0x4483F7),
    ("const.47946C", 0x47946C, 0x32, 1, 0x448402, 0x448407),
    ("const.4794A0", 0x4794A0, 0x28, 1, 0x448412, 0x448417),
    ("const.4794C8", 0x4794C8, 0x1E, 1, 0x448422, 0x448427),
    ("const.4794E8", 0x4794E8, 0x40, 1, 0x448432, 0x448437),
    ("const.479528", 0x479528, 0x18, 1, 0x448442, 0x448447),
    ("const.479540", 0x479540, 0x50, 1, 0x448452, 0x448457),
    ("merc_label_names", 0x49CC94, 0x410, 1, 0x448462, 0x448467),
    ("merc_pool", 0x49D0A4, 0xBC4, 1, 0x448472, 0x448477),
    ("leader_names", 0x49DC68, 0x1380, 1, 0x448482, 0x448487),
    ("news", 0x49F994, 0x988, 1, 0x448492, 0x448497),
]
# Copies the loader makes right after a read: start-of-game values.
DAT_COPIES = [("NATION.wealth0", 0x430, 0x434, 4, 0x4482C3), ("NATION.treasury0", 0x438, 0x43C, 4, 0x4482E0),
              ("NATION.cities0", 0x446, 0x448, 2, 0x448330)]
NEWGAME_INIT, NEWGAME_END = 0x448AA4, 0x448E71
MERC_TEMPLATES, MERC_LIVE = 201, 50
LEADERS_PER_NATION, LEADER_LEN = 12, 26


def pe(path):
    b = Path(path).read_bytes()
    p = struct.unpack_from("<I", b, 0x3C)[0]
    nsec, opt = struct.unpack_from("<H", b, p + 6)[0], struct.unpack_from("<H", b, p + 20)[0]
    base = struct.unpack_from("<I", b, p + 24 + 28)[0]
    secs = []
    for k in range(nsec):
        s = p + 24 + opt + 40 * k
        vsize, va, rsize, raw = (struct.unpack_from("<I", b, s + o)[0] for o in (8, 12, 16, 20))
        secs.append((base + va, raw, min(vsize, rsize)))
    return b, secs


def at(img, va, n):
    b, secs = img
    for sva, raw, size in secs:
        if sva <= va and va + n <= sva + size:
            return b[raw + va - sva: raw + va - sva + n]
    raise ValueError(hex(va))


def check_instr(img, va, value, kind):
    """True when the instruction at va loads `value` as described (see DAT_LAYOUT)."""
    if va is None:
        return True
    b = at(img, va, 7)
    imm = struct.pack("<I", value)
    if kind == "len":
        return b[0] == 0xB9 and b[1:5] == imm
    if b[0] in (0xBA, 0xBE) and b[1:5] == imm:
        return True
    if b[:2] == b"\x8D\x96" and b[2:6] == imm:
        return True
    return b[:2] == b"\x8D\x56" and b[2] == value and value < 0x80


def dat_offsets():
    """{block: [DAT offset per repeat]} in the loader's read order."""
    out, o = defaultdict(list), 0
    nation_blocks = [e for e in DAT_LAYOUT if e[0].startswith("nation.")]
    for e in DAT_LAYOUT:
        if e[0].startswith("nation."):
            continue
        if e[0] == "const.478FB0":  # the nation loop runs between the fleets and the constants
            for n in range(16):
                for ne in nation_blocks:
                    out[ne[0]].append(o)
                    o += ne[2]
        for _ in range(e[3]):
            out[e[0]].append(o)
            o += e[2]
    return out, o


def newgame_colours(img):
    """{(nation, k): colour} from the initialiser's `mov dword [edi+disp], imm|eax` stores."""
    from capstone import CS_ARCH_X86, CS_MODE_32, Cs
    from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    code = at(img, NEWGAME_INIT, NEWGAME_END - NEWGAME_INIT)
    out, eax = {}, None
    for ins in md.disasm(code, NEWGAME_INIT):
        ops = list(ins.operands)
        if ins.mnemonic == "xor" and ins.op_str == "eax, eax":
            eax = 0
            continue
        if ins.mnemonic == "mov" and len(ops) == 2 and ops[0].type == X86_OP_MEM \
                and md.reg_name(ops[0].mem.base) == "edi" and ops[0].size == 4:
            d = ops[0].mem.disp
            n, off = divmod(d, NATION_LEN)
            if 0x424 <= off < 0x430:
                v = ops[1].imm if ops[1].type == X86_OP_IMM else eax if ops[1].type == X86_OP_REG else None
                out[(n, (off - 0x424) // 4)] = v & 0xFFFFFFFF if v is not None else None
        elif ins.mnemonic not in ("mov",):
            eax = None if "eax" in ins.op_str.split(",")[0] else eax
    return out


def cstr(b):
    return b.split(b"\0", 1)[0]


def compare(sav, dat, offs, colours):
    """Per-check (equal, total) counts for one framed SAV."""
    blocks, facts = cov.frame(sav)
    pos = {rec: o for rec, o, _ in blocks}
    r = defaultdict(lambda: [0, 0])

    def tally(key, ok):
        r[key][0] += bool(ok)
        r[key][1] += 1

    c_sav, c_dat = pos["city"], offs["city"][0]
    for i in range(334):
        s, d = sav[c_sav + 34 * i: c_sav + 34 * i + 34], dat[c_dat + 34 * i: c_dat + 34 * i + 34]
        tally("CITY.name(14 bytes)", s[0:14] == d[0:14])
        tally("CITY.x", s[14:16] == d[14:16])
        tally("CITY.y", s[16:18] == d[16:18])
        tally("CITY.allegiance", s[20:22] == d[20:22])
        tally("contrast:CITY.owner", s[18:20] == d[18:20])
        tally("contrast:CITY.pop", s[28:30] == d[28:30])
    n0 = pos["nation"]
    for n in range(16):
        rec = sav[n0 + NATION_LEN * n: n0 + NATION_LEN * (n + 1)]
        tally("NATION.name(11 bytes)", rec[0:11] == dat[offs["nation.name"][n]: offs["nation.name"][n] + 11])
        for fid, src, dst, w, _ in DAT_COPIES:
            blk = "nation." + fid.split(".")[1].rstrip("0")
            d = dat[offs[blk][n]: offs[blk][n] + w]
            tally(fid + "==DAT", rec[dst:dst + w] == d)
            tally("contrast:" + fid.rstrip("0") + "==DAT", rec[src:src + w] == d)
        lt = offs["leader_names"][0] + n * LEADERS_PER_NATION * LEADER_LEN
        names = {cstr(dat[lt + k * LEADER_LEN: lt + (k + 1) * LEADER_LEN]) for k in range(LEADERS_PER_NATION)}
        tally("NATION.leader in DAT leader list of its nation", cstr(rec[0xB:0x26]) in names)
        tally("NATION.colours==NewGame constants",
              all(struct.unpack_from("<I", rec, 0x424 + 4 * k)[0] == colours.get((n, k)) for k in range(3)))
        tally("NATION.unknown27 all zero", not any(rec[0x450:0x46B]))
        tally("NATION.unknown1 zero", rec[0x46D] == 0)
        tally("NATION.unknown3 all zero", not any(rec[0x491:0x494]))
    order = [struct.unpack_from("<h", sav, pos["trailer"] + 2 * k)[0] for k in range(16)]
    tally("TRAILER.turn_order is a permutation of 0..15", sorted(order) == list(range(16)))
    m0, t0 = pos["merc"], offs["merc_pool"][0]
    templates = {dat[t0 + 12 * k: t0 + 12 * k + 8] for k in range(MERC_TEMPLATES)}
    template_xy = {dat[t0 + 12 * k: t0 + 12 * k + 4] for k in range(MERC_TEMPLATES)}
    for s in range(MERC_LIVE):
        slot = sav[m0 + 12 * s: m0 + 12 * s + 12]
        if slot == b"\0\0\0\0\0\0\0\0\xff\xff\0\0":
            tally("MERC never-filled slot", True)
            continue
        tally("MERC (x,y) equals a template's", slot[0:4] in template_xy)
        tally("MERC (x,y,label,type) equals a template's", slot[0:8] in templates)
    return r, facts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exe", type=Path, required=True)
    ap.add_argument("--dat", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=Path("."), help="paths in the receipt are relative to this")
    ap.add_argument("dirs", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    img = pe(a.exe)
    dat = a.dat.read_bytes()
    layout = []
    for name, dest, n, rep, dva, lva in DAT_LAYOUT:
        dval = dest if not name.startswith("nation.") or dest else None
        ok = check_instr(img, lva, n, "len") and (dval is None or check_instr(img, dva, dval, "dest"))
        layout.append(dict(block=name, dest=hex(dest), length=n, repeat=rep, dest_instr=hex(dva) if dva else None,
                           len_instr=hex(lva), instr_bytes_match=ok))
    copies_ok = []
    for fid, src, dst, w, va in DAT_COPIES:
        b = at(img, va, 7)
        # mov eax,[esi+src] / mov [esi+dst],eax (dword: 8B 86 / 89 86) or the word forms (66 8B 86 / 66 89 86)
        nxt = at(img, va + (6 if w == 4 else 7), 7)
        enc = (lambda x, op: (b"\x66" if w == 2 else b"") + op + b"\x86" + struct.pack("<I", x))
        copies_ok.append(dict(field=fid, from_off=hex(src), to_off=hex(dst), instr=hex(va),
                              instr_bytes_match=b.startswith(enc(src, b"\x8B")) and nxt.startswith(enc(dst, b"\x89"))))
    offs, total = dat_offsets()
    colours = newgame_colours(img)
    groups = {}
    for d in a.dirs:
        files = sorted(p for p in d.rglob("*") if p.suffix.lower() == ".sav")
        agg, per = defaultdict(lambda: [0, 0]), []
        for p in files:
            r, facts = compare(p.read_bytes(), dat, offs, colours)
            for k, (e, t) in r.items():
                agg[k][0] += e
                agg[k][1] += t
            per.append(dict(file=str(p.relative_to(a.root)) if p.is_relative_to(a.root) else p.name,
                            sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                            mismatches={k: t - e for k, (e, t) in sorted(r.items()) if e != t}))
        groups[str(d.relative_to(a.root)) if d.is_relative_to(a.root) else str(d)] = dict(
            files=len(files), equal_of_total={k: v for k, v in sorted(agg.items())}, per_file=per)
    out = dict(exe_sha256=hashlib.sha256(a.exe.read_bytes()).hexdigest(), dat_sha256=hashlib.sha256(dat).hexdigest(),
               dat_size=len(dat), dat_layout_sum=total, dat_fully_consumed=total == len(dat),
               dat_layout=layout, dat_copies=copies_ok,
               newgame_colours_found=len(colours), newgame_colours_complete=len(colours) == 48 and None not in colours.values(),
               dat_offsets={k: v[0] for k, v in offs.items()}, groups=groups)
    with open(a.out, "x") as fh:
        json.dump(out, fh, indent=1); fh.write("\n")
    print(json.dumps(dict(dat_fully_consumed=out["dat_fully_consumed"],
                          layout_instr_ok=all(x["instr_bytes_match"] for x in layout),
                          copies_ok=all(x["instr_bytes_match"] for x in copies_ok),
                          colours=out["newgame_colours_complete"])))
    for g, v in groups.items():
        print(g, v["files"])
        for k, (e, t) in v["equal_of_total"].items():
            print(f"   {k}: {e}/{t}")


if __name__ == "__main__":
    sys.exit(main())
