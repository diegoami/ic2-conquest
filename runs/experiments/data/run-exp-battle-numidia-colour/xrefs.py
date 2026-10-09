"""Read-only capstone sweep of Imperial Conquest 2.exe: callers of FUN_0044a6c8 (unit recolour)
and instructions whose operands mention the nation recolour dwords (0x474a94/98/9c base).
Usage: python3 xrefs.py <exe> > xrefs.txt"""
import sys, struct, capstone
data = open(sys.argv[1], 'rb').read()
pe = struct.unpack_from('<I', data, 0x3c)[0]
nsec = struct.unpack_from('<H', data, pe + 6)[0]
opt = struct.unpack_from('<H', data, pe + 20)[0]
base = struct.unpack_from('<I', data, pe + 52)[0]
code = None
for i in range(nsec):
    o = pe + 24 + opt + 40 * i
    name = data[o:o + 8].rstrip(b'\0').decode()
    vsz, va, rsz, raw = struct.unpack_from('<IIII', data, o + 8)
    if name == 'CODE':
        code = (data[raw:raw + rsz], base + va)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
targets = ['0x44a6c8', '0x474a94', '0x474a98', '0x474a9c']
for ins in md.disasm(*code):
    s = ins.op_str
    if any(t in s for t in targets) or ('0x424]' in s or '0x428]' in s or '0x42c]' in s):
        print(f'{ins.address:#x} {ins.mnemonic} {s}')
