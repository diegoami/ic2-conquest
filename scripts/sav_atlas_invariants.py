#!/usr/bin/env python3
"""Cross-record invariants and observed domains of the original-SAV fields (conquest issue #107).

    B=$HOME/ic2-inputs/ic2-research-inputs-20261021
    python3 -I scripts/sav_atlas_invariants.py --root $B $B/source-saves $B/native-evidence $B/research40-saves \
        --out runs/experiments/data/run-exp-sav-atlas107/<new-name>.json

Each invariant states what the code implies (the source is named in INVARIANTS) and is checked in every
framed SAV: the receipt holds, per group and invariant, the number of cases checked and of violations, with
the file and record indices of the first violations; never field values. The domain section holds, per leaf
field, the observed minimum, maximum and number of distinct values over the live records (the documented
sentinels included). Observed domains are samples, not the legal domain. The output file is created
exclusively (CLAUDE.md rule 6).
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

W, H = 320, 140
INVARIANTS = {
    "army_marker": "a live army not aboard (cell != -1) has an army marker of its owner at (x, y): 200..247 with "
                   "(marker - 200) mod 16 = owner",
    "army_marker_band_current": "the marker's band equals 200/216/232 by total troops div 1000 <25/<50/else "
                                "(FUN_0044A80C over FUN_0044A698); a violation is a band not yet refreshed",
    "army_cell_terrain_or_city": "a live army not aboard stores what its marker covers: on a city tile a city marker of "
                                 "that city's owner ((cell - 20) mod 16 = owner); elsewhere a terrain code 0..11",
    "aboard_link_army_side": "an army with cell = -1 is the cargo (fleet +22) of exactly one live fleet",
    "aboard_link_fleet_side": "a fleet's cargo index is a live army with cell = -1 and the fleet's owner",
    "fleet_marker": "a launched fleet (countdown -1) has map[x][y] = owner + 300/316/332 by ships <25/<50/else "
                    "(FUN_0044A878)",
    "fleet_countdown": "countdown is -1 (launched) or an even 0..24 (24 at order, -2 per tick; FUN_0044A004, FUN_004514EC)",
    "fleet_building_city": "under construction, +20 is a city index 0..333",
    "fleet_condition": "launched, +20 (condition) is 0..100",
    "city_marker": "map at a city tile is 20 + owner + 16 * variant, i.e. (marker - 20) mod 16 = owner",
    "city_list_equals_owned": "a nation's city list up to the first -1 is the set of cities it owns",
    "city_list_sorted": "the city list is in byte order of the city names (FUN_0044B8F4 inserts with StrComp)",
    "city_count": "for a nation with a capital (not eliminated), NATION.cities equals the length of the city list",
    "city_count_eliminated": "for an eliminated nation (capital -1), NATION.cities equals the length of the list "
                             "(a violation is the documented stale count)",
    "capital_owned": "a capital >= 0 is a city the nation owns",
    "slots_packed": "in a live army no live slot (troops > 0) follows an empty one",
    "slot_troops_nonnegative": "slot troops >= 0 (increment 5)",
    "recruit_city_index": "a recruit entry with troops > 0 names a city index 0..333",
    "merc_live_on_city": "a live merc slot (troops >= 0) sits on a city tile (restock copies template positions)",
    "fort_encoding": "fort >= 0, and either fort <= 100 or (pending = fort div 100 >= 1, current = fort mod 100) "
                     "with pending + current <= 100 (hypothesis: pending points cannot lift the fort past 100)",
    "news_index": "news index in -1..39",
    "battle_grid_count": "with a battle block, the grid holds one non-50 icon per battle slot with troops > 0",
}


def i16(b, o):
    return struct.unpack_from("<h", b, o)[0]


def check(b):
    blocks, facts = cov.frame(b)
    pos = {rec: o for rec, o, _ in blocks}
    cell = lambda x, y: i16(b, 2 * (x * H + y))
    res = defaultdict(lambda: [0, []])

    def t(name, ok, where):
        res[name][0] += 1
        if not ok:
            res[name][1].append(where)

    A, F = facts["armies"], facts["fleets"]
    a0, f0, n0, c0 = pos.get("army", 0), pos.get("fleet", 0), pos["nation"], pos["city"]
    army = [struct.unpack_from("<8h", b, a0 + 656 * k) for k in range(A)]
    fleet = [struct.unpack_from("<13h", b, f0 + 26 * k) for k in range(F)]
    city = [struct.unpack_from("<10h", b, c0 + 34 * i + 14) for i in range(334)]   # x y owner alleg loyal sup fort pop max trib
    city_at = {(c[0], c[1]): c[2] for c in city}                  # tile -> owning nation
    for k, (x, y, own, mv, cl, *_r) in enumerate(army):
        if own < 0:
            continue
        if cl != -1:
            on_city = city_at.get((x, y))
            t("army_cell_terrain_or_city", (20 <= cl <= 99 and (cl - 20) % 16 == on_city) if on_city is not None
              else 0 <= cl <= 11, k)
            total = sum(i16(b, a0 + 656 * k + 16 + 32 * s + 4) for s in range(20)) or 1
            band = 200 if total // 1000 < 25 else 216 if total // 1000 < 50 else 232
            m = cell(x, y) if 0 <= x < W and 0 <= y < H else None
            t("army_marker", m is not None and 200 <= m <= 247 and (m - 200) % 16 == own, k)
            t("army_marker_band_current", m == own + band, k)
        else:
            carriers = [j for j, f in enumerate(fleet) if f[4] >= 0 and f[11] == k]
            t("aboard_link_army_side", len(carriers) == 1, k)
        empty = False
        for s in range(20):
            tr = i16(b, a0 + 656 * k + 16 + 32 * s + 4)
            t("slot_troops_nonnegative", tr >= 0, (k, s))
            t("slots_packed", not (tr > 0 and empty), (k, s))
            empty |= tr <= 0
    for j, f in enumerate(fleet):
        x, y, rx, ry, own, cd, mv, sup, mon, ships, cc, carg, cl = f
        if own < 0:
            continue
        t("fleet_countdown", cd == -1 or (0 <= cd <= 24 and cd % 2 == 0), j)
        if cd >= 0:
            t("fleet_building_city", 0 <= cc < 334, j)
        else:
            t("fleet_condition", 0 <= cc <= 100, j)
            band = 300 if ships < 25 else 316 if ships < 50 else 332
            t("fleet_marker", 0 <= x < W and 0 <= y < H and cell(x, y) == own + band, j)
        if carg >= 0:
            t("aboard_link_fleet_side", carg < A and army[carg][2] == own and army[carg][4] == -1, j)
    owned = defaultdict(set)
    for i, (x, y, own, *_r) in enumerate(city):
        owned[own].add(i)
        m = cell(x, y)
        t("city_marker", 20 <= m <= 99 and (m - 20) % 16 == own, i)
        fort = _r[3]                                    # _r = allegiance, loyalty, supplies, fort, pop, ...
        t("fort_encoding", fort >= 0 and (fort <= 100 or fort // 100 + fort % 100 <= 100), i)
    for n in range(16):
        o = n0 + 1172 * n
        lst = []
        for e in range(334):
            v = i16(b, o + 0x48 + 2 * e)
            if v == -1:
                break
            lst.append(v)
        t("city_list_equals_owned", set(lst) == owned.get(n, set()), n)
        names = [b[c0 + 34 * i: c0 + 34 * i + 14].split(b"\0", 1)[0] for i in lst]
        t("city_list_sorted", names == sorted(names), n)
        cap = i16(b, o + 0x444)
        t("city_count" if cap >= 0 else "city_count_eliminated", i16(b, o + 0x446) == len(lst), n)
        if cap >= 0:
            t("capital_owned", cap < 334 and city[cap][2] == n, n)
        for e in range(40):
            st, ty, tr, ci = struct.unpack_from("<4h", b, o + 0x2E4 + 8 * e)
            if tr > 0:
                t("recruit_city_index", 0 <= ci < 334, (n, e))
    tiles = {(c[0], c[1]) for c in city}
    m0 = pos["merc"]
    for s in range(50):
        x, y, lab, ty, tr, q = struct.unpack_from("<6h", b, m0 + 12 * s)
        if tr >= 0:
            t("merc_live_on_city", (x, y) in tiles, s)
    t("news_index", -1 <= facts["news_index"] <= 39, 0)
    if facts["battle_flag"]:
        bo = pos["battle"]
        live = sum(i16(b, bo + 9 + 44 * s + 8) > 0 for s in range(40))
        icons = sum(i16(b, bo + 0x6E9 + 2 * g) != 50 for g in range(168))
        t("battle_grid_count", live == icons, (live, icons))
    return res


def domains(b, rows, acc):
    """Fold min/max/distinct of every scalar leaf field (i16/u16/u8/i32/u32) of live records into acc."""
    blocks, facts = cov.frame(b)
    fmt = {"i16": "<h", "u16": "<H", "u8": "<B", "i32": "<i", "u32": "<I"}
    by_rec = defaultdict(list)
    for r in rows:
        by_rec[r["record"]].append(r)
    for rec, off, n in blocks:
        for k in range(n):
            base = off + cov.RECORD_LEN[rec] * k
            if rec == "army" and i16(b, base + 4) < 0 or rec == "fleet" and i16(b, base + 8) < 0:
                continue
            for r in by_rec.get(rec, []):
                f = fmt.get(r["type"])
                if not f:
                    continue
                v = struct.unpack_from(f, b, base + r["first"])[0]
                a = acc[r["field_id"]]
                a["min"] = v if a["min"] is None else min(a["min"], v)
                a["max"] = v if a["max"] is None else max(a["max"], v)
                if len(a["values"]) <= 4096:
                    a["values"].add(v)
            if rec == "army":                                       # nested unit slots
                for s in range(20):
                    sb = base + 16 + 32 * s
                    for r in by_rec["army_slot"]:
                        f = fmt.get(r["type"])
                        if f:
                            v = struct.unpack_from(f, b, sb + r["first"])[0]
                            a = acc[r["field_id"]]
                            a["min"] = v if a["min"] is None else min(a["min"], v)
                            a["max"] = v if a["max"] is None else max(a["max"], v)
                            a["values"].add(v)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+", type=Path)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    rows = cov.load_map()
    out = dict(field_map=cov.FIELD_MAP.name, field_map_sha256=hashlib.sha256(cov.FIELD_MAP.read_bytes()).hexdigest(),
               invariants=INVARIANTS, groups={})
    acc = defaultdict(lambda: {"min": None, "max": None, "values": set()})
    for d in a.dirs:
        files = sorted(p for p in d.rglob("*") if p.suffix.lower() == ".sav")
        g = defaultdict(lambda: {"checked": 0, "violations": 0, "first": []})
        for p in files:
            b = p.read_bytes()
            name = str(p.relative_to(a.root)) if p.is_relative_to(a.root) else p.name
            for inv, (n, bad) in check(b).items():
                g[inv]["checked"] += n
                g[inv]["violations"] += len(bad)
                g[inv]["first"] += [[name, w] for w in bad[: max(0, 5 - len(g[inv]["first"]))]]
            domains(b, rows, acc)
        out["groups"][str(d.relative_to(a.root)) if d.is_relative_to(a.root) else str(d)] = dict(files=len(files), invariants=g)
    out["observed_domains"] = {k: dict(min=v["min"], max=v["max"], distinct=len(v["values"])) for k, v in sorted(acc.items())}
    with open(a.out, "x") as fh:
        json.dump(out, fh, indent=1); fh.write("\n")
    for gname, g in out["groups"].items():
        print(gname, g["files"])
        for inv, v in sorted(g["invariants"].items()):
            print(f"   {inv}: {v['violations']}/{v['checked']}", v["first"][:2] if v["violations"] else "")


if __name__ == "__main__":
    sys.exit(main())
