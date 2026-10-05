"""The exchange hook of the battle lab (battles plan B11, task docs/tasks/battles-b11-hook.md). Observation only: it never changes what the game does.

`battle_lab.py [seed] --hook` calls `apply(b)` after the lab caves are in `b` (the exe, a bytearray). What `apply` does:

  1. checks every `Random` call site of the battle module (12) and of TBattleOver (2) is `E8 rel32` -> Random (0x40284C), and that a scan of the
     whole CODE section for any reference to Random (E8/E9 rel32, FF 15/FF 25, an absolute dword) finds, inside the battle module and TBattleOver,
     exactly that list: it raises HookBuildError otherwise (nothing is patched);
  2. re-points each of those calls to one cave (`RANDOM_CAVE`) which appends a record before the real call, calls the real `Random` with the caller's
     registers untouched, and completes the record (result, RandSeed after) when it returns;
  3. (also) takes a boundary record just before each of the two instructions that reseed RandSeed (RESEED), and puts a marker (a record with EAX/EDX/ECX) at the entry of the shot (0x43910C), melee pass (0x4393EC) and Rout (0x438FB0) routines: their first
     7/7/5 bytes are moved into a cave and re-executed there; and a boundary record at the two writes that clear the battle flag 0x4A0B7C
     (0x437B8C the Surrender handler, 0x45C21F the TPremierForm clean-up) and one where the lab seed cave writes RandSeed at battle start;
  4. grows the `.patch` section (virtual size) with a zero-filled control block and a buffer of BUF_RECORDS records (never wraps: when full, the
     overflow flag is set and nothing more is written).

Every cave preserves all registers, EFLAGS and ESP the way the call or entry it replaces would leave them (tests/test_battle_hook_caves.py runs them
under an x86 emulator against a direct call). The record layout is `state/hook_log.py`'s (12 little-endian dwords, 48 bytes).
All addresses are [R-code] (the research report 2026-10-04-decompiled-tactical-battle-rules.md) and checked against the game by
runs/experiments/battles/b11_addresses.py.
"""
import struct

BASE = 0x400000
CODE_VA, CODE_RAW, CODE_SIZE = 0x401000, 0x400, 0x5B3D4
RANDOM = 0x40284C
RAND_SEED = 0x45E030
COUNTER_HR, SIDE, FLAG = 0x4A0B7A, 0x4A0B78, 0x4A0B7C           # half-round counter (u16), side to move (u16), battle flag (u8)
BATTLE_MODULE = (0x436FB4, 0x43ADAC)       # TBattleMap.StartBattle .. the last `ret` of the module's last function (0x43ADAB; disassembled)
BATTLEOVER_MODULE = (0x458BC8, 0x45958B)   # unit BattleOverUnit: first code byte after its published-method names .. last `ret` before the next data (disassembled)
BATTLE_SITES = (0x43801A, 0x43812F, 0x43820D, 0x438FFB, 0x439006, 0x439188, 0x439191, 0x439557, 0x43955F, 0x4395CE, 0x4395D8, 0x43AA88)
POST_SITES = (0x4592BD, 0x45951C)
SITES = BATTLE_SITES + POST_SITES

# routine entries: (name, va, bytes that the build expects there and moves into the marker cave)
MARKERS = (("shot", 0x43910C, bytes.fromhex("53565755" "83C4EC")),
           ("melee", 0x4393EC, bytes.fromhex("53565755" "83C4D0")),
           ("rout", 0x438FB0, bytes.fromhex("5356575551")))
# the two writes `mov byte [0x4A0B7C], 0`
FLAG_CLEAR = (("battle_over_clear", 0x437B8C), ("after_battle_clear", 0x45C21F))
FLAG_CLEAR_BYTES = bytes.fromhex("C6057C0B4A0000")
# the two instructions that write RandSeed from outside the RTL (a reseed): a boundary record is taken just BEFORE each writes, which pins "nothing was
# drawn between the last post-battle Random site and the reseed" (0x457907 is in the TBattlePols unit, whose name strings are at 0x457BA8)
RESEED = (("reseed_battlepols", 0x457907, bytes.fromhex("A330E04500")),
          ("reseed_450c7b", 0x450C7B, bytes.fromhex("891530E04500")))

