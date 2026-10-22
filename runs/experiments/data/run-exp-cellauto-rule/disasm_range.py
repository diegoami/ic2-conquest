"""Read-only capstone linear sweep of a VA range of Imperial Conquest 2.exe.
Usage: python3 disasm_range.py <exe> <start_va_hex> <end_va_hex>"""
import sys, struct, capstone
data = open(sys.argv[1], 'rb').read()
lo, hi = int(sys.argv[2], 16), int(sys.argv[3], 16)
off = lo - 0x401000 + 0x400
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.skipdata = True
for ins in md.disasm(data[off:hi - 0x401000 + 0x400], lo):
    print(f'{ins.address:#x} {ins.mnemonic} {ins.op_str}')
