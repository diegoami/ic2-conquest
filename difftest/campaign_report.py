"""Summarise the #232 campaigns (one row per campaign) and compare the bot's orders by IDENTITY.

    python3 -m difftest.campaign_report artifacts/run-exp-<name> OUT_PREFIX

campaign.py compared the two games' orders as written, and an order names an army by its record index, which differs
between the games for the same army (the original re-uses freed records; ptolemaic, turn 2: army 7 vs army 6, one
army of 56,400 at (189,94)). Here each army or fleet index in an order is replaced by (owner, x, y) of that record in
the state the bot read, so "orders differ" means different orders for the same units.
"""
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from state.sav import load  # noqa: E402


def identity(orders, s):
    out = []
    for o in orders:
        o = dict(o)
        for k in ("army", "partner", "target"):
            if k in o and o["op"] not in ("attack_fleet",) and o[k] < len(s["armies"]):
                a = s["armies"][o[k]]
                o[k] = ("army", a["owner"], a["x"], a["y"])
        if "fleet" in o and o["fleet"] < len(s["fleets"]):
            f = s["fleets"][o["fleet"]]
            o["fleet"] = ("fleet", f["owner"], f["x"], f["y"])
        out.append(o)
    return out


def bot_input(run, side, k):
    """The state the bot read before turn k's orders."""
    if side == "original":
        if k == 1:
            return load(run / "original/t00-start.SAV")
        return load(sorted((run / "original").glob(f"t{k - 1:02d}-a*.SAV"))[-1])
    return load(sorted((run / "remake" / f"t{k - 1:02d}").glob("a*.SAV"))[-1])


def report(base):
    rows = []
    for summary in sorted(Path(base).glob("*/summary.json")):
        run = summary.parent
        turns = [json.loads(l) for l in (run / "turns.jsonl").read_text().splitlines() if l.strip()]
        first_order, first_own = None, None
        per_turn = []
        for t in turns:
            k = t["turn"]
            same = identity(t["orders_original"], bot_input(run, "original", k)) == identity(t["orders_remake"], bot_input(run, "remake", k))
            per_turn.append({"turn": k, "orders_same_by_identity": same, "own_differences": t["own_differences"]})
            if not same and first_order is None:
                first_order = k
            if t["own_differences"] and first_own is None:
                first_own = k
        rows.append({"campaign": run.name, "turns": len(turns), "first_own_difference_turn": first_own,
                     "first_order_difference_turn": first_order, "per_turn": per_turn,
                     "first_own_fields": next((t["own_fields"][:10] for t in turns if t["own_differences"]), [])})
    return rows


if __name__ == "__main__":
    rows = report(sys.argv[1])
    prefix = Path(sys.argv[2])
    for ext in (".json", ".txt"):
        if prefix.with_suffix(ext).exists():
            raise SystemExit(f"refusing to overwrite {prefix.with_suffix(ext)}")
    prefix.with_suffix(".json").write_text(json.dumps(rows, indent=1, default=str))
    lines = ["| campaign | turns | first own difference | first order difference (by identity) |", "|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['campaign']} | {r['turns']} | {r['first_own_difference_turn'] or 'none'} | {r['first_order_difference_turn'] or 'none'} |")
    prefix.with_suffix(".txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
