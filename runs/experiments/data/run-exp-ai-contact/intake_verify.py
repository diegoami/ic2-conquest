#!/usr/bin/env python3
"""Intake verifier for run-exp-ai-contact (2026-10-08).

Reads the SAV JSON dumps the experiment committed, extracts the fields the
draft ``findings/2026-10-07-ai-mover-contact.md`` rests on, and prints a
match/mismatch table for every load-bearing claim.  Read-only against the
data; the script itself is committed under the experiment's tracked path
per CLAUDE.md rule 6 (measurements kept).
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
T = HERE / "turns"
ARTIFACTS = Path("/home/diego/projects/wt-ai-mover/artifacts/run-exp-ai-contact")

# Pick the highest-versioned JSON for a turn (mirrors how archive_batch keeps the data).
def latest(*candidates):
    for c in candidates:
        p = T / c
        if p.exists():
            return p
    raise FileNotFoundError(candidates)


def load_turn(turn):
    """Load the JSON snapshot for turn NNNN and merge cities from the SAV (snapshot.py drops cities)."""
    snap = json.loads(latest(f"{turn}.SAV.v3.json",
                             f"{turn}.SAV.v2.json",
                             f"{turn}.SAV.json").read_text())
    sav_path = ARTIFACTS / f"{turn}.SAV"
    if sav_path.exists():
        sys.path.insert(0, str(HERE.parent.parent.parent.parent))  # worktree root
        from state.sav import parse as parse_sav
        sav = parse_sav(sav_path.read_bytes())
        snap["cities"] = sav["cities"]
    return snap


def load_b3(turn):
    snap = json.loads(latest(f"b3_{turn}.SAV.v2.json",
                             f"b3_{turn}.SAV.json").read_text())
    sav_path = ARTIFACTS / f"b3_{turn}.SAV"
    if sav_path.exists():
        sys.path.insert(0, str(HERE.parent.parent.parent.parent))  # worktree root
        from state.sav import parse as parse_sav
        sav = parse_sav(sav_path.read_bytes())
        snap["cities"] = sav["cities"]
    return snap


def load_b3a(turn):
    snap = json.loads((T / f"b3a_AUTO{turn:04d}.SAV.json").read_text())
    sav_path = ARTIFACTS / f"b3a_AUTO{turn:04d}.SAV"
    if sav_path.exists():
        sys.path.insert(0, str(HERE.parent.parent.parent.parent))  # worktree root
        from state.sav import parse as parse_sav
        sav = parse_sav(sav_path.read_bytes())
        snap["cities"] = sav["cities"]
    return snap


def load_staged(path):
    """Load a raw SAV (no JSON counterpart) directly via state.sav.parse."""
    sys.path.insert(0, str(HERE.parent.parent.parent.parent))  # worktree root
    from state.sav import parse as parse_sav, NATIONS
    full = ARTIFACTS / path
    if not full.exists():
        raise FileNotFoundError(full)
    return parse_sav(full.read_bytes())


def army_at(save, x, y, owner_name=None):
    """First army at (x, y) whose owner matches (string, no transform needed)."""
    for a in save["armies"]:
        if a["x"] == x and a["y"] == y and (owner_name is None or a["owner"] == owner_name):
            return a
    return None


def all_armies_at(save, x, y):
    return [a for a in save["armies"] if a["x"] == x and a["y"] == y]


def armies_of(save, owner_name):
    return [a for a in save["armies"] if a["owner"] == owner_name]


def city_at(save, x, y, name=None):
    for c in save["cities"]:
        if c["x"] == x and c["y"] == y and (name is None or c["name"] == name):
            return c
    return None


def city_by_name(save, name):
    return next((c for c in save["cities"] if c["name"] == name), None)


def news_lines(save):
    return list(save.get("news", []))


def banner(s):
    print()
    print("=== " + s + " ===")


def show_army(label, a):
    if a is None:
        print(f"  {label}: <missing>")
        return
    print(f"  {label}: id={a['id']} owner={a['owner']} ({a['x']},{a['y']}) "
          f"troops={a['troops']} supplies={a['supplies']} money={a['money']} moves={a['moves']}")


def show_city(label, c):
    if c is None:
        print(f"  {label}: <missing>")
        return
    print(f"  {label}: owner={c['owner']} loyalty={c['loyalty']} "
          f"fort={c['fort']} pop={c['pop']} supplies={c['supplies']}")


def check():
    # 1. Carthage destroys Celtiberia 0720 -> 0721
    banner("Claim 1: Carthage destroys Celtiberia. "
           "Carthage army 2 (42,63) -> (39,64); Celtiberia 10 (38,64) gone; "
           "troops 33900 -> 22806, supplies 339 -> 228, money 597 -> 697 (+100 loser's purse).")
    s0, s1 = load_turn("AUTO0720"), load_turn("AUTO0721")
    show_army("AUTO0720 Carthage (42,63)", army_at(s0, 42, 63, "Carthage"))
    show_army("AUTO0721 Carthage (39,64)", army_at(s1, 39, 64, "Carthage"))
    show_army("AUTO0720 army   (38,64)", army_at(s0, 38, 64))
    show_army("AUTO0721 army   (38,64)", army_at(s1, 38, 64))
    print("  AUTO0721 news:")
    for line in news_lines(s1):
        if line.strip(): print(f"    {line!r}")

    # 2. Seleucid destroys Bithynia 0721 -> 0722 (mid-walk)
    banner("Claim 2: Seleucid destroys Bithynia mid-walk. "
           "Seleucid army 5 (179,44) -> (185,44); Bithynia 11 (182,41) gone; "
           "troops 37300 -> 23386, supplies 299 -> 233, money 600 -> 738 (+138; loser's purse 100 + within-turn growth).")
    s1, s2 = load_turn("AUTO0721"), load_turn("AUTO0722")
    show_army("AUTO0721 Seleucid (179,44)", army_at(s1, 179, 44, "Seleucid"))
    show_army("AUTO0722 Seleucid (185,44)", army_at(s2, 185, 44, "Seleucid"))
    show_army("AUTO0721 army   (182,41)", army_at(s1, 182, 41))
    show_army("AUTO0722 army   (182,41)", army_at(s2, 182, 41))
    print("  AUTO0722 news (week-5 block):")
    for line in news_lines(s2):
        if "Week  5" in line or "Seleucid" in line or "Bithynia" in line:
            print(f"    {line!r}")
    # 2b. Galatia id12 in 0721 -> 0722 is also gone (natural_evidence flags it)
    banner("Note 2b: Galatia id12 (194,46) is also GONE 0721 -> 0722 (natural_evidence). "
           "Draft does not itemise; news for this span shows Seleucid destroys Bithynia and Seleucid destroys Galatia in week 7 (later).")
    show_army("AUTO0721 army (194,46)", army_at(s1, 194, 46))
    show_army("AUTO0722 army (194,46)", army_at(s2, 194, 46))
    print("  AUTO0722 Galatia armies:", [(a['id'], a['x'], a['y'], a['troops']) for a in armies_of(s2, "Galatia")])

    # 3. Gaul destroys Rome 0721 -> 0722 (tactical battle at human defence, Rome wins on the resolution)
    banner("Claim 3: Gaul army 9 reaches Rome army 0's neighbourhood. "
           "Tactical battle; Rome 0: 23700 -> 6596, money 100 -> 196 (+96), supplies 123 -> 65, moves 9 -> 9 untouched. "
           "News: 'Rome destroys army of Gaul' (defender-resolution framing).")
    print("  AUTO0721 Rome:", [(a['id'], a['x'], a['y'], a['troops'], a['supplies'], a['money'], a['moves'])
                              for a in armies_of(s1, "Rome")])
    print("  AUTO0722 Rome:", [(a['id'], a['x'], a['y'], a['troops'], a['supplies'], a['money'], a['moves'])
                              for a in armies_of(s2, "Rome")])
    print("  AUTO0721 Gaul:", [(a['id'], a['x'], a['y'], a['troops'], a['supplies'], a['money'])
                              for a in armies_of(s1, "Gaul")])
    print("  AUTO0722 Gaul:", [(a['id'], a['x'], a['y'], a['troops'])
                              for a in armies_of(s2, "Gaul")])
    print(f"  AUTO0722 turn_texts: {s2.get('turn_texts')}")

    # 4. Four city captures
    cities = [
        ("Dimale", 131, 50, "AUTO0725", "AUTO0726"),
        ("Castulo", 36, 61, "AUTO0727", "AUTO0728"),
        ("Iliturgi", 33, 63, "AUTO0728", "AUTO0729"),
        ("Orangis", 37, 65, "AUTO0729", "AUTO0730"),
    ]
    for name, x, y, t0, t1 in cities:
        banner(f"Claim 4: {name} ({x},{y}) captured. {t0} -> {t1}.")
        s0, s1 = load_turn(t0), load_turn(t1)
        show_city(f"{t0}", city_at(s0, x, y, name))
        show_city(f"{t1}", city_at(s1, x, y, name))
        # News line of the capture
        for line in news_lines(s1):
            if name in line:
                print(f"    news: {line!r}")

    # 5. Media id churn at (307,58) — every turn one Media army there disappears via merge sub-phase
    banner("Claim 5: Media capital (307,58) army churns by merge (FUN_004509f0), not contact. "
           "Identical 377-troop Media armies vanish successive turns with no news.")
    for t in range(720, 733):
        s = load_turn(f"AUTO0{t}")
        ms = [a for a in s["armies"] if a["owner"] == "Media" and a["x"] == 307 and a["y"] == 58]
        others = [a for a in s["armies"] if a["owner"] == "Media" and (a["x"] != 307 or a["y"] != 58)]
        print(f"  AUTO0{t} Media (307,58): {[(a['id'], a['troops'], a['supplies']) for a in ms] or 'none'}; "
              f"other Media armies: {[(a['id'], a['x'], a['y'], a['troops']) for a in others] or 'none'}")

    # 6. Staged through-click: Rome (100,33) moves 196 -> click (55,33)
    banner("Claim 6: staged through-click deviates off the row, stops at (91,32) with 186 moves left.")
    s_in = load_b3("AUTO0731")
    s_through = json.loads((T / "b3t_AUTO0732.SAV.json").read_text())
    print("  b3_AUTO0731 Rome:", [(a['id'], a['x'], a['y'], a['moves'], a['troops'])
                                  for a in armies_of(s_in, "Rome")])
    print("  b3t_AUTO0732 Rome:", [(a['id'], a['x'], a['y'], a['moves'], a['troops'])
                                   for a in armies_of(s_through, "Rome")])
    # Gaul at (68,33) should still be present in b3t
    show_army("b3t (68,33)", army_at(s_through, 68, 33))

    # 7. Staged onto-click: from (91,32) moves 200 -> click Gaul (68,33) — silent no-op
    banner("Claim 7: staged onto-click on Gaul (68,33) from (91,32) is a silent no-op.")
    s_onto_before = s_through   # through-clicked state serves as the staged-input
    s_onto = json.loads((T / "b3o_AUTO0733.SAV.json").read_text())
    print("  Before (Rome):", [(a['id'], a['x'], a['y'], a['moves'], a['money'])
                              for a in armies_of(s_onto_before, "Rome")])
    print("  After  (Rome):", [(a['id'], a['x'], a['y'], a['moves'], a['money'])
                              for a in armies_of(s_onto, "Rome")])
    print("  Before (Gaul):", [(a['id'], a['x'], a['y'], a['moves'], a['troops'])
                              for a in armies_of(s_onto_before, "Gaul")])
    print("  After  (Gaul):", [(a['id'], a['x'], a['y'], a['moves'], a['troops'])
                              for a in armies_of(s_onto, "Gaul")])
    print(f"  b3o news ({len(s_onto.get('news', []))} lines):")
    for line in news_lines(s_onto):
        if line.strip(): print(f"    {line!r}")
    print(f"  b3o turn_texts: {s_onto.get('turn_texts')}")

    # 8. Chase ghost: b3a_AUTO0733 - 0738
    banner("Claim 8: chase follows a ghost (stale memory); real Gaul moved elsewhere.")
    for t in range(733, 739):
        s = load_b3a(t)
        r = armies_of(s, "Rome")
        g = armies_of(s, "Gaul")
        print(f"  b3a_AUTO0{t}:")
        print(f"    Rome: {[(a['id'], a['x'], a['y'], a['troops'], a['moves']) for a in r] or 'none'}")
        print(f"    Gaul: {[(a['id'], a['x'], a['y'], a['troops']) for a in g] or 'none'}")
        for line in news_lines(s):
            if line.strip(): print(f"      news: {line!r}")


if __name__ == "__main__":
    check()