# --- memory plan (VA). The lab's caves live at 0x564400-0x5645F0 inside the first 0x600 bytes of .patch. -----------------------------------------------
PATCH_VA, PATCH_RAW_START = 0x564000, 0x11CC00
LAB_PATCH_SIZE = 0x600                      # patch_exe.PATCH_SIZE: raw/virtual size the lab leaves
HOOK_CODE = 0x564600                        # first byte of the hook's caves
RAW_SIZE = 0x1200                           # raw size of .patch after the hook: the caves, then the control block + private stack (0x565000-0x565100) in the file
CTL = 0x565000                              # control block: +0 index (next free record), +4 overflow flag, +8 pending record, +12 capacity, +16 magic,
SV, TAGV = CTL + 20, CTL + 24               #   +20 the program's ESP while a cave works, +24 the tag of the record being written;
BUSY, REENT = CTL + 32, CTL + 36            #   +32 busy (a cave is working), +36 REENTERED (a cave was entered while busy: it logged nothing, ran the original code);
S_EAX, S_FL = CTL + 40, CTL + 44            #   +40/+44 EAX and EFLAGS (AH = SF ZF AF PF CF, AL = OF) parked while the busy test runs;
PRIV_TOP = CTL + 0x100                      #   0x565040-0x565100: the cave's private stack (grows down from 0x565100)
BUF = 0x565100
BUF_RECORDS = 65536
REC = 48
MAGIC = 0x48434231                          # 'HCB1' at CTL+16 (so a reader can tell a hooked process)
NAMES = {}                                  # filled by build(): cave name -> VA (written to the data folder by the build script)


class HookBuildError(RuntimeError):
    """The build refuses: a site is not `E8 rel32 -> Random`, the scan list differs from the hooked list, or the bytes at an entry are not the expected ones."""


def off(va):
    return va - CODE_VA + CODE_RAW


def rel32(src, target):
    return struct.pack("<i", target - (src + 5))


def u32(v):
    return struct.pack("<I", v & 0xFFFFFFFF)


# ---------------------------------------------------------------------------------------------------------------------------------------------
# checks on the exe bytes
# ---------------------------------------------------------------------------------------------------------------------------------------------
def sections(b):
    """The PE section table of the image: [(name, va, vsize, raw_ptr, raw_size, flags)] (VA = image base + RVA)."""
    n = struct.unpack_from("<H", b, 0x106)[0]
    out = []
    for i in range(n):
        o = 0x1F8 + 40 * i
        name = bytes(b[o:o + 8]).rstrip(b"\0").decode("latin1")
        vsize, rva, rsize, rptr = struct.unpack_from("<IIII", b, o + 8)
        out.append((name, BASE + rva, vsize, rptr, rsize, struct.unpack_from("<I", b, o + 36)[0]))
    return out


def iat_slots(b):
    """The VAs of every import address table slot, from the PE import directory (data directory 1; the PE header is at 0x100, as `sections` assumes): for each
    import descriptor (20 bytes, until an all-zero one) its FirstThunk array, one dword per imported function, until a zero dword. Only these slots are filled by
    the loader with DLL addresses; any other dword of .idata (descriptors, name tables, hint/name entries) is ordinary data (PR #42 round 3)."""
    secs = sections(b)

    def foff(rva):
        for _, va, vsize, rptr, rsize, _f in secs:
            if va <= BASE + rva < va + min(vsize, rsize) and rptr:
                return rptr + (BASE + rva - va)
        return None
    imp_rva = struct.unpack_from("<I", b, 0x118 + 96 + 8)[0]
    slots, d = set(), foff(imp_rva) if imp_rva else None
    while d is not None and d + 20 <= len(b):
        oft, _ts, _fc, name, ft = struct.unpack_from("<IIIII", b, d)
        if not (oft or name or ft):
            break
        t = foff(ft) if ft else None
        k = 0
        while t is not None and t + 4 * k + 4 <= len(b) and struct.unpack_from("<I", b, t + 4 * k)[0] and k < 4096:
            slots.add(BASE + ft + 4 * k)
            k += 1
        d += 20
    return slots


