#!/usr/bin/env python3
"""Check F, static part: every instruction of the unpatched `Imperial Conquest 2.exe` that holds the absolute address 0x4a0334 (the save flag,
TPremierForm_SaveGameFile 58109), with its raw bytes, and the whole function that clears it (disassembled from 0x448aa4 up to its `ret`),
plus its callers (E8 rel32 scan of the CODE section). Writes static_flag_xrefs.txt beside this script (next free version). Needs capstone."""
import hashlib, struct, sys
from pathlib import Path
import capstone
sys.path.insert(0, str(Path(__file__).resolve().parent)); from versioned import write_new
EXE = Path.home() / "ic2-work/build/Imperial Conquest 2.exe"
b = EXE.read_bytes(); sha = hashlib.sha256(b).hexdigest()
CODE_RAW, CODE_VA, CODE_LEN = 0x400, 0x401000, 0x5b400
code = b[CODE_RAW:CODE_RAW + CODE_LEN]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
out = [f"# {EXE.name}, SHA-256 {sha} (CODE section: file 0x{CODE_RAW:x}, VA 0x{CODE_VA:x}, size 0x{CODE_LEN:x}); capstone {capstone.__version__}",
       "# 1. every occurrence of the 4 bytes 34 03 4a 00 (the address 0x4a0334) in CODE, with the bytes around it"]
pat = struct.pack("<I", 0x4a0334); i = -1
while True:
    i = code.find(pat, i + 1)
    if i < 0: break
    out.append(f"  imm32 at VA 0x{CODE_VA + i:x}: bytes {code[i-3:i+6].hex(' ')}")
out.append("# 2. the function that holds the clear (start 0x448aa4, from the call sites below), disassembled to the first ret")
start = 0x448aa4; o = start - CODE_VA; n = 0; stop = False
for ins in md.disasm(code[o:o + 0x400], start):
    out.append(f"  0x{ins.address:x}\t{ins.bytes.hex(' '):<24}\t{ins.mnemonic} {ins.op_str}")
    if ins.mnemonic == "ret": break
out.append("# 3. direct calls (E8 rel32) to 0x448aa4 in CODE")
for k in range(len(code) - 4):
    if code[k] == 0xE8 and CODE_VA + k + 5 + struct.unpack_from("<i", code, k + 1)[0] == start:
        out.append(f"  call at VA 0x{CODE_VA + k:x}")
print(write_new(Path(__file__).resolve().parent / "static_flag_xrefs.txt", "\n".join(out) + "\n"))
