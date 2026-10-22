#!/usr/bin/env python3
"""The AI-decision hook: an observation-only build of the seed exe that logs, in memory, every homeland-intercept dispatch and every fleet
hunt-or-port move of a computer seat (AI checks 3 and 4 of the research report 2026-10-07-strategic-ai-turn.md, §3.1 and §4).

    python3 patches/ai_hook.py <game folder>      # reads "Imperial Conquest 2 fast rollingsave seed.exe", writes "... seed aihook.exe"

Hooked call sites (each `E8 rel32` is re-pointed to its own stub; the stub jumps on to the original target):
  intercept_capital  0x44F2E7  FUN_0044efc8 -> FUN_0044dba8(army, capital xy)        (threat aboard a fleet, or not at war)
  intercept_army     0x44F2F9  FUN_0044efc8 -> FUN_0044dba8(army, threat army xy)    (threat at war, on land)
  fleet_hunt         0x44F69A  FUN_0044f608 -> FUN_0044e1fc(fleet, target fleet xy)  (hunt score > 100)
  fleet_port         0x44F6BE  FUN_0044f608 -> FUN_0044e1fc(fleet, port city xy)     (hunt score <= 100, a port was found)
  fleet_stored_dest  0x44F667  FUN_0044f608 -> FUN_0044e1fc(fleet, stored destination) (the fleet's +4 destination is set: no hunt, no port)  [v4]

A stub: pushfd; pushad; if count < CAP: write a 72-byte record at BUF + 72*count = (site id, EAX, EDX, current nation [0x4A0320] sign-extended,
the caller's top 24 stack bytes, then at +40 the unit's own record at decision time (army table 0x47C1EC + 0x290*i: its first 16 bytes; fleet
table 0x49C26C + 0x1A*i: 28 bytes, the whole 26-byte record), and at +68 the OTHER unit's record (the chosen threat army [caller+0xA]: 12 bytes;
the hunt target fleet [caller+2]: 28 bytes; nothing when the index is negative), then count += 1; popad; popfd; jmp target.
Versions: v1 'AIH1' 40-byte records (no unit records); v2 'AIH2' 72 bytes (16 + 12 bytes of the unit records: army and fleet indices shift
within a turn when a record is deleted, so a save cannot stand in for the decision-time state); v3 'AIH3' 96 bytes (whole fleet records,
so the hunt score can be recomputed from the decision-time ships and condition). Registers, EFLAGS and ESP reach the target exactly as the original call
left them (tests/test_ai_hook.py runs each stub under unicorn). The caller's stack holds the decision's inputs:
  FUN_0044efc8 frame: +2 threats, +4 dispatched so far, this one included (incremented before the call), +6 distance army-capital, +8 distance to the chosen threat,
                      +0xA the chosen threat army, +0xE/+0x10 best army-target score/distance, +0x14/+0x16 best city-target score/distance
  FUN_0044f608 frame: +0 hunt score, +2 hunt target fleet, +4 chosen port city
The log lives in a grown `.patch` section (made writable): CTL 0x565000 (+0 count, +4 magic 'AIH1', +8 capacity), BUF 0x565100.
"""
import struct
import sys
from pathlib import Path

BASE = 0x400000
CODE_VA, CODE_RAW = 0x401000, 0x400
PATCH_VA, PATCH_RAW, SEED_PATCH_SIZE = 0x564000, 0x11CC00, 0x600
CAVES = 0x564600
CTL, BUF = 0x565000, 0x565100
RAW_SIZE = 0x1200                       # caves + control block in the file; the buffer is zero-fill (virtual size only)
REC, CAP = 96, 65536
MAGIC = 0x34484941                      # 'AIH4' (v4 = v3 + the fleet_stored_dest site)
ARMIES, ARMY_LEN, FLEETS, FLEET_LEN = 0x47C1EC, 0x290, 0x49C26C, 0x1A
NATION = 0x4A0320
SITES = (("intercept_capital", 1, 0x44F2E7, 0x44DBA8), ("intercept_army", 2, 0x44F2F9, 0x44DBA8),
         ("fleet_hunt", 3, 0x44F69A, 0x44E1FC), ("fleet_port", 4, 0x44F6BE, 0x44E1FC), ("fleet_stored_dest", 5, 0x44F667, 0x44E1FC))