def resolve_pointer(b, p):
    """What a `call [p]` / `jmp [p]` reaches, as far as the image says: ("value", v) p is in a
    READ-ONLY section with file data: v is the dword stored there; ("import", None) p is exactly an import address table slot (`iat_slots`, from the import
    directory), which the loader fills with a DLL address (never the address of code in this image); any other dword of .idata is unresolved; ("unresolved", None) p is in other writable memory, in a section without file data, outside every section,
    or its four bytes cross the end of the mapped and file-backed part of its section: its value at run time cannot be established statically (PR #42 round 2)."""
    for name, va, vsize, rptr, rsize, flags in sections(b):
        if va <= p < va + max(vsize, rsize):
            # all four bytes must lie in this one section, in the part that is both mapped (vsize) and backed by file data (rsize): a pointer that
            # crosses the section's end may take its remaining bytes from another section or from zero fill, so its value is not established
            if p + 4 > va + min(vsize, rsize) or rptr == 0:
                return "unresolved", None
            if name == ".idata":
                # an import only if p is exactly one of the IAT slots; any other dword of .idata could hold anything, including Random's address
                return ("import", None) if p in iat_slots(b) else ("unresolved", None)
            if flags & 0x80000000:
                return "unresolved", None
            return "value", struct.unpack_from("<I", b, rptr + (p - va))[0]
    # outside every section of the image: memory allocated at run time (or a false hit of the byte-wise scan); its value is not established either
    return "unresolved", None


def scan_random_refs(b):
    """Every reference to Random in the CODE section: [(va, kind)], kind in E8 / E9 (rel32 to it), FF15 / FF25 (`call [p]` / `jmp [p]` whose pointer p holds it: the
    operand is the ADDRESS OF A POINTER, so the dword at p is read from the image and compared), FF15? / FF25? (the pointer is in writable memory other than the IAT, so the
    target cannot be established statically: an unresolved reference, which `check_scan` treats as a failure inside the two modules), abs (an absolute dword equal to it)."""
    code = bytes(b[CODE_RAW:CODE_RAW + CODE_SIZE])
    t, hits = RANDOM, []
    for i in range(len(code) - 4):
        va = CODE_VA + i
        op = code[i]
        if op in (0xE8, 0xE9) and va + 5 + struct.unpack_from("<i", code, i + 1)[0] == t:
            hits.append((va, "E8" if op == 0xE8 else "E9"))
        if op == 0xFF and i + 6 <= len(code) and code[i + 1] in (0x15, 0x25):
            kind = "FF15" if code[i + 1] == 0x15 else "FF25"
            how, v = resolve_pointer(b, struct.unpack_from("<I", code, i + 2)[0])
            if how == "value" and v == t:
                hits.append((va, kind))
            elif how == "unresolved":
                hits.append((va, kind + "?"))
        if struct.unpack_from("<I", code, i)[0] == t:
            hits.append((va, "abs"))
    return hits


def in_ranges(va, ranges):
    return any(lo <= va < hi for lo, hi in ranges)


def check_sites(b, sites=SITES):
    """Refuse unless every site is `E8 rel32` to Random."""
    for va in sites:
        o = off(va)
        if b[o] != 0xE8 or va + 5 + struct.unpack_from("<i", b, o + 1)[0] != RANDOM:
            raise HookBuildError("site 0x%X is not `E8 rel32` -> Random (0x%X): bytes %s" % (va, RANDOM, bytes(b[o:o + 5]).hex()))


def check_scan(b, sites=SITES):
    """Refuse unless the scan's list of references inside the battle module and TBattleOver equals the hooked list. Returns (inside, outside)."""
    refs = scan_random_refs(b)
    inside = sorted(va for va, _ in refs if in_ranges(va, (BATTLE_MODULE, BATTLEOVER_MODULE)))
    unresolved = [(hex(va), k) for va, k in refs if k.endswith("?") and in_ranges(va, (BATTLE_MODULE, BATTLEOVER_MODULE))]
    if unresolved:
        raise HookBuildError("indirect call/jump inside the battle module or TBattleOver whose pointer cannot be established statically (it may reach Random): %s" % unresolved)
    if inside != sorted(sites) or any(k != "E8" for va, k in refs if va in sites):
        raise HookBuildError("scan of CODE finds %s inside the battle module and TBattleOver, the hooked list is %s"
                             % ([hex(v) for v in inside], [hex(v) for v in sorted(sites)]))
    return inside, sorted(va for va, k in refs if va not in inside and not k.endswith("?"))


