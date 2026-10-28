"""Neutral projection and comparison of two original-format saves (#229).

Both sides are read with `state/sav.py`: the original's own saves, and the remake's state exported to the
original format by the remake's exporter (`difftest/remake_adapter`). The projection keeps the fields that
carry game state and drops interface-only ones; MAPPING lists every field with its treatment.

    python3 -m difftest.compare A.SAV B.SAV [--json out.json]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from state.sav import NATIONS, load  # noqa: E402

# Field treatment. "compare": a difference is reported. "ignore": never reported, with the reason.
MAPPING = {
    "map": "compare: terrain and marker code of every one of the 44,800 cells",
    "cities.*": "compare: name, x, y, owner, allegiance, loyalty, supplies, fort, fort_pending, pop, max_pop, tribute",
    "armies.*": "compare: by record index; x, y, owner, moves, cell, supplies, money, morale, units (slot, type, troops, quality, merc label); unit names ignored",
    "armies.*.units.*.name": "ignore: generated names; the remake's exporter may write export-only aliases",
    "fleets.*": "compare: by record index; every parsed field",
    "nations.*": "compare: relations, neighbours, city_list, recruit_slots, wealth, treasury, unity, mobilization, capital, cities_count, tax, tax_base, conquered_by, human, alive",
    "nations.*.view": "ignore: the map view origin is interface state",
    "nations.*.name/leader": "compare",
    "mercenaries": "compare: every slot",
    "news": "ignore for divergence: wording and line breaking are presentation; kept in the report as context",
    "turn_order, current_nation, seat_index, week, year_bc, season, pending_offer": "compare",
    "battle_flag": "compare",
    "size, tail_off, turn, date": "ignore: derived from other fields or from the news length",
}

NATION_KEYS = ["name", "leader", "relations", "neighbours", "city_list", "recruit_slots", "wealth", "treasury", "unity",
               "mobilization", "capital", "cities_count", "tax", "tax_base", "conquered_by", "human", "alive"]
TAIL_KEYS = ["turn_order", "current_nation", "seat_index", "week", "year_bc", "season", "pending_offer", "battle_flag"]


def project(s):
    """The compared view of one parsed save: {path: value} with stable, readable paths."""
    out = {}
    for k in TAIL_KEYS:
        out[k] = s[k]
    for c in s["cities"]:
        for k, v in c.items():
            if k != "id":
                out[f"cities.{c['id']}.{k}"] = v
    out["armies.count"] = len(s["armies"])
    for a in s["armies"]:
        for k in ("x", "y", "owner", "moves", "cell", "supplies", "money", "morale"):
            out[f"armies.{a['id']}.{k}"] = a[k]
        out[f"armies.{a['id']}.units"] = [(u["slot"], u["type"], u["troops"], u["quality"], u["merc"]) for u in a["units"]]
    out["fleets.count"] = len(s["fleets"])
    for f in s["fleets"]:
        for k, v in f.items():
            if k != "id":
                out[f"fleets.{f['id']}.{k}"] = v
    for n in s["nations"]:
        for k in NATION_KEYS:
            out[f"nations.{NATIONS[n['id']]}.{k}"] = n[k]
    for m in s["mercenaries"]:
        out[f"mercenaries.{m['slot']}"] = (m["x"], m["y"], m["label"], m["type"], m["troops"], m["quality"])
    out["mercenaries.slots"] = sorted(m["slot"] for m in s["mercenaries"])
    return out


def map_diff(a, b, limit=40):
    cells = [(i // 140, i % 140, x, y) for i, (x, y) in enumerate(zip(a["map"], b["map"])) if x != y]
    return {"count": len(cells), "first": [{"x": x, "y": y, "a": p, "b": q} for x, y, p, q in cells[:limit]]}


def compare(a, b):
    """Differences between two parsed saves: {"fields": [{path, a, b}], "map": {...}}."""
    pa, pb = project(a), project(b)
    fields = []
    for k in sorted(set(pa) | set(pb), key=_order):
        va, vb = pa.get(k, "<absent>"), pb.get(k, "<absent>")
        if _norm(va) != _norm(vb):
            fields.append({"path": k, "a": va, "b": vb})
    return {"fields": fields, "map": map_diff(a, b)}


def _norm(v):
    return json.loads(json.dumps(v))


def _order(path):
    return [(0, int(p), "") if p.isdigit() else (1, 0, p) for p in path.split(".")]


def compare_files(pa, pb):
    a, b = load(pa), load(pb)
    d = compare(a, b)
    d["a"] = {"path": str(pa), "date": a["date"], "turn": a["turn"]}
    d["b"] = {"path": str(pb), "date": b["date"], "turn": b["turn"]}
    return d


def summary(d, n=25):
    lines = [f"{d['a']['path']} ({d['a']['date']}) vs {d['b']['path']} ({d['b']['date']}): "
             f"{len(d['fields'])} field differences, {d['map']['count']} map cells"]
    for f in d["fields"][:n]:
        lines.append(f"  {f['path']}: {f['a']!r} vs {f['b']!r}")
    if len(d["fields"]) > n:
        lines.append(f"  ... {len(d['fields']) - n} more")
    for c in d["map"]["first"][:5]:
        lines.append(f"  map ({c['x']},{c['y']}): {c['a']} vs {c['b']}")
    return "\n".join(lines)


if __name__ == "__main__":
    d = compare_files(sys.argv[1], sys.argv[2])
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(d, indent=1))
    print(summary(d))


def scoped(d, a, b, nation):
    """The differences of `d` (from compare(a, b)) that belong to `nation`: its nation record, and the cities,
    armies and fleets it owns in either save. Used after End turn, where other nations' AI and random draws act."""
    name = NATIONS[nation]
    keep = set()
    for kind in ("cities", "armies", "fleets"):
        for s in (a, b):
            keep |= {f"{kind}.{r['id']}" for r in s[kind] if r["owner"] == nation}
    out = []
    for f in d["fields"]:
        p = f["path"].split(".")
        if p[0] == "nations" and p[1] == name or ".".join(p[:2]) in keep:
            out.append(f)
    return out