SRC = "Imperial Conquest 2 fast rollingsave seed.exe"
DST = "Imperial Conquest 2 fast rollingsave seed aihook.exe"


def off(va):
    return va - CODE_VA + CODE_RAW


def rel32(src, target):
    return struct.pack("<i", target - (src + 5))


def u32(v):
    return struct.pack("<I", v & 0xFFFFFFFF)


def stub(va, site_id, target):
    """The stub's bytes at `va` (hand-assembled; disassembled in tests/test_ai_hook.py)."""
    body = bytearray()
    body += b"\x9C\x60"                                     # pushfd; pushad
    body += b"\x8B\x0D" + u32(CTL)                          # mov ecx, [CTL]
    body += b"\x81\xF9" + u32(CAP)                          # cmp ecx, CAP
    jae_at = len(body); body += b"\x0F\x83\0\0\0\0"         # jae skip (near; patched below)
    body += b"\x6B\xC9" + bytes([REC])                      # imul ecx, ecx, 40
    body += b"\x81\xC1" + u32(BUF)                          # add ecx, BUF
    body += b"\xC7\x01" + u32(site_id)                      # mov dword [ecx], id
    body += b"\x8B\x44\x24\x1C\x89\x41\x04"                 # mov eax, [esp+0x1C] (saved EAX); mov [ecx+4], eax
    body += b"\x8B\x44\x24\x14\x89\x41\x08"                 # mov eax, [esp+0x14] (saved EDX); mov [ecx+8], eax
    body += b"\x0F\xBF\x05" + u32(NATION) + b"\x89\x41\x0C"  # movsx eax, word [NATION]; mov [ecx+0xC], eax
    for k in range(6):                                      # the caller's [esp+4k]: stub esp + 4 (ret) + 4 (eflags) + 32 (pushad) = +0x28
        body += b"\x8B\x44\x24" + bytes([0x28 + 4 * k]) + b"\x89\x41" + bytes([0x10 + 4 * k])
    table, stride, other = (ARMIES, ARMY_LEN, 0x28 + 0xA) if site_id in (1, 2) else (FLEETS, FLEET_LEN, 0x28 + 2)
    body += b"\x0F\xBF\x44\x24\x1C"                         # movsx eax, word [esp+0x1C] (the unit index, saved EAX)
    body += b"\x69\xC0" + u32(stride)                       # imul eax, eax, stride
    nu, no = (4, 3) if site_id in (1, 2) else (7, 7)
    for k in range(nu):                                     # mov edx, [eax+table+4k]; mov [ecx+0x28+4k], edx
        body += b"\x8B\x90" + u32(table + 4 * k) + b"\x89\x51" + bytes([0x28 + 4 * k])
    body += b"\x0F\xBF\x44\x24" + bytes([other])            # movsx eax, word [caller + other] (threat army / hunt fleet)
    body += b"\x85\xC0"                                     # test eax, eax (movsx sets no flags)
    js_at = len(body); body += b"\x78\x00"                  # js no_other
    body += b"\x69\xC0" + u32(stride)
    for k in range(no):                                     # mov edx, [eax+table+4k]; mov [ecx+0x44+4k], edx
        body += b"\x8B\x90" + u32(table + 4 * k) + b"\x89\x51" + bytes([0x44 + 4 * k])
    body[js_at + 1] = len(body) - (js_at + 2)
    body += b"\xFF\x05" + u32(CTL)                          # inc dword [CTL]
    skip = len(body)
    body[jae_at + 2:jae_at + 6] = struct.pack("<i", skip - (jae_at + 6))
    body += b"\x61\x9D"                                     # popad; popfd
    body += b"\xE9" + rel32(va + len(body), target)         # jmp target
    return bytes(body)