def check_entries(b):
    """The bytes at every marker entry, flag-clear and reseed site are the recorded ones, and no rel32 branch (E8, E9, 0F 8x) of the CODE section lands
    strictly inside a displaced range. (Short rel8 branches are not scanned here: a byte-wise scan of CODE finds false ones inside longer instructions;
    runs/experiments/battles/b11_addresses.py checks them on a disassembly of each function and writes the result.)"""
    for name, va, exp in MARKERS:
        if bytes(b[off(va):off(va) + len(exp)]) != exp:
            raise HookBuildError("entry %s 0x%X: bytes %s, expected %s" % (name, va, bytes(b[off(va):off(va) + len(exp)]).hex(), exp.hex()))
    for name, va in FLAG_CLEAR:
        if bytes(b[off(va):off(va) + 7]) != FLAG_CLEAR_BYTES:
            raise HookBuildError("flag-clear site %s 0x%X: bytes %s" % (name, va, bytes(b[off(va):off(va) + 7]).hex()))
    for name, va, exp in RESEED:
        if bytes(b[off(va):off(va) + len(exp)]) != exp:
            raise HookBuildError("reseed site %s 0x%X: bytes %s, expected %s" % (name, va, bytes(b[off(va):off(va) + len(exp)]).hex(), exp.hex()))
    spans = [(va, va + len(exp)) for _, va, exp in MARKERS] + [(va, va + 7) for _, va in FLAG_CLEAR] + [(va, va + len(exp)) for _, va, exp in RESEED]
    code = bytes(b[CODE_RAW:CODE_RAW + CODE_SIZE])
    for i in range(len(code) - 6):
        op, va, tgt = code[i], CODE_VA + i, None
        if op in (0xE8, 0xE9):
            tgt = va + 5 + struct.unpack_from("<i", code, i + 1)[0]
        elif op == 0x0F and 0x80 <= code[i + 1] <= 0x8F:
            tgt = va + 6 + struct.unpack_from("<i", code, i + 2)[0]
        for lo, hi in spans:
            if tgt is not None and lo < tgt < hi:
                raise HookBuildError("a branch at 0x%X lands inside the displaced bytes 0x%X-0x%X" % (va, lo, hi))


# ---------------------------------------------------------------------------------------------------------------------------------------------
# caves (all preserve every register, EFLAGS and ESP)
# ---------------------------------------------------------------------------------------------------------------------------------------------
class Asm:
    """bytes + labels + rel32 call/jmp to absolute VAs + short jumps to labels."""

    def __init__(self, origin):
        self.origin, self.out, self.labels, self.fix, self.fix32 = origin, bytearray(), {}, [], []

    def b(self, *chunks):
        for c in chunks:
            self.out += c if isinstance(c, (bytes, bytearray)) else bytes(c)
        return self

    def label(self, name):
        self.labels[name] = len(self.out)
        return self

    def call(self, va):
        self.out += b"\xE8" + rel32(self.origin + len(self.out), va)
        return self

    def jmp(self, va):
        self.out += b"\xE9" + rel32(self.origin + len(self.out), va)
        return self

    def j8(self, op, name):
        self.fix.append((len(self.out) + 1, name))
        self.out += bytes([op, 0])
        return self

    def j32(self, op2, name):
        """0F <op2> rel32 (a near conditional jump to a label)."""
        self.fix32.append((len(self.out) + 2, name))
        self.out += bytes([0x0F, op2]) + bytes(4)
        return self

    def done(self):
        for pos, name in self.fix:
            rel = self.labels[name] - (pos + 1)
            assert -128 <= rel <= 127
            self.out[pos] = rel & 0xFF
        for pos, name in self.fix32:
            self.out[pos:pos + 4] = struct.pack("<i", self.labels[name] - (pos + 4))
        return bytes(self.out)


