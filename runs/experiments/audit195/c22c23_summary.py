#!/usr/bin/env python3
"""#195 C22/C23: summarise the D734 hook logs (patches/d734tail_hook.py via difftest.probes.fleetphase_hook_run,
<start>-d734.jsonl): per tail action (entry, resupply = the F6D8 tail of row C23, siege, attack) and per caller of the
FUN_0044dba8 that called D734 (ret_outer, resolved to the containing function through the decompile's headers).

    python3 runs/experiments/audit195/c22c23_summary.py <hook out dir> > summary.json

D734 entered from its own recursion (ret 0x44D8EA) has the outer D734 frame's return in ret_outer; those rows are counted
under "recursion". Read-only.
"""
import bisect
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import harness.decompile as dec  # noqa: E402

DBA8_SITES = {0x44DC1B: "dba8@0x44DC16", 0x44DC3F: "dba8@0x44DC3A", 0x44DC71: "dba8@0x44DC6C"}
RECURSION = 0x44D8EA


def functions():
    starts = []
    for line in Path(dec.path("all_app_functions.txt")).read_text(errors="replace").splitlines():
        m = re.match(r"// ==== (\S+) @ ([0-9a-fA-F]{8}) ====", line)
        if m:
            starts.append((int(m.group(2), 16), m.group(1)))
    starts.sort()
    return [a for a, _ in starts], [n for _, n in starts]


def main():
    addrs, names = functions()

    def fn(a):
        i = bisect.bisect_right(addrs, a) - 1
        return names[i] if i >= 0 else hex(a)

    counts = collections.Counter()
    examples = collections.defaultdict(list)
    for f in sorted(Path(sys.argv[1]).glob("*-d734.jsonl")):
        for l in f.read_text().splitlines():
            r = json.loads(l)
            ret = r["ret"]
            if ret == RECURSION:
                caller = "recursion"
            elif ret in DBA8_SITES:
                caller = f"{fn(r['ret_outer'])}@{r['ret_outer']:#x}"
            else:
                caller = f"direct:{fn(ret)}@{ret:#x}"
            key = (r["kind"], caller)
            counts[key] += 1
            if len(examples[key]) < 3:
                examples[key].append({"start": f.name.split("-d734")[0], "seq": r["seq"], "nation": r["nation"],
                                      "week": r["week"], **{k: r[k] for k in ("army", "city", "target", "target_army", "army_pos")
                                                              if k in r}})
    out = [{"kind": k, "caller": c, "count": n, "examples": examples[(k, c)]} for (k, c), n in sorted(counts.items())]
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