def build(b):
    """Patch the seed exe `b` (bytearray) in place. Returns {site name: stub va}."""
    if len(b) != PATCH_RAW + SEED_PATCH_SIZE:
        raise SystemExit("unexpected size %d (the seed exe has %d)" % (len(b), PATCH_RAW + SEED_PATCH_SIZE))
    if any(x != 0xCC for x in b[PATCH_RAW + (CAVES - PATCH_VA):PATCH_RAW + SEED_PATCH_SIZE]):
        raise SystemExit("the .patch space from 0x%X is not free" % CAVES)
    for name, _, site, target in SITES:
        o = off(site)
        if b[o] != 0xE8 or site + 5 + struct.unpack_from("<i", b, o + 1)[0] != target:
            raise SystemExit("site %s 0x%X is not `call 0x%X`: %s" % (name, site, target, bytes(b[o:o + 5]).hex()))
    hdr = 0x1F8 + 8 * 40                                    # the 9th section header: .patch
    if bytes(b[hdr:hdr + 6]) != b".patch":
        raise SystemExit(".patch is not the 9th section")
    vsize = BUF + CAP * REC - PATCH_VA
    struct.pack_into("<I", b, hdr + 8, vsize)                                   # VirtualSize
    struct.pack_into("<I", b, hdr + 16, RAW_SIZE)                               # SizeOfRawData
    flags = struct.unpack_from("<I", b, hdr + 36)[0]
    struct.pack_into("<I", b, hdr + 36, flags | 0x80000000)                     # + MEM_WRITE (the log)
    struct.pack_into("<I", b, 0x118 + 56, (PATCH_VA - BASE + vsize + 0xFFF) & ~0xFFF)   # SizeOfImage
    b += b"\xCC" * (CTL - PATCH_VA - SEED_PATCH_SIZE) + bytes(RAW_SIZE - (CTL - PATCH_VA))
    raw = lambda va: PATCH_RAW + (va - PATCH_VA)
    b[raw(CTL + 4):raw(CTL + 8)] = u32(MAGIC)
    b[raw(CTL + 8):raw(CTL + 12)] = u32(CAP)
    va, out = CAVES, {}
    for name, sid, site, target in SITES:
        code = stub(va, sid, target)
        b[raw(va):raw(va) + len(code)] = code
        b[off(site):off(site) + 5] = b"\xE8" + rel32(site, va)
        out[name] = va
        va = (va + len(code) + 15) & ~15
    if va > CTL:
        raise SystemExit("caves overflow into the control block")
    return out


def decode(buf, n):
    """Records from the raw buffer bytes: list of dicts."""
    names = {sid: name for name, sid, _, _ in SITES}
    out = []
    for i in range(n):
        sid, eax, edx, nation = struct.unpack_from("<IIIi", buf, i * REC)
        st = buf[i * REC + 16:i * REC + 40]
        r = {"i": i, "site": names.get(sid, sid), "nation": nation, "unit": struct.unpack("<h", struct.pack("<I", eax)[:2])[0],
             "target_x": struct.unpack("<h", struct.pack("<I", edx)[:2])[0], "target_y": struct.unpack("<h", struct.pack("<I", edx)[2:])[0],
             "stack": st.hex()}
        w = lambda o: struct.unpack_from("<h", st, o)[0]
        u = buf[i * REC + 40:i * REC + 68]; o = buf[i * REC + 68:i * REC + 96]
        if sid in (1, 2):                                   # army record: +0 x, +2 y, +4 owner, +6 moves, +8 cell, +0xA supplies, +0xC money, +0xE morale
            r["unit_rec"] = dict(zip(("x", "y", "owner", "moves", "cell", "supplies", "money", "morale"), struct.unpack("<8h", u[:16])))
            r["other_rec"] = dict(zip(("x", "y", "owner", "moves", "cell", "supplies"), struct.unpack("<6h", o[:12])))
        else:                                               # fleet record (state/sav.py): x, y, destination x/y, owner, countdown, moves, supplies, money, ships, condition, army, cell
            F = ("x", "y", "dest_x", "dest_y", "owner", "countdown", "moves", "supplies", "money", "ships", "condition", "army", "cell")
            r["unit_rec"] = dict(zip(F, struct.unpack("<13h", u[:26])))
            r["other_rec"] = dict(zip(F, struct.unpack("<13h", o[:26])))
        if sid in (1, 2):
            r.update(threats=w(2), dispatched_incl_this=w(4), dist_capital=w(6), dist_threat=w(8), threat_army=w(0xA),
                     army_target_score=w(0xE), army_target_dist=w(0x10), city_target_score=w(0x14), city_target_dist=w(0x16))
        else:
            r.update(hunt_score=w(0), hunt_fleet=w(2), port_city=w(4))
        out.append(r)
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    b = bytearray((folder / SRC).read_bytes())
    caves = build(b)
    (folder / DST).write_bytes(bytes(b))
    print("wrote", folder / DST, {k: hex(v) for k, v in caves.items()})
