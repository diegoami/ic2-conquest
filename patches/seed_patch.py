#!/usr/bin/env python3
"""The seeded build: fast rollingsave, with RandSeed taken from a file.

    python3 patches/seed_patch.py <fixtures dir>

writes "Imperial Conquest 2 fast rollingsave seed.exe" into <fixtures dir>,
next to the untouched "Imperial Conquest 2.exe" that patch_exe.py checks.

The game seeds Delphi's RandSeed (0x45E030) through System.Randomize
(0x402744), which reads the clock (GetSystemTime). It has two call sites:

  0x448AB0  in FUN_00448AA4, New Game's leader and turn-order draw, which runs
            at program start (TPremierForm_InitialiseForm, 0x45A93A) and at
            every New Game (0x45AA32)
  0x456759  in a handler with no direct caller (not reached in our runs)

File > Open does NOT reseed (observed: SEED.LOG gains no line on a load; see
findings/2026-09-29-loading-a-save-does-not-reseed.md). The seed therefore
takes effect at program start, so the driver restarts the game before every
load: turn N = f(the save, SEED.TXT, the orders).

The patch sends Randomize itself through a cave, so both callers are covered.
The cave looks for SEED.TXT beside the exe (GetModuleFileNameA, as the
autosave cave does, because the file dialog moves the current directory). If
the file opens, its leading decimal digits become RandSeed (an empty or
non-numeric file gives 0). If it does not exist, the original clock code runs
unchanged. Each firing appends one 14-byte line to SEED.LOG beside the exe,
"S 0000012345\r\n" (seeded from the file) or "C 0123456789\r\n" (clock), so a
run can show which seed every load used.

RandSeed is also set from map coordinates by two paint routines (0x450C7B,
0x457907); those are deterministic and left alone.
"""

import struct
import sys
from pathlib import Path

FIXTURES = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
sys.path.insert(0, str(FIXTURES))
import patch_exe as P  # noqa: E402

RANDOMIZE = 0x402744                    # System.Randomize: RandSeed := clock
RANDOMIZE_BODY = 0x40274A               # past its prologue: push ebp; mov ebp,esp; add esp,-18h
RANDOMIZE_PROLOGUE = bytes.fromhex("558BEC83C4E8")
RAND_SEED = 0x45E030                    # System.RandSeed
READ_FILE = 0x40498C                    # Windows unit thunk (jmp [IAT])
SEED_CAVE = P.EXTRA_VA + 0x400          # after the autosave cave, inside .patch (0x600)