def _rec_body(a):
    """rec_body: appends a record {tag, seq, eax, edx, ecx, seed, seed, 0, counter|side<<16, flag, 0, ebp} for the state the caller saved on the PRIVATE
    stack (`pushfd; pushad` then `call rec_body`), tag from TAGV; sets CUR to it. At capacity: the overflow flag, CUR = 0, nothing written.
    Frame at entry: [esp] ret, +4 edi, +8 esi, +12 ebp, +16 esp, +20 ebx, +24 edx, +28 ecx, +32 eax, +36 eflags. Free to clobber registers (they are saved)."""
    a.b(b"\x8B\x15" + u32(CTL))                                        # mov edx,[IDX]
    a.b(b"\x81\xFA" + u32(BUF_RECORDS))                                # cmp edx,CAP
    a.j8(0x73, "ovf")                                                  # jae ovf
    a.b(b"\x89\xD6", b"\x6B\xF6" + bytes([REC]), b"\x81\xC6" + u32(BUF))   # mov esi,edx; imul esi,esi,48; add esi,BUF
    a.b(b"\xA1" + u32(TAGV), b"\x89\x06")                              # tag
    a.b(b"\x89\x56\x04")                                               # seq = edx
    a.b(b"\x8B\x44\x24\x20", b"\x89\x46\x08")                          # eax_in = [esp+32]
    a.b(b"\x8B\x44\x24\x18", b"\x89\x46\x0C")                          # edx_in = [esp+24]
    a.b(b"\x8B\x44\x24\x1C", b"\x89\x46\x10")                          # ecx_in = [esp+28]
    a.b(b"\xA1" + u32(RAND_SEED), b"\x89\x46\x14", b"\x89\x46\x18")    # seed before; seed after (default: same)
    a.b(b"\x31\xC0", b"\x89\x46\x1C")                                  # result = 0
    a.b(b"\x0F\xB7\x05" + u32(COUNTER_HR), b"\x0F\xB7\x0D" + u32(SIDE), b"\xC1\xE1\x10", b"\x09\xC8", b"\x89\x46\x20")   # counter | side << 16
    a.b(b"\x0F\xB6\x05" + u32(FLAG), b"\x89\x46\x24")                  # battle flag
    a.b(b"\x31\xC0", b"\x89\x46\x28")                                  # reserved = 0
    a.b(b"\x8B\x44\x24\x0C", b"\x89\x46\x2C")                          # ebp_in = [esp+12]
    a.b(b"\x42", b"\x89\x15" + u32(CTL))                               # inc edx; IDX = edx
    a.b(b"\x89\x35" + u32(CTL + 8))                                    # CUR = esi
    a.j8(0xEB, "done")                                                 # jmp done
    a.label("ovf")
    a.b(b"\xC7\x05" + u32(CTL + 4) + u32(1))                           # OVF = 1
    a.b(b"\xC7\x05" + u32(CTL + 8) + u32(0))                           # CUR = 0
    a.label("done")
    a.b(b"\xC3")
    return a


def _rec_end_body(a):
    """rec_end_body: right after the real Random (same private-stack frame, EAX = the result at +32): completes CUR with the result and RandSeed."""
    a.b(b"\x8B\x35" + u32(CTL + 8))                                    # esi = CUR
    a.b(b"\x85\xF6")                                                   # test esi,esi
    a.j8(0x74, "skip")                                                 # jz skip
    a.b(b"\x8B\x44\x24\x20", b"\x89\x46\x1C")                          # result = [esp+32]
    a.b(b"\xA1" + u32(RAND_SEED), b"\x89\x46\x18")                     # seed_after
    a.b(b"\xC7\x05" + u32(CTL + 8) + u32(0))                           # CUR = 0
    a.label("skip")
    a.b(b"\xC3")
    return a


# Prologue/epilogue of a cave's own work. It runs on a PRIVATE stack inside the control page, so the program's stack below ESP is never written.
# A cave first tests the BUSY flag WITHOUT disturbing a register or a flag (EAX and the flags are parked in memory with LAHF/SETO, restored with ADD AL,7Fh/SAHF):
# if a cave is already working (re-entry), it sets REENTERED, logs nothing, does not touch SV or the private stack, restores EAX and the flags and runs the original
# instruction(s) / the real Random. Otherwise it sets BUSY and goes on; SWITCH_OUT clears BUSY.
PARK = (b"\xA3" + u32(S_EAX) + b"\x9F\x0F\x90\xC0" + b"\xA3" + u32(S_FL))             # mov [S_EAX],eax; lahf; seto al; mov [S_FL],eax
UNPARK = (b"\xA1" + u32(S_FL) + b"\x04\x7F\x9E" + b"\xA1" + u32(S_EAX))                # mov eax,[S_FL]; add al,7Fh (OF = AL); sahf; mov eax,[S_EAX]
SWITCH_IN = b"\x89\x25" + u32(SV) + b"\xBC" + u32(PRIV_TOP) + b"\x9C\x60"      # mov [SV],esp; mov esp,PRIV_TOP; pushfd; pushad
SWITCH_OUT = b"\x61\x9D\x8B\x25" + u32(SV) + b"\xC7\x05" + u32(BUSY) + u32(0)  # popad; popfd; mov esp,[SV]; BUSY = 0   (movs leave EFLAGS alone)


