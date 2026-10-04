"""Reader of the exchange hook's in-memory log (`patches/battle_hook.py`, battles plan B11).

The hooked lab exe keeps, in its `.patch` section, a control block and a buffer of fixed 48-byte records. The harness reads both through
`/proc/<pid>/mem` after the battle. This module only parses; it never writes game memory.

Control block at CTL (0x565000): +0 u32 index (the next free record = the number written), +4 u32 overflow flag, +8 u32 pending record pointer,
+12 u32 capacity, +16 u32 magic 'HCB1'. Records at BUF (0x565100), 12 little-endian u32 each:
  0 tag      for a Random call, the call site's RETURN address (site + 5); 0x01000000|entry for a marker at a routine entry; 0x02000000|site for a
             flag-clear boundary; 0x03000000 for the battle-start boundary (the lab seed cave); 0x04000000|site for the
             boundary taken just before an instruction that reseeds RandSeed (0x457907 TBattlePols, 0x450C7B)
  1 seq      the record's index (a check against drops)
  2 eax  3 edx  4 ecx   registers at the record (for Random: EAX = the range; for a marker: the routine's arguments)
  5 seed_before   RandSeed (0x45E030) just before the call      6 seed_after   RandSeed just after (equal to seed_before for a non-Random record)
  7 result   Random's return value (0 for a non-Random record)
  8 counter | side << 16   half-round counter (0x4A0B7A) and side to move (0x4A0B78)
  9 flag     battle flag (0x4A0B7C)      10 reserved (0)      11 ebp
"""
import struct

CTL, BUF, REC = 0x565000, 0x565100, 48
MAGIC = 0x48434231
LCG_MUL = 0x08088405

KIND_RANDOM, KIND_MARKER, KIND_FLAG_CLEAR, KIND_START, KIND_RESEED = "random", "marker", "flag_clear", "start", "reseed"
FIELDS = ("tag", "seq", "eax", "edx", "ecx", "seed_before", "seed_after", "result", "cs", "flag", "reserved", "ebp")


def lcg(seed):
    """One step of Delphi's RandSeed: seed * 0x08088405 + 1 (mod 2^32)."""
    return (seed * LCG_MUL + 1) & 0xFFFFFFFF


def parse_ctl(ctl):
    idx, ovf, cur, cap, magic = struct.unpack_from("<5I", ctl, 0)
    return {"index": idx, "overflow": ovf, "pending": cur, "capacity": cap, "magic_ok": magic == MAGIC}


def decode(raw, seq_expected):
    f = dict(zip(FIELDS, struct.unpack("<12I", raw)))
    top = f["tag"] >> 24
    if top == 0:
        f["kind"], f["site"] = KIND_RANDOM, f["tag"] - 5
    elif top == 1:
        f["kind"], f["site"] = KIND_MARKER, f["tag"] & 0xFFFFFF
    elif top == 2:
        f["kind"], f["site"] = KIND_FLAG_CLEAR, f["tag"] & 0xFFFFFF
    elif top == 3:
        f["kind"], f["site"] = KIND_START, 0
    elif top == 4:
        f["kind"], f["site"] = KIND_RESEED, f["tag"] & 0xFFFFFF
    else:
        f["kind"], f["site"] = "unknown", f["tag"]
    f["counter"], f["side"] = f["cs"] & 0xFFFF, f["cs"] >> 16
    f["seq_ok"] = f["seq"] == seq_expected
    return f


def parse(ctl, buf):
    """(control dict, records). Reads exactly `index` records (never past the write index, never more than the capacity or than `buf` holds);
    the overflow flag is reported in the control dict, never hidden. `ctl`: the first 20+ bytes of the control block; `buf`: the buffer bytes."""
    c = parse_ctl(ctl)
    n = min(c["index"], c["capacity"], len(buf) // REC)
    recs = [decode(buf[i * REC:(i + 1) * REC], i) for i in range(n)]
    c["records"] = n
    c["truncated_reader"] = n < c["index"]
    return c, recs


def read_process(mem):
    """Read the log of a running hooked game: `mem(addr, n)` is `Game.mem`. Returns (control, records)."""
    ctl = mem(CTL, 32)
    c = parse_ctl(ctl)
    n = min(c["index"], c["capacity"]) if c["magic_ok"] else 0
    buf = mem(BUF, n * REC) if n else b""
    return parse(ctl, buf)


def to_rows(recs):
    return [{k: r[k] for k in ("seq", "kind", "site", "eax", "edx", "ecx", "seed_before", "seed_after", "result", "counter", "side", "flag", "ebp")}
            for r in recs]


def chain_check(recs, start_seed=None, sites=None):
    """The seed chain: each Random record's seed_after = lcg(seed_before); each record's seed_before equals the previous record's seed_after (every
    kind of record carries the seed; markers and boundaries carry it in both fields); the first record's seed_before equals `start_seed` when given;
    every Random record's site is in `sites` when given. A reseed record is itself checked (its seed_before continues the chain) and ends the chain: the
    record after it is not compared. Returns a list of breaks (empty = unbroken): dicts {seq, why, ...}."""
    breaks, prev = [], start_seed
    for r in recs:
        if not r["seq_ok"]:
            breaks.append({"seq": r["seq"], "why": "sequence number out of order"})
        if prev is not None and r["seed_before"] != prev:
            breaks.append({"seq": r["seq"], "why": "seed_before != previous seed_after", "expected": prev, "got": r["seed_before"], "site": r["site"], "kind": r["kind"]})
        if r["kind"] == KIND_RANDOM:
            if r["seed_after"] != lcg(r["seed_before"]):
                breaks.append({"seq": r["seq"], "why": "seed_after is not one LCG step from seed_before", "site": r["site"]})
            if sites is not None and r["site"] not in sites:
                breaks.append({"seq": r["seq"], "why": "site is not a module call site", "site": r["site"]})
        elif r["seed_after"] != r["seed_before"]:
            breaks.append({"seq": r["seq"], "why": "a non-Random record with seed_after != seed_before", "kind": r["kind"]})
        prev = None if r["kind"] == KIND_RESEED else r["seed_after"]        # the instruction after a reseed record rewrites RandSeed: a new chain starts
    return breaks


def result_check(recs):
    """Delphi's Random(range) = (range * RandSeed_after) >> 32 (unsigned `mul`): the range is EAX at the call, the result EAX at the return.
    Returns the Random records whose result differs (empty = the calling convention and the formula hold on every record)."""
    return [{"seq": r["seq"], "site": r["site"], "range": r["eax"], "result": r["result"], "expected": (r["eax"] * r["seed_after"]) >> 32}
            for r in recs if r["kind"] == KIND_RANDOM and r["result"] != (r["eax"] * r["seed_after"]) >> 32]