def seed_from_file(b):
    # Randomize: RandSeed := the number in SEED.TXT beside the exe if it
    # exists, else the clock as before; append "S/C nnnnnnnnnn" to SEED.LOG.
    LINE, N, NAME, BUF, PATH = -0x10, -0x14, -0x18, -0x28, -0x130
    JB, JE, JNE, JA, JMP = 0x72, 0x74, 0x75, 0x77, 0xEB

    def ebp(op, disp, imm=b""):                     # [ebp+disp], disp8 form when it fits
        if -0x80 <= disp < 0x80:
            return op[:-1] + bytes([op[-1] - 0x40]) + struct.pack("<b", disp) + imm
        return P.ebp(op, disp, imm)

    def digit(i):                                   # eax /= 10, LINE[2+i] = remainder
        return b"\x33\xD2\xF7\xF3\x80\xC2\x30" + ebp(b"\x88\x95", LINE + 2 + i)

    def beside(name):                               # PATH = exe dir + name (8.3, 12 chars)
        return [ebp(b"\x8B\xBD", NAME),
                b"\xC7\x07" + name[0:4], b"\xC7\x47\x04" + name[4:8],
                b"\xC7\x47\x08" + name[8:12], b"\xC6\x47\x0C\x00"]

    def create(access, disposition):                # eax = CreateFileA(PATH, access, share read, 0, disp, normal, 0)
        return [b"\x6A\x00\x68\x80\x00\x00\x00\x6A" + bytes([disposition]) + b"\x6A\x00\x6A\x01",
                b"\x68" + struct.pack("<I", access), ebp(b"\x8D\x85", PATH), b"\x50",
                ("call", P.CREATE_FILE)]

    code = P.assemble(SEED_CAVE, [
        b"\x55\x8B\xEC\x81\xEC" + struct.pack("<I", -PATH + 0x10),  # push ebp; mov ebp,esp; sub esp,locals
        b"\x60",                                    # pushad
        b"\x68\x04\x01\x00\x00", ebp(b"\x8D\x85", PATH), b"\x50\x6A\x00",
        ("call", P.GET_MODULE_FILE_NAME),           # GetModuleFileNameA(0, PATH, 260)
        ebp(b"\x8D\xBD", PATH), b"\x03\xF8",        # edi = PATH + length
        ("label", "back"),                          # back up to the last backslash
        b"\x4F", ebp(b"\x8D\x85", PATH), b"\x3B\xF8", ("j", JB, "dir"),
        b"\x80\x3F\x5C", ("j", JNE, "back"),
        ("label", "dir"),
        b"\x47", ebp(b"\x89\xBD", NAME),            # NAME = just past the backslash
        *beside(b"SEED.TXT\0\0\0\0"),
        *create(0x80000000, 3),                     # GENERIC_READ, OPEN_EXISTING
        b"\x83\xF8\xFF", ("jn", JE, "clock"),
        b"\x8B\xD8",                                # ebx = handle
        ebp(b"\xC7\x85", N, b"\0\0\0\0"),
        b"\x6A\x00", ebp(b"\x8D\x85", N), b"\x50\x6A\x10",
        ebp(b"\x8D\x85", BUF), b"\x50\x53",
        ("call", READ_FILE),                        # ReadFile(h, BUF, 16, &N, 0)
        b"\x53", ("call", P.CLOSE_HANDLE),
        b"\x33\xC0", ebp(b"\x8D\xB5", BUF), ebp(b"\x8B\x8D", N),   # eax = 0; esi = BUF; ecx = N
        ("label", "digit"),
        b"\x85\xC9", ("j", JE, "parsed"),
        b"\x0F\xB6\x16\x80\xEA\x30\x80\xFA\x09", ("j", JA, "parsed"),  # edx = [esi] - '0'; > 9: stop
        b"\x6B\xC0\x0A\x03\xC2\x46\x49", ("j", JMP, "digit"),     # eax = eax*10 + edx; esi++; ecx--
        ("label", "parsed"),
        b"\xA3" + struct.pack("<I", RAND_SEED),     # RandSeed = eax
        ebp(b"\xC6\x85", LINE, b"S"),
        ("j", JMP, "log"),
        ("label", "clock"),
        ("call", SEED_CAVE),                        # patched below to call "stub"
        ebp(b"\xC6\x85", LINE, b"C"),
        ("label", "log"),                           # LINE = "S nnnnnnnnnn\r\n"
        ebp(b"\xC6\x85", LINE + 1, b" "),
        ebp(b"\x66\xC7\x85", LINE + 12, b"\r\n"),
        b"\xA1" + struct.pack("<I", RAND_SEED), b"\xBB\x0A\x00\x00\x00",
        *(digit(i) for i in range(9, -1, -1)),
        *beside(b"SEED.LOG\0\0\0\0"),
        *create(0x40000000, 4),                     # GENERIC_WRITE, OPEN_ALWAYS
        b"\x83\xF8\xFF", ("j", JE, "done"),
        b"\x8B\xD8\x6A\x02\x6A\x00\x6A\x00\x53",  # SetFilePointer(h, 0, 0, FILE_END)
        ("call", P.SET_FILE_POINTER),
        b"\x6A\x00", ebp(b"\x8D\x85", N), b"\x50\x6A\x0E",
        ebp(b"\x8D\x85", LINE), b"\x50\x53",        # WriteFile(h, LINE, 14, &N, 0)
        ("call", P.WRITE_FILE),
        b"\x53", ("call", P.CLOSE_HANDLE),
        ("label", "done"),
        b"\x61\x8B\xE5\x5D\xC3",                  # popad; mov esp,ebp; pop ebp; ret
        ("label", "stub"),                          # the original Randomize: prologue, then its body
        RANDOMIZE_PROLOGUE,
        ("jmp", RANDOMIZE_BODY),
    ])
    # point the "clock" call at the stub (assemble() has no call-to-label form)
    stub = SEED_CAVE + len(code) - len(RANDOMIZE_PROLOGUE) - 5
    code = bytearray(code)
    call_at = _find_self_call(code)
    code[call_at + 1:call_at + 5] = P.rel32(SEED_CAVE + call_at, stub)
    end = SEED_CAVE + len(code)
    if end > P.EXTRA_VA + P.PATCH_SIZE:
        raise SystemExit("seed cave overflows .patch by %d bytes" % (end - P.EXTRA_VA - P.PATCH_SIZE))
    raw = SEED_CAVE - P.EXTRA_VA + P.EXTRA_RAW
    if len(b) != P.EXTRA_RAW + P.PATCH_SIZE or any(x != 0xCC for x in b[raw:raw + len(code)]):
        raise SystemExit("seed_from_file must follow autosave (free .patch space expected at 0x%x)" % SEED_CAVE)
    b[raw:raw + len(code)] = code
    P.patch(b, RANDOMIZE, RANDOMIZE_PROLOGUE, b"\xE9" + P.rel32(RANDOMIZE, SEED_CAVE) + b"\x90")


def _find_self_call(code):
    # the one "call SEED_CAVE" placeholder: E8 with rel32 pointing back at offset 0
    for i in range(len(code) - 5):
        if code[i] == 0xE8 and struct.unpack_from("<i", code, i + 1)[0] == -(i + 5):
            return i
    raise SystemExit("placeholder call not found")


if __name__ == "__main__":
    import os
    os.chdir(FIXTURES)
    P.build("Imperial Conquest 2 fast rollingsave seed.exe",
            P.async_sound, P.no_delay, P.autosave, seed_from_file)