def enter(a, reent):
    """Busy test + SWITCH_IN. Jumps to label `reent` (with EAX and flags still parked) when busy; otherwise falls through with the caller's state restored, BUSY = 1,
    on the private stack with flags and registers pushed."""
    a.b(PARK)
    a.b(b"\xA1" + u32(BUSY), b"\x85\xC0")                                      # mov eax,[BUSY]; test eax,eax
    a.j32(0x85, reent)                                                            # jnz reent
    a.b(b"\xC7\x05" + u32(BUSY) + u32(1))                                        # BUSY = 1
    a.b(UNPARK)
    a.b(SWITCH_IN)


def reentered(a):
    """The re-entry path: REENTERED = 1, then the caller's EAX and flags back."""
    a.b(b"\xC7\x05" + u32(REENT) + u32(1))
    a.b(UNPARK)


def build_caves(code_va=HOOK_CODE):
    """The hook's caves as {name: (va, bytes)}, laid out from `code_va`. Pure: no exe needed."""
    caves, cur = {}, [code_va]

    def put(name, build):
        va = cur[0]
        a = Asm(va)
        data = build(a, va)
        caves[name] = (va, data)
        cur[0] = (va + len(data) + 3) & ~3

    put("rec_body", build=lambda a, va: _rec_body(a).done())
    put("rec_end_body", build=lambda a, va: _rec_end_body(a).done())
    RB, RE = caves["rec_body"][0], caves["rec_end_body"][0]

    def random_cave(a, va):
        enter(a, "reent1")
        a.b(b"\xA1" + u32(SV), b"\x8B\x00", b"\xA3" + u32(TAGV))       # eax = [SV]; eax = [eax] (the site's return address); TAGV = eax
        a.call(RB)
        a.b(SWITCH_OUT)
        a.call(RANDOM)                                                 # the caller's EAX and stack, exactly as a direct call
        enter(a, "reent2")
        a.call(RE)
        a.b(SWITCH_OUT)
        a.b(b"\xC3")
        a.label("reent1")                                              # re-entered before the draw: no record, the real Random, back
        reentered(a)
        a.call(RANDOM)
        a.b(b"\xC3")
        a.label("reent2")                                              # re-entered after the draw: the result is in EAX and the flags are Random's: keep them
        reentered(a)
        a.b(b"\xC3")
        return a.done()
    put("random", build=random_cave)

    def tagged(a, tag, reent):
        enter(a, reent)
        a.b(b"\xC7\x05" + u32(TAGV) + u32(tag))
        a.call(RB)
        a.b(SWITCH_OUT)

    def marker(name, entry, displaced):
        def f(a, va):
            tagged(a, 0x01000000 | entry, "reent")
            a.b(displaced)
            a.jmp(entry + len(displaced))
            a.label("reent")
            reentered(a)
            a.b(displaced)
            a.jmp(entry + len(displaced))
            return a.done()
        put("marker_" + name, build=f)

    for name, entry, displaced in MARKERS:
        marker(name, entry, displaced)

    def flagcave(name, site):
        def f(a, va):
            a.b(FLAG_CLEAR_BYTES)                                      # the displaced `mov byte [FLAG],0`
            tagged(a, 0x02000000 | site, "reent")
            a.jmp(site + 7)
            a.label("reent")
            reentered(a)
            a.jmp(site + 7)
            return a.done()
        put(name, build=f)

    for name, site in FLAG_CLEAR:
        flagcave(name, site)

    def reseedcave(name, site, displaced):
        def f(a, va):
            tagged(a, 0x04000000 | site, "reent")                      # the record first (the seed that is about to be overwritten) ...
            a.b(displaced)                                             # ... then the displaced `mov [RandSeed], reg`
            a.jmp(site + len(displaced))
            a.label("reent")
            reentered(a)
            a.b(displaced)
            a.jmp(site + len(displaced))
            return a.done()
        put(name, build=f)

    for name, site, displaced in RESEED:
        reseedcave(name, site, displaced)
    return caves


