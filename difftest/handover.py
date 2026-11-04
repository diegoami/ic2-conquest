"""Hand the human seat to another nation (owner 2026-11-04: the rule bot gets conquered, so the long games "hand over the
human seat" to keep the world going to the later years).

    python3 -m difftest.handover SRC.SAV DST.SAV [--to NATION]      # default heir: the living nation with the most cities

Only the per-nation human flag changes (nation record +0x490, u8: 1 human, 0 computer; docs/sav-layout-notes.md §5).
Everything else is the original's own state. The current seat is left as it is. If it is the old human nation, that nation
is now computer-controlled, and the human End turn that follows passes its seat without orders; the AI seats then play,
and the original stops at the heir's turn.
"""
import argparse
import shutil
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from state.sav import ARMY_LEN, ARMY_OFF, FLEET_LEN, NATION_LEN, NATIONS, load  # noqa: E402

HUMAN = 0x490


def nation_table(b):
    na = struct.unpack_from("<h", b, ARMY_OFF)[0]
    o = ARMY_OFF + 2 + na * ARMY_LEN
    nf = struct.unpack_from("<h", b, o)[0]
    return o + 2 + nf * FLEET_LEN


def heir(s, exclude=()):
    alive = [(n["cities_count"], -i, i) for i, n in enumerate(s["nations"])
             if n["unity"] > 0 and n["capital"] >= 0 and NATIONS[i] not in exclude]
    return max(alive)[2] if alive else None


def handover(src, dst, to=None):
    s = load(src)
    old = [i for i, n in enumerate(s["nations"]) if n["human"]]
    new = NATIONS.index(to) if to else heir(s, exclude=[NATIONS[i] for i in old])
    b = bytearray(Path(src).read_bytes())
    t = nation_table(b)
    for i in range(16):
        b[t + i * NATION_LEN + HUMAN] = 1 if i == new else 0
    Path(dst).write_bytes(bytes(b))
    d = load(dst)
    assert [i for i, n in enumerate(d["nations"]) if n["human"]] == [new], "human flags did not land"
    assert d["armies"] == s["armies"] and d["cities"] == s["cities"], "something else changed"
    return {"from": [NATIONS[i] for i in old], "to": NATIONS[new], "date": s["date"],
            "cities": s["nations"][new]["cities_count"], "current_seat": NATIONS[s["current_nation"]]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--to")
    a = ap.parse_args(argv)
    if Path(a.dst).exists():
        raise SystemExit(f"refusing to overwrite {a.dst}")
    print(handover(a.src, a.dst, a.to))


if __name__ == "__main__":
    main()
