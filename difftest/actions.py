"""The shared action format (#229): one JSON object per line, read by both game adapters.

    {"format": "diff-actions/1", "name": "toy3", "seat": "Rome", "note": "..."}     first line: header
    {"op": "set_tax", "percent": 20}
    {"op": "move", "army": 0, "x": 101, "y": 38}
    {"op": "recruit", "city": 85, "type": "hi", "troops": 1000}
    {"op": "end_turn"}

Records are named by their index in the original format at the moment the action runs (army 0 is the save's
first army record, city 85 is Rome). Unit types use `state/sav.py`'s codes (li, hi, ar, lc, hc). The format is
plain data with no game logic; a new op is added here first, then to both adapters.
"""
import json
from pathlib import Path

FORMAT = "diff-actions/1"
OPS = {
    "set_tax": {"percent": int},
    "move": {"army": int, "x": int, "y": int},
    "recruit": {"city": int, "type": str, "troops": int},
    "end_turn": {},
    "relation": {"nation": int, "kind": str},          # kind: peace, trade, ally, war (International Relations radio)
    "fortify": {"city": int, "points": int},
    "disband_army": {"army": int},
    "split_army": {"army": int, "units": list},        # unit rows of the army (its live units in slot order)
    "join_armies": {"army": int, "partner": int},      # original: Join on `army` (the game picks the adjacent partner)
    "buy_supply": {"army": int, "city": int, "tons": int},
    "build_fleet": {"ships": int},
    "disband_slot": {"slot": int},                     # index among the nation's occupied recruitment slots
    "hire_mercenary": {"army": int, "pool": int},      # pool slot of the adjacent offer
}
RELATION_KINDS = ("peace", "trade", "ally", "war")
UNIT_TYPES = {"li": "light_infantry", "hi": "heavy_infantry", "ar": "archers", "lc": "light_cavalry", "hc": "heavy_cavalry"}


class ActionError(ValueError):
    pass


def validate(a, line=0):
    op = a.get("op")
    if op not in OPS:
        raise ActionError(f"line {line}: unknown op {op!r} (known: {', '.join(OPS)})")
    for k, t in OPS[op].items():
        if not isinstance(a.get(k), t):
            raise ActionError(f"line {line}: {op} needs {k} ({t.__name__})")
    extra = set(a) - set(OPS[op]) - {"op", "note"}
    if extra:
        raise ActionError(f"line {line}: {op} has unknown fields {sorted(extra)}")
    if op == "set_tax" and not 0 <= a["percent"] <= 40:
        raise ActionError(f"line {line}: tax percent out of 0..40")
    if op == "relation" and a["kind"] not in RELATION_KINDS:
        raise ActionError(f"line {line}: relation kind {a['kind']!r} (known: {', '.join(RELATION_KINDS)})")
    if op == "recruit":
        if a["type"] not in UNIT_TYPES:
            raise ActionError(f"line {line}: unit type {a['type']!r} (known: {', '.join(UNIT_TYPES)})")
        if a["troops"] <= 0 or a["troops"] % 100:
            raise ActionError(f"line {line}: recruit troops must be a positive multiple of 100")
    return a


def load(path):
    """(header, [actions]) of a script file; raises ActionError on the first bad line."""
    lines = [l for l in Path(path).read_text().splitlines() if l.strip()]
    if not lines:
        raise ActionError("empty script")
    header = json.loads(lines[0])
    if header.get("format") != FORMAT:
        raise ActionError(f"first line must be a header with format {FORMAT!r}")
    return header, [validate(json.loads(l), i + 2) for i, l in enumerate(lines[1:])]


def checkpoint_names(actions):
    """Names of the states both adapters save: 'a000' (start), then one after each action ('a001', ...)."""
    return [f"a{k:03d}" for k in range(len(actions) + 1)]
