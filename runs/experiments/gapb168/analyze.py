#!/usr/bin/env python3
"""Research #168 (gap B): per-army call sequences from the gapb hook logs (patches/gapb_hook.py).

    python3 runs/experiments/gapb168/analyze.py <hooks dir> [<start> ...]

For each F31C army (from its E41C supply entry to the aab4ret record): the calls in order with their call sites and the army's
moves at each entry; sieges with the caller and guards' inputs; and the Q3 comparison: AAB4's result against a per-command
test (did the LAST walk before AAB4 spend moves: moves at that DBA8 entry vs moves at AAB4's entry).
Also the watched armies' moves changes across the round (the mid-round refill).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from state.sav import NATIONS  # noqa: E402

CALLSITE = {"0x44f48a": "F31C 0x44F485 (E84C)", "0x44f4cc": "F31C 0x44F4C7 (city>85 continuation)",
            "0x44f4a8": "F31C 0x44F4A3 (army>70 continuation)", "0x44f40e": "F31C 0x44F409 (army>100)",
            "0x44f444": "F31C 0x44F43F (city>100)", "0x44f481": "F31C 0x44F47C (resupply)", "0x44e918": "E84C 0x44E913 (run)",
            "0x44dc1b": "DBA8 0x44DC16 (line clear, FUN_0044cb40 true)", "0x44dc3f": "DBA8 0x44DC3A (waypoint from DB38)",
            "0x44dc71": "DBA8 0x44DC6C (swing after CEC8)", "0x44d94e": "D734 0x44D949 (end check)",
            "0x44dca6": "DBA8 0x44DCA1 (recursion)", "0x44f4de": "F31C 0x44F4D9 (EBE8)", "0x44d9a0": "D734 0x44D99B (end check)"}


def main():
    root = Path(sys.argv[1])
    starts = sys.argv[2:] or sorted(p.name[:-len("-gapb.jsonl")] for p in root.glob("*-gapb.jsonl"))
    out = {}
    for st in starts:
        rows = [json.loads(l) for l in (root / f"{st}-gapb.jsonl").read_text().splitlines() if l.strip()]
        armies, cur = [], None
        for r in rows:
            k = r["kind"]
            if k == "E41C supply" and r["ret"] == "0x44f36b":
                cur = {"nation": NATIONS[r["nation"]], "army": r["eax"], "at": [r.get("x"), r.get("y")], "moves0": r.get("moves"),
                       "calls": []}
                armies.append(cur)
                continue
            if cur is None or k in ("FA20 seat", "F31C armies"):
                continue
            c = {"seq": r["seq"], "kind": k, "site": CALLSITE.get(r["ret"], r["ret"]), "eax": r["eax"], "moves": r.get("moves")}
            if k in ("DBA8 walk", "D734 line walk"):
                c["target"] = [r["edx"] & 0xFFFF, r["edx"] >> 16]
            if k == "B27C SIEGE":
                c["city"] = r["edx"] & 0xFFFF
            if k == "aab4ret":
                c["aab4"] = r["aab4"]
                cur["calls"].append(c)
                walks = [x for x in cur["calls"] if x["kind"] == "DBA8 walk" and x["site"].startswith("F31C")]
                gate = next((x for x in reversed(cur["calls"]) if x["kind"] == "AAB4 gate"), None)
                last = walks[-1]["moves"] if walks else None
                cur["aab4"] = r["aab4"]
                cur["moves_at_last_f31c_walk"] = last
                cur["moves_at_aab4"] = gate["moves"] if gate else None
                cur["per_command_spent"] = None if last is None or gate is None else gate["moves"] < last
                cur["full_budget_spent"] = r["aab4"] == 1
                cur["predicates_differ"] = cur["per_command_spent"] is not None and cur["per_command_spent"] != cur["full_budget_spent"]
                cur["sieges"] = [x for x in cur["calls"] if x["kind"] == "B27C SIEGE"]
                cur = None
                continue
            cur["calls"].append(c)
        watch, prev = [], None
        for r in rows:
            w = r["watch"]
            if w != prev:
                watch.append({"seq": r["seq"], "seat": NATIONS[r["nation"]], "kind": r["kind"], "moves": w})
                prev = w
        out[st] = {"armies": armies, "watch_changes": watch}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