def seed_cave(origin, seed, tbattle_start):
    """The hooked replacement of the lab's seed cave: RandSeed := seed, a boundary record (tag 0x03000000), then the battle start."""
    a = Asm(origin)
    a.b(b"\xC7\x05" + u32(RAND_SEED) + u32(seed))
    enter(a, "reent")
    a.b(b"\xC7\x05" + u32(TAGV) + u32(0x03000000))
    a.call(build_caves()["rec_body"][0])
    a.b(SWITCH_OUT)
    a.jmp(tbattle_start)
    a.label("reent")
    reentered(a)
    a.jmp(tbattle_start)
    return a.done()


def apply(b, seed, lab):
    """Patch the lab exe `b` (bytearray) in place into the hooked exe. `lab` is the battle_lab module's constants (BATTLE_START_CALL, SEED_CAVE,
    TBATTLE_START). Returns {cave name: va} plus the lists, for the build record."""
    if len(b) != PATCH_RAW_START + LAB_PATCH_SIZE:
        raise HookBuildError("the lab exe has %d bytes, expected %d (build the lab first)" % (len(b), PATCH_RAW_START + LAB_PATCH_SIZE))
    check_sites(b)
    inside, outside = check_scan(b)
    check_entries(b)
    caves = build_caves()
    last = max(va + len(d) for va, d in caves.values())
    seed_va = (last + 3) & ~3
    seed_bytes = seed_cave(seed_va, seed, lab.TBATTLE_START)
    if seed_va + len(seed_bytes) > CTL:
        raise HookBuildError("hook caves overflow into the control block")
    # section header: virtual size and raw size, SizeOfImage
    vsize = BUF + BUF_RECORDS * REC - PATCH_VA
    hdr = 0x1F8 + 8 * 40
    struct.pack_into("<I", b, hdr + 8, vsize)                          # VirtualSize
    struct.pack_into("<I", b, hdr + 16, RAW_SIZE)                      # SizeOfRawData
    struct.pack_into("<I", b, 0x118 + 56, (PATCH_VA - BASE + vsize + 0xFFF) & ~0xFFF)   # SizeOfImage
    b += b"\xCC" * (CTL - PATCH_VA - LAB_PATCH_SIZE) + bytes(RAW_SIZE - (CTL - PATCH_VA))   # filler up to the control block, then zeros (the block starts clean)
    raw = lambda va: PATCH_RAW_START + (va - PATCH_VA)
    for va, data in list(caves.values()) + [(seed_va, seed_bytes)]:
        b[raw(va):raw(va) + len(data)] = data
    b[raw(CTL + 16):raw(CTL + 16) + 4] = u32(MAGIC)
    b[raw(CTL + 12):raw(CTL + 12) + 4] = u32(BUF_RECORDS)
    # re-point: the Random calls, the marker entries, the flag-clear sites, the battle start
    rnd = caves["random"][0]
    for site in SITES:
        b[off(site):off(site) + 5] = b"\xE8" + rel32(site, rnd)
    for name, entry, exp in MARKERS:
        va = caves["marker_" + name][0]
        b[off(entry):off(entry) + len(exp)] = b"\xE9" + rel32(entry, va) + b"\x90" * (len(exp) - 5)
    for name, site in FLAG_CLEAR:
        b[off(site):off(site) + 7] = b"\xE9" + rel32(site, caves[name][0]) + b"\x90\x90"
    for name, site, exp in RESEED:
        b[off(site):off(site) + len(exp)] = b"\xE9" + rel32(site, caves[name][0]) + b"\x90" * (len(exp) - 5)
    start = lab.BATTLE_START_CALL
    exp = b"\xE8" + rel32(start, lab.SEED_CAVE)
    if bytes(b[off(start):off(start) + 5]) != exp:
        raise HookBuildError("battle start call is not the lab's")
    b[off(start):off(start) + 5] = b"\xE8" + rel32(start, seed_va)
    names = {k: v[0] for k, v in caves.items()}
    names["seed"] = seed_va
    NAMES.clear()
    NAMES.update(names)
    return {"caves": names, "hooked_sites": list(SITES), "scan_inside": inside, "scan_outside_count": len(outside)}
