"""Memory-only entry records at guarded original strategic move CALL sites.

Uses ai_hook's established writable section builder. Each stub saves/restores
all GPRs, EFLAGS, ESP, stack and original return address, then jumps to the
unchanged original callee. No RNG draw or game-state write. Logs stay private.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'patches'))
import ai_hook as A

CTL, BUF, REC, CAP = 0x566000, 0x566100, 64, 8192
MAGIC = 0x38383153
SNAP, SNAP_BASE, SNAP_SIZE = 0x5e7000, 0x45e000, 0x43000

def stub(va, sid, target):
    b = bytearray(b'\x9c\x60\x8b\x0d' + A.u32(CTL))
    b += b'\x81\xf9' + A.u32(CAP)
    skip = len(b)
    b += b'\x0f\x83' + bytes(4)
    b += b'\x6b\xc9' + bytes([REC]) + b'\x81\xc1' + A.u32(BUF)
    b += b'\xc7\x01' + A.u32(sid)
    for saved, out in ((28, 4), (20, 8), (36, 16)):
        b += b'\x8b\x44\x24' + bytes([saved]) + b'\x89\x41' + bytes([out])
    b += b'\x0f\xbf\x05' + A.u32(A.NATION) + b'\x89\x41\x0c'
    b += b'\xa1' + A.u32(0x45e030) + b'\x89\x41\x14'
    b += b'\x0f\xbf\x44\x24\x1c\x69\xc0' + A.u32(A.ARMY_LEN)
    for k in range(8):
        b += b'\x8b\x90' + A.u32(A.ARMIES + 4*k) + b'\x89\x51' + bytes([24 + 4*k])
    if target == 0x44d734:
        # One atomic pre-walk RAM snapshot for the owner's defender only.
        # Scratch memory is private to the observer, outside original game RAM.
        b += b'\x66\x83\x7c\x24\x1c\x04'  # cmp saved AX,4
        miss1=len(b); b += b'\x0f\x85'+bytes(4)
        b += b'\x83\x3d'+A.u32(CTL+12)+b'\x00'
        miss2=len(b); b += b'\x0f\x85'+bytes(4)
        # ECX is the record pointer used below, so preserve it explicitly.
        b += b'\x51\xfc\xbe'+A.u32(SNAP_BASE)+b'\xbf'+A.u32(SNAP)
        b += b'\xb9'+A.u32(SNAP_SIZE//4)+b'\xf3\xa5\x59'
        b += b'\xff\x05'+A.u32(CTL+12)
        for jump in (miss1,miss2):struct.pack_into('<i',b,jump+2,len(b)-jump-6)
    b += b'\xff\x05' + A.u32(CTL)
    struct.pack_into('<i', b, skip + 2, len(b) - skip - 6)
    b += b'\x61\x9d\xe9' + A.rel32(va + len(b) + 2, target)
    return bytes(b)

def configure(source):
    # Scan guarded rel32 calls, rather than a linear disassembly across embedded
    # data. Every patched site must decode as exactly the expected five-byte CALL.
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    sites = []
    for off in range(0x400, 0x5b800 - 4):
        if source[off] != 0xe8:
            continue
        va = off + 0x401000 - 0x400
        target = va + 5 + struct.unpack_from('<i', source, off + 1)[0]
        if target not in (0x44dba8, 0x44d734):
            continue
        ins = list(md.disasm(source[off:off+5], va))
        assert len(ins) == 1 and ins[0].mnemonic == 'call' and ins[0].size == 5
        sites.append((f'{va:08x}', len(sites)+1, va, target))
    assert len(sites) >= 8 and any(s[2] == 0x44dc3a for s in sites)
    A.SITES = tuple(sites)
    A.CTL, A.BUF, A.RAW_SIZE = CTL, BUF, 0x2200
    A.REC, A.CAP, A.MAGIC, A.stub = REC, CAP, MAGIC, stub
    return sites

def build(source):
    sites = configure(source)
    b = bytearray(source)
    caves = A.build(b)
    hdr=0x1f8+8*40
    vsize=SNAP+SNAP_SIZE-A.PATCH_VA
    struct.pack_into('<I',b,hdr+8,vsize)
    struct.pack_into('<I',b,0x118+56,(A.PATCH_VA-A.BASE+vsize+0xfff)&~0xfff)
    return bytes(b), sites, caves

def read(g):
    count, magic, cap = struct.unpack('<III', g.mem(CTL, 12))
    assert magic == MAGIC and cap == CAP and count < CAP, 'invalid/full observer'
    raw = g.mem(BUF, count * REC)
    records = []
    for i in range(count):
        sid, eax, edx, nation, ret, seed = struct.unpack_from('<IIIiII', raw, i*REC)
        header = struct.unpack_from('<16h', raw, i*REC+24)
        records.append(dict(seq=i, site=A.SITES[sid-1][2], target=A.SITES[sid-1][3],
            army=eax & 65535, goal=list(struct.unpack('<2h', struct.pack('<I', edx))),
            nation=nation, return_address=ret, seed=seed, army_header=header))
    return records, raw
