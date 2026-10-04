"""Independent recomputation for `claims_audit.py` (PR #40 round 3): every function here reads the RAW inputs (the saves of the series, the screenshots, `trials.jsonl`,
the B8 ladder records) and implements its rule on its own, WITHOUT importing `b5_analyze`, `b2_analyze`, `b8_analyze`, `halflog`, `BB.diff`, `BB.attribute`,
`BB.check_grid` or `stage.sprite_value`. What it SHARES with the analysers: the save decoder `state.battle_block.from_save` (bytes -> slots/grid; checked separately by
B2's memory-v-Save-As comparison and by the round-trip tests) and `trials.backfill_halflog` is not used. The audit prints this list in its header."""
import glob
import hashlib
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from state import battle_block as BB          # the shared decoder (bytes -> dict)

STD = {"li": 15000, "hi": 6000, "ar": 3500, "lc": 7000, "hc": 2500}
TYPES = ["li", "hi", "ar", "lc", "hc"]
cheb = lambda p, q: max(abs(p[0] - q[0]), abs(p[1] - q[1]))
pos = lambda s: (s["x"], s["y"])


def size_of(typ, troops):
    return min(2, troops // (STD[typ] // 3))


def old_rule(a, b):
    """(loss rows, rows whose actor is fixed) by the first B2 rule: a loss is 'melee' with an enemy within 1 cell (at the start or the end), 'shooting' with an enemy
    whose ammo fell; fixed when exactly one candidate and the kind is not mixed/unknown."""
    rows = fixed = 0
    for k in range(40):
        sa, sb = a["slots"][k], b["slots"][k]
        if sb["troops"] >= sa["troops"] or not sa["alive"]:
            continue
        rows += 1
        foe = 1 - sa["side"]
        adj = [e["slot"] for e in b["slots"] if e["side"] == foe and (e["alive"] or a["slots"][e["slot"]]["alive"])
               and (cheb(pos(sa), pos(a["slots"][e["slot"]])) <= 1 or cheb(pos(sb), pos(e)) <= 1)]
        sh = [x["slot"] for x in b["slots"] if x["side"] == foe and (x["alive"] or a["slots"][x["slot"]]["alive"]) and x["ammo"] < a["slots"][x["slot"]]["ammo"]]
        if adj and not sh:
            cands = adj
        elif sh and not adj:
            cands = sh
        else:
            continue
        fixed += len(cands) == 1
    return rows, fixed


def words_rule(a, b):
    """The words-8-and-9 attribution (battles.md R-code): (loss rows, fixed rows, kind counter)."""
    shot = {s["slot"] for s in a["slots"] if s["alive"] and b["slots"][s["slot"]]["ammo"] < s["ammo"]}
    pairs = []
    for u in a["slots"]:
        t = u["target"]
        if u["alive"] and 0 <= t < 40 and a["slots"][t]["alive"] and a["slots"][t]["side"] != u["side"] and (t, u["slot"]) not in pairs and (u["slot"], t) not in pairs:
            pairs.append((u["slot"], t))
    losers = [s["slot"] for s in a["slots"] if s["alive"] and b["slots"][s["slot"]]["troops"] < s["troops"]]
    kinds, fixed = Counter(), 0
    for v in losers:
        side = a["slots"][v]["side"]
        mine = [p for p in pairs if v in p]
        shooters = sorted(x for x in shot if a["slots"][x]["side"] != side)
        if mine and not shooters:
            kinds["melee"] += 1
            fixed += len(mine) == 1
        elif shooters and not mine:
            kinds["shooting"] += 1
            fixed += len(shooters) == 1 and [x for x in losers if a["slots"][x]["side"] == side] == [v]
        elif shooters and mine:
            kinds["mixed"] += 1
        else:
            kinds["unknown"] += 1
    return len(losers), fixed, kinds


def series_stats(paths):
    """Over consecutive files of ONE series: (losses, old fixed, words fixed, kinds)."""
    tot = [0, 0, 0, Counter()]
    prev = None
    for p in paths:
        b = BB.from_save(p)
        if prev is not None:
            r, o = old_rule(prev, b)
            r2, w, k = words_rule(prev, b)
            assert r == r2
            tot[0] += r
            tot[1] += o
            tot[2] += w
            tot[3].update(k)
        prev = b
    return tot


def grid_report(b):
    """(inconsistent?, sprite violations): the grid word of an alive slot's cell must be 20*side + 3*type + size; empty cells hold 50; no word without a slot."""
    cells = {}
    viol = 0
    for s in b["slots"]:
        if s["alive"]:
            ti = TYPES.index(s["type"])
            want = 20 * s["side"] + 3 * ti + size_of(s["type"], s["troops"])
            cells[s["x"] * 12 + s["y"]] = (s["side"], ti)
            viol += b["grid"][s["x"] * 12 + s["y"]] != want
    bad = False
    for i, w in enumerate(b["grid"]):
        if w == 50:
            bad |= i in cells
        elif i not in cells:
            bad = True
        else:
            side, ti = cells[i]
            bad |= not 0 <= w - 20 * side - 3 * ti <= 2
    return bad, viol


def b2_sets(art, probe, trials):
    """The 241 files of the B2 analysis: B0's gate2_a and gate2_s2a series and the 12 hi-hi-one trials' series (from trials.jsonl)."""
    b0 = [sorted(glob.glob(str(probe / f"{t}_BATTLE[0-9][0-9].SAV"))) for t in ("gate2_a", "gate2_s2a")]
    tr = [[str(art / n) for n in r["series"]] for r in trials if r["cell"] == "hi-hi-one"]
    return b0, tr


def tile_hash(png, x, y, y0=28, t=32, inset=3):
    raw = subprocess.run(["convert", str(png), "-depth", "8", "rgb:-"], capture_output=True).stdout
    w = int(subprocess.run(["identify", "-format", "%w", str(png)], capture_output=True, text=True).stdout)
    rows = b"".join(raw[((y0 + y * t + r) * w + x * t + inset) * 3:((y0 + y * t + r) * w + x * t + t - inset) * 3] for r in range(inset, t - inset))
    return hashlib.sha256(rows).hexdigest()[:12]


# ---- per-trial facts from the RAW saves (start save, post-battle save, the BATTLEnn series) ----
def trial_facts(rec, art):
    """Facts of one sweep trial recomputed from its saves: winner (which army survives in the post-battle save), destroyed flags, surviving units' quality,
    the winner army's money change, the series as parsed blocks."""
    from state import sav
    pre, post = sav.load(str(art / "start" / rec["start_save"])), sav.load(str(art / rec["post_save"]))
    def army(s, i):
        a = s["armies"][i] if i < len(s["armies"]) else None
        return a if a and a["owner"] >= 0 and a["troops"] > 0 else None
    a_post, d_post = army(post, 0), army(post, 10)
    winner = "attacker" if a_post and not d_post else "defender" if d_post and not a_post else "both" if a_post and d_post else "none"
    wa, wi = (a_post, 0) if winner == "attacker" else (d_post, 10)
    promoted = [u for u in (wa["units"] if wa else []) if u["troops"] > 0 and u["quality"] > 6]
    money = (wa["money"] - pre["armies"][wi]["money"]) if wa else None
    supplies = (wa["supplies"] - pre["armies"][wi]["supplies"]) if wa else None
    return {"winner": winner, "att_destroyed": a_post is None, "def_destroyed": d_post is None, "promoted": [(u["type"], u["quality"]) for u in promoted],
            "att_troops": a_post["troops"] if a_post else 0, "def_troops": d_post["troops"] if d_post else 0, "money_delta": money, "supplies_delta": supplies, "blocks": [BB.from_save(art / n) for n in rec["series"]]}


def acting_sides(a, b):
    """Sides with a unit that moved, whose ammo fell, or whose target word went from another value to a slot (>= 0) between snapshots a and b."""
    out = set()
    for k in range(40):
        sa, sb = a["slots"][k], b["slots"][k]
        if not (sa["alive"] or sb["alive"]):
            continue
        if pos(sa) != pos(sb) or sb["ammo"] < sa["ammo"] or (sb["target"] != sa["target"] and sb["target"] != -1):
            out.add(sa["side"])
    return sorted(out)


def target_events(blocks):
    """Counter of (resulting-snapshot ranks, previous-snapshot ranks) of the enemy a unit's word 9 first shows, with >= 2 enemies alive in that snapshot."""
    c = Counter()
    for pv, cu in zip(blocks, blocks[1:]):
        for u in cu["slots"]:
            o = pv["slots"][u["slot"]]
            if not (u["alive"] and o["alive"]) or u["target"] == o["target"] or u["target"] < 0:
                continue
            foes = [e for e in cu["slots"] if e["alive"] and e["side"] != u["side"]]
            t = cu["slots"][u["target"]]
            if not t["alive"] or t["side"] == u["side"] or len(foes) < 2:
                continue
            d = lambda x: cheb(pos(u), pos(x))
            nearer = [e for e in foes if d(e) < d(t)]
            tie = [e for e in foes if e["slot"] != t["slot"] and d(e) == d(t)]
            c["events"] += 1
            c["res_nearest"] += not nearer
            c["res_unique"] += not nearer and not tie
            c["res_weakest"] += not [e for e in foes if e["troops"] < t["troops"]]
            pf = [e for e in pv["slots"] if e["alive"] and e["side"] != u["side"]]
            pt = pv["slots"][u["target"]]
            if pt["alive"] and pt["side"] != u["side"] and len(pf) >= 2:
                dp = lambda x: cheb(pos(o), pos(x))
                pn = [e for e in pf if dp(e) < dp(pt)]
                ptie = [e for e in pf if e["slot"] != pt["slot"] and dp(e) == dp(pt)]
                c["prev_events"] += 1
                c["prev_nearest"] += not pn
                c["prev_unique"] += not pn and not ptie
                c["prev_weakest"] += not [e for e in pf if e["troops"] < pt["troops"]]
    return c


def end_state(blocks, winner):
    """Loser's state in the LAST saved file: 'empty', 'no unit rout-eligible' or 'some rout-eligible' (eligible: troops < std div 25 or morale <= 39)."""
    loser = 1 if winner == "attacker" else 0
    ls = [s for s in blocks[-1]["slots"] if s["alive"] and s["side"] == loser]
    if not ls:
        return "empty"
    return "some rout-eligible" if any(s["troops"] < STD[s["type"]] // 25 or s["morale"] <= 39 for s in ls) else "no unit rout-eligible"


def b8_observations(files):
    """{(type, side): {troops: size class}} from the BATTLE01 saves of the B8 v2 rounds: a unit counts only when alone on its cell; class = grid word - 20*side - 3*type."""
    obs = defaultdict(dict)
    for f in files:
        b = BB.from_save(f)
        occ = Counter((s["x"], s["y"]) for s in b["slots"] if s["alive"])
        for s in b["slots"]:
            if s["alive"] and occ[(s["x"], s["y"])] == 1:
                obs[(s["type"], s["side"])][s["troops"]] = b["grid"][s["x"] * 12 + s["y"]] - 20 * s["side"] - 3 * TYPES.index(s["type"])
    return obs
